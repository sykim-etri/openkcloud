# app/api/routes/metrics.py
import requests
import httpx
from collections import defaultdict
from typing import Dict, List, Any
import re
from pprint import pprint
from app.core.logger import app_logger

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.config import PROMETHEUS_URL, NODE_NAMES, v1_api
from app.utils import parse_gpu_data
from app.db.dependencies import get_db
from kubernetes import client, config
from app.models.gpu import GPUUsage, Flavor, ServerGpuMapping
from app.db.fetch_gpu import query_prometheus, sync_flavors_to_db, sync_gpu_pod_status_from_prometheus
from app.models.k8s import PodCreation
from app.models.user import User
from app.db.session import SessionLocal


router = APIRouter()


async def get_gpu_node_resources(db: Session):
    """Calculate GPU resource usage per node."""
    
    # Query all GPU information from gpu_flavor table
    flavors = db.query(Flavor).all()
    
    # Aggregate by node and GPU type
    gpu_stats = defaultdict(lambda: defaultdict(lambda: {"total": 0, "in_use": 0, "free": 0}))
    
    for flavor in flavors:
        node_name = flavor.worker_node.strip()  # 공백 제거
        gpu_name = flavor.gpu_name
        
        # Increment total count
        gpu_stats[node_name][gpu_name]["total"] += 1
        
        # Check if in use (check server_gpu_mapping table)
        mapping = db.query(ServerGpuMapping).filter(
            ServerGpuMapping.gpu_id == flavor.id
        ).first()
        
        if mapping:
            # Check if server is actually in Running status
            server = db.query(PodCreation).filter(
                PodCreation.id == mapping.server_id,
                PodCreation.status == "Running"
            ).first()
            
            if server:
                gpu_stats[node_name][gpu_name]["in_use"] += 1
        
        # Calculate available count
        gpu_stats[node_name][gpu_name]["free"] = (
            gpu_stats[node_name][gpu_name]["total"] - 
            gpu_stats[node_name][gpu_name]["in_use"]
        )
    
    return gpu_stats


@router.get("/node-resource")
async def get_node_resources(db: Session = Depends(get_db)):
    cpu_total_res = await query_prometheus('kube_node_status_allocatable{resource="cpu", unit="core"}')
    mem_total_res = await query_prometheus('kube_node_status_allocatable{resource="memory", unit="byte"}')
    cpu_used_res = await query_prometheus('sum by(node) (kube_pod_container_resource_limits{resource="cpu", unit="core"})')
    mem_used_res = await query_prometheus('sum by(node) (kube_pod_container_resource_limits{resource="memory", unit="byte"})')

    cpu_total = {item["metric"]["node"]: float(item["value"][1]) for item in cpu_total_res}
    cpu_used = {item["metric"]["node"]: float(item["value"][1]) for item in cpu_used_res}
    mem_total = {item["metric"]["node"]: float(item["value"][1]) / (1024**3) for item in mem_total_res}
    mem_used = {item["metric"]["node"]: float(item["value"][1]) / (1024**3) for item in mem_used_res}

    # Collect GPU information
    gpu_data = await get_gpu_node_resources(db)

    result = []
    for node in NODE_NAMES.split(','):
        node = node.strip()  # Remove whitespace from node name
        c_total = cpu_total.get(node, 0)
        c_used = cpu_used.get(node, 0)
        m_total = mem_total.get(node, 0)
        m_used = mem_used.get(node, 0)

        # Convert GPU information for this node
        node_gpu_list = []
        if node in gpu_data:
            for gpu_name, stats in gpu_data[node].items():
                node_gpu_list.append({
                    gpu_name: {
                        "total": stats["total"],
                        "in_use": stats["in_use"],
                        "free": stats["free"]
                    }
                })

        result.append({
            "node": node,
            "cpu_total": round(c_total, 2),
            "cpu_used": round(c_used, 2),
            "cpu_remaining": round(c_total - c_used, 2),
            "memory_total": round(m_total, 2),
            "memory_used": round(m_used, 2),
            "memory_remaining": round(m_total - m_used, 2),
            "gpu": node_gpu_list
        })

    return {"nodes": result}



@router.get("/gpu-resource")
async def get_gpu_resource(db: Session = Depends(get_db)):
    """Query GPU resource information from DB and return response including actual user and status information"""
    
    node_set = set()
    gpu_data = defaultdict(lambda: defaultdict(list))

    # Query all GPU information from gpu_flavor table
    flavors = db.query(Flavor).all()
    
    for flavor in flavors:
        node_name = flavor.worker_node
        gpu_id = str(flavor.gpu_id)
        
        # Calculate compute value based on MIG presence
        if flavor.mig_id is not None:
            # MIG instance - extract number from flavor name
            compute = int(re.search(r'\d+', flavor.gpu_name)[0]) if re.search(r'\d+', flavor.gpu_name) else 0
        else:
            # Non-MIG GPU
            compute = 0
        
        # Find assigned server through server_gpu_mapping
        mapping = db.query(ServerGpuMapping).filter(
            ServerGpuMapping.gpu_id == flavor.id
        ).first()
        
        if mapping:
            # If server is assigned
            server = db.query(PodCreation).filter(
                PodCreation.id == mapping.server_id
            ).first()
            
            if server:
                # Query user information
                user_obj = db.query(User).filter(User.id == server.user_id).first()
                user = user_obj.name if user_obj else 'Unknown'
                status = 'RUNNING' if server.status == 'Running' else server.status
            else:
                user = 'EMPTY'
                status = 'EMPTY'
        else:
            # Unassigned GPU
            user = 'EMPTY'
            status = 'EMPTY'

        insert_data = {
            'flavor': flavor.gpu_name,
            'compute': compute,
            'user': user,
            'status': status
        }

        node_set.add(node_name)
        gpu_data[node_name][gpu_id].append(insert_data)

    node_list = sorted(list(node_set))

    return {
        'nodeList': node_list,
        'gpuData': gpu_data
    }

@router.post("/update-gpu-resource")
async def update_gpu_resource(db: Session = Depends(get_db)):
    """
    Find GPU pod from k8s api
    Return pod info using GPU and update DB
    """
    pods = v1_api.list_pod_for_all_namespaces(watch=False)

    gpu_pods = []
    for pod in pods.items:
        containers = pod.spec.containers
        for container in containers:
            resources = container.resources
            limits = resources.limits or {}
            # Check for NVIDIA GPU resource requests
            for key, value in limits.items():
                if key.startswith("nvidia.com/") and int(value) > 0:
                    split_pod_name = pod.metadata.name.split('-')
                    if split_pod_name[0] == 'jupyter':
                        user_name = '.'.join(split_pod_name[1:3])
                    elif split_pod_name[0] == 'ailabServer':
                        continue
                    else:
                        user_name = None
                    pod_info = {
                        "pod_name": pod.metadata.name,
                        "namespace": pod.metadata.namespace,
                        "node_name": pod.spec.node_name,
                        "gpu_count": int(value),
                        "container_name": container.name,
                        "gpu_resource_type": key,
                        "user": user_name
                    }
                    gpu_pods.append(pod_info)
    data = await query_prometheus('DCGM_FI_DEV_MIG_MODE')
    for _data in data:
        app_logger.debug(f"Metrics data: {_data}")


    return {"gpu_pods": gpu_pods}
    
@router.post("/sync-gpu-flavors")
async def sync_gpu_flavors():
    await sync_flavors_to_db()  # Synchronize gpu_flavor table
    await sync_gpu_pod_status_from_prometheus()  # Synchronize servers table
    return {"message": "GPU flavors and servers synced successfully"}
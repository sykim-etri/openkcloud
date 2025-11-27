import httpx
from collections import defaultdict
from pprint import pprint
from collections import Counter

from sqlalchemy.orm import Session
from app.models.gpu import Flavor, ServerGpuMapping
from app.db.session import SessionLocal
from app.core.config import PROMETHEUS_URL, v1_api
from app.models.k8s import PodCreation
from app.models.user import User
from app.core.logger import app_logger

url = f"http://{PROMETHEUS_URL}/api/v1/query"

async def query_prometheus(query: str):
    async with httpx.AsyncClient() as client_http:
        response = await client_http.get(url+'?query='+query)
    if response.status_code != 200:
        raise Exception(f"Prometheus query failed: {response.text}")
    result = response.json()
    return result.get("data", {}).get("result", [])

async def fetch_gpu_status_from_prometheus():
    query = 'DCGM_FI_DEV_MIG_MODE'
    data = await query_prometheus(query)
    flavors = dict()
    for item in data:
        metric = item["metric"]
        worker_node = metric.get("Hostname")
        gpu_id = int(metric.get("gpu", 0))
        # MIG instance
        if "GPU_I_PROFILE" in metric:
            gpu_name = metric["GPU_I_PROFILE"]
            mig_id = int(metric.get("GPU_I_ID", None))
        # Non-MIG
        elif "modelName" in metric:
            gpu_name = metric["modelName"].removeprefix("NVIDIA ").strip()
            mig_id = None
        else:
            continue

        if metric.get("exported_pod"):
            flavors[(worker_node, gpu_id, mig_id, gpu_name)] = 1
        else:
            flavors[(worker_node, gpu_id, mig_id, gpu_name)] = 0
    return flavors

async def get_cpu_memory_from_k8s(pod_name, namespace=None):
    """
    Receive pod_name and (optionally) namespace, and return the pod's CPU and memory limits.
    """
    try:
        if namespace is None:
            # set to default if namespace not given
            namespace = "default"
        
        pod = v1_api.read_namespaced_pod(name=pod_name, namespace=namespace)
        container = pod.spec.containers[0]  # assume the first container
        
        limits = container.resources.limits or {}
        cpu = limits.get('cpu', 'N/A')
        memory = limits.get('memory', 'N/A')
        
        return cpu, memory
    except Exception as e:
        app_logger.error(f"Error while fetching CPU/Memory information for Pod {pod_name}: {e}")
        return "N/A", "N/A"

async def get_pod_internal_ip(pod_name, namespace=None):
    """
    Receive pod_name and (optionally) namespace, and return the pod's internal IP.
    """
    try:
        if namespace is None:
            namespace = "default"
        
        pod = v1_api.read_namespaced_pod(name=pod_name, namespace=namespace)
        internal_ip = pod.status.pod_ip
        
        return internal_ip
    except Exception as e:
        app_logger.error(f"Pod {pod_name}의 Internal IP를 가져오는 중 오류: {e}")
        return None

async def sync_flavors_to_db():
    db: Session = SessionLocal()
    try:
        # extract all GPU information from Prometheus
        prometheus_flavors = await fetch_gpu_status_from_prometheus()  # {(worker_node, gpu_id, gpu_name): 0}
        db_flavors = db.query(Flavor).all()
        db_flavor_keys = {(f.worker_node, f.gpu_id, f.gpu_name) for f in db_flavors}
        prometheus_keys = set(prometheus_flavors.keys())
        # Normalize key before upsert and delete
        def normalize_key(worker_node, gpu_id, mig_id, gpu_name):
            # Keep mig_id as is without conversion
            return (
                str(worker_node).strip().lower() if worker_node else "",
                int(gpu_id) if gpu_id is not None else -1,
                mig_id,  # Keep as is without conversion
                str(gpu_name).strip().lower() if gpu_name else ""
            )

        # upsert
        for (worker_node, gpu_id, mig_id, gpu_name), available in prometheus_flavors.items():
            norm_key = normalize_key(worker_node, gpu_id, mig_id, gpu_name)
            flavor = db.query(Flavor).filter(
                Flavor.worker_node == norm_key[0],
                Flavor.gpu_id == norm_key[1],
                Flavor.mig_id == norm_key[2], # Compare mig_id as is
                Flavor.gpu_name == norm_key[3]
            ).first()
            if flavor:
                flavor.available = available
            else:
                db.add(Flavor(
                    worker_node=norm_key[0],
                    gpu_id=norm_key[1],
                    mig_id=norm_key[2], # Store mig_id as is
                    gpu_name=norm_key[3],
                    available=available
                ))

        # delete
        db_flavor_keys = {normalize_key(f.worker_node, f.gpu_id, f.mig_id, f.gpu_name) for f in db_flavors} # Compare mig_id as is
        prometheus_keys = {normalize_key(*k) for k in prometheus_flavors.keys()}

        for flavor in db_flavors:
            norm_key = normalize_key(flavor.worker_node, flavor.gpu_id, flavor.mig_id, flavor.gpu_name) # Compare mig_id as is
            if norm_key not in prometheus_keys:
                db.delete(flavor)
        db.commit()
        app_logger.info(f"Synchronized flavor: {len(prometheus_flavors)}개")
    finally:
        db.close()

def extract_user_name_from_pod(pod_name):
    # 예: jupyter-js-lee---a4b212d2 → js.lee
    if pod_name.startswith("jupyter-"):
        parts = pod_name.split('-')
        if len(parts) >= 3:
            return f"{parts[1]}.{parts[2]}"
    return None

async def sync_gpu_pod_status_from_prometheus():
    db = SessionLocal()
    try:
        data = await query_prometheus('DCGM_FI_DEV_MIG_MODE')
    
        
        # 1. Collect currently running Pod list from Prometheus
        prometheus_pods = set()
        
        # 1. Collect gpu_name occupied by each pod
        pod_gpu_map = defaultdict(list)
        pod_info_map = dict()  # Store additional pod information
        pod_gpu_details = defaultdict(list)  # Store detailed GPU information per pod (worker_node, gpu_id, mig_id, gpu_name)

        for item in data:
            metric = item["metric"]
            exported_pod = metric.get("exported_pod")
            if not exported_pod:
                continue

            prometheus_pods.add(exported_pod)  # Add to currently running Pod list

            # Extract GPU name
   
            if "GPU_I_PROFILE" in metric:
                gpu_name = metric["GPU_I_PROFILE"]
                # Keep None if GPU_I_ID is None
                mig_id_raw = metric.get("GPU_I_ID")
                mig_id = int(mig_id_raw) if mig_id_raw is not None else None
            else:
                gpu_name = metric.get("modelName", "").removeprefix("NVIDIA ").strip()
                mig_id = None

            worker_node = metric.get("Hostname")
            gpu_id = int(metric.get("gpu", 0))

            pod_gpu_map[exported_pod].append(gpu_name)
            pod_gpu_details[exported_pod].append((worker_node, gpu_id, mig_id, gpu_name))
            # Store additional information with last value (can be refined if needed)
            pod_info_map[exported_pod] = metric

        # 2. Query Pod list from DB servers
        db_servers = db.query(PodCreation).all()

        # 3. Find Pods that exist in DB but not in Prometheus (deleted Pods)
        deleted_pods = []
        for server in db_servers:
            if server.pod_name not in prometheus_pods and server.tags != 'LEGEND':
                deleted_pods.append(server)

        # 4. Remove deleted Pods from DB
        for server in deleted_pods:
            # Also delete related GPU mappings
            db.query(ServerGpuMapping).filter(ServerGpuMapping.server_id == server.id).delete()
            db.delete(server)

        # 5. Process currently running Pods (existing logic)
        for pod_name, gpu_names in pod_gpu_map.items():
            app_logger.debug(f"pod_name: {pod_name} gpu_names: {gpu_names}")
            
            gpu_counter = Counter(gpu_names)
            gpu_str_list = []
            for name, count in gpu_counter.items():
                if count > 1:
                    gpu_str_list.append(f"{name} * {count}")
                else:
                    gpu_str_list.append(name)
            gpu_str = ", ".join(gpu_str_list)
            metric = pod_info_map[pod_name]
            
            
            if pod_name.startswith("ailabserver-"):
                server = db.query(PodCreation).filter(PodCreation.pod_name == pod_name).first()
            else:
                # extract user_name and look for user_id
                user_name = extract_user_name_from_pod(pod_name)
                user = db.query(User).filter(User.name == user_name).first()
                if not user:
                    user = db.query(User).filter(User.name == "dev").first()
                user_id = user.id if user else None

                # Get CPU and memory information
                namespace = metric.get("exported_namespace") or metric.get("namespace") or "default"
                cpu, memory = await get_cpu_memory_from_k8s(pod_name, namespace)
                
                # Get internal IP
                internal_ip = await get_pod_internal_ip(pod_name, namespace)
                
                # Determine tags
                if pod_name.startswith("jupyter-"):
                    tags = "JUPYTER"
                elif pod_name.startswith("ailabserver-"):
                    tags = "DASHBOARD"
                else:
                    tags = "DEV"

                # Upsert servers table (only if not LEGEND tag)
                server = db.query(PodCreation).filter(
                    PodCreation.pod_name == pod_name,
                    (PodCreation.tags != 'LEGEND') | (PodCreation.tags.is_(None))
                ).first()
                
                if server:
                    server.gpu = gpu_str
                    server.cpu = cpu
                    server.memory = memory
                    if internal_ip:
                        server.internal_ip = internal_ip
                    server.tags = tags  # Always update tags
                    if server.status != "Running":
                        server.status = "Running"

                else:
                    # Check if server with LEGEND tag already exists
                    existing_legend = db.query(PodCreation).filter(
                        PodCreation.pod_name == pod_name,
                        PodCreation.tags == 'LEGEND'
                    ).first()
                    
                    if not existing_legend:
                        # Create only if not LEGEND and is a new server
                        server = PodCreation(
                            user_id=user_id,
                            server_name=pod_name,
                            pod_name=pod_name,
                            cpu=cpu,
                            memory=memory,
                            gpu=gpu_str,
                            description=None,
                            internal_ip=internal_ip,
                            status="Running",
                            tags=tags
                        )
                        db.add(server)
                        db.flush()  # Flush to get server.id
                        pass  # New server created
                    else:
                        continue  # Skip LEGEND tag server
  
                        
            # Process server-GPU mapping (only if not LEGEND)
            if server:
                # Delete existing mappings
                deleted_count = db.query(ServerGpuMapping).filter(ServerGpuMapping.server_id == server.id).delete()
                
                # Add new mappings
                mapping_count = 0
                for worker_node, gpu_id, mig_id, gpu_name in pod_gpu_details[pod_name]:

                    
                    # Define normalization function externally (to avoid redefining each time)
                    norm_worker_node = str(worker_node).strip().lower() if worker_node else ""
                    norm_gpu_id = int(gpu_id) if gpu_id is not None else -1
                    norm_mig_id = mig_id  # mig_id can be None
                    norm_gpu_name = str(gpu_name).strip().lower() if gpu_name else ""
                    

                    
                    # Find corresponding GPU in gpu_flavor table
                    query = db.query(Flavor).filter(
                        Flavor.worker_node == norm_worker_node,
                        Flavor.gpu_id == norm_gpu_id,
                        Flavor.gpu_name == norm_gpu_name
                    )
                    
                    # Add mig_id condition (including None handling)
                    if norm_mig_id is None:
                        query = query.filter(Flavor.mig_id.is_(None))
                    else:
                        query = query.filter(Flavor.mig_id == norm_mig_id)
                    
                    gpu_flavor = query.first()
                    
                    if gpu_flavor:
                        # Check for duplicates
                        existing_mapping = db.query(ServerGpuMapping).filter(
                            ServerGpuMapping.server_id == server.id,
                            ServerGpuMapping.gpu_id == gpu_flavor.id
                        ).first()
                        
                        if not existing_mapping:
                            # Add mapping
                            mapping = ServerGpuMapping(

                                server_id=server.id,
                                gpu_id=gpu_flavor.id
                            )
                            db.add(mapping)
                            mapping_count += 1


        db.commit()
    except Exception as e:
        app_logger.error(f"Error while executing sync_gpu_pod_status_from_prometheus: {e}")
        db.rollback()
        raise
    finally:
        db.close()

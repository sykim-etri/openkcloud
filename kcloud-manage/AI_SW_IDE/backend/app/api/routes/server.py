import time
import uuid
import re
import requests

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from kubernetes.client.rest import ApiException

from app.db.dependencies import get_db
from app.models.k8s import PodCreation, PVC, pvc_server_association
from app.core.logger import app_logger
from app.models.user import User
from app.models.gpu import ServerGpuMapping, Flavor
from app.schemas.k8s import EntireServerResponse, MyServerResponse, PodCreateRequest, DeleteRequest, PVCDropdownResponse, PVCListResponse, DeletePVCRequest
from app.utils import get_current_user, get_bound_pv_name, delete_pvc, delete_pod, now_kst
from app.core.config import NAMESPACE, v1_api, DATA_OBSERVER_URL

router = APIRouter()

@router.get("/browse")
def browse_files(path: str = "/"):
    """
    Endpoint that receives a path, forwards it to data-observer-service, and returns the result
    """
    try:
        # Construct external service URL
        base_url = f"{DATA_OBSERVER_URL}/browse"
        
        params = {"path": "/"+"/".join(path.split('/')[2:])}
        app_logger.debug(f"Server creation params: {params}")
        
        # Request to external service
        response = requests.get(base_url, params=params, timeout=20)
        response.raise_for_status()
        
        # Check if response is JSON and return
        try:
            return response.json()
        except ValueError:
            # Return as text if not JSON
            return {"data": response.text}
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"External service call failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while browsing files: {str(e)}"
        )

@router.get("/list", response_model=list[EntireServerResponse])
def get_servers(db: Session = Depends(get_db)):
    pods = (
        db.query(PodCreation)
        .all()
    )

    response = []
    for pod in pods:
        # Get GPU mapping information for this server
        gpu_mappings = (
            db.query(ServerGpuMapping, Flavor)
            .join(Flavor, ServerGpuMapping.gpu_id == Flavor.id)
            .filter(ServerGpuMapping.server_id == pod.id)
            .all()
        )
        
        # Generate node information (format: worker_node [gpu_id, mig_id])
        node_info = []
        for mapping, flavor in gpu_mappings:
            if flavor.mig_id is not None:
                node_info.append(f"{flavor.worker_node} [{flavor.gpu_id}, {flavor.mig_id}]")
            else:
                node_info.append(f"{flavor.worker_node} [{flavor.gpu_id}]")
        
        # Use default value if no node information
        if not node_info:
            node_info = ["None"]
        
        response.append(EntireServerResponse(
            userName=pod.user.name,
            gpu=pod.gpu,
            cpuMem=f'{pod.cpu}/{pod.memory}',
            createdAt=pod.request_time,
            status=pod.status,
            node=node_info,
            tags=pod.tags
        ))
    return response
    # return {'data': db.query(PodCreation).all()}

@router.get("/my-server", response_model=list[MyServerResponse])
def get_my_servers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pods = (
        db.query(PodCreation)
        .filter(PodCreation.user_id == current_user.id, PodCreation.tags == 'LEGEND')
        .all()
    )

    response = []
    for pod in pods:
        response.append(MyServerResponse(
            id=pod.id,
            userName=current_user.name,
            serverName=pod.server_name,
            podName=pod.pod_name,
            description=pod.description,
            gpu=pod.gpu,
            cpu=pod.cpu,
            memory=pod.memory,
            createdAt=pod.request_time,
            status=pod.status,
            internal_ip=pod.internal_ip,
            tags=pod.tags
        ))
    return response

@router.get("/my-pvcs", response_model=PVCListResponse)
def get_my_pvcs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return user's PVC list for dropdown"""
    pvcs = (
        db.query(PVC)
        .filter(PVC.user_id == current_user.id)
        .all()
    )

    response = []
    for pvc in pvcs:
        response.append(PVCDropdownResponse(
            id=pvc.id,
            pvc_name=pvc.pvc_name,
            path=pvc.path
        ))
    return PVCListResponse(pvcs=response)

@router.delete("/delete-pvc", status_code=204)
def delete_pvc_endpoint(
    request: DeletePVCRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pvc = db.query(PVC).filter(PVC.pvc_name == request.name, PVC.user_id == current_user.id).first()
    if not pvc:
        raise HTTPException(status_code=404, detail="PVC not found or not authorized")
    delete_pvc(pvc.pvc_name, NAMESPACE, db=db, delete_db=True, delete_pv=request.pv)
    return

@router.delete("/delete-server", status_code=204)
def delete_server(
    request: DeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pod = (
        db.query(PodCreation)
        .filter(PodCreation.pod_name == request.name, PodCreation.user_id == current_user.id)
        .first()
    )
    if not pod:
        raise HTTPException(status_code=404, detail="Server not found or not authorized")

    try:
        # 1. First, set available to 0 for GPUs connected to this server (release GPU)
        gpu_mappings = db.query(ServerGpuMapping).filter(ServerGpuMapping.server_id == pod.id).all()
        for mapping in gpu_mappings:
            gpu_flavor = db.query(Flavor).filter(Flavor.id == mapping.gpu_id).first()
            if gpu_flavor:
                gpu_flavor.available = 0
        db.flush()
        
        # 2. Delete related records from server_gpu_mapping table
        db.query(ServerGpuMapping).filter(ServerGpuMapping.server_id == pod.id).delete()
        db.flush()
        
        pod.pvcs.clear()
        db.flush()

        db.delete(pod)
        db.flush()
            
        delete_pod(pod.pod_name, NAMESPACE, db=db, delete_db=False)
        db.commit()
        # print(f"✅ Pod for server_name={pod.name} successfully deleted in a single transaction.")
    except Exception as e:
        app_logger.error(f"Transaction rollback due to: {e}")
        raise e
    return

@router.post("/create-pod")
def create_pod(
    request: PodCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    gpu_mapping = {
        '2g.20gb': ('nvidia.com/mig-2g.20gb',1),
        '3g.40gb': ('nvidia.com/mig-3g.40gb',1),
        '4g.40gb': ('nvidia.com/mig-4g.40gb',1),
        'A100 80GB': ('nvidia.com/gpu',1),
        'A100 80GB × 2': ('nvidia.com/gpu',2)
    }
    pod_created=False
    existing_pvc = True
    # Generate unique pod name
    name = f"{request.name.replace(' ', '-')}-{uuid.uuid4().hex[:6]}"
    pod_name = f"ailabserver-{name}"
    print(f"request : {request}")

    # Recommended alternative name for the existing pvc variable is `existing_persistent_volume_claim`.
    if request.pvc:
        existing_pvc = False
        pvc_name = f"ailabserver-claim-{name}"

        # Create PVC manifest
        pvc_manifest = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"name": pvc_name},
            "spec": {
                "accessModes": ["ReadWriteMany"],
                "resources": {"requests": {"storage": "1Gi"}},
            }
        }

        try:
            v1_api.create_namespaced_persistent_volume_claim(
                namespace=NAMESPACE,
                body=pvc_manifest
            )
            try:
                pv_name = get_bound_pv_name(pvc_name, NAMESPACE)
                pvc_obj = PVC(
                    user_id=current_user.id,
                    pvc_name=f"{pvc_name}",
                    pv=pv_name,
                    path=f"/nfsvolume/{NAMESPACE}-{pvc_name}-{pv_name}"
                )
                db.add(pvc_obj)
                db.commit()
                db.refresh(pvc_obj)
            except Exception as e:
                delete_pvc(pvc_name, NAMESPACE)
                
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to save PVC to DB: {str(e)}"
                )
        except ApiException as e:
            raise HTTPException(status_code=e.status, detail=f"PVC creation failed: {e.body}")

    else:
        pvc_name = request.pvc_name
        # check db
        pvc_obj = (
            db.query(PVC)
            .filter(PVC.id == request.pvc_id)
            .first()
        )
        if pvc_obj.pvc_name != pvc_name:
            raise HTTPException(status_code=404, detail="PVC not found")
    
    # Create Pod manifest
    cpu = ''.join(re.findall(r'\d+', request.cpu))
    memory = ''.join(re.findall(r'\d+', request.memory)) + 'Gi'
    pod_manifest = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": pod_name,
            "labels": {"app": "my-server"}
        },
        "spec": {
            "containers": [
                {
                    "name": "server-container",
                    "image": request.image,
                    "command": ["bash", "-lc"],
                    "args": [
                        "jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --ServerApp.token='' --ServerApp.root_dir=/home/jovyan/workspace"
                    ],
                    "ports": [{"containerPort": 8888}],
                    "volumeMounts": [
                        {"mountPath": f"/home/jovyan/workspace", "name": "storage-volume"},
                        {"mountPath": "/home/share", "name": "shared-volume"}
                    ],
                    "resources": {
                        "limits": {
                            "cpu": cpu,
                            "memory": memory
                        }
                    },
                }
            ],
            "imagePullSecrets": [
              {"name": "harbor-secret"}  
            ],
            "volumes": [
                {"name": "storage-volume", "persistentVolumeClaim": {"claimName": pvc_name}},
                {"name": "shared-volume", "persistentVolumeClaim": {"claimName": "ailabserver-claim-shared-<hashed>"}}
            ],
            "restartPolicy": "Never"
        }
    }
    if request.gpu!='None':
        gpu_name, gpu_cnt = gpu_mapping[request.gpu]
        pod_manifest['spec']['containers'][0]['resources']['limits'][gpu_name] = gpu_cnt
    try:

        v1_api.create_namespaced_pod(
            namespace=NAMESPACE,
            body=pod_manifest
        )
        
        # Save Pod creation record to DB
        pod_record = PodCreation(
            user_id=current_user.id,
            description=request.description,
            # server_name=pod_name,
            server_name=request.name,
            pod_name=pod_name,
            cpu=request.cpu,
            memory=request.memory,
            gpu=request.gpu,
            request_time=now_kst(),
            internal_ip='',
            status='Creating',
            tags='LEGEND' 
        )
        
        pod_created = True

        db.add(pod_record)
        db.commit()
        db.refresh(pod_record)
        
        timeout = 180
        start_time = time.time()
        internal_ip = None
        while time.time() - start_time < timeout:
            pod_status = v1_api.read_namespaced_pod(name=pod_name, namespace=NAMESPACE)
            internal_ip = pod_status.status.pod_ip
            if internal_ip:
                break
            time.sleep(2)

        if not internal_ip:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Pod did not receive an internal IP within timeout period"
            )
        pod_record.internal_ip = internal_ip
        pod_record.status="Running"
        pod_record.pvcs.append(pvc_obj)
        db.commit()
        db.refresh(pod_record)
    except ApiException as e:
        print(f"Pod creation failed: {e.body}")
        raise HTTPException(status_code=e.status, detail=f"Pod creation failed: {e.body}") 
    except Exception as e:
        if pod_created:
            delete_pod(pod_name, NAMESPACE, db=db, delete_db=True)
        if not existing_pvc:
            delete_pvc(pvc_name, NAMESPACE, db=db, delete_db=True)
        raise e

    return {"detail": "Success!"}
    
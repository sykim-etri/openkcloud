from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from kubernetes.client.rest import ApiException

from app.schemas.k8s import PVCResponse, DeleteRequest, NFSPVCCreateRequest
from app.models.k8s import PVC
from app.core.logger import app_logger
from app.models.user import User

from app.utils import get_current_user, delete_pvc, now_kst
from app.db.dependencies import get_db
from app.core.config import NAMESPACE, v1_api


router = APIRouter()

@router.post("/create-nfs-storage")
async def create_nfs_storage(
    request: NFSPVCCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Receive NFS path, create PV and PVC, and add to DB"""
    
    # Generate unique PV and PVC names
    unique_id = uuid.uuid4().hex[:8]
    pv_name = f"ailabserver-pv-{request.pvc_name}-{unique_id}"
    pvc_name = f"ailabserver-claim-{request.pvc_name}-{unique_id}"
    
    try:
        # Create PV manifest (NFS)
        pv_manifest = {
            "apiVersion": "v1",
            "kind": "PersistentVolume",
            "metadata": {
                "name": pv_name,
                "labels": {
                    "type": "nfs",
                    "pv": pv_name
                }
            },
            "spec": {
                # "storageClassName": "",
                "capacity": {
                    "storage": request.storage_size
                },
                "accessModes": ["ReadWriteMany"],
                "persistentVolumeReclaimPolicy": "Retain",
                "nfs": {
                    "server": request.nfs_server,
                    "path": request.nfs_path
                }
            }
        }
        
        # Create PVC manifest
        pvc_manifest = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim", 
            "metadata": {
                "name": pvc_name,
                "namespace": NAMESPACE
            },
            "spec": {
                "storageClassName": "",
                "accessModes": ["ReadWriteMany"],
                "resources": {
                    "requests": {
                        "storage": request.storage_size
                    }
                },
                "selector": {
                    "matchLabels": {
                        "type": "nfs",
                        "pv": pv_name
                    }
                }
            }
        }
        
        # Create PV
        v1_api.create_persistent_volume(body=pv_manifest)
        
        # Create PVC
        v1_api.create_namespaced_persistent_volume_claim(
            namespace=NAMESPACE,
            body=pvc_manifest
        )
        
        # Save PVC information to DB
        pvc_obj = PVC(
            user_id=current_user.id,
            pvc_name=pvc_name,
            pv=pv_name,
            path=request.nfs_path,
            created_at=now_kst()
        )
        
        db.add(pvc_obj)
        db.commit()
        db.refresh(pvc_obj)
        
        return {
            "message": "NFS PV/PVC created successfully",
            "pv_name": pv_name,
            "pvc_name": pvc_name,
            "nfs_path": request.nfs_path,
            "pvc_id": pvc_obj.id
        }
        
    except ApiException as e:
        # Cleanup on creation failure
        try:
            v1_api.delete_namespaced_persistent_volume_claim(name=pvc_name, namespace=NAMESPACE)
            v1_api.delete_persistent_volume(name=pv_name)
        except:
            pass
        raise HTTPException(
            status_code=e.status,
            detail=f"Kubernetes PV/PVC 생성 실패: {e.body}"
        )
    except Exception as e:
        # Cleanup on creation failure
        try:
            v1_api.delete_namespaced_persistent_volume_claim(name=pvc_name, namespace=NAMESPACE)
            v1_api.delete_persistent_volume(name=pv_name)
        except:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while creating NFS storage: {str(e)}"
        )

@router.get("/storage-list", response_model=List[PVCResponse])
async def get_storage_list(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    pvcs = db.query(PVC).filter(PVC.user_id == current_user.id).all()
    return pvcs

@router.delete("/storage", status_code=204)
async def delete_storage_by_name(
    request: DeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pvc_name = request.name

    pvc = db.query(PVC).filter(PVC.pvc_name == pvc_name, PVC.user_id == current_user.id).first()
    if not pvc:
        raise HTTPException(status_code=404, detail="PVC not found or not authorized")

    try:
        delete_pvc(
            pvc_name=pvc.pvc_name,
            namespace=NAMESPACE,
            db=db,
            delete_db=True,
            delete_pv=True
        )
        return
    except Exception as e:
        app_logger.error(f"PVC deletion failed: {e}")
        raise HTTPException(status_code=500, detail="PVC deletion failed")

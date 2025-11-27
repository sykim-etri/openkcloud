import time

from kubernetes.client.rest import ApiException
from sqlalchemy.orm import Session

from app.models.k8s import PVC, PodCreation
from app.core.logger import app_logger
from app.core.config import v1_api


def get_bound_pv_name(pvc_name: str, namespace: str, timeout: int = 30):
    for _ in range(timeout):
        pvc = v1_api.read_namespaced_persistent_volume_claim(name=pvc_name, namespace=namespace)
        if pvc.status.phase == "Bound":
            return pvc.spec.volume_name
        time.sleep(1)
    return None 
  
def delete_pvc(pvc_name: str, namespace: str, db: Session = None, delete_db: bool = False, delete_pv: bool = True):
    if delete_pv:
        try:
            bound_pv_name = get_bound_pv_name(pvc_name, namespace)
            if bound_pv_name:
                app_logger.info(f"Found bound PV: {bound_pv_name}")
            else:
                app_logger.warning(f"No bound PV found for PVC '{pvc_name}'")
        except Exception as e:
            app_logger.error(f"Failed to get bound PV name: {e}")

    try:
        v1_api.delete_namespaced_persistent_volume_claim(
            name=pvc_name,
            namespace=namespace
        )
        app_logger.info(f"PVC '{pvc_name}' deleted from Kubernetes")
    except ApiException as e:
        app_logger.error(f"Failed to delete PVC from Kubernetes: {e}")

    if delete_pv and bound_pv_name:
        try:
            v1_api.delete_persistent_volume(name=bound_pv_name)
            app_logger.info(f"PV '{bound_pv_name}' deleted from Kubernetes")
        except ApiException as e:
            app_logger.error(f"Failed to delete PV '{bound_pv_name}': {e}")

    if delete_db and db is not None:
        try:
            pvc_record = db.query(PVC).filter(PVC.pvc_name == pvc_name).first()
            if pvc_record:
                db.delete(pvc_record)
                db.commit()
                app_logger.info(f"PVC record '{pvc_name}' successfully deleted from DB")
            else:
                app_logger.warning(f"No PVC record found in DB with name: {pvc_name}")
        except Exception as e:
            app_logger.error(f"Error while deleting PVC from DB: {e}")
            
def delete_pod(pod_name: str, namespace: str, db: Session = None, delete_db: bool = False):
    try:
        v1_api.delete_namespaced_pod(
            name=pod_name,
            namespace=namespace
        )
        app_logger.info(f"Pod '{pod_name}' deleted from Kubernetes")
    except ApiException as e:
        app_logger.error(f"Failed to delete Pod from Kubernetes: {e}")

    if delete_db and db is not None:
        try:
            pod_record = db.query(PodCreation).filter(PodCreation.server_name == pod_name).first()
            if pod_record:
                db.delete(pod_record)
                db.commit()
                app_logger.info(f"Pod record '{pod_name}' deleted from DB")
            else:
                app_logger.warning(f"No Pod record found in DB with name: {pod_name}")
        except Exception as e:
            app_logger.error(f"Error while deleting Pod from DB: {e}")
            

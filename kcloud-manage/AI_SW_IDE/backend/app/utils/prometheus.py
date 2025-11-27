from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.k8s import PodCreation


def parse_gpu_data(raw_data: list[dict], db: Session):
    pod_names = [item["exported_pod"] for item in raw_data if item["exported_pod"]]
    print(raw_data)
    print(pod_names)
    pod_user_map = {
        pod.pod_name: pod.user.name for pod in db.query(PodCreation).filter(PodCreation.pod_name.in_(pod_names)).all()
    }
    print(pod_user_map)

    result = defaultdict(lambda: defaultdict(list))

    for item in raw_data:
        node = item["nodeName"]
        gpu_id = int(item["gpuId"])
        flavor = item["gpu"]
        is_mig = item["isMIG"]
        mig_id = item["migId"]

        pod_name = item["exported_pod"]
        user = "None" or pod_user_map.get(pod_name, "Unknown")

        slot_info = {
            "flavor": flavor,
            "compute": 0 if not is_mig else int(flavor[0]),  # 예: 2g.20gb → 2
            "user": user,
            "status": "RUNNING" if pod_name else "EMPTY"
        }

        # For MIG: allocate by MIG slice; otherwise; allocate entier GPU
        if is_mig:
            result[node][gpu_id].append(slot_info)
        else:
            result[node][gpu_id] = [slot_info]  # non-MIG: single slot

    return result

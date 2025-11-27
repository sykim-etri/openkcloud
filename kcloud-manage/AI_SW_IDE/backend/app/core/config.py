import os

from kubernetes import client, config
from dotenv import load_dotenv


load_dotenv(dotenv_path='./prod.env')
try:
    config.load_incluster_config()
    pass  # Successfully loaded in-cluster configuration
except Exception as e:
    pass  # Fallback to local configuration
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    api_server_url = f'https://{os.getenv("MASTER_SERVER")}:6443'
    bearer_token = os.getenv("K8S_BEARER_TOKEN")

    configuration = client.Configuration()
    configuration.host = api_server_url
    configuration.verify_ssl = False
    configuration.api_key = {"authorization": f"Bearer {bearer_token}"}

    client.Configuration.set_default(configuration)
    
    
v1_api = client.CoreV1Api()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://<DB_USER>:<DB_PASSWORD>@<DB_HOST>:<DB_PORT>/<DB_NAME>")
SECRET_KEY = os.getenv("SECRET_KEY", "<YOUR_SECRET_KEY>")
ALGORITHM = os.getenv("SECRET_ALGORITHM", "HS256")
NAMESPACE = os.getenv("NAMESPACE", "gpu-dashboard")
PROMETHEUS_URL = os.getenv("PROMETHEUS_ADDRESS", "<YOUR_PROMETHEUS_ADDRESS>")
NODE_NAMES = os.getenv("NODE_NAMES", "")
DATA_OBSERVER_URL = os.getenv("DATA_OBSERVER_URL", "http://data-observer-service.gpu-dashboard.svc.cluster.local:8000")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:4000,http://127.0.0.1:4000").split(",")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
GPU_FETCH = int(os.getenv("GPU_FETCH", "30"))
NFS_ADDRESS = os.getenv("NFS_ADDRESS", "<YOUR_NFS_SERVER_IP>")
# AI Software IDE Helm Chart

This Helm chart deploys the AI SOFTWARE IDE application to a Kubernetes cluster.

## Components 

- **Backend**: FastAPI-based backend API server
- **Frontend**: React-based frontend web application  
- **Data Observer**: NFS volume data monitoring service
- **PostgreSQL**: Database (using Bitnami chart)

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2.0+
- PV Provisioner (for persistent volumes)
- NFS Server (for Data Observer)

## Environment-specific Configuration

AI SOFTWARE IDE centrally manages environment-specific settings in the `global.environment` section.

### Key Environment Settings

```yaml
global:
  environment:
    # NFS server configuration
    nfs:
      address: "<YOUR_NFS_SERVER_IP>"
    
    # Kubernetes worker node names
    nodes:
      workers: "<YOUR_WORKER_NODE_NAMES>(comma-separated: e.g. k8s-worker-1,k8s-worker-2)"
    
    # Exterenal service URLs
    services:
      prometheus: "<YOUR_PROMETHEUS_ADDRESS>"
      redis: "redis://<YOUR_REDIS_HOST>:6379/0"
    
    # CORS configuration
    cors:
      origins: "http://gpu-dashboard-frontend.gpu-dashboard.svc.cluster.local:4000,http://localhost:4000,http://127.0.0.1:4000"
    
    # Application settings
    app:
      logLevel: "INFO"
      gpuFetchInterval: "30"
      secretAlgorithm: "HS256"
      secretKey: "<YOUR_SECRET_KEY>"
```

### How to Change Environment-specific Settings

1. **Edit values.yaml directly**
   ```bash
   vi values.yaml
   # Edit global.environment section
   ```

2. **Override during Helm install**
   ```bash
   helm install gpu-dashboard . \
     --set global.environment.nfs.address="<YOUR_NFS_SERVER_IP> \
     --set global.environment.nodes.workers="<YOUR_WORKER_NODE_NAMES>"
   ```

3. **Use separate values file**
   ```bash
   # Create production-values.yaml 
   echo "
   global:
     environment:
       nfs:
         address: 'prod-nfs-server.company.com'
       nodes:
         workers: 'prod-worker-1,prod-worker-2,prod-worker-3'
   " > production-values.yaml
   
   helm install gpu-dashboard . -f production-values.yaml
   ```

## Quick Start

### 1. Navigate to this folder
```bash
cd helm-chart
```

### 2. One-click deployment
```bash
./quick-start.sh
```

**AI SOFTWARE IDE Deployment Tool** provides the following features:
- 🔍 **Environment Validation**: Check kubectl, helm installation and cluster access
- 🏷️  **Namespace Management**: Automatic detection and creation
- 📦 **Dependency Resolution**: Automatic handling of Helm repositories and chart dependencies
- 🚀 **One-click Deployment**: Fully automated deployment with progress display
- 📊 **Status Verification**: Real-time checking of all Pod statuses after deployment
- 📋 **Access Information**: Automatic generation of service access URLs and management commands

## Manual Installation

### 1. Add Helm repository
```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

### 2. Update dependencies
```bash
helm dependency update
```

### 3. Install
```bash
helm install gpu-dashboard . -n gpu-dashboard --create-namespace
```

### 4. Install with custom values
```bash
helm install gpu-dashboard . -n gpu-dashboard --create-namespace -f custom-values.yaml
```

## Configuration

### Key Configuration Values

```yaml
# Global settings
global:
  imageRegistry: ""
  namespace: gpu-dashboard

# Backend settings
backend:
  enabled: true
  image:
    repository: gpu-dashboard/backend
    tag: "latest"
  service:
    type: NodePort
    port: 8000
    nodePort: 30800
  env:
    - name: DATABASE_URL
      value: "postgresql://<DB_USER>:<DB_PASSWORD>@gpu-dashboard-postgresql:5432/gpu_dashboard"

# Frontend settings
frontend:
  enabled: true
  image:
    repository: gpu-dashboard/frontend
    tag: "latest"
  service:
    type: NodePort
    port: 80
    nodePort: 30080
  ingress:
    enabled: false

# Data Observer settings
data-observer:
  enabled: true
  image:
    repository: gpu-dashboard/data-observer
    tag: "latest"
  nfs:
    enabled: true
    server: "your-nfs-server.example.com"
    path: "/path/to/nfs/share"

# PostgreSQL settings
postgresql:
  enabled: true
  auth:
    database: "gpu_dashboard"
    username: "<DB_USER>"
    password: "<DB_PASSWORD>"
```

### NFS Configuration

To use NFS volumes with Data Observer::

```yaml
data-observer:
  nfs:
    enabled: true
    server: "<YOUR_NFS_SERVER_IP>"  # NFS server IP
    path: "/mnt/nfs/data"    # NFS share path
    mountPath: "/nfsvolume"  # Mount path inside container
```

### NodePort Access


Frontend and Backend are configured as NodePort services, allowing direct access from outside the cluster:

```bash
# Check node IP 
export NODE_IP=$(kubectl get nodes -o jsonpath="{.items[0].status.addresses[0].address}")

# 서비스 접근
echo "Frontend: http://$NODE_IP:30080"
echo "Backend API: http://$NODE_IP:30800/docs"
```

### Ingress Configuration (Optional)

You can enable Ingress if needed:

```yaml
frontend:
  ingress:
    enabled: true
    className: "nginx"
    annotations:
      nginx.ingress.kubernetes.io/rewrite-target: /
    hosts:
      - host: gpu-dashboard.yourdomain.com
        paths:
          - path: /
            pathType: Prefix
```

## Upgrade

```bash
helm upgrade gpu-dashboard . -n gpu-dashboard
```

## Removal

```bash
helm uninstall gpu-dashboard -n gpu-dashboard
```

## Troubleshooting

### 1. Check Pod Status
```bash
kubectl get pods -n gpu-dashboard
```

### 2. Check Logs
```bash
kubectl logs -n gpu-dashboard deployment/gpu-dashboard-backend
kubectl logs -n gpu-dashboard deployment/gpu-dashboard-frontend  
kubectl logs -n gpu-dashboard deployment/gpu-dashboard-data-observer
```

### 3. Check Services
```bash
kubectl get svc -n gpu-dashboard
```

### 4. Check Ingress
```bash
kubectl get ingress -n gpu-dashboard
```

## Development

### Service Accecss Methods

#### Direct Access via NodePort (Recommended)
```bash
# Check node IP 
export NODE_IP=$(kubectl get nodes -o jsonpath="{.items[0].status.addresses[0].address}")

# Access services
echo "Frontend: http://$NODE_IP:30080"
echo "Backend API: http://$NODE_IP:30800/docs"
```

#### Access via Port Forwarding
```bash
# Backend API
kubectl port-forward -n gpu-dashboard svc/gpu-dashboard-backend 8000:8000

# Frontend
kubectl port-forward -n gpu-dashboard svc/gpu-dashboard-frontend 8080:80

# Data Observer  
kubectl port-forward -n gpu-dashboard svc/gpu-dashboard-data-observer 8001:8000

# PostgreSQL
kubectl port-forward -n gpu-dashboard svc/gpu-dashboard-postgresql 5432:5432
```

## Folder Structure

```
helm-chart/
├── Chart.yaml              # Chart metadata
├── values.yaml             # Default configuration values
├── templates/              # Main templates
│   ├── _helpers.tpl        # Helper functions
│   └── NOTES.txt          # Post-installation notes
├── charts/                 # Subcharts
│   ├── backend/           # Backend subchart
│   ├── frontend/          # Frontend subchart
│   └── data-observer/     # Data Observer subchart
├── README.md              # This file
├── install-guide.md       # Detailed installation guide
└── quick-start.sh         # Quick installation script
```

## License

This project follows the Apache2.0 license.



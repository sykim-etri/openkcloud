# AI Software IDE Helm Chart Installation Guide

## 1. Prerequisites

### Kubernetes Cluster
- Kubernetes 1.19 or higher
- kubectl installed and cluster access configured
- Helm 3.2.0 or higher installed

### Required Resources
- Storage Class (for PostgreSQL)
- NFS Server (for Data Observer)
- Ingress Controller (optional)

## 2. Installation Steps

### 2.1. Navigate to helm-chart Directory
```bash
cd helm-chart
```

### 2.2. Add Helm Repository
```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

### 2.3. Namespace Configuration
The quick-start.sh script automatically checks and creates the namespace configured in values.yaml.

To manually create a namespace:
```bash
# Check namespace configured in values.yaml
grep "namespace:" values.yaml

# Manual creation (optional)
kubectl create namespace helm-test
```

### 2.4. Create Custom Values File (Optional)
```bash
cp values.yaml custom-values.yaml
```

Edit `custom-values.yaml` to match your environment:
```yaml
# Modify NFS server information
data-observer:
  nfs:
    server: "YOUR_NFS_SERVER_IP"
    path: "/path/to/your/nfs/share"

# Modify domain information
frontend:
  ingress:
    hosts:
      - host: gpu-dashboard.yourdomain.com

# Change database password
postgresql:
  auth:
    postgresPassword: "your-secure-password"
    password: "your-secure-password"

# Modify image tags (if needed)
backend:
  image:
    tag: "v1.0.0"
frontend:
  image:
    tag: "v1.0.0"
data-observer:
  image:
    tag: "v1.0.0"
```

### 2.5. Update Dependencies
```bash
helm dependency update
```

### 2.6. Install Chart

#### One-Click Deployment (Recommended)
```bash
./quick-start.sh
```

**AI Software IDE Deployment Tool** provides a production-grade deployment environment:
- Real-time progress tracking
- Automatic environment validation and error handling
- Post-deployment status check and access information

#### Manual Installation
```bash
# Install with default configuration
helm install gpu-dashboard . -n gpu-dashboard

# Or install with custom configuration
helm install gpu-dashboard . -n gpu-dashboard -f custom-values.yaml
```

## 3. Verify Installation

### 3.1. Check Pod Status
```bash
kubectl get pods -n gpu-dashboard
```

Wait until all Pods are in `Running` state.

### 3.2. Check Services
```bash
kubectl get svc -n gpu-dashboard
```

### 3.3. Check Ingress (if enabled)
```bash
kubectl get ingress -n gpu-dashboard
```

## 4. Access Methods

### 4.1. Direct Access via NodePort (Recommended)
```bash
# Get node IP
export NODE_IP=$(kubectl get nodes -o jsonpath="{.items[0].status.addresses[0].address}")

# Access Frontend
echo "Frontend URL: http://$NODE_IP:30080"

# Access Backend API
echo "Backend API URL: http://$NODE_IP:30800/docs"
```

### 4.2. Access via Port Forwarding (Optional)
```bash
# Access Frontend
kubectl port-forward -n gpu-dashboard svc/gpu-dashboard-frontend 8080:80
# Access at http://localhost:8080

# Access Backend API
kubectl port-forward -n gpu-dashboard svc/gpu-dashboard-backend 8000:8000
# View API documentation at http://localhost:8000/docs
```

### 4.3. Access Data Observer API
```bash
kubectl port-forward -n gpu-dashboard svc/gpu-dashboard-data-observer 8001:8000
# View API documentation at http://localhost:8001/docs
```

## 5. Upgrade
```bash
# Run from helm-chart directory
helm upgrade gpu-dashboard . -n gpu-dashboard -f custom-values.yaml
```

## 6. Uninstall
```bash
helm uninstall gpu-dashboard -n gpu-dashboard
kubectl delete namespace gpu-dashboard
```

## 7. Troubleshooting

### 7.1. Pods in Pending State
```bash
kubectl describe pod <pod-name> -n gpu-dashboard
```

Common causes:
- Missing storage class
- Insufficient resources
- NFS server inaccessible

### 7.2. NFS Mount Failure
Check Data Observer Pod logs:
```bash
kubectl logs -n gpu-dashboard deployment/gpu-dashboard-data-observer
```

Verify NFS server configuration:
- Confirm NFS server is running
- Check firewall settings (ports 2049, 111)
- Ensure proper permissions in exports file

### 7.3. Database Connection Failure
Check Backend Pod logs:
```bash
kubectl logs -n gpu-dashboard deployment/gpu-dashboard-backend
```

Check PostgreSQL service status:
```bash
kubectl get pods -n gpu-dashboard -l app.kubernetes.io/name=postgresql
```

## 8. Monitoring

### 8.1. Check Resource Usage
```bash
kubectl top pods -n gpu-dashboard
kubectl top nodes
```

### 8.2. Check Events
```bash
kubectl get events -n gpu-dashboard --sort-by='.lastTimestamp'
```

## 9. Backup and Restore

### 9.1. Database Backup
```bash
kubectl exec -n gpu-dashboard deployment/gpu-dashboard-postgresql -- pg_dump -U postgres gpu_dashboard > backup.sql
```

### 9.2. Configuration Backup
```bash
helm get values gpu-dashboard -n gpu-dashboard > values-backup.yaml
```

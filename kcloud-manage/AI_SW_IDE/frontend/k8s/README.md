# AI SOFTWARE IDE Frontend - Kubernetes Deployment

This directory contains manifest files for deploying AI SOFTWARE IDE Frontend to Kubernetes.

## Key Changes

### ConfigMap-separated Configuration
- **API_URL**: Backend API server URL
- **nginx.conf**: Nginx configuration file

### Runtime Environment Variable Injection
- Environment variables can be changed after build
- Use `config.js.template` to inject environment variables at runtime

## File Structure

```
k8s/
├── configmap.yaml      # ConfigMap configuration
├── deployment.yaml     # Deployment configuration
├── service.yaml        # Service configuration (ClusterIP + NodePort)
├── kustomization.yaml  # Kustomize configuration
└── README.md          # This file
```

## Deployment Methods

### 1. Manual Deployment

```bash
# Create namespace
kubectl create namespace monitoring

# Deploy all resources
kubectl apply -k k8s/

# Check deployment status
kubectl rollout status deployment/gpu-dashboard-frontend -n monitoring
```

### 2. Deployment Using Script

```bash
# Use local image
./scripts/build-and-deploy.sh

# Use specific tag and registry
./scripts/build-and-deploy.sh v1.0.0 your-registry.com
```

## Configuration Changes

### Change API URL
```bash
kubectl patch configmap gpu-dashboard-frontend-config -n monitoring \
  --patch '{"data":{"API_URL":"http://new-api-url:8000"}}'

# Restart Pod to apply changes
kubectl rollout restart deployment/gpu-dashboard-frontend -n monitoring
```

### Change Nginx Configuration
```bash
kubectl edit configmap gpu-dashboard-frontend-config -n monitoring
# Modify nginx.conf section and save

# Restart Pod
kubectl rollout restart deployment/gpu-dashboard-frontend -n monitoring
```

## Access Methods

### Access from Within Cluster
```
http://gpu-dashboard-frontend-svc.monitoring.svc.cluster.local
```

### External Access
```
http://<NODE_IP>:30080
```

## Monitoring

### Check Pod Status
```bash
kubectl get pods -n monitoring -l app=gpu-dashboard-frontend
```

### Check Logs
```bash
kubectl logs -f deployment/gpu-dashboard-frontend -n monitoring
```

### Check Service Status
```bash
kubectl get svc -n monitoring | grep gpu-dashboard-frontend
```

## Troubleshooting

### 1. Pod Not Starting
```bash
kubectl describe pod <pod-name> -n monitoring
kubectl logs <pod-name> -n monitoring
```

### 2. Environment Variables Not Injected Properly
```bash
# Check environment variables inside Pod
kubectl exec -it <pod-name> -n monitoring -- env | grep API_URL

# Check config.js file
kubectl exec -it <pod-name> -n monitoring -- cat /usr/share/nginx/html/config.js
```

### 3. Backend Connection Issues
- Check if API_URL in ConfigMap is correct
- Check if backend service is running
- Check if network policies are blocking communication

## Resource Cleanup

```bash
# Delete all resources
kubectl delete -k k8s/

# Or delete individually
kubectl delete deployment gpu-dashboard-frontend -n monitoring
kubectl delete service gpu-dashboard-frontend-svc gpu-dashboard-frontend-nodeport -n monitoring
kubectl delete configmap gpu-dashboard-frontend-config -n monitoring
```
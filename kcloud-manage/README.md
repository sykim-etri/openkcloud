# kcloud-manage

## Modules

### AI_SW_IDE

**GPU Resource Management & Development Environment Platform**

AI_SW_IDE is a Kubernetes-native platform that provides GPU resource monitoring, allocation, and user-initiated development environment provisioning.

#### Core Concept

- **Purpose**: Self-service GPU resource management and user-initiated development environment provisioning in Kubernetes clusters
- **Target Environment**: Kubernetes clusters with GPU nodes
- **Primary Use Case**: AI/ML researchers and developers who need on-demand GPU-accelerated development environments (Jupyter Lab)

#### Key Characteristics

1. **GPU Resource Management**
   - Real-time GPU monitoring 
   - Node resource monitoring (CPU,memoryu) from Prometheus
   - User-selected GPU allocation (MIG and full GPU support)
   - Resource availability tracking

2. **User-Initiated Development Environment Provisioning**
   - Kubernetes Pod-based development environment server creation (containerized IDE: Jupyter Lab)
   - Resource selection from predefined options (CPU, Memory, GPU)
   - Custom container image and command configuration
   - Manual environment deletion with resource reclamation

3. **Multi-Tenant Resource Isolation**
   - Per-user resource ownership and access control
   - JWT-based authentication and authorization

4. **Storage Management Integration**
   - PersistentVolumeClaim (PVC) creation and deletion
   - NFS volume mounting and file system browsing

5. **Kubernetes-Native Architecture**
   - Direct Kubernetes API integration for resource management
   - Helm-based deployment with subchart architecture
   - Prometheus metrics integration for monitoring

#### Operational Scope

- **Resource Types**: GPU nodes, Kubernetes Pods, PersistentVolumes
- **Monitoring**: GPU utilization, node resources, pod status
- **Provisioning**: User-initiated creation of containerized development environment servers with GPU acceleration (configurable IDE/editor)
- **Storage**: NFS and PVC-based persistent storage

  

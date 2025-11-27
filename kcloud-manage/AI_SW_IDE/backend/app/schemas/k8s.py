from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.core.config import NFS_ADDRESS

class PodCreateRequest(BaseModel):
    image: str  
    cpu: str
    memory: str
    gpu: str
    name: str
    description: Optional[str] = None
    pvc: bool
    pvc_id: Optional[int] = None
    pvc_name: Optional[str] = None

class NFSPVCCreateRequest(BaseModel):
    nfs_path: str
    pvc_name: str
    nfs_server: Optional[str] = NFS_ADDRESS  # default NFS server
    storage_size: Optional[str] = "10Gi"  # default storage size


class EntireServerResponse(BaseModel):
    userName: str
    gpu: str
    cpuMem: str
    createdAt: datetime
    status: str
    node: Optional[List[str]] = []
    tags: Optional[str] = None

    class Config:
        from_attributes = True
        

class MyServerResponse(BaseModel):
    id: int
    userName: str
    serverName: str
    podName: str
    description: Optional[str]
    cpu: str
    memory: str
    gpu: str
    createdAt: datetime
    status: str
    internal_ip: Optional[str] = None
    tags: Optional[str] = None

    class Config:
        from_attributes = True
        
class DeleteRequest(BaseModel):
    name: str


class DeletePVCRequest(BaseModel):
    name: str
    pv: Optional[bool] = False
    

class PVCResponse(BaseModel):
    pvc_name: str
    pv: str
    path: str
    created_at: datetime

    class Config:
        from_attributes = True

class PVCDropdownResponse(BaseModel):
    id: int
    pvc_name: str
    path: str
    
    class Config:
        from_attributes = True

class PVCListResponse(BaseModel):
    pvcs: list[PVCDropdownResponse]

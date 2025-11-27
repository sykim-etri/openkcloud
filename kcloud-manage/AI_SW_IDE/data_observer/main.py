import os
import stat
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel


app = FastAPI(
    title="Data Observer API",
    description="API for monitoring data status of NFS volumes",
    version="1.0.0"
)

# NFS volume mount point
NFS_ROOT = os.getenv("NFS_ROOT", "/home/jovyan")

class FileInfo(BaseModel):
    name: str
    type: str  # 'file' or 'directory'
    extension: Optional[str] = None  # File extension (None for directories)
    size: int  # bytes
    size_human: str  # human readable size
    modified: datetime
    permissions: str

class DirectoryResponse(BaseModel):
    path: str
    total_items: int
    total_size: int
    total_size_human: str
    items: List[FileInfo]

def get_human_readable_size(size_bytes: int) -> str:
    """Convert bytes to human-readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def get_file_info(file_path: Path, calculate_dir_size: bool = False) -> FileInfo:
    """Get file/directory information"""
    try:
        stat_info = file_path.stat()
        
        # Determine file type
        file_type = "directory" if file_path.is_dir() else "file"
        
        # Calculate size
        if file_type == "file":
            size = stat_info.st_size
        elif file_type == "directory" and calculate_dir_size:
            # Calculate size of all files in directory
            size = calculate_directory_size(file_path)
        else:
            # Directory but not calculating size
            size = 0
        
        # Extract extension
        extension = None
        if file_type == "file":
            name_parts = file_path.name.rsplit('.', 1)
            if len(name_parts) > 1:
                extension = name_parts[1]
        
        # Permission information
        mode = stat_info.st_mode
        permissions = stat.filemode(mode)
        
        # Modified time
        modified = datetime.fromtimestamp(stat_info.st_mtime)
        
        return FileInfo(
            name=file_path.name,
            type=file_type,
            extension=extension,
            size=size,
            size_human=get_human_readable_size(size),
            modified=modified,
            permissions=permissions
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to get file information: {str(e)}")

def vscode_sort(items: List[FileInfo]) -> List[FileInfo]:
    """VSCode-style sorting: directories first, then files sorted by name"""
    directories = [item for item in items if item.type == "directory"]
    files = [item for item in items if item.type == "file"]
    
    # Sort each by name (case-insensitive)
    directories.sort(key=lambda x: x.name.lower())
    files.sort(key=lambda x: x.name.lower())
    
    # Directories first, then files
    return directories + files

def calculate_directory_size(directory_path: Path) -> int:
    """Calculate total size of directory (including subdirectories)"""
    total_size = 0
    try:
        for item in directory_path.rglob('*'):
            if item.is_file():
                try:
                    total_size += item.stat().st_size
                except (OSError, PermissionError):
                    continue
    except (OSError, PermissionError):
        pass
    return total_size

@app.get("/")
def root():
    return {
        "message": "Data Observer API",
        "version": "1.0.0",
        "nfs_root": NFS_ROOT
    }

@app.get("/browse", response_model=DirectoryResponse)
def browse_directory(
    path: str = Query("/", description="Path to browse (relative to NFS root)"),
    include_hidden: bool = Query(False, description="Include hidden files"),
    sort_by: str = Query("vscode", description="Sort criteria: vscode, name, size, modified, type"),
    calculate_dir_size: bool = Query(True, description="Whether to calculate actual directory size (may take time)")
):
    """Return directory contents of the specified path"""
    
    # Path normalization and security validation
    if path.startswith("/"):
        path = path[1:]  # Remove leading /
    
    # Prevent .. path manipulation
    if ".." in path:
        raise HTTPException(status_code=400, detail="Access to parent directory is not allowed")
    
    full_path = Path(NFS_ROOT) / path
    
    # Check if path exists
    if not full_path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")
    
    # Check if it's a directory
    if not full_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Specified path is not a directory: {path}")
    
    try:
        # Collect directory items
        items = []
        total_size = 0
        
        for item in full_path.iterdir():
            # Handle hidden files
            if not include_hidden and item.name.startswith('.'):
                continue
            
            try:
                file_info = get_file_info(item, calculate_dir_size)
                items.append(file_info)
                
                # Accumulate size for files
                if file_info.type == "file":
                    total_size += file_info.size
                    
            except Exception as e:
                print(f"Failed to get file information: {item.name}, error: {e}")
                continue
        
        # Sort
        if sort_by == "vscode":
            items = vscode_sort(items)
        else:
            sort_key_map = {
                "name": lambda x: x.name.lower(),
                "size": lambda x: x.size,
                "modified": lambda x: x.modified,
                "type": lambda x: (x.type, x.name.lower())  # Directories first, then by name
            }
            
            if sort_by in sort_key_map:
                items.sort(key=sort_key_map[sort_by])
        
        return DirectoryResponse(
            path=f"/{path}" if path else "/",
            total_items=len(items),
            total_size=total_size,
            total_size_human=get_human_readable_size(total_size),
            items=items
        )
        
    except PermissionError:
        raise HTTPException(status_code=403, detail="No permission to access directory")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to read directory: {str(e)}")

@app.get("/info")
def get_path_info(path: str = Query("/", description="Path to query information for")):
    """Return detailed information for a specific path"""
    
    # Path normalization and security validation
    if path.startswith("/"):
        path = path[1:]
    
    if ".." in path:
        raise HTTPException(status_code=400, detail="Access to parent directory is not allowed")
    
    full_path = Path(NFS_ROOT) / path
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")
    
    try:
        file_info = get_file_info(full_path, True)  # Always calculate directory size for /info endpoint
        
        # Calculate number of child items and total size for directories
        additional_info = {}
        if full_path.is_dir():
            try:
                child_count = len(list(full_path.iterdir()))
                dir_size = calculate_directory_size(full_path)
                additional_info.update({
                    "child_count": child_count,
                    "directory_size": dir_size,
                    "directory_size_human": get_human_readable_size(dir_size)
                })
            except PermissionError:
                additional_info["error"] = "No permission to access subdirectories"
        
        return {
            "path": f"/{path}" if path else "/",
            "info": file_info,
            **additional_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to get file information: {str(e)}")

@app.get("/health")
def health_check():
    """Health check endpoint"""
    nfs_accessible = os.path.exists(NFS_ROOT) and os.access(NFS_ROOT, os.R_OK)
    
    return {
        "status": "healthy" if nfs_accessible else "unhealthy",
        "nfs_root": NFS_ROOT,
        "nfs_accessible": nfs_accessible,
        "timestamp": datetime.now()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
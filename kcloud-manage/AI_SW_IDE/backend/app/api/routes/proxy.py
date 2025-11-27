# app/api/routes/proxy.py

from fastapi import APIRouter, Request, WebSocket, Response, Depends, HTTPException
from starlette.responses import RedirectResponse
from starlette.websockets import WebSocketState, WebSocketDisconnect
from sqlalchemy.orm import Session
import httpx, asyncio, websockets, re
import websockets.exceptions

from app.db.dependencies import get_db
from app.models.k8s import PodCreation
from app.core.logger import app_logger

router = APIRouter()

# Query server information from database
def get_server_address(db: Session, instance_id: str) -> str:
    """Get internal IP by instance_id (server ID)"""
    try:
        server = db.query(PodCreation).filter(PodCreation.id == int(instance_id)).first()
        if not server:
            # print(f"DEBUG: Server with ID {instance_id} not found in database")
            return None
        if not server.internal_ip:
            # print(f"DEBUG: Server {instance_id} found but internal_ip is None/empty")
            return None
        # print(f"DEBUG: Found server {instance_id} with internal_ip: {server.internal_ip}")
        return server.internal_ip
    except ValueError as e:
        # print(f"DEBUG: Invalid instance_id format: {instance_id}, error: {e}")
        return None
    except Exception as e:
        # print(f"DEBUG: Database query error: {e}")
        return None

@router.api_route("/{user_name}/{instance_id}/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_http_request(
    request: Request, 
    user_name: str, 
    instance_id: str, 
    full_path: str = "",
    db: Session = Depends(get_db)
):
    server_address = get_server_address(db, instance_id) + ":8888"
    # print(f"DEBUG: server_address = {server_address}")
    if not server_address:
        raise HTTPException(status_code=404, detail=f"Server with instance_id {instance_id} not found or no internal IP")

    target_url = f"http://{server_address}/{full_path}"
    # print(f"DEBUG: Attempting to connect to: {target_url}")
    
    method = request.method.lower()
    headers = dict(request.headers)
    headers.pop("host", None)
    if "origin" in headers:
        headers["origin"] = f"http://{server_address}"

    try:
        async with httpx.AsyncClient(follow_redirects=False, timeout=10.0) as client:
            if method in ["get", "delete", "options"]:
                response = await getattr(client, method)(target_url, headers=headers)
            else:
                content = await request.body()
                response = await getattr(client, method)(target_url, headers=headers, content=content)

            if response.status_code in [301, 302, 307, 308]:
                redirect_url = response.headers.get("Location", "")
                if redirect_url.startswith("/"):
                    redirect_url = f"/proxy/{user_name}/{instance_id}{redirect_url}"
                return RedirectResponse(url=redirect_url, status_code=response.status_code, headers=dict(response.headers))

            content_type = response.headers.get("content-type", "")
            modified_content = response.content

            def _convert_endpoint(_content):
                for key in ["baseUrl", "fullStaticUrl", "fullLabextensionsUrl"]:
                    _content = re.sub(
                        rf'("{key}":\s*")/',
                        rf'\1/proxy/{user_name}/{instance_id}/',
                        _content
                    )
                _content = re.sub(
                    r'(window\.__.*?base_url__\s*=\s*["\'])/',
                    rf'\1/proxy/{user_name}/{instance_id}/',
                    _content
                )
                return _content

            if "text/html" in content_type:
                modified_content = response.text
                modified_content = re.sub(
                    r'(?P<pre>(href|src|action|data-src|link)=["\'])/(?P<path>(kernelspecs|nbextensions|files|static)/[^"\']+)',
                    rf'\g<pre>/proxy/{user_name}/{instance_id}/\g<path>',
                    modified_content
                )
                # Also cover src attribute in img tags
                modified_content = re.sub(
                    r'(<img[^>]+src=["\'])/([^"\']+)',
                    rf'\1/proxy/{user_name}/{instance_id}/\2',
                    modified_content
                )
                modified_content = _convert_endpoint(modified_content)
            elif "application/json" in content_type:
                modified_content = response.text
                modified_content = _convert_endpoint(modified_content)

            response_headers = dict(response.headers)
            response_headers.pop("content-length", None)
            return Response(content=modified_content, status_code=response.status_code, headers=response_headers)
    
    except httpx.ConnectError as e:
        raise HTTPException(status_code=502, detail=f"Cannot connect to server {server_address}")
    except httpx.TimeoutException as e:
        raise HTTPException(status_code=504, detail=f"Timeout connecting to server {server_address}")
    except Exception as e:
        app_logger.error(f"HTTP proxy error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Router for specific paths like kernelspecs
@router.api_route("/kernelspecs/{path:path}", methods=["GET"])
async def proxy_kernelspecs(
    request: Request,
    path: str,
    db: Session = Depends(get_db)
):
    """Handle kernelspecs requests"""
    return await handle_static_proxy(request, f"kernelspecs/{path}", db)

@router.api_route("/static/{path:path}", methods=["GET"]) 
async def proxy_static_files(
    request: Request,
    path: str,
    db: Session = Depends(get_db)
):
    """Handle static file requests"""
    return await handle_static_proxy(request, f"static/{path}", db)

@router.api_route("/nbextensions/{path:path}", methods=["GET"])
async def proxy_nbextensions(
    request: Request,
    path: str,
    db: Session = Depends(get_db)
):
    """Handle nbextensions requests"""
    return await handle_static_proxy(request, f"nbextensions/{path}", db)

async def handle_static_proxy(request: Request, static_path: str, db: Session):
    """Common static file proxy handler function"""
    # Extract user and instance information from Referer header
    referer = request.headers.get("referer", "")
    
    # Find /proxy/{user_name}/{instance_id} pattern in Referer
    import re
    match = re.search(r'/proxy/([^/]+)/(\d+)', referer)
    if not match:
        raise HTTPException(status_code=404, detail="Cannot determine target server from referer")
    
    user_name, instance_id = match.groups()
    
    # Reuse existing proxy logic
    base_address = get_server_address(db, instance_id)
    if not base_address:
        raise HTTPException(status_code=404, detail=f"Server with instance_id {instance_id} not found or no internal IP")

    target_url = f"http://{base_address}:8888/{static_path}"
    
    headers = dict(request.headers)
    headers.pop("host", None)
    if "origin" in headers:
        headers["origin"] = f"http://{base_address}:8888"

    try:
        async with httpx.AsyncClient(follow_redirects=False, timeout=10.0) as client:
            response = await client.get(target_url, headers=headers)
            
            response_headers = dict(response.headers)
            response_headers.pop("content-length", None)
            return Response(content=response.content, status_code=response.status_code, headers=response_headers)
    
    except httpx.ConnectError as e:
        raise HTTPException(status_code=502, detail=f"Cannot connect to server {base_address}:8888")
    except Exception as e:
        app_logger.error(f"Static proxy error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.websocket("/{user_name}/{instance_id}/{full_path:path}")
async def proxy_websocket(websocket: WebSocket, user_name: str, instance_id: str, full_path: str):
    # Cannot use Depends directly in WebSocket, so create DB session manually
    from app.db.session import SessionLocal
    db = SessionLocal()
    jupyter_ws = None
    client_to_jupyter = None
    jupyter_to_client = None
    
    try:
        server_address = get_server_address(db, instance_id)
        if not server_address:
            await websocket.accept()
            await websocket.send_text(f"Error: Server with instance_id {instance_id} not found or no internal IP")
            await websocket.close()
            return

        server_address += ":8888"
        await websocket.accept()
        jupyter_ws_url = f"ws://{server_address}/{full_path}"

        try:
            jupyter_ws = await websockets.connect(jupyter_ws_url, close_timeout=1.0)
            
            # Create tasks
            client_to_jupyter = asyncio.create_task(
                relay_client_to_jupyter(websocket, jupyter_ws)
            )
            jupyter_to_client = asyncio.create_task(
                relay_jupyter_to_client(websocket, jupyter_ws)
            )
            
            # Wait for tasks and cleanup
            try:
                done, pending = await asyncio.wait(
                    [client_to_jupyter, jupyter_to_client], 
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Check exceptions from completed tasks
                for task in done:
                    try:
                        result = await task
                    except Exception as e:
                        app_logger.error(f"WebSocket task error: {e}")
                
                # Clean up remaining tasks
                for task in pending:
                    task.cancel()
                    try:
                        await asyncio.wait_for(task, timeout=1.0)
                    except (asyncio.CancelledError, asyncio.TimeoutError):
                        pass
                        
            except Exception as e:
                app_logger.error(f"WebSocket relay error: {e}")
                
        except websockets.exceptions.ConnectionClosed:
            pass  # Normal connection close
        except websockets.exceptions.InvalidHandshake as e:
            app_logger.error(f"WebSocket handshake failed: {e}")
        except Exception as e:
            app_logger.error(f"WebSocket connection error: {e}")
            
    except WebSocketDisconnect:
        pass  # Client disconnection is a normal situation
    except Exception as e:
        app_logger.error(f"WebSocket proxy error: {e}")
    finally:
        # Force cleanup of tasks
        await cleanup_tasks(client_to_jupyter, jupyter_to_client)
        # Clean up resources
        await cleanup_websocket_resources(websocket, jupyter_ws, db)

async def cleanup_tasks(*tasks):
    """Safely cleanup asyncio tasks"""
    for task in tasks:
        if task and not task.done():
            task.cancel()
            try:
                await asyncio.wait_for(task, timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            except Exception as e:
                app_logger.error(f"Error cleaning up task: {e}")

async def cleanup_websocket_resources(websocket: WebSocket, jupyter_ws, db):
    """Safely cleanup WebSocket resources"""
    # Cleanup Jupyter WebSocket
    if jupyter_ws:
        try:
            await asyncio.wait_for(jupyter_ws.close(), timeout=2.0)
        except (asyncio.TimeoutError, Exception):
            pass  # Ignore errors during cleanup
    
    # Cleanup client WebSocket
    try:
        if (hasattr(websocket, 'client_state') and 
            websocket.client_state not in [WebSocketState.DISCONNECTED]):
            await asyncio.wait_for(websocket.close(code=1000), timeout=2.0)
    except (asyncio.TimeoutError, Exception):
        pass  # Ignore errors during cleanup
    
    # Cleanup DB session
    try:
        if db:
            db.close()
    except Exception:
        pass  # Ignore DB cleanup errors
    
    # Memory cleanup (don't touch logging system)
    import gc
    gc.collect()

async def relay_client_to_jupyter(websocket: WebSocket, jupyter_ws):
    """Relay messages from client to Jupyter"""
    try:
        while True:
            try:
                msg = await websocket.receive_text()
                # Improved connection state checking for websockets library
                try:
                    await jupyter_ws.send(msg)
                except websockets.exceptions.ConnectionClosed:
                    break
            except WebSocketDisconnect:
                break
            except websockets.exceptions.ConnectionClosed:
                break
            except Exception as e:
                app_logger.error(f"Client to Jupyter relay error: {e}")
                break
    except asyncio.CancelledError:
        raise
    except Exception as e:
        app_logger.error(f"Client to Jupyter relay error: {e}")

async def relay_jupyter_to_client(websocket: WebSocket, jupyter_ws):
    """Relay messages from Jupyter to client"""
    try:
        while True:
            try:
                msg = await jupyter_ws.recv()
                # Safer client connection state checking
                if (hasattr(websocket, 'client_state') and 
                    websocket.client_state == WebSocketState.DISCONNECTED):
                    break
                await websocket.send_text(msg)
            except websockets.exceptions.ConnectionClosed:
                break
            except WebSocketDisconnect:
                break
            except Exception as e:
                app_logger.error(f"Jupyter to client relay error: {e}")
                break
    except asyncio.CancelledError:
        raise
    except Exception as e:
        app_logger.error(f"Jupyter to client relay error: {e}")
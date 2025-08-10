import os
import json
import asyncio
from datetime import datetime
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from enum import Enum
import logging
import httpx

# Import GraphitiMCPServer
from graphiti_pro_core import GraphitiMCPServer, MCPStatus, mcp_status, MCPStatusObserver

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"])

class MCPAction(str, Enum):
    START = "start"
    STOP = "stop"
    RESTART = "restart"

class MCPControlRequest(BaseModel):
    action: MCPAction

class MCPControlResponse(BaseModel):
    success: bool
    action: str
    status: MCPStatus

class MCPHealthResponse(BaseModel):
    status: str

class SSEStatusObserver(MCPStatusObserver):
    """SSE Status Observer for pushing status changes to clients"""
    
    def __init__(self):
        self.status_queue = asyncio.Queue()
    
    def on_change(self, status: MCPStatus) -> None:
        """Handle status change notification"""
        try:
            # Non-blocking put to queue
            status_data = {
                "status": status.value,
                "timestamp": datetime.now().isoformat()
            }
            self.status_queue.put_nowait(status_data)
        except asyncio.QueueFull:
            # Ignore queue full situation
            logger.warning("Status queue is full, dropping status update")
        except Exception as e:
            logger.error(f"Error in SSE status observer: {e}")

# Global SSE observer instance
sse_observer: SSEStatusObserver = None

def get_sse_observer() -> SSEStatusObserver:
    """Get global SSE observer instance"""
    global sse_observer
    if sse_observer is None:
        sse_observer = SSEStatusObserver()
    return sse_observer

@router.post("/control", response_model=MCPControlResponse)
async def control_mcp(request: MCPControlRequest):
    """Control MCP service (start/stop/restart)"""
    
    try:
        action = request.action
        logger.info(f"Received MCP control request: {action}")
        
        # Execute the requested action
        if action == MCPAction.START:
            if mcp_status.value == MCPStatus.RUNNING:
                return MCPControlResponse(
                    success=False,
                    action=action,
                    status=mcp_status.value
                )
            
            # Initialize if not already initialized
            if not GraphitiMCPServer.is_initialized():
                await GraphitiMCPServer.initialize()
            
            await GraphitiMCPServer.start()
            
        elif action == MCPAction.STOP:
            if mcp_status.value == MCPStatus.STOPPED:
                return MCPControlResponse(
                    success=False,
                    action=action,
                    status=mcp_status.value
                )
            
            await GraphitiMCPServer.stop()
            
        elif action == MCPAction.RESTART:
            if mcp_status.value == MCPStatus.STOPPED:
                # If not running, just start it
                if not GraphitiMCPServer.is_initialized():
                    await GraphitiMCPServer.initialize()
                await GraphitiMCPServer.start()
            else:
                await GraphitiMCPServer.restart()
        
        # Get final running status
        final_status = mcp_status.value
        
        logger.info(f"MCP control action '{action}' completed successfully")
        
        return MCPControlResponse(
            success=True,
            action=action,
            status=final_status
        )
        
    except Exception as e:
        logger.error(f"MCP control action '{request.action}' failed: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to {request.action} MCP service: {str(e)}"
        )

@router.get("/health", response_model=MCPHealthResponse)
async def get_mcp_health():
    """Get MCP service health status by proxying to MCP server"""
    
    try:
        # Get MCP port from environment variable
        mcp_port = os.getenv("MCP_PORT", "8082")
        health_url = f"http://127.0.0.1:{mcp_port}/health"
        
        logger.debug(f"Checking MCP health at: {health_url}")
        
        # Make request to MCP health endpoint with timeout
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(health_url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "running":
                    logger.debug("MCP service health check: running")
                    return MCPHealthResponse(status="running")
        
        logger.debug("MCP service health check: stopped")
        return MCPHealthResponse(status="stopped")
        
    except Exception as e:
        logger.warning(f"MCP health check failed: {str(e)}")
        return MCPHealthResponse(status="stopped")

async def status_stream_generator() -> AsyncGenerator[str, None]:
    """SSE status stream generator"""
    observer = get_sse_observer()
    
    # Send initial status
    try:
        initial_status = {
            "status": mcp_status.value.value,
            "timestamp": datetime.now().isoformat()
        }
        yield f"data: {json.dumps(initial_status)}\n\n"
    except Exception as e:
        logger.error(f"Error sending initial status: {e}")
    
    # Listen for status changes
    while True:
        try:
            # Wait for status change
            status_data = await observer.status_queue.get()
            yield f"data: {json.dumps(status_data)}\n\n"
            
        except Exception as e:
            logger.error(f"Error in status stream: {e}")
            error_data = {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            # Wait a bit before continuing
            await asyncio.sleep(1)

@router.get("/status")
async def get_mcp_status_stream():
    """MCP status stream (Server-Sent Events)"""
    return StreamingResponse(
        status_stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

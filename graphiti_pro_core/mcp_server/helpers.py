"""
General helper functions for MCP operations.
"""

import os
import socket
import asyncio
import time

from starlette.requests import Request
from starlette.responses import JSONResponse
from utils import logger, initialize_async_logging, usage_collector

from .stateful_fastmcp import StatefulFastMCP
from .settings import default_host


def initialize_network(mcp: StatefulFastMCP) -> None:
    """Initialize network settings"""
    mcp.settings.host = default_host
    mcp.settings.port = int(os.getenv("MCP_PORT", "8082"))


def add_custom_routes(mcp: StatefulFastMCP) -> None:
    """Add custom routes"""
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        """Health check endpoint"""
        return JSONResponse({"status": "running"})

def add_tools(mcp: StatefulFastMCP) -> None:
    """Add tools"""
    from .tools import (
        add_memory, search_memory_nodes, search_memory_facts,
        get_add_memory_task_status, list_add_memory_tasks, wait_for_add_memory_task, cancel_add_memory_task,
        delete_entity_edge, get_entity_edge, delete_episode,
        get_episodes, clear_graph
    )

    tools = [
        add_memory, search_memory_nodes, search_memory_facts,
        get_add_memory_task_status, list_add_memory_tasks, wait_for_add_memory_task, cancel_add_memory_task,
        delete_entity_edge, get_entity_edge, delete_episode,
        get_episodes, clear_graph
    ]

    for tool in tools:
        mcp.add_tool(tool)


def add_resources(mcp: StatefulFastMCP) -> None:
    """Add resources"""
    from .resources import get_status_resource
    mcp.add_resource(get_status_resource)


async def initialize_integrators() -> None:
    """Initialize integration modules"""
    # Initialize async logging system
    await initialize_async_logging()
    logger.info("🔧 Async logging system initialized")

    # Initialize usage collector
    await usage_collector.start_worker()
    logger.info("📊 Usage collector initialized")


def get_server_instance():
    """Get server instance"""
    from .__state__ import get_mcp_server
    server = get_mcp_server()
    if not server:
        raise RuntimeError("Server not initialized")
    return server


async def cleanup_integrators() -> None:
    """Clean up integration modules"""
    try:
        # Clean up usage collector
        logger.info("📊 Shutting down usage collector...")
        await usage_collector.flush_queue()
        await usage_collector.stop_worker()
        logger.info("📊 Usage collector shutdown complete")

    except Exception as e:
        logger.error(f"❌ Error during integrators cleanup: {e}")

def is_port_available(port: int, host: str = "127.0.0.1") -> bool:
    """Check if port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex((host, port)) != 0
    except OSError:
        return False

async def wait_for_port_release(port: int, timeout: int = 10) -> bool:
    """Wait for port to be released"""
    logger.info(f"⏳ Waiting for port {port} to be released...")
    start_time = time.time()
    check_count = 0

    while time.time() - start_time < timeout:
        if is_port_available(port):
            logger.info(f"✅ Port {port} is now available after {check_count} checks")
            return True
        check_count += 1
        if check_count % 10 == 0:  # Log every 1 second (10 * 0.1s)
            elapsed = time.time() - start_time
            logger.info(f"⏳ Still waiting for port {port} (elapsed: {elapsed:.1f}s)")
        await asyncio.sleep(0.1)

    logger.warning(f"⚠️ Port {port} was not released within {timeout}s")
    return False
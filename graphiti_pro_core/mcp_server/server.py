import asyncio
import socket
import uvicorn
from typing import Optional
from starlette.middleware.cors import CORSMiddleware

from utils import logger
from .stateful_fastmcp import StatefulFastMCP
from .helpers import (
    initialize_network, add_custom_routes, add_tools, add_resources,
    initialize_integrators, cleanup_integrators,
    is_port_available, wait_for_port_release
)
from .instructions import GRAPHITI_MCP_INSTRUCTIONS
from .__state__ import mcp_status
from .types import MCPStatus

# Diagnostic flag to verify Starlette lifespan shutdown
starlette_shutdown_fired: bool = False

class MCPServer:
    """Refactored MCP Server - merged Controller functionality"""

    def __init__(self):
        # Private attributes
        self._mcp: Optional[StatefulFastMCP] = None
        self._uvicorn: Optional[uvicorn.Server] = None
        self._serve_task: Optional[asyncio.Task] = None

    async def _initialize(self) -> "MCPServer":
        """Initialize server components"""
        try:
            # Create StatefulFastMCP instance
            self._mcp = StatefulFastMCP(
                'Graphiti Agent Memory',
                instructions=GRAPHITI_MCP_INSTRUCTIONS,
            )

            # Initialize various components
            initialize_network(self._mcp)
            add_custom_routes(self._mcp)
            add_tools(self._mcp)
            add_resources(self._mcp)

            # Initialize integration modules
            await initialize_integrators()

            # Initialize task management system
            from .tools.memory.__task__ import initialize_task_manager
            initialize_task_manager()
            logger.info("🔧 Task manager initialized")

            # Create Starlette application
            app = self._mcp.streamable_http_app()
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"]
            )
            # Attach explicit shutdown event handler for diagnostics
            async def _on_shutdown_event():
                global starlette_shutdown_fired
                starlette_shutdown_fired = True
                logger.info("🔚 Starlette shutdown event fired")
            app.add_event_handler("shutdown", _on_shutdown_event)


            # Create uvicorn server with very aggressive shutdown settings
            server_config = uvicorn.Config(
                app=app,
                host=self._mcp.settings.host,
                port=self._mcp.settings.port,
                log_config=None,  # Use our own logging system
                timeout_graceful_shutdown=3,  # Minimal graceful shutdown timeout
            )

            # Create uvicorn server
            self._uvicorn = uvicorn.Server(config=server_config)

            return self

        except Exception as e:
            logger.error(f"❌ Failed to initialize MCPServer: {str(e)}")
            raise

    def _deinit(self) -> None:
        """Reset private attributes"""
        self._mcp = None
        self._uvicorn = None
        self._serve_task = None

        # Reset global server instance
        from .__state__ import set_mcp_server
        set_mcp_server(None)

    async def _pre_start(self) -> None:
        """Pre-start preparation - status and port checks"""
        # 1. Status check
        if mcp_status.value is not MCPStatus.STOPPED:
            raise RuntimeError(f"Server status is {mcp_status.value}, cannot start")

        # 2. Set starting status
        mcp_status.value = MCPStatus.STARTING
        logger.info("🚀 Starting server...")

        # 3. Port availability check
        if not self._mcp:
            raise RuntimeError("Server not initialized")

        port = self._mcp.settings.port
        host = self._mcp.settings.host

        if not is_port_available(port, host):
            mcp_status.value = MCPStatus.STOPPED  # Rollback status
            raise RuntimeError(f"Port {port} is not available")

        logger.info(f"🚀 Starting server on {host}:{port}")

    async def _post_stop(self) -> None:
        """Post-stop cleanup - session cleanup and resource release"""
        logger.info("🛑 Stopping server...")

        port = self._mcp.settings.port if self._mcp else 0

        # Set stopping status
        mcp_status.value = MCPStatus.STOPPING

        try:
            # 1. Clear MCP sessions
            if self._mcp:
                try:
                    session_manager = self._mcp._session_manager
                    if session_manager:
                        await session_manager.terminate_sessions()
                    else:
                        logger.info("🔌 No session manager or server instances found")
                except Exception as e:
                    logger.warning(f"⚠️ Error clearing MCP sessions: {e}")

            # 2. Force shutdown uvicorn (faster port release)
            if self._uvicorn:
                logger.info("🔄 Shutting down uvicorn server...")
                try:
                    await self._uvicorn.shutdown()
                    logger.info("🔧 Uvicorn shutdown() completed")
                except Exception as e:
                    logger.error(f"❌ Error calling uvicorn shutdown(): {e}")

            # 3. Execute resource cleanup
            await self._cleanup()

            # 4. Wait for port release
            await wait_for_port_release(port)

            # 5. Set stopped status
            mcp_status.value = MCPStatus.STOPPED
            logger.info("✅ Server stopped successfully")

        except Exception as e:
            logger.error(f"❌ Error during server shutdown: {str(e)}")
        finally:
            # Reset instance
            self._deinit()

    async def _run_server(self) -> None:
        """Server running logic"""
        try:
            # Pre-start preparation
            await self._pre_start()

            # Check uvicorn instance
            if not self._uvicorn:
                raise RuntimeError("Server not initialized")

            # Run server
            await self._uvicorn.serve()

        except asyncio.CancelledError:
            # Post-stop cleanup
            await self._post_stop()
            logger.info("✅ Server task cancelled gracefully")
            raise
        except Exception as e:
            logger.error(f"❌ Server error: {str(e)}")
            # Rollback status on error
            mcp_status.value = MCPStatus.STOPPED
            raise

    async def _cleanup(self) -> None:
        """Clean up resources"""
        try:
            # Clean up task manager
            from .tools.memory.__task__ import cleanup_task_manager
            await cleanup_task_manager()
            logger.info("🔧 Task manager cleanup complete")

            # Clean up integration modules
            await cleanup_integrators()
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")

    @staticmethod
    async def initialize() -> "MCPServer":
        """Initialize server instance"""
        server = MCPServer()
        initialized_server = await server._initialize()

        # Set global instance
        from .__state__ import set_mcp_server
        set_mcp_server(initialized_server)

        return initialized_server

    @staticmethod
    async def start() -> None:
        """Start server - pure task management"""
        from .helpers import get_server_instance
        server = get_server_instance()

        try:
            # Create and start server task
            server._serve_task = asyncio.create_task(server._run_server())

            # Wait a moment to ensure startup completion
            await asyncio.sleep(0.1)

        except Exception as e:
            # Clean up task on startup failure
            if server._serve_task:
                server._serve_task.cancel()
                server._serve_task = None
            logger.error(f"❌ Failed to start server: {str(e)}")
            raise

    @staticmethod
    async def stop() -> None:
        """Stop server - pure task management"""
        from .helpers import get_server_instance
        server = get_server_instance()

        if mcp_status.value is not MCPStatus.RUNNING:
            logger.warning(f"⚠️ Server status is {mcp_status.value}, cannot stop now")
            return

        try:
            # Cancel server task
            if server._serve_task and not server._serve_task.done():
                logger.info("� Cancelling serve task...")
                server._serve_task.cancel()

                # Wait for task completion (including cleanup logic)
                try:
                    await server._serve_task
                except asyncio.CancelledError:
                    logger.info("✅ Server task cancelled")

        except Exception as e:
            logger.error(f"❌ Error during server stop: {str(e)}")
        finally:
            # Ensure task reference is cleaned up
            server._serve_task = None

    @staticmethod
    async def restart() -> None:
        """Restart server"""
        logger.info("🔄 Restarting server...")

        # Stop server
        await MCPServer.stop()

        # Wait a moment to ensure complete stop
        await asyncio.sleep(0.5)

        # Re-initialize and start
        await MCPServer.initialize()
        await MCPServer.start()

__all__ = [
    "MCPServer",
]

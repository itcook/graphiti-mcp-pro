import contextlib
from collections.abc import AsyncIterator
from mcp.server.fastmcp import FastMCP
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from utils import logger
from .__state__ import mcp_status
from .types import MCPStatus

class StatefulSessionManager(StreamableHTTPSessionManager):
    """Status-aware Session Manager"""

    @contextlib.asynccontextmanager
    async def run(self) -> AsyncIterator[None]:
        """Override run method to add status management"""
        logger.info("🚀 Starting StatefulSessionManager...")

        try:
            async with super().run():
                # Only set RUNNING status after super().run() successfully starts
                mcp_status.value = MCPStatus.RUNNING
                logger.info("✅ MCP service ready")

                yield  # Let the application run

        except Exception as e:
            logger.error(f"❌ MCP service error: {str(e)}")
            raise
        # finally:
        #     # Always set STOPPED status when exiting, regardless of how we exit
        #     mcp_status.value = MCPStatus.STOPPED
        #     logger.info("✅ MCP service stopped")
        
    async def terminate_sessions(self) -> None:
        if hasattr(self, '_server_instances'):
            active_sessions = len(self._server_instances)
            logger.info(f"🔌 Found {active_sessions} active MCP sessions")
            if active_sessions == 0:
                return
            logger.info("🔌 Clearing active MCP sessions...")
            for transport in self._server_instances.values():
                if hasattr(transport, '_terminate_session'):
                    await transport._terminate_session()
                    logger.info("🔌 Session terminated")
            self._server_instances.clear()
            logger.info("🔌 Active MCP sessions cleared")


class StatefulFastMCP(FastMCP):
    """Status-aware FastMCP - simplified version"""

    def streamable_http_app(self) -> Starlette:
        """Override to use custom Session Manager"""
        # Create custom session manager (if not already created)
        if self._session_manager is None:
            self._session_manager = StatefulSessionManager(
                app=self._mcp_server,
                event_store=self._event_store,
                json_response=self.settings.json_response,
                stateless=self.settings.stateless_http,
                security_settings=self.settings.transport_security,
            )

        # Call parent method to get Starlette application
        return super().streamable_http_app()

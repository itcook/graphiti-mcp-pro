#!/usr/bin/env python3
"""
Graphiti MCP Server - Exposes Graphiti functionality through the Model Context Protocol (MCP)
"""

import asyncio

from .mcp_server import MCPServer,is_mcp_initialized
from .clients import GraphitiClient, is_graphiti_initialized


class GraphitiMCPServer:
    
    @staticmethod
    async def initialize():
        """Create and start the Graphiti MCP server"""
        if not is_graphiti_initialized():
            await GraphitiClient.initialize()
        if not is_mcp_initialized():
            await MCPServer.initialize()

    @staticmethod
    async def start():
        """Start the Graphiti MCP server"""
        if not GraphitiMCPServer.is_initialized():
            await GraphitiMCPServer.initialize()
            
        await MCPServer.start()
        
    
    @staticmethod
    async def stop():
        """Stop the Graphiti MCP server"""
        await MCPServer.stop()
        await GraphitiClient.cleanup()
        
    @staticmethod
    async def restart():
        """Restart the Graphiti MCP server"""
        await GraphitiClient.cleanup()
        await GraphitiClient.initialize()
        await MCPServer.restart()
                
    @staticmethod
    def is_initialized() -> bool:
        """Check if the server is initialized"""
        return is_graphiti_initialized() and is_mcp_initialized()
    

async def run_mcp_server():
    """Run the Graphiti MCP server"""
    await GraphitiMCPServer.initialize()
    await GraphitiMCPServer.start()
    
async def graceful_stop_mcp_server():
    """Gracefully stop the Graphiti MCP server"""
    await GraphitiMCPServer.stop()
    

if __name__ == '__main__':
    asyncio.run(run_mcp_server())

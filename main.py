#!/usr/bin/env python3
"""
Graphiti MCP Server - Exposes Graphiti functionality through the Model Context Protocol (MCP)
"""

import asyncio
import argparse

from graphiti_pro_core import run_mcp_server, graceful_stop_mcp_server
from utils import setup_logging, set_library_log_level, LogLevel, logger

# Conditional import for backend server to handle different environments
try:
    # Local development environment path
    from manager.backend.app import run_backend_server
except ImportError:
    try:
        # Docker environment path
        from backend.app import run_backend_server # pyright: ignore[reportMissingImports]
    except ImportError as e:
        logger.error(f"Failed to import backend modules: {e}")
        run_backend_server = None


setup_logging()
set_library_log_level('neo4j', LogLevel.ERROR)

async def main_async():
    """Main async function to run the Graphiti MCP server."""
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Graphiti MCP Server')
        parser.add_argument('-m', '--manager', action='store_true',
                          help='Run with manager backend server')
        args = parser.parse_args()

        if args.manager:
            # Run both MCP server and backend server concurrently
            logger.info("🚀 Starting MCP server with manager backend...")
            await asyncio.gather(
                run_mcp_server(),
                run_backend_server()
            )
        else:
            # Run only MCP server
            logger.info("🚀 Starting MCP server only...")
            await run_mcp_server()

    except asyncio.CancelledError:
        await graceful_stop_mcp_server()
        logger.info("🛑 Received cancellation, shutting down gracefully")
        raise
    except Exception as e:
        logger.error(f'❌ Error running Graphiti MCP server: {str(e)}')
        raise

def main():
    """Main function to run the Graphiti MCP server."""
    try:
        # Run everything in a single event loop
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt (Ctrl+C), shutting down gracefully")
    except Exception as e:
        logger.error(f'❌ Error running Graphiti MCP server: {str(e)}')
        raise

if __name__ == '__main__':
    main()
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import manager_config
from .database import init_database
from .api.settings import router as settings_router
from .api.token_usage import router as token_usage_router
from .api.logs import router as logs_router
from .api.mcp import router as mcp_router
from .scheduler import log_cleanup_scheduler
from graphiti_pro_core import mcp_status

# Lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup event"""
    print("🛠️ Initializing backend database...")
    await init_database()

    # Initialize and attach SSE observer for MCP status
    print("🔗 Initializing MCP status SSE observer...")
    from .api.mcp import get_sse_observer
    sse_observer = get_sse_observer()
    mcp_status.attach(sse_observer)
    print("✅ MCP status SSE observer attached")

    print("Initializing log cleanup scheduler...")
    try:
        log_cleanup_scheduler.initialize()
        log_cleanup_scheduler.start()
        print("Log cleanup scheduler initialized and started")
    except Exception as e:
        print(f"Warning: Failed to initialize log cleanup scheduler: {e}")

    print(f"Server starting on port {manager_config.MANAGER_SERVER_PORT}")

    yield

    # Cleanup on shutdown
    print("🔗 Detaching MCP status observer...")
    mcp_status.detach()
    print("✅ MCP status observer detached")

    print("Shutting down log cleanup scheduler...")
    try:
        log_cleanup_scheduler.stop()
        print("Log cleanup scheduler stopped")
    except Exception as e:
        print(f"Warning: Error stopping log cleanup scheduler: {e}")


# Create FastAPI application
app = FastAPI(
    title="Graphiti MCP Manager API",
    description="Backend API for managing Graphiti MCP configuration and token usage statistics",
    version="1.0.0",
    lifespan=lifespan
)

# origins = [
#     "http://localhost:*",
#     "http://manager_frontend:*",
#     "http://127.0.0.1:*",
# ]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(settings_router, prefix="/api")
app.include_router(token_usage_router, prefix="/api")
app.include_router(logs_router, prefix="/api")
app.include_router(mcp_router, prefix="/api")


@app.get("/")
async def root():
    """Root path"""
    return {"message": "Graphiti MCP Manager API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "OK"}


async def run_backend_server():
    """Run backend server"""
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=manager_config.MANAGER_SERVER_PORT,
        reload=False
    )
    server = uvicorn.Server(config)
    await server.serve()
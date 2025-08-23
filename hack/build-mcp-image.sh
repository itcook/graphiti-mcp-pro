#!/bin/bash

# Build script for mcp-with-manager image
# This script builds the mcp-with-manager Docker image using the root Dockerfile

set -e  # Exit on any error
set -o pipefail  # Exit on pipe failure

# Configuration
IMAGE_NAME="ghcr.io/itcook/graphiti-mcp-pro/mcp-with-manager"
TAG="${TAG:-latest}"
DOCKERFILE_PATH="."
BUILD_CONTEXT="."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed or not available in PATH"
    exit 1
fi

# Check if Dockerfile exists
if [[ ! -f "Dockerfile" ]]; then
    log_error "Dockerfile not found in current directory"
    exit 1
fi

log_info "Starting build for mcp-with-manager image..."
log_info "Image name: ${IMAGE_NAME}:${TAG}"
log_info "Build context: ${BUILD_CONTEXT}"
log_info "Dockerfile path: ${DOCKERFILE_PATH}"

# Build the Docker image
log_info "Building Docker image..."
if docker build -t "${IMAGE_NAME}:${TAG}" -f "${DOCKERFILE_PATH}/Dockerfile" "${BUILD_CONTEXT}"; then
    log_info "✅ Successfully built ${IMAGE_NAME}:${TAG}"
else
    log_error "❌ Failed to build ${IMAGE_NAME}:${TAG}"
    exit 1
fi 

log_info "🎉 Build completed successfully!"

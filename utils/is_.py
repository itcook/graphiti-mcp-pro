"""
Environment detection utilities for Graphiti MCP Server.

This module provides functions to detect the runtime environment,
which helps determine the appropriate execution mode for different scenarios.
"""

import os
import pathlib
import socket

def is_in_docker() -> bool:
    """
    Detect if the current process is running inside a Docker container.
    
    This function uses multiple detection methods to reliably identify
    Docker environments across different platforms and configurations.
    
    Returns:
        bool: True if running in Docker, False otherwise
        
    Detection Methods:
        1. Check for /.dockerenv file (most reliable)
        2. Check /proc/1/cgroup for docker/containerd patterns
        3. Check environment variables commonly set in Docker
        4. Check for container-specific mount points
    """
    # Method 1: Check for /.dockerenv file (most reliable)
    if pathlib.Path("/.dockerenv").exists():
        return True
    
    # Method 2: Check /proc/1/cgroup for container patterns
    try:
        with open("/proc/1/cgroup", "r") as f:
            content = f.read()
            # Look for docker, containerd, or other container runtimes
            container_patterns = ["docker", "containerd", "lxc", "kubepods"]
            if any(pattern in content.lower() for pattern in container_patterns):
                return True
    except (FileNotFoundError, PermissionError, OSError):
        # /proc/1/cgroup might not exist on non-Linux systems
        pass
    
    # Method 3: Check environment variables
    docker_env_vars = [
        "DOCKER_CONTAINER",
        "CONTAINER",
        "KUBERNETES_SERVICE_HOST",  # Kubernetes pods
        "HOSTNAME"  # Docker often sets specific hostname patterns
    ]
    
    for env_var in docker_env_vars:
        if env_var in os.environ:
            if env_var == "HOSTNAME":
                # Docker hostnames are often container IDs (12 hex chars)
                hostname = os.environ[env_var]
                if len(hostname) == 12 and all(c in "0123456789abcdef" for c in hostname.lower()):
                    return True
            else:
                return True
    
    # Method 4: Check for container-specific mount points
    try:
        with open("/proc/mounts", "r") as f:
            mounts = f.read()
            # Look for overlay filesystems commonly used in containers
            if "overlay" in mounts or "aufs" in mounts:
                return True
    except (FileNotFoundError, PermissionError, OSError):
        pass
    
    return False


def is_in_kubernetes() -> bool:
    """
    Detect if running in a Kubernetes pod.
    
    Returns:
        bool: True if running in Kubernetes, False otherwise
    """
    # Kubernetes sets these service account files
    k8s_files = [
        "/var/run/secrets/kubernetes.io/serviceaccount/token",
        "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
    ]
    
    if any(pathlib.Path(f).exists() for f in k8s_files):
        return True
    
    # Check for Kubernetes environment variables
    k8s_env_vars = [
        "KUBERNETES_SERVICE_HOST",
        "KUBERNETES_SERVICE_PORT",
        "KUBERNETES_PORT"
    ]
    
    return any(var in os.environ for var in k8s_env_vars)
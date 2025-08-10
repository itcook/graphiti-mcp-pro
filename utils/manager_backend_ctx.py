"""
Management backend context manager

Provides context manager for management backend availability and operations.
"""

import os
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
import aiohttp


def get_manager_backend_url() -> str:
    """Get management backend URL"""
    host = os.environ.get('MANAGER_BACKEND_HOST', 'localhost')
    port = os.environ.get('MANAGER_BACKEND_PORT', '7072')
    return f"http://{host}:{port}"


class ManagerBackendUnavailableError(Exception):
    """Raised when management backend is not available"""
    pass


class ManagerBackend:
    """Management backend client context"""

    def __init__(self, url: str, timeout: int = 5):
        self.url = url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None
        self.is_available = False

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        # Check health on entry
        try:
            async with self.session.get(f"{self.url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    self.is_available = data.get('status') == 'OK'
                else:
                    self.is_available = False
        except Exception:
            # Silently handle health check failures
            self.is_available = False

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    def _check_availability(self):
        """Check if management backend is available"""
        if not self.is_available or not self.session:
            raise ManagerBackendUnavailableError("Management backend is not available")

    async def get_settings(self) -> Dict[str, Any]:
        """Get settings from management backend

        Returns:
            Dict containing all settings

        Raises:
            ManagerBackendUnavailableError: If backend is not available
            Exception: If request fails
        """
        self._check_availability()

        try:
            async with self.session.get(f"{self.url}/api/settings/") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get settings, status: {response.status}")
        except Exception as e:
            # Print error for debugging but still raise the exception
            print(f"Error getting settings from management backend: {e}")
            raise

    async def create_log(self, level: str, message: str, source: Optional[str] = None) -> Dict[str, Any]:
        """Create a log entry

        Args:
            level: Log level ('info', 'warn', 'error', 'debug')
            message: Log message
            source: Optional source identifier

        Returns:
            Dict containing the created log entry

        Raises:
            ManagerBackendUnavailableError: If backend is not available
            Exception: If request fails
        """
        self._check_availability()

        log_data = {
            "level": level,
            "message": message,
            "source": source
        }

        try:
            async with self.session.post(f"{self.url}/api/logs/", json=log_data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to create log entry, status: {response.status}")
        except Exception as e:
            # Print error for debugging but still raise the exception
            print(f"Error creating log entry: {e}")
            raise

    async def create_token_usage(
        self,
        llm_model_name: str,
        episode_name: str,
        response_model: str,
        completion_tokens: int,
        prompt_tokens: int,
        total_tokens: int
    ) -> Dict[str, Any]:
        """Create a token usage record

        Args:
            llm_model_name: Name of the LLM model
            episode_name: Name of the episode/conversation
            response_model: Response model type
            completion_tokens: Number of completion tokens
            prompt_tokens: Number of prompt tokens
            total_tokens: Total number of tokens

        Returns:
            Dict containing the created token usage record

        Raises:
            ManagerBackendUnavailableError: If backend is not available
            Exception: If request fails
        """
        self._check_availability()

        token_usage_data = {
            "llm_model_name": llm_model_name,
            "episode_name": episode_name,
            "response_model": response_model,
            "completion_tokens": completion_tokens,
            "prompt_tokens": prompt_tokens,
            "total_tokens": total_tokens
        }

        try:
            async with self.session.post(f"{self.url}/api/token-usage/", json=token_usage_data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to create token usage record, status: {response.status}")
        except Exception as e:
            # Print error for debugging but still raise the exception
            print(f"Error creating token usage record: {e}")
            raise


@asynccontextmanager
async def available_manager_backend():
    """Context manager for management backend availability

    Only yields if the backend is available, otherwise raises ManagerBackendUnavailableError.

    Raises:
        ManagerBackendUnavailableError: If backend is not available
    """
    backend_url = get_manager_backend_url()
    async with ManagerBackend(backend_url) as backend:
        backend._check_availability()
        yield backend

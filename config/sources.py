"""
Configuration sources

Implements abstract configuration source interface and concrete implementations
for different configuration sources (environment variables, management backend).
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .constants import CONFIG_METADATA, ConfigType
from .exceptions import ConfigSourceError
from utils import logger

class ConfigSource(ABC):
    """Abstract configuration source interface"""
    
    @abstractmethod
    async def get_values(self, keys: list[str]) -> Dict[str, Any]:
        """Get configuration values for the specified keys
        
        Args:
            keys: List of configuration keys to retrieve
            
        Returns:
            Dictionary mapping keys to their values
        """
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """Get source priority (lower number = higher priority)"""
        pass

class EnvironmentConfigSource(ConfigSource):
    """Environment variables configuration source"""
    
    def get_priority(self) -> int:
        return 100  # Lower priority than management backend
    
    def _convert_value(self, key: str, value: str) -> Any:
        """Convert string value to appropriate type based on metadata"""
        metadata = CONFIG_METADATA.get(key, {})
        config_type = metadata.get('type', ConfigType.STRING)
        
        try:
            if config_type == ConfigType.INTEGER:
                return int(value)
            elif config_type == ConfigType.FLOAT:
                return float(value)
            elif config_type == ConfigType.BOOLEAN:
                return value.lower() in ('true', '1', 'yes', 'on')
            else:  # STRING
                return value
        except (ValueError, AttributeError) as e:
            raise ConfigSourceError(f"Type conversion failed for {key}={value}: {e}")
    
    async def get_values(self, keys: list[str]) -> Dict[str, Any]:
        """Get configuration values from environment variables"""
        result = {}
        
        for key in keys:
            if key not in CONFIG_METADATA:
                logger.warning(f"Unknown configuration key: {key}")
                continue
                
            metadata = CONFIG_METADATA[key]
            env_key = metadata.get('env_key')
            
            if env_key and (env_value := os.environ.get(env_key)):
                try:
                    result[key] = self._convert_value(key, env_value)
                    logger.debug(f"Retrieved {key} from environment variable {env_key}")
                except ConfigSourceError as e:
                    logger.error(f"Failed to convert environment variable {env_key}: {e}")
                    
        return result

class ManagerBackendConfigSource(ConfigSource):
    """Management backend configuration source"""
    
    def get_priority(self) -> int:
        return 10  # Higher priority than environment variables
    
    async def get_values(self, keys: list[str]) -> Dict[str, Any]:
        """Get configuration values from management backend"""
        
        try:
            from utils.manager_backend_ctx import (
                available_manager_backend, 
                ManagerBackendUnavailableError
            )
            
            async with available_manager_backend() as backend:
                data = await backend.get_settings()
                result = {k: data[k] for k in keys if k in data}
                
                if result:
                    logger.debug(f"Retrieved {list(result.keys())} from management backend")
                    
                return result
                
        except ManagerBackendUnavailableError:
            logger.debug("Management backend is not available")
            return {}
        except Exception as e:
            logger.debug(f"Error getting settings from management backend: {e}")
            return {}

class DefaultValueConfigSource(ConfigSource):
    """Default values configuration source (lowest priority)"""
    
    def get_priority(self) -> int:
        return 1000  # Lowest priority
    
    async def get_values(self, keys: list[str]) -> Dict[str, Any]:
        """Get default values for configuration keys"""
        result = {}
        
        for key in keys:
            metadata = CONFIG_METADATA.get(key, {})
            if 'default' in metadata:
                result[key] = metadata['default']
                
        return result

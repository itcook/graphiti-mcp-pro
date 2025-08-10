"""
Configuration models

Defines configuration models with automatic fallback mechanisms and
modern async configuration creation patterns.
"""

from abc import ABC
from typing import Set, Type, TypeVar, Optional, Dict, Any
from pydantic import BaseModel, Field
from utils import logger
import os
from .manager import config_manager
from .exceptions import ConfigValidationError
from graphiti_core.llm_client.config import LLMConfig


T = TypeVar('T', bound='BaseConfig')

class BaseConfig(BaseModel, ABC):
    """Base configuration class with common functionality"""
    
    @classmethod
    def get_config_keys(cls) -> Set[str]:
        """Get configuration keys from field aliases"""
        keys = set()
        for field_name, field_info in cls.model_fields.items():
            key = field_info.alias or field_name
            keys.add(key)
        return keys
    
    @classmethod
    async def acquire(cls: Type[T]) -> T:
        """Create configuration instance from configuration manager"""
        
        keys = list(cls.get_config_keys())
        config_data = await config_manager.get_config(keys)
        
        try:
            instance = cls.model_validate(config_data)
            logger.debug(f"Created {cls.__name__} instance")
            return instance
        except Exception as e:
            logger.error(f"Failed to create {cls.__name__}: {e}")
            raise ConfigValidationError(f"Configuration validation failed for {cls.__name__}: {e}")

class Neo4jConfig(BaseConfig):
    """Neo4j database configuration"""
    uri: str = Field(alias='neo4j_uri', description='Neo4j database URI')
    user: str = Field(alias='neo4j_user', description='Neo4j username')
    password: str = Field(alias='neo4j_password', description='Neo4j password')

class LLMCompatConfig(BaseConfig):
    """LLM configuration (primary AI model)"""
    api_key: Optional[str] = Field(default=None, alias='llm_api_key', description='LLM API key')
    base_url: str = Field(alias='llm_base_url', description='LLM API base URL')
    model: str = Field(alias='llm_model_name', description='LLM model name')
    temperature: float = Field(alias='llm_temperature', description='LLM temperature')

class EmbedderCompatConfig(BaseConfig):
    """Embedder configuration"""
    model: str = Field(alias='embedding_model_name', description='Embedding model name')
    api_key: Optional[str] = Field(default=None, alias='embedding_api_key', description='Embedding API key')
    base_url: str = Field(alias='embedding_base_url', description='Embedding API base URL')



class SmallLLMCompatConfig(BaseConfig):
    """Reranker configuration"""
    api_key: Optional[str] = Field(default=None, alias='small_llm_api_key', description='Reranker API key')
    base_url: str = Field(alias='small_llm_base_url', description='Reranker API base URL')
    model: str = Field(alias='small_llm_model_name', description='Reranker model name')
    
    def is_same_as_llm(self, llm_config: LLMCompatConfig | LLMConfig) -> bool:
        """Check if small LLM config is same as main LLM config"""
        return (self.api_key == llm_config.api_key and
                self.base_url == llm_config.base_url and
                self.model == llm_config.model)
class MCPConfig(BaseConfig):
    """MCP specific settings"""
    enable_sync_return: bool = Field(alias='enable_sync_return', description='Enable synchronous return')

class LogSetting(BaseConfig):
    """Log specific settings"""
    log_save_days: int = Field(alias='log_save_days', description='Number of days to keep logs')

class GraphitiCompatConfig(BaseConfig):
    """Main Graphiti configuration with all sub-configurations"""
    neo4j: Neo4jConfig
    llm: LLMCompatConfig
    embedder: EmbedderCompatConfig
    small_llm: SmallLLMCompatConfig
    semaphore_limit: int = Field(alias='semaphore_limit', description='Maximum concurrent operations')
    
    @classmethod
    async def acquire(cls) -> 'GraphitiCompatConfig':
        """Create complete Graphiti configuration with fallback mechanisms"""

        try:
            # Create sub-configs via manager-driven fallbacks
            neo4j_config = await Neo4jConfig.acquire()
            llm_config = await LLMCompatConfig.acquire()
            embedder_config = await EmbedderCompatConfig.acquire()
            small_llm_config = await SmallLLMCompatConfig.acquire()

            # Get semaphore_limit configuration
            semaphore_config = await config_manager.get_config(['semaphore_limit'])

            # Create main configuration
            instance = cls(
                neo4j=neo4j_config,
                llm=llm_config,
                embedder=embedder_config,
                small_llm=small_llm_config,
                semaphore_limit=semaphore_config.get('semaphore_limit', 10)
            )

            logger.info("Successfully created complete GraphitiCompatConfig with fallback mechanisms")
            return instance

        except Exception as e:
            logger.error(f"Failed to create GraphitiCompatConfig: {e}")
            raise ConfigValidationError(f"GraphitiCompatConfig creation failed: {e}")

    @classmethod
    def get_config_keys(cls) -> Set[str]:
        """Get all configuration keys from nested models"""
        keys = set()
        keys.update(Neo4jConfig.get_config_keys())
        keys.update(LLMCompatConfig.get_config_keys())
        keys.update(EmbedderCompatConfig.get_config_keys())
        keys.update(SmallLLMCompatConfig.get_config_keys())
        # Add semaphore_limit key
        keys.add('semaphore_limit')
        return keys

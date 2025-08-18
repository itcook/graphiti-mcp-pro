"""
Configuration constants and metadata

Centralized configuration metadata management with support for fallback mechanisms.
"""

from enum import Enum
from typing import Dict, Any, Optional, List

class ConfigType(Enum):
    """Configuration value types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"

class ConfigGroup(Enum):
    """Configuration groups for logical organization"""
    LLM = "llm"
    EMBEDDER = "embedder"
    RERANKER = "reranker"
    NEO4J = "neo4j"
    SYSTEM = "system"

# Configuration metadata with fallback support
CONFIG_METADATA: Dict[str, Dict[str, Any]] = {
    # LLM Configuration (Primary)
    'llm_api_key': {
        'env_key': 'LLM_API_KEY',
        'type': ConfigType.STRING,
        'required': False,
        'sensitive': True,
        'nullable': True,
        'group': ConfigGroup.LLM,
        'description': 'LLM API key'
    },
    'llm_base_url': {
        'env_key': 'LLM_BASE_URL',
        'type': ConfigType.STRING,
        'required': True,
        'group': ConfigGroup.LLM,
        'description': 'LLM API base URL',
        'validation': {
            # not work if set 'regex' or 'pattern'
            'schema_extra': {
                'pattern': r'^https?://.*$'
            }
        }
    },
    'llm_model_name': {
        'env_key': 'LLM_MODEL_NAME',
        'type': ConfigType.STRING,
        'required': True,
        'group': ConfigGroup.LLM,
        'description': 'LLM model name'
    },
    'llm_temperature': {
        'env_key': 'LLM_TEMPERATURE',
        'type': ConfigType.FLOAT,
        'default': 0.0,
        'group': ConfigGroup.LLM,
        'description': 'LLM temperature',
        'validation': {
            'ge': 0.0,
            'le': 2.0
        }
    },

    # Embedder Configuration (with LLM fallback)
    'embedding_model_name': {
        'env_key': 'EMBEDDING_MODEL_NAME',
        'type': ConfigType.STRING,
        'required': False,
        'group': ConfigGroup.EMBEDDER,
        'fallback_key': 'llm_model_name',
        'required_in_group': True,
        'description': 'Embedding model name'
    },
    'embedding_api_key': {
        'env_key': 'EMBEDDING_API_KEY',
        'type': ConfigType.STRING,
        'required': False,
        'sensitive': True,
        'nullable': True,
        'group': ConfigGroup.EMBEDDER,
        'fallback_key': 'llm_api_key',
        'description': 'Embedding API key'
    },
    'embedding_base_url': {
        'env_key': 'EMBEDDING_BASE_URL',
        'type': ConfigType.STRING,
        'required': False,
        'group': ConfigGroup.EMBEDDER,
        'fallback_key': 'llm_base_url',
        'required_in_group': True,
        'description': 'Embedding API base URL',
        'validation': {
            'schema_extra': {
                'pattern': r'^https?://.*$'
            }

        }
    },

    # Reranker Configuration (with LLM fallback)
    'small_llm_model_name': {
        'env_key': 'SMALL_LLM_MODEL_NAME',
        'type': ConfigType.STRING,
        'required': False,
        'group': ConfigGroup.RERANKER,
        'fallback_key': 'llm_model_name',
        'required_in_group': True,
        'description': 'Small LLM model name for reranking'
    },
    'small_llm_api_key': {
        'env_key': 'SMALL_LLM_API_KEY',
        'type': ConfigType.STRING,
        'required': False,
        'sensitive': True,
        'nullable': True,
        'group': ConfigGroup.RERANKER,
        'fallback_key': 'llm_api_key',
        'description': 'Reranker (small model) API key'
    },
    'small_llm_base_url': {
        'env_key': 'SMALL_LLM_BASE_URL',
        'type': ConfigType.STRING,
        'required': False,
        'group': ConfigGroup.RERANKER,
        'fallback_key': 'llm_base_url',
        'required_in_group': True,
        'description': 'Reranker (small model) API base URL',
        'validation': {
            'schema_extra': {
                'pattern': r'^https?://.*$'
            }
        }
    },

    # Neo4j Configuration
    'neo4j_uri': {
        'env_key': 'NEO4J_URI',
        'type': ConfigType.STRING,
        'default': 'bolt://neo4j:7687',
        'group': ConfigGroup.NEO4J,
        'description': 'Neo4j database URI'
    },
    'neo4j_user': {
        'env_key': 'NEO4J_USER',
        'type': ConfigType.STRING,
        'default': 'neo4j',
        'group': ConfigGroup.NEO4J,
        'description': 'Neo4j username'
    },
    'neo4j_password': {
        'env_key': 'NEO4J_PASSWORD',
        'type': ConfigType.STRING,
        'default': 'graphiti',
        'sensitive': True,
        'group': ConfigGroup.NEO4J,
        'description': 'Neo4j password'
    },

    # System Configuration
    'semaphore_limit': {
        'env_key': 'SEMAPHORE_LIMIT',
        'type': ConfigType.INTEGER,
        'default': 20,
        'group': ConfigGroup.SYSTEM,
        'description': 'Maximum number of concurrent operations',
        'validation': {
            'ge': 1,
            'le': 100
        }
    },
    'enable_sync_return': {
        'env_key': 'ENABLE_SYNC_RETURN',
        'type': ConfigType.BOOLEAN,
        'default': False,
        'group': ConfigGroup.SYSTEM,
        'description': 'Enable synchronous return'
    },
    'log_save_days': {
        'env_key': 'LOG_SAVE_DAYS',
        'type': ConfigType.INTEGER,
        'default': 7,
        'group': ConfigGroup.SYSTEM,
        'description': 'Number of days to keep logs',
        'validation': {
            'ge': 3,
            'le': 30
        }
    },
    'clean_logs_at_hour': {
        'env_key': 'CLEAN_LOGS_AT_HOUR',
        'type': ConfigType.INTEGER,
        'default': 12,
        'group': ConfigGroup.SYSTEM,
        'description': 'Number of hours to wait before cleaning logs',
        'validation': {
            'ge': 0,
            'le': 23
        }
    }
}

# Fallback configuration mapping
FALLBACK_GROUPS = {
    ConfigGroup.EMBEDDER: ConfigGroup.LLM,
    ConfigGroup.RERANKER: ConfigGroup.LLM
}

def get_config_keys_by_group(group: ConfigGroup) -> List[str]:
    """Get all configuration keys for a specific group"""
    return [key for key, metadata in CONFIG_METADATA.items() 
            if metadata.get('group') == group]

def get_fallback_key(key: str) -> Optional[str]:
    """Get fallback key for a configuration key"""
    return CONFIG_METADATA.get(key, {}).get('fallback_key')

def is_required_config(key: str) -> bool:
    """Check if a configuration key is required"""
    return CONFIG_METADATA.get(key, {}).get('required', False)

def get_default_value(key: str) -> Any:
    """Get default value for a configuration key"""
    return CONFIG_METADATA.get(key, {}).get('default')

def is_sensitive_config(key: str) -> bool:
    """Check if a configuration key contains sensitive data"""
    return CONFIG_METADATA.get(key, {}).get('sensitive', False)

def get_sensitive_config_keys() -> List[str]:
    """Get all sensitive configuration keys"""
    return [key for key in CONFIG_METADATA.keys() if is_sensitive_config(key)]

def get_required_config_keys() -> List[str]:
    """Get all required configuration keys"""
    return [key for key in CONFIG_METADATA.keys() if is_required_config(key)]

def get_all_config_keys() -> List[str]:
    """Get all configuration keys"""
    return list(CONFIG_METADATA.keys())

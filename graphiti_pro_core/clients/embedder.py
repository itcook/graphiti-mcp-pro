"""
Embedder client creation module

Responsible for creating Embedder client instances based on configuration.
"""

from graphiti_core.embedder.client import EmbedderClient
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig

from config import EmbedderCompatConfig


def create_embedder_client(config: EmbedderCompatConfig) -> EmbedderClient | None:
    """
    Create Embedder client based on configuration
    
    Args:
        config: Embedder configuration instance
        
    Returns:
        EmbedderClient instance, returns None if creation fails
    """
    # Support for local embedding models (no API key required)
    # Support for local embedding models (no API key required)
    embedder_config = OpenAIEmbedderConfig(
        api_key=config.api_key or "dummy",
        base_url=config.base_url,
        embedding_model=config.model
    )

    return OpenAIEmbedder(config=embedder_config)

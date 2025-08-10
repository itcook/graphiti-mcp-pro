"""
GraphitiClient - Encapsulates Graphiti client initialization and management.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from graphiti_core import Graphiti

from utils import logger


class GraphitiClient:
    """Graphiti client management class."""

    @staticmethod
    async def initialize() -> "Graphiti":
        """Initialize the Graphiti client with the configured settings.

        Returns:
            Initialized Graphiti client instance

        Raises:
            ValueError: If required configuration is missing
            Exception: If initialization fails
        """
        try:
            
            # Import configuration models, manager
            from config import GraphitiCompatConfig, config_manager
            
            # Refresh config cache to ensure latest values are used
            await config_manager.refresh_cache()

            # Build configurations
            graphiti_config = await GraphitiCompatConfig.acquire()
    
            # Create LLM client with dual model support
            from .llm import create_llm_client
            llm_client = create_llm_client(graphiti_config.llm, graphiti_config.small_llm)
            if not llm_client:
                # If custom entities are enabled, we must have an LLM client
                raise ValueError('LLM_BASE_URL and LLM_API_KEY must be set when custom entities are enabled')

            # Validate Neo4j configuration
            if not graphiti_config.neo4j.uri or not graphiti_config.neo4j.user or not graphiti_config.neo4j.password:
                raise ValueError('NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD must be set')

            # Create embedder client if possible
            from .embedder import create_embedder_client
            embedder_client = create_embedder_client(graphiti_config.embedder)
            if embedder_client is None:
                logger.error("❌ Embedder client is None! This will cause embedding to be skipped.")

            # Create compatible cross_encoder using small model config
            from .reranker import create_reranker_client
            cross_encoder_client = create_reranker_client(graphiti_config.small_llm)
            if cross_encoder_client is None:
                logger.error("❌ Cross encoder client is None! This will cause ranking to be skipped.")

            # Initialize Graphiti client
            from graphiti_core import Graphiti
            graphiti_client = Graphiti(
                uri=graphiti_config.neo4j.uri,
                user=graphiti_config.neo4j.user,
                password=graphiti_config.neo4j.password,
                llm_client=llm_client,
                embedder=embedder_client,
                cross_encoder=cross_encoder_client,
                max_coroutines=graphiti_config.semaphore_limit,
            )

            # Set global variables in modules using state management
            from .__state__ import set_graphiti_client

            set_graphiti_client(graphiti_client)

            # Initialize the graph database with Graphiti's indices
            await graphiti_client.build_indices_and_constraints()
            logger.info('✅ Graphiti client initialized successfully')

            # Log configuration details for transparency
            if llm_client:
                logger.info(f'💡 Using LLM model: {graphiti_config.llm.model}')
                logger.info(f'💡 Using LLM base URL: {graphiti_config.llm.base_url}')
                logger.info(f'💡 Using temperature: {graphiti_config.llm.temperature}')
            else:
                logger.warning('⚠️ No LLM client configured - entity extraction will be limited')

            if embedder_client:
                logger.info(f'💡 Using embedding model: {graphiti_config.embedder.model}')
                logger.info(f'💡 Using embedding base URL: {graphiti_config.embedder.base_url}')
            else:
                logger.warning('⚠️ No embedder client configured')

            logger.info(f'💡 Using concurrency limit: {graphiti_config.semaphore_limit}')

            return graphiti_client

        except Exception as e:
            logger.error(f'❌ Failed to initialize Graphiti: {str(e)}')
            raise

    @staticmethod
    async def cleanup() -> None:
        """Clean up the Graphiti client instance and related resources."""
        from .__state__ import get_graphiti_client, set_graphiti_client

        graphiti_client = get_graphiti_client()
        if graphiti_client is not None:
            try:
                # Close Neo4j driver connection
                if hasattr(graphiti_client, 'driver') and graphiti_client.driver:
                    await graphiti_client.driver.close()
                logger.info("✅ Graphiti client cleaned up successfully")
            except Exception as e:
                logger.error(f"❌ Error cleaning up Graphiti client: {str(e)}")
            finally:
                set_graphiti_client(None)

# Convenience function for backward compatibility
async def initialize_graphiti_client() -> "Graphiti":
    """Initialize the Graphiti client.

    This is a convenience function that delegates to GraphitiClient.initialize_graphiti_client().
    """
    return await GraphitiClient.initialize()

async def cleanup_graphiti_client() -> None:
    """Clean up Graphiti client instance and related resources."""
    return await GraphitiClient.cleanup()

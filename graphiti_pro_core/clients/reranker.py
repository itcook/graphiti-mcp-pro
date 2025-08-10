"""
Reranker client creation module

Responsible for creating Reranker client instances based on configuration.
"""

from typing import Any

from openai import AsyncOpenAI

from graphiti_core.prompts.models import Message
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.cross_encoder.client import CrossEncoderClient
from graphiti_core.helpers import semaphore_gather
from graphiti_core.prompts import Message

import numpy as np

from config import SmallLLMCompatConfig, config_manager
from utils import logger


class RerankerCompatClient(CrossEncoderClient):
    """
    Reranker compatible client for cross-encoder functionality
    """

    def __init__(self, config: LLMConfig):
        """
        Initialize the RerankerCompatClient with LLM configuration.
        """
        self.config = config
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )

    async def rank(self, query: str, passages: list[str]) -> list[tuple[str, float]]:
        """Rank passages based on relevance to query"""
        openai_messages_list: Any = [
            [
                Message(
                    role='system',
                    content='You are an expert tasked with determining whether the passage is relevant to the query',
                ),
                Message(
                    role='user',
                    content=f"""
                           Respond with "True" if PASSAGE is relevant to QUERY and "False" otherwise.
                           <PASSAGE>
                           {passage}
                           </PASSAGE>
                           <QUERY>
                           {query}
                           </QUERY>
                           """,
                ),
            ]
            for passage in passages
        ]

        try:
            max_concurrent = config_manager.get_config(['semaphore_limit'])['semaphore_limit']
            responses = await semaphore_gather(
                *[
                    self.client.chat.completions.create(
                        model=self.config.model,
                        messages=[
                            {'role': msg.role, 'content': msg.content}
                            for msg in messages
                        ],
                        max_tokens=10,
                        temperature=0.0,
                    )
                    for messages in openai_messages_list
                ],
                max_concurrent=max_concurrent,
            )

            # Process responses and assign scores
            ranked_passages = []
            for i, response in enumerate(responses):
                content = response.choices[0].message.content.strip().lower()
                # Simple scoring: True = 1.0, False = 0.0
                score = 1.0 if content == 'true' else 0.0
                ranked_passages.append((passages[i], score))

            # Sort by score (descending)
            ranked_passages.sort(key=lambda x: x[1], reverse=True)
            return ranked_passages

        except Exception as e:
            logger.error(f"Error in reranker ranking: {e}")
            # Return passages with neutral scores if ranking fails
            return [(passage, 0.5) for passage in passages]


def create_reranker_client(config: SmallLLMCompatConfig) -> RerankerCompatClient:
    """
    Create a reranker client based on configuration
    
    Args:
        config: Reranker configuration instance
        
    Returns:
        RerankerCompatClient instance
    """
    llm_config = LLMConfig(
        api_key=config.api_key,
        base_url=config.base_url,
        model=config.model,
    )
    
    return RerankerCompatClient(llm_config)

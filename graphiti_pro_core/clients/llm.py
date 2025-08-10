import typing
from typing import Any, ClassVar

import instructor
from openai import AsyncOpenAI
from pydantic import BaseModel

from graphiti_core.prompts.models import Message
from graphiti_core.llm_client.client import MULTILINGUAL_EXTRACTION_RESPONSES, LLMClient
from graphiti_core.llm_client.config import DEFAULT_MAX_TOKENS, LLMConfig, ModelSize
from graphiti_core.llm_client.errors import RateLimitError, RefusalError

from config.models import LLMCompatConfig, SmallLLMCompatConfig

from utils import logger
from utils.usage_collector import usage_collector, get_current_episode_name


class LLMCompatClient(LLMClient):
    """
    OpenAI API compatible client based on instructor library

    Solves LLM JSON standardized output issues:
    - Automatic conversion from Pydantic models to structured output
    - Built-in retry and validation mechanisms
    - Support for complex nested structures
    - Better error handling and debugging information
    """

    # Maintain compatibility with other clients
    MAX_RETRIES: ClassVar[int] = 3

    def __init__(
        self,
        config: LLMConfig | None = None,
        small_config: SmallLLMCompatConfig | None = None,
        cache: bool = False,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ):
        if cache:
            raise NotImplementedError('Caching is not implemented for LLMCompatClient')

        if config is None:
            config = LLMConfig()

        super().__init__(config, cache)
        self.max_tokens = max_tokens

        # Main model client
        self.main_client = instructor.from_openai(AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        ))

        # Determine if we need a separate small model client
        if (small_config and not small_config.is_same_as_llm(config)):
            self.small_client = instructor.from_openai(AsyncOpenAI(
                api_key=small_config.api_key,
                base_url=small_config.base_url,
            ))
            self.small_config = small_config
            logger.info(f"🔹 Small model configured: {small_config.model} @ {small_config.base_url} (separate auth)")
        else:
            self.small_client = self.main_client
            self.small_config = config
            logger.info("🔸 Using main model for all tasks (small model config identical to main)")

        # Maintain backward compatibility, set original client attribute to main client
        self.client = self.main_client

    def _get_client_and_config(self, model_size: ModelSize) -> tuple[Any, LLMConfig]:
        """Select appropriate client and config based on model size"""
        if model_size == ModelSize.small:
            if self.small_client != self.main_client:
                _config: LLMConfig = LLMConfig(
                    api_key=self.small_config.api_key,
                    base_url=self.small_config.base_url,
                    model=self.small_config.model,
                    temperature=self.config.temperature # Use main model temperature
                )
                logger.debug(f"🔹 Using small model: {self.small_config.model} @ {self.small_config.base_url}")
            else:
                logger.debug(f"🔸 Using main model for small task: {self.config.model}")
            return self.small_client, _config
        else:
            logger.debug(f"🔸 Using main model: {self.config.model} @ {self.config.base_url}")
            return self.main_client, self.config

    def _convert_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert internal Message format to OpenAI format"""
        return [
            {
                "role": message.role,
                "content": message.content
            }
            for message in messages
        ]

    async def _generate_response(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        model_size: ModelSize = ModelSize.medium,
    ) -> dict[str, typing.Any]:
        """Generate structured response using appropriate model"""
        try:
            # Select appropriate client and config based on model size
            client, config = self._get_client_and_config(model_size)

            # Add multilingual support prompt
            messages[0].content += MULTILINGUAL_EXTRACTION_RESPONSES

            # Convert message format
            openai_messages = self._convert_messages(messages)

            # Cause some LLM will occasionally fails with default max_tokens and don't know why
            # use the 'safe_max_tokens' to avoid this issue
            safe_max_tokens = min(max_tokens, 8192)

            # Log the model being used
            model_name = config.model
            logger.debug(f"🎯 Using model: {model_name} (size: {model_size.value})")
            logger.debug("🔍 Sending messages to LLM (LLMCompatClient with Instructor):")
            
            # cloud enable this logger for logging the input messages if you need
            # for i, msg in enumerate(openai_messages):
            #     content = msg["content"]
            #     logger.info(f"  Message {i+1} ({msg['role']}): {content[:500]}...")
            #     if len(content) > 500:
            #         logger.info(f"    [Message truncated, full length: {len(content)} chars]")

            if response_model is not None:
                # Use instructor's response_model parameter
                logger.info(f"🎯 Using response_model: {response_model.__name__} with {model_name}")
                structured_response, completion = await client.chat.completions.create_with_completion(
                    model=model_name,
                    messages=openai_messages,
                    response_model=response_model,
                    max_tokens=safe_max_tokens,
                    temperature=config.temperature,
                )
                
                if structured_response is None:
                    raise ValueError("Structured response is None")
                
                response_model_name = "EntityAttributes" if response_model.__name__.startswith("EntityAttributes_") else response_model.__name__
                logger.info(f"✅ Responded with Structured for {response_model_name}")
                # instructor directly returns Pydantic object, convert to dictionary
                result = structured_response.model_dump()

                # Print total tokens usage and collect statistics
                if hasattr(completion, 'usage') and completion.usage:
                    # Collect usage statistics
                    await self._collect_usage_stats(
                        model_name=model_name,
                        response_model=response_model,
                        completion_tokens=completion.usage.completion_tokens,
                        prompt_tokens=completion.usage.prompt_tokens,
                        total_tokens=completion.usage.total_tokens
                    )

                # cloud enable this logger for logging the output messages if you need
                # logger.info(f"✅ Structured Response: {result}")
                return result
            else:
                # Use regular text generation when no response_model
                logger.info(f"📝 Using text generation mode with {model_name}")
                logger.info(f"🔧 Using safe_max_tokens: {safe_max_tokens} (original: {max_tokens})")
                response = await client.chat.completions.create(
                    model=model_name,
                    messages=openai_messages,
                    max_tokens=safe_max_tokens,
                    temperature=config.temperature,
                )
                result = {"content": response.choices[0].message.content}

                # Print total tokens usage and collect statistics
                if hasattr(response, 'usage') and response.usage:

                    # Collect usage statistics for text responses
                    await self._collect_usage_stats(
                        model_name=model_name,
                        response_model=None,  # No structured response model for text
                        completion_tokens=completion.usage.completion_tokens,
                        prompt_tokens=completion.usage.prompt_tokens,
                        total_tokens=completion.usage.total_tokens
                    )

                logger.info(f"📄 Text responded")

                # cloud enable this logger for logging the output messages if you need
                # logger.info(f"📄 Text Response: {result}")
                return result

        except instructor.exceptions.InstructorRetryException as e:
            logger.error(f'❌ Instructor retry failed: {e}')
            raise RefusalError(f"Failed to generate valid structured output: {e}")
        except Exception as e:
            logger.error(f'❌ Error in generating LLM response: {e}')
            if "rate limit" in str(e).lower():
                raise RateLimitError from e
            raise

    async def generate_response(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int | None = None,
        model_size: ModelSize = ModelSize.medium,
    ) -> dict[str, typing.Any]:
        """Public interface for generating responses"""
        if max_tokens is None:
            max_tokens = self.max_tokens

        # Directly call _generate_response, instructor has built-in retry mechanism
        return await self._generate_response(
            messages, response_model, max_tokens, model_size
        )

    async def _collect_usage_stats(
        self,
        model_name: str,
        response_model: type[BaseModel] | None,
        completion_tokens: int,
        prompt_tokens: int,
        total_tokens: int
    ):
        """Collect usage statistics and send to management backend"""
        try:
            # Get episode name from context
            episode_name = get_current_episode_name()

            # Determine response model name
            response_model_name = response_model.__name__ if response_model else None
            
            # handle EntityAttributes_xxx model name
            if (response_model_name is not None and response_model_name.startswith("EntityAttributes_")):
                response_model_name = "EntityAttributes"

            # Collect usage data
            await usage_collector.collect_usage(
                llm_model_name=model_name,
                episode_name=episode_name,
                response_model=response_model_name,
                completion_tokens=completion_tokens,
                prompt_tokens=prompt_tokens,
                total_tokens=total_tokens
            )

        except Exception as e:
            logger.error(f"📊 Error collecting usage statistics: {e}")
            # Don't let statistics collection errors affect the main flow

from config import LLMCompatConfig, SmallLLMCompatConfig

def create_llm_client(
    main_config: LLMCompatConfig,
    small_config: SmallLLMCompatConfig
) -> LLMClient:
    """
    Create an LLM client with dual model support

    Args:
        main_config: Main LLM configuration
        small_config: Small LLM configuration (guaranteed by fallback mechanism)

    Returns:
        LLMClient instance with dual model support
    """
    if not main_config.api_key:
        raise ValueError('LLM_API_KEY must be set when using OpenAI API')

    # Main model configuration
    main_llm_config = LLMConfig(
        api_key=main_config.api_key,
        base_url=main_config.base_url,
        model=main_config.model,
        temperature=main_config.temperature
    )

    return LLMCompatClient(
        config=main_llm_config,
        small_config=small_config
    )

"""
Token usage collector for LLM statistics
"""

import asyncio
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from utils import logger
from utils.manager_backend_ctx import available_manager_backend, ManagerBackendUnavailableError


@dataclass
class UsageData:
    """Token usage data structure"""
    llm_model_name: str
    episode_name: str
    response_model: str
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int
    timestamp: datetime


class UsageCollector:
    """Collects and queues token usage statistics for backend submission"""
    
    def __init__(self, max_queue_size: int = 1000):
        self.usage_queue: asyncio.Queue[UsageData] = asyncio.Queue(maxsize=max_queue_size)
        self.worker_running = False
        self._worker_task: Optional[asyncio.Task] = None
        
    async def collect_usage(
        self,
        llm_model_name: str,
        episode_name: str,
        response_model: str,
        completion_tokens: int,
        prompt_tokens: int,
        total_tokens: int
    ):
        """Collect usage data and add to queue for processing
        
        Args:
            llm_model_name: Name of the LLM model used
            episode_name: Name of the episode/conversation
            response_model: Response model type (e.g., 'EntityExtraction', 'text')
            completion_tokens: Number of completion tokens
            prompt_tokens: Number of prompt tokens  
            total_tokens: Total number of tokens
        """
        try:
            usage_data = UsageData(
                llm_model_name=llm_model_name,
                episode_name=episode_name,
                response_model=response_model,
                completion_tokens=completion_tokens,
                prompt_tokens=prompt_tokens,
                total_tokens=total_tokens,
                timestamp=datetime.now()
            )
            
            # Add to queue (non-blocking)
            try:
                self.usage_queue.put_nowait(usage_data)
                logger.debug(f"📊 Usage data queued for episode '{episode_name}' (tokens: {total_tokens})")
            except asyncio.QueueFull:
                logger.warning("📊 Usage queue is full, dropping usage data")
                
        except Exception as e:
            logger.error(f"📊 Error collecting usage data: {e}")
    
    async def start_worker(self):
        """Start the background worker to process usage queue"""
        if self.worker_running:
            return
            
        self.worker_running = True
        self._worker_task = asyncio.create_task(self._process_usage_queue())
        logger.info("📊 Usage collector worker started")
    
    async def stop_worker(self):
        """Stop the background worker"""
        if not self.worker_running:
            return
            
        self.worker_running = False
        
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
                
        logger.info("📊 Usage collector worker stopped")
    
    async def _process_usage_queue(self):
        """Background worker to process usage data queue"""
        logger.info("📊 Starting usage queue processing worker")
        
        while self.worker_running:
            try:
                # Wait for usage data with timeout
                try:
                    usage_data = await asyncio.wait_for(
                        self.usage_queue.get(), 
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Submit to management backend
                await self._submit_usage_data(usage_data)
                
            except asyncio.CancelledError:
                logger.info("📊 Usage queue worker cancelled")
                break
            except Exception as e:
                logger.error(f"📊 Error in usage queue worker: {e}")
                # Continue processing other items
                await asyncio.sleep(1)
    
    async def _submit_usage_data(self, usage_data: UsageData):
        """Submit usage data to management backend"""
        try:
            async with available_manager_backend() as backend:
                await backend.create_token_usage(
                    llm_model_name=usage_data.llm_model_name,
                    episode_name=usage_data.episode_name,
                    response_model=usage_data.response_model,
                    completion_tokens=usage_data.completion_tokens,
                    prompt_tokens=usage_data.prompt_tokens,
                    total_tokens=usage_data.total_tokens
                )
                
                logger.debug(
                    f"📊 Usage data submitted for episode '{usage_data.episode_name}' "
                    f"(model: {usage_data.llm_model_name}, tokens: {usage_data.total_tokens})"
                )
                
        except ManagerBackendUnavailableError:
            logger.debug("📊 Management backend unavailable, usage data not submitted")
        except Exception as e:
            logger.error(f"📊 Error submitting usage data: {e}")
    
    async def flush_queue(self):
        """Process all remaining items in the queue"""
        logger.info("📊 Flushing usage queue...")
        
        processed = 0
        while not self.usage_queue.empty():
            try:
                usage_data = self.usage_queue.get_nowait()
                await self._submit_usage_data(usage_data)
                processed += 1
            except asyncio.QueueEmpty:
                break
            except Exception as e:
                logger.error(f"📊 Error flushing usage data: {e}")
        
        if processed > 0:
            logger.info(f"📊 Flushed {processed} usage records")
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.usage_queue.qsize()


# Global usage collector instance
usage_collector = UsageCollector()


# Context manager for episode-scoped usage collection
class EpisodeUsageContext:
    """Context manager for collecting usage within an episode context"""
    
    def __init__(self, episode_name: str):
        self.episode_name = episode_name
        self.original_episode_name = None
        
    async def __aenter__(self):
        # Store current episode context (if any)
        self.original_episode_name = getattr(usage_collector, '_current_episode_name', None)
        usage_collector._current_episode_name = self.episode_name
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Restore previous episode context
        if self.original_episode_name is not None:
            usage_collector._current_episode_name = self.original_episode_name
        else:
            if hasattr(usage_collector, '_current_episode_name'):
                delattr(usage_collector, '_current_episode_name')


def get_current_episode_name() -> str | None:
    """Get current episode name from context, fallback to default"""
    return getattr(usage_collector, '_current_episode_name', None)

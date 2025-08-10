"""
Configuration manager

Centralized configuration management with multi-source support, caching,
and fallback mechanisms.
"""

from typing import Dict, Any, List, Optional
from threading import Lock
from .sources import (
    ConfigSource, 
    ManagerBackendConfigSource, 
    EnvironmentConfigSource, 
    DefaultValueConfigSource
)
from .constants import CONFIG_METADATA, FALLBACK_GROUPS, get_config_keys_by_group, is_required_config
from .exceptions import ConfigValidationError
from utils import logger


class ConfigManager:
    """Configuration manager with multi-source support and caching"""
    
    def __init__(self):
        # Initialize configuration sources in priority order
        self._sources: List[ConfigSource] = [
            ManagerBackendConfigSource(),
            EnvironmentConfigSource(),
            DefaultValueConfigSource()
        ]
        # Sort by priority (lower number = higher priority)
        self._sources.sort(key=lambda s: s.get_priority())
        
        # Configuration cache
        self._cache: Dict[str, Any] = {}
        self._cache_lock = Lock()
        self._cache_initialized = False
    
    async def get_config(self, keys: List[str]) -> Dict[str, Any]:
        """Get configuration values for specified keys
        
        Args:
            keys: List of configuration keys to retrieve
            
        Returns:
            Dictionary mapping keys to their values
            
        Raises:
            ConfigValidationError: If required configuration is missing
        """
        
        # Initialize cache if needed
        if not self._cache_initialized:
            await self._initialize_cache()
        
        result = {}
        
        # Get values from cache
        with self._cache_lock:
            for key in keys:
                if key in self._cache:
                    result[key] = self._cache[key]
        
        # Apply group-level fallback mechanism
        result = await self._apply_group_fallbacks(result, keys)

        # Validate required configurations (global required flags)
        self._validate_required_configs(result, keys)

        # Validate partial group constraints for fallback-enabled groups
        self._validate_group_partial_configs(result, keys)
        
        logger.debug(f"Retrieved configuration for keys: {list(result.keys())}")
        return result
    
    async def _initialize_cache(self) -> None:
        """Initialize configuration cache from all sources"""
        
        with self._cache_lock:
            if self._cache_initialized:
                return
            
            # Get all possible configuration keys
            all_keys = list(CONFIG_METADATA.keys())
            
            # Collect values from all sources
            for source in self._sources:
                try:
                    values = await source.get_values(all_keys)
                    # Only update cache with new values (higher priority sources win)
                    # Treat empty (None/"") as not provided, so lower priority sources can fill
                    for key, value in values.items():
                        if key not in self._cache and not self._is_empty(value):
                            self._cache[key] = value
                except Exception as e:
                    logger.warning(f"Error getting values from {source.__class__.__name__}: {e}")
            
            self._cache_initialized = True
            logger.info(f"Configuration cache initialized with {len(self._cache)} values")
    
    def _is_empty(self, value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str) and value.strip() == "":
            return True
        return False

    async def _apply_group_fallbacks(self, result: Dict[str, Any], requested_keys: List[str]) -> Dict[str, Any]:
        """Apply group-level fallback when all keys in a group are empty"""
        # Build groups touched by requested keys
        groups: Dict[Any, List[str]] = {}
        for key in requested_keys:
            meta = CONFIG_METADATA.get(key, {})
            group = meta.get('group')
            if group is None:
                continue
            groups.setdefault(group, []).append(key)

        # For each group that has a fallback mapping
        for group, _ in groups.items():
            if group not in FALLBACK_GROUPS:
                continue

            # Determine all keys of this group for full evaluation
            group_keys = get_config_keys_by_group(group)

            # Check if entire group is empty
            with self._cache_lock:
                all_empty = True
                for gk in group_keys:
                    val = self._cache.get(gk)
                    if not self._is_empty(val):
                        all_empty = False
                        break

            if all_empty:
                # Apply fallback from mapped group using per-key fallback_key mapping
                with self._cache_lock:
                    for gk in group_keys:
                        meta = CONFIG_METADATA.get(gk, {})
                        fallback_key = meta.get('fallback_key')
                        if fallback_key and fallback_key in self._cache:
                            result[gk] = self._cache[fallback_key]
                logger.info(f"Applied group fallback for {group.name} from {FALLBACK_GROUPS[group].name}")
            else:
                # Partially configured: ensure required_in_group fields get fallback if missing
                required_keys = [k for k in group_keys if CONFIG_METADATA.get(k, {}).get('required_in_group')]
                with self._cache_lock:
                    for rk in required_keys:
                        # Determine current value (prefer result override, then cache)
                        current_val = result.get(rk, self._cache.get(rk))
                        if self._is_empty(current_val):
                            fk = CONFIG_METADATA.get(rk, {}).get('fallback_key')
                            if fk and fk in self._cache and not self._is_empty(self._cache.get(fk)):
                                result[rk] = self._cache[fk]
                                logger.info(f"Applied required field fallback for {rk}: using {fk}")

        return result

    def _validate_group_partial_configs(self, result: Dict[str, Any], requested_keys: List[str]) -> None:
        """Validate that partially configured fallback-enabled groups meet required_in_group constraints"""
        # Build group -> keys mapping for requested keys
        group_to_keys: Dict[Any, List[str]] = {}
        for key in requested_keys:
            meta = CONFIG_METADATA.get(key, {})
            group = meta.get('group')
            if group is None:
                continue
            group_to_keys.setdefault(group, []).append(key)

        for group, _ in group_to_keys.items():
            if group not in FALLBACK_GROUPS:
                continue

            # Evaluate group's values presence (after group fallbacks)
            values = [result.get(k) for k in get_config_keys_by_group(group)]
            non_empty_count = sum(0 if self._is_empty(v) else 1 for v in values)
            if non_empty_count == 0:
                # Entire group empty -> either fallback applied or caller expects empty; no partial validation
                continue

            # If partially configured (not all keys provided), enforce required_in_group fields
            total_keys = len(get_config_keys_by_group(group))
            if non_empty_count < total_keys:
                required_keys = [k for k in get_config_keys_by_group(group)
                                 if CONFIG_METADATA.get(k, {}).get('required_in_group')]
                missing = [rk for rk in required_keys if self._is_empty(result.get(rk))]
                if missing:
                    names = ', '.join(missing)
                    raise ConfigValidationError(
                        f"Partial config invalid for group {group.name}: {names} is required when the group is partially configured"
                    )

        return None
    
    def _validate_required_configs(self, config: Dict[str, Any], requested_keys: List[str]) -> None:
        """Validate that all required configurations are present"""
        missing_required = []
        
        for key in requested_keys:
            if is_required_config(key) and (key not in config or config[key] is None):
                missing_required.append(key)
        
        if missing_required:
            raise ConfigValidationError(f"Missing required configuration: {missing_required}")
    
    async def refresh_cache(self) -> None:
        """Refresh configuration cache"""
        
        with self._cache_lock:
            self._cache.clear()
            self._cache_initialized = False
        
        await self._initialize_cache()
        logger.info("Configuration cache refreshed")
    
    def get_cached_value(self, key: str) -> Optional[Any]:
        """Get a single cached value synchronously"""
        with self._cache_lock:
            return self._cache.get(key)
    
    def clear_cache(self) -> None:
        """Clear configuration cache (mainly for testing)"""
        with self._cache_lock:
            self._cache.clear()
            self._cache_initialized = False

# Global configuration manager instance
config_manager = ConfigManager()

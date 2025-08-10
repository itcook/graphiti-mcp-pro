"""
Configuration exceptions

Defines all configuration-related exceptions for better error handling.
"""

class ConfigError(Exception):
    """Base configuration exception"""
    pass

class ConfigValidationError(ConfigError):
    """Configuration validation exception
    
    Raised when configuration validation fails, such as missing required fields
    or invalid field values.
    """
    pass

class ConfigSourceError(ConfigError):
    """Configuration source exception
    
    Raised when there are issues with configuration sources, such as
    type conversion failures or source unavailability.
    """
    pass

class ConfigFallbackError(ConfigError):
    """Configuration fallback exception
    
    Raised when fallback mechanism fails to provide valid configuration.
    """
    pass

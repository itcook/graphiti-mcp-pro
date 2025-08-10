import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ManagerConfig:
    """Application configuration class"""
    
    # Server configuration
    MANAGER_SERVER_PORT: int = int(os.getenv("MANAGER_SERVER_PORT", "7072"))
    
    # Encryption configuration
    CRYPTO_SECRET: str = os.getenv("CRYPTO_SECRET", "X@}XcfV]MKXbiP,i2k4wBZQbf7wot7et")
    CRYPTO_SALT: str = os.getenv("CRYPTO_SALT", "K8Zdm)0Cos^tFVdX")


# Configuration instance
manager_config = ManagerConfig()

"""Configuration settings for the Google Photos Upload tool."""

import os
from dataclasses import dataclass
from typing import List

@dataclass
class Config:
    """Configuration settings for the Google Photos Upload tool."""
    
    # API Configuration
    API_BASE_URL: str = "https://photoslibrary.googleapis.com/v1"
    SCOPES: List[str] = [
        "https://www.googleapis.com/auth/photoslibrary",
        "https://www.googleapis.com/auth/photoslibrary.sharing"
    ]
    
    # Authentication
    AUTH_PORT: int = 8080
    AUTH_HOST: str = "localhost"
    AUTH_SUCCESS_MESSAGE: str = "The auth flow is complete; you may close this window."
    
    # Upload Configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5  # seconds
    
    # Logging
    LOG_FORMAT: str = "%(asctime)s %(module)s.%(funcName)s:%(levelname)s:%(message)s"
    LOG_DATE_FORMAT: str = "%m/%d/%Y %I_%M_%S %p"
    DEFAULT_LOG_LEVEL: str = "INFO"
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create a Config instance from environment variables."""
        return cls(
            API_BASE_URL=os.getenv("GPHOTOS_API_BASE_URL", cls.API_BASE_URL),
            AUTH_PORT=int(os.getenv("GPHOTOS_AUTH_PORT", str(cls.AUTH_PORT))),
            AUTH_HOST=os.getenv("GPHOTOS_AUTH_HOST", cls.AUTH_HOST),
            MAX_RETRIES=int(os.getenv("GPHOTOS_MAX_RETRIES", str(cls.MAX_RETRIES))),
            RETRY_DELAY=int(os.getenv("GPHOTOS_RETRY_DELAY", str(cls.RETRY_DELAY))),
            DEFAULT_LOG_LEVEL=os.getenv("GPHOTOS_LOG_LEVEL", cls.DEFAULT_LOG_LEVEL)
        ) 
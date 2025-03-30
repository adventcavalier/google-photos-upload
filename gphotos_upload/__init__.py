"""
Google Photos Upload Tool

A tool for uploading photos to Google Photos with album organization.
"""

from .client import GooglePhotosClient
from .config import Config
from .exceptions import GooglePhotosError

__version__ = "1.0.0"
__all__ = ["GooglePhotosClient", "Config", "GooglePhotosError"] 
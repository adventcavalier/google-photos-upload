"""Custom exceptions for the Google Photos Upload tool."""

class GooglePhotosError(Exception):
    """Base exception for all Google Photos Upload errors."""
    pass

class AuthenticationError(GooglePhotosError):
    """Raised when there are issues with authentication."""
    pass

class AlbumError(GooglePhotosError):
    """Raised when there are issues with album operations."""
    pass

class UploadError(GooglePhotosError):
    """Raised when there are issues with photo uploads."""
    pass

class APIError(GooglePhotosError):
    """Raised when there are issues with the Google Photos API."""
    pass 
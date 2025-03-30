"""Main entry point for the Google Photos Upload tool."""

import argparse
import logging
from typing import Optional

from .client import GooglePhotosClient
from .config import Config
from .exceptions import GooglePhotosError

def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(description="Upload photos to Google Photos.")
    parser.add_argument(
        "--auth",
        metavar="auth_file",
        dest="auth_file",
        help="File for reading/storing user authentication tokens"
    )
    parser.add_argument(
        "--album",
        metavar="album_name",
        dest="album_name",
        help="Name of photo album to create (if it doesn't exist). "
             "Uploaded photos will be added to this album."
    )
    parser.add_argument(
        "--log",
        metavar="log_file",
        dest="log_file",
        help="Name of output file for log messages"
    )
    parser.add_argument(
        "photos",
        metavar="photo",
        type=str,
        nargs="*",
        help="Filename of a photo to upload"
    )
    return parser.parse_args()

def setup_logging(log_file: Optional[str] = None) -> None:
    """Set up logging configuration.
    
    Args:
        log_file: Optional path to log file
    """
    config = Config.from_env()
    
    if log_file:
        logging.basicConfig(
            format=config.LOG_FORMAT,
            datefmt=config.LOG_DATE_FORMAT,
            filename=log_file,
            level=getattr(logging, config.DEFAULT_LOG_LEVEL)
        )
    else:
        logging.basicConfig(
            format=config.LOG_FORMAT,
            datefmt=config.LOG_DATE_FORMAT,
            level=getattr(logging, config.DEFAULT_LOG_LEVEL)
        )

def main() -> None:
    """Main entry point for the Google Photos Upload tool."""
    args = parse_arguments()
    setup_logging(args.log)
    
    try:
        config = Config.from_env()
        client = GooglePhotosClient(config, args.auth_file)
        
        if not args.photos:
            print("Error: No photos specified")
            return
        
        client.upload_photos(args.photos, args.album)
        
    except GooglePhotosError as e:
        logging.error(f"Error: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 
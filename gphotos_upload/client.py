"""Google Photos API client implementation."""

import json
import logging
import os
from typing import Generator, List, Optional
from time import sleep

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials

from .config import Config
from .exceptions import (
    GooglePhotosError,
    AuthenticationError,
    AlbumError,
    UploadError,
    APIError
)

class GooglePhotosClient:
    """Client for interacting with the Google Photos API."""
    
    def __init__(self, config: Config, auth_file: Optional[str] = None):
        """Initialize the Google Photos client.
        
        Args:
            config: Configuration settings
            auth_file: Path to the authentication token file
        """
        self.config = config
        self.auth_file = auth_file
        self.session = self._get_authorized_session()
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        logging.basicConfig(
            format=self.config.LOG_FORMAT,
            datefmt=self.config.LOG_DATE_FORMAT,
            level=getattr(logging, self.config.DEFAULT_LOG_LEVEL)
        )
        self.logger = logging.getLogger(__name__)
    
    def _get_authorized_session(self) -> AuthorizedSession:
        """Get an authorized session for API requests.
        
        Returns:
            AuthorizedSession: An authorized session object
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            credentials = None
            if self.auth_file:
                try:
                    credentials = Credentials.from_authorized_user_file(
                        self.auth_file, self.config.SCOPES
                    )
                except (OSError, ValueError) as e:
                    self.logger.debug(f"Error loading auth tokens: {e}")
            
            if not credentials:
                credentials = self._authenticate()
            
            session = AuthorizedSession(credentials)
            
            if self.auth_file:
                try:
                    self._save_credentials(credentials)
                except OSError as e:
                    self.logger.debug(f"Could not save auth tokens: {e}")
            
            return session
            
        except Exception as e:
            raise AuthenticationError(f"Failed to get authorized session: {e}")
    
    def _authenticate(self) -> Credentials:
        """Authenticate with Google Photos API.
        
        Returns:
            Credentials: The user's authentication credentials
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_id.json",
                scopes=self.config.SCOPES
            )
            
            return flow.run_local_server(
                host=self.config.AUTH_HOST,
                port=self.config.AUTH_PORT,
                authorization_prompt_message="",
                success_message=self.config.AUTH_SUCCESS_MESSAGE,
                open_browser=True
            )
        except Exception as e:
            raise AuthenticationError(f"Authentication failed: {e}")
    
    def _save_credentials(self, credentials: Credentials) -> None:
        """Save credentials to file.
        
        Args:
            credentials: The credentials to save
            
        Raises:
            AuthenticationError: If saving credentials fails
        """
        try:
            credentials_dict = {
                "token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "id_token": credentials.id_token,
                "scopes": credentials.scopes,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret
            }
            
            with open(self.auth_file, "w") as f:
                json.dump(credentials_dict, f, indent=4)
        except Exception as e:
            raise AuthenticationError(f"Failed to save credentials: {e}")
    
    def get_albums(self, app_created_only: bool = False) -> Generator[dict, None, None]:
        """Get all albums from Google Photos.
        
        Args:
            app_created_only: Whether to only include albums created by this app
            
        Yields:
            dict: Album information
            
        Raises:
            APIError: If the API request fails
        """
        params = {"excludeNonAppCreatedData": app_created_only}
        
        while True:
            try:
                response = self.session.get(
                    f"{self.config.API_BASE_URL}/albums",
                    params=params
                )
                response.raise_for_status()
                albums_data = response.json()
                
                if "albums" in albums_data:
                    for album in albums_data["albums"]:
                        yield album
                    
                    if "nextPageToken" in albums_data:
                        params["pageToken"] = albums_data["nextPageToken"]
                    else:
                        return
                else:
                    return
                    
            except Exception as e:
                raise APIError(f"Failed to get albums: {e}")
    
    def create_or_retrieve_album(self, album_title: str) -> Optional[str]:
        """Create a new album or retrieve an existing one.
        
        Args:
            album_title: The title of the album
            
        Returns:
            str: The album ID, or None if creation/retrieval failed
            
        Raises:
            AlbumError: If album operations fail
        """
        try:
            # Check for existing album
            for album in self.get_albums(True):
                if album["title"].lower() == album_title.lower():
                    self.logger.info(f"Using existing album: '{album_title}'")
                    return album["id"]
            
            # Create new album
            create_album_body = json.dumps({"album": {"title": album_title}})
            response = self.session.post(
                f"{self.config.API_BASE_URL}/albums",
                data=create_album_body
            )
            response.raise_for_status()
            response_data = response.json()
            
            if "id" in response_data:
                self.logger.info(f"Created new album: '{album_title}'")
                return response_data["id"]
            else:
                self.logger.error(f"Failed to create album '{album_title}': {response_data}")
                return None
                
        except Exception as e:
            raise AlbumError(f"Album operation failed: {e}")
    
    def upload_photos(self, photo_file_list: List[str], album_name: Optional[str] = None) -> None:
        """Upload photos to Google Photos.
        
        Args:
            photo_file_list: List of photo file paths to upload
            album_name: Optional name of the album to upload to
            
        Raises:
            UploadError: If photo upload fails
        """
        try:
            album_id = self.create_or_retrieve_album(album_name) if album_name else None
            
            if album_name and not album_id:
                return
            
            self.session.headers.update({
                "Content-type": "application/octet-stream",
                "X-Goog-Upload-Protocol": "raw"
            })
            
            for photo_file_name in photo_file_list:
                try:
                    with open(photo_file_name, mode="rb") as photo_file:
                        photo_bytes = photo_file.read()
                except OSError as e:
                    self.logger.error(f"Could not read file '{photo_file_name}': {e}")
                    continue
                
                self.session.headers["X-Goog-Upload-File-Name"] = os.path.basename(photo_file_name)
                self.logger.info(f"Uploading photo: '{photo_file_name}'")
                
                # Upload with retries
                for attempt in range(self.config.MAX_RETRIES):
                    try:
                        upload_token_response = self.session.post(
                            f"{self.config.API_BASE_URL}/uploads",
                            data=photo_bytes
                        )
                        upload_token_response.raise_for_status()
                        break
                    except Exception as e:
                        if attempt == self.config.MAX_RETRIES - 1:
                            raise
                        self.logger.warning(f"Upload attempt {attempt + 1} failed: {e}")
                        sleep(self.config.RETRY_DELAY)
                
                if upload_token_response.content:
                    upload_token = upload_token_response.content.decode()
                    create_body = json.dumps({
                        "albumId": album_id,
                        "newMediaItems": [{
                            "description": "",
                            "simpleMediaItem": {"uploadToken": upload_token}
                        }]
                    })
                    
                    media_item_response = self.session.post(
                        f"{self.config.API_BASE_URL}/mediaItems:batchCreate",
                        data=create_body
                    )
                    media_item_response.raise_for_status()
                    media_item_data = media_item_response.json()
                    
                    if "newMediaItemResults" in media_item_data:
                        status = media_item_data["newMediaItemResults"][0]["status"]
                        if status.get("code") and status.get("code") > 0:
                            self.logger.error(
                                f"Failed to add '{os.path.basename(photo_file_name)}' "
                                f"to library: {status['message']}"
                            )
                        else:
                            self.logger.info(
                                f"Added '{os.path.basename(photo_file_name)}' "
                                f"to library and album '{album_name}'"
                            )
                    else:
                        self.logger.error(
                            f"Failed to add '{os.path.basename(photo_file_name)}' "
                            f"to library: {media_item_data}"
                        )
                else:
                    self.logger.error(
                        f"Failed to upload '{os.path.basename(photo_file_name)}': "
                        f"{upload_token_response}"
                    )
            
            # Clean up headers
            for header in ["Content-type", "X-Goog-Upload-Protocol", "X-Goog-Upload-File-Name"]:
                self.session.headers.pop(header, None)
                
        except Exception as e:
            raise UploadError(f"Photo upload failed: {e}")
    
    def upload_photos_from_directory(self, root_directory: str) -> None:
        """Upload photos from a directory structure to Google Photos.
        
        Args:
            root_directory: Path to the root directory containing photo albums
            
        Raises:
            UploadError: If photo upload fails
        """
        try:
            for subdirectory, subdirectories, _ in os.walk(root_directory):
                for album_name in subdirectories:
                    album_path = os.path.join(subdirectory, album_name)
                    self.logger.info(f"Processing album: {album_name}")
                    
                    photo_paths = [
                        os.path.abspath(os.path.join(album_path, photo_filename))
                        for photo_filename in sorted(os.listdir(album_path))
                    ]
                    
                    self.upload_photos(photo_paths, album_name)
                    
        except Exception as e:
            raise UploadError(f"Directory upload failed: {e}") 
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
import json
import os.path
import argparse
import logging
from tqdm import tqdm
from time import sleep
import os
from natsort import natsorted


def parse_arguments(arg_input=None):
    """Parses command-line arguments for the photo uploader.

    Args:
        arg_input (list, optional): A list of arguments to parse (for testing). Defaults to None.

    Returns:
        argparse.Namespace: An object containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(description='Upload photos to Google Photos.')
    parser.add_argument('--auth', metavar='auth_file', dest='auth_file',
                        help='File for reading/storing user authentication tokens')
    parser.add_argument('--album', metavar='album_name', dest='album_name',
                        help='Name of photo album to create (if it doesn\'t exist). '
                             'Uploaded photos will be added to this album.')
    parser.add_argument('--log', metavar='log_file', dest='log_file',
                        help='Name of output file for log messages')
    parser.add_argument('photos', metavar='photo', type=str, nargs='*',
                        help='Filename of a photo to upload')
    return parser.parse_args(arg_input)


def authenticate(scopes):
    """Authenticates the user and obtains credentials.

    Args:
        scopes (list): A list of OAuth scopes required for the application.

    Returns:
        Credentials: The user's authentication credentials.
    """
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_id.json',
        scopes=scopes)

    credentials = flow.run_local_server(host='localhost',
                                      port=8080,
                                      authorization_prompt_message="",
                                      success_message='The auth flow is complete; you may close this window.',
                                      open_browser=True)

    return credentials


def get_authorized_session(auth_token_file):
    """Gets an authorized session for interacting with the Google Photos API.

    Args:
        auth_token_file (str): Path to the file where authentication tokens are stored.

    Returns:
        AuthorizedSession: An authorized session object.
    """
    scopes = ['https://www.googleapis.com/auth/photoslibrary',
              'https://www.googleapis.com/auth/photoslibrary.sharing']

    credentials = None

    if auth_token_file:
        try:
            credentials = Credentials.from_authorized_user_file(auth_token_file, scopes)
        except OSError as err:
            logging.debug(f"Error opening auth token file: {err}")
        except ValueError:
            logging.debug("Error loading auth tokens: Incorrect format")

    if not credentials:
        credentials = authenticate(scopes)

    session = AuthorizedSession(credentials)

    if auth_token_file:
        try:
            save_credentials(credentials, auth_token_file)
        except OSError as err:
            logging.debug(f"Could not save auth tokens: {err}")

    return session


def save_credentials(credentials, auth_file):
    """Saves the user's credentials to a file.

    Args:
        credentials (Credentials): The user's authentication credentials.
        auth_file (str): The path to the file where credentials should be saved.
    """
    credentials_dict = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'id_token': credentials.id_token,
        'scopes': credentials.scopes,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret
    }

    with open(auth_file, 'w') as f:
        json.dump(credentials_dict, f, indent=4)


def get_albums(session, app_created_only=False):
    """Generator that yields albums from the Google Photos API.

    Args:
        session (AuthorizedSession): An authorized session object.
        app_created_only (bool, optional): Whether to only include albums created by this app. Defaults to False.

    Yields:
        dict: A dictionary representing an album.
    """
    params = {
        'excludeNonAppCreatedData': app_created_only
    }

    while True:
        response = session.get('https://photoslibrary.googleapis.com/v1/albums', params=params)
        response.raise_for_status()
        albums_data = response.json()

        logging.debug(f"Server response: {albums_data}")

        if 'albums' in albums_data:
            for album in albums_data["albums"]:
                yield album

            if 'nextPageToken' in albums_data:
                params["pageToken"] = albums_data["nextPageToken"]
            else:
                return
        else:
            return


def create_or_retrieve_album(session, album_title):
    """Creates a new album or retrieves an existing one with the given title.

    Args:
        session (AuthorizedSession): An authorized session object.
        album_title (str): The title of the album.

    Returns:
        str: The ID of the album, or None if the album could not be created or found.
    """
    for album in get_albums(session, True):
        if album["title"].lower() == album_title.lower():
            album_id = album["id"]
            logging.info(f"Uploading into EXISTING photo album: '{album_title}'")
            return album_id

    # No matches, create new album
    create_album_body = json.dumps({"album": {"title": album_title}})
    response = session.post('https://photoslibrary.googleapis.com/v1/albums', data=create_album_body)
    response.raise_for_status()
    response_data = response.json()

    logging.debug(f"Server response: {response_data}")

    if "id" in response_data:
        logging.info(f"Uploading into NEW photo album: '{album_title}'")
        return response_data['id']
    else:
        logging.error(f"Could not find or create photo album '{album_title}'. "
                      f"Server Response: {response_data}")
        return None


def upload_photos(session, photo_file_list, album_name):
    """Uploads a list of photos to Google Photos.

    Args:
        session (AuthorizedSession): An authorized session object.
        photo_file_list (list): A list of photo file paths to upload.
        album_name (str): The name of the album to upload photos to.
    """
    album_id = create_or_retrieve_album(session, album_name) if album_name else None

    # Interrupt upload if an upload was requested but could not be created
    if album_name and not album_id:
        return

    session.headers["Content-type"] = "application/octet-stream"
    session.headers["X-Goog-Upload-Protocol"] = "raw"

    for photo_file_name in tqdm(photo_file_list, desc='Photos'):
        try:
            with open(photo_file_name, mode='rb') as photo_file:
                photo_bytes = photo_file.read()
        except OSError as err:
            logging.error(f"Could not read file '{photo_file_name}': {err}")
            continue

        session.headers["X-Goog-Upload-File-Name"] = os.path.basename(photo_file_name)

        logging.info(f"Uploading photo: '{photo_file_name}'")

        upload_token_response = session.post('https://photoslibrary.googleapis.com/v1/uploads', data=photo_bytes)
        upload_token_response.raise_for_status()

        if upload_token_response.content:
            upload_token = upload_token_response.content.decode()
            create_body = json.dumps({"albumId": album_id,
                                    "newMediaItems": [{"description": "",
                                                     "simpleMediaItem": {"uploadToken": upload_token}}]},
                                   indent=4)

            media_item_response = session.post('https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate',
                                             data=create_body)
            media_item_response.raise_for_status()
            media_item_data = media_item_response.json()

            logging.debug(f"Server response: {media_item_data}")

            if "newMediaItemResults" in media_item_data:
                status = media_item_data["newMediaItemResults"][0]["status"]
                if status.get("code") and status.get("code") > 0:
                    logging.error(f"Could not add '{os.path.basename(photo_file_name)}' to library: {status['message']}")
                else:
                    logging.info(f"Added '{os.path.basename(photo_file_name)}' to library and album '{album_name}'")
            else:
                logging.error(f"Could not add '{os.path.basename(photo_file_name)}' to library. "
                            f"Server Response: {media_item_data}")
        else:
            logging.error(f"Could not upload '{os.path.basename(photo_file_name)}'. "
                         f"Server Response: {upload_token_response}")

    # Clean up headers
    for header in ["Content-type", "X-Goog-Upload-Protocol", "X-Goog-Upload-File-Name"]:
        try:
            del session.headers[header]
        except KeyError:
            pass


def upload_photos_from_directory(root_directory):
    """
    Uploads photos from subdirectories within a root directory to Google Photos,
    creating albums for each subdirectory.

    Args:
        root_directory (str): The path to the root directory containing photo albums.
    """
    logging.basicConfig(
        format='%(asctime)s %(module)s.%(funcName)s:%(levelname)s:%(message)s',
        datefmt='%m/%d/%Y %I_%M_%S %p',
        filename='log_file',
        level=logging.INFO
    )

    session = get_authorized_session('client_id.json')

    for subdirectory, subdirectories, _ in os.walk(root_directory):
        for album_name in tqdm(subdirectories, desc='Albums'):
            album_path = os.path.join(subdirectory, album_name)
            logging.info(f"Processing album: {album_name}")

            photo_paths = [
                os.path.abspath(os.path.join(album_path, photo_filename))
                for photo_filename in natsorted(os.listdir(album_path))
            ]
            logging.debug(f"Photos in album '{album_name}': {photo_paths}")

            upload_photos(session, photo_paths, album_name)


def main():
    """Main function to handle command line arguments and start the upload process."""
    args = parse_arguments()
    
    if args.log:
        logging.basicConfig(
            format='%(asctime)s %(module)s.%(funcName)s:%(levelname)s:%(message)s',
            datefmt='%m/%d/%Y %I_%M_%S %p',
            filename=args.log,
            level=logging.INFO
        )
    
    if not args.photos:
        print("Error: No photos specified")
        return
    
    session = get_authorized_session(args.auth)
    upload_photos(session, args.photos, args.album)


if __name__ == "__main__":
    main() 
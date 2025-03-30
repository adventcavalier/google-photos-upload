# Google Photos Upload Container

This Docker container allows you to upload photos to Google Photos from a local directory.

## Prerequisites

1. Docker installed on your system
2. Google Photos API credentials (`client_id.json`)
3. A directory containing photos to upload

## Setup

1. Place your `client_id.json` file in the same directory as the Dockerfile
2. Build the Docker image:
   ```bash
   docker build -t gphotos-upload .
   ```

## Usage

Run the container by mounting your photos directory and the client_id.json file:

```bash
docker run -it \
  -v /path/to/your/photos:/photos \
  -v /path/to/client_id.json:/app/client_id.json \
  gphotos-upload
```

Replace:
- `/path/to/your/photos` with the path to your local photos directory
- `/path/to/client_id.json` with the path to your Google Photos API credentials file

## Authentication

The first time you run the container, it will open a browser window for Google Photos authentication. You'll need to:
1. Log in to your Google account
2. Grant the necessary permissions
3. Copy the authentication code back to the terminal

## Notes

- The container will create albums based on the directory structure in your photos folder
- Each subdirectory will become a separate album in Google Photos
- Photos will be uploaded in natural sort order within each album
- Progress bars will show the upload status for both albums and photos
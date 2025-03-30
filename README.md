# Google Photos Upload Container

This Docker container allows you to upload photos to Google Photos from a local directory.

## Prerequisites

1. Docker installed on your system
2. Google Photos API credentials (`client_id.json`)
3. A directory containing photos to upload

## Setting up Google Photos API Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Photos Library API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Photos Library API"
   - Click "Enable"

4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as the application type
   - Give it a name (e.g., "Google Photos Uploader")
   - Click "Create"

5. Download the credentials:
   - Click the download button (looks like a download arrow) next to your new OAuth 2.0 Client ID
   - Save the downloaded file as `client_id.json`
   - Place this file in the same directory as the Dockerfile

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

## Directory Structure and Album Creation

The script automatically mirrors your local folder structure to create albums in Google Photos. Here's how it works:

1. **Root Directory**: The directory you mount to `/photos` in the container becomes your root directory
2. **Album Creation**: 
   - Each subdirectory in your root directory becomes a separate album in Google Photos
   - The album name will match the subdirectory name exactly
   - If an album with the same name already exists in Google Photos, the script will use the existing album
3. **Photo Organization**:
   - Photos within each subdirectory are uploaded to their corresponding album
   - Photos are uploaded in natural sort order (e.g., IMG_1.jpg, IMG_2.jpg, IMG_10.jpg)
   - The original file names are preserved in Google Photos

Example structure:
```
/path/to/your/photos/
├── Vacation 2023/
│   ├── IMG_001.jpg
│   ├── IMG_002.jpg
│   └── IMG_003.jpg
├── Family Photos/
│   ├── IMG_004.jpg
│   └── IMG_005.jpg
└── Events/
    ├── Wedding/
    │   ├── IMG_006.jpg
    │   └── IMG_007.jpg
    └── Birthday/
        ├── IMG_008.jpg
        └── IMG_009.jpg
```

This will create the following albums in Google Photos:
- "Vacation 2023" containing IMG_001.jpg, IMG_002.jpg, and IMG_003.jpg
- "Family Photos" containing IMG_004.jpg and IMG_005.jpg
- "Events" containing IMG_006.jpg, IMG_007.jpg, IMG_008.jpg, and IMG_009.jpg

## Notes

- The container will create albums based on the directory structure in your photos folder
- Each subdirectory will become a separate album in Google Photos
- Photos will be uploaded in natural sort order within each album
- Progress bars will show the upload status for both albums and photos
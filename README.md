# Google Photos Upload

A Python tool for uploading photos to Google Photos with automatic album organization based on directory structure.

## Prerequisites

1. Python 3.7 or higher
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

## Installation

You can install the package in several ways:

1. **From GitHub (recommended)**:
```bash
pip install git+https://github.com/adventcavalier/gphotos-upload.git
```

2. **For Development**:
```bash
git clone https://github.com/adventcavalier/gphotos-upload.git
cd gphotos-upload
pip install -e .
```

## Usage

### Simple Directory Upload

The simplest way to use the tool is to specify a directory containing your photos. The tool will automatically create albums based on the folder structure:

```bash
gphotos-upload /path/to/your/photos
```

This will:
- Create albums based on your folder structure
- Upload all photos to their respective albums
- Show progress bars for both album creation and photo uploads

### Command Line Interface

1. **Upload photos to a specific album**:
```bash
gphotos-upload --album "My Album" photo1.jpg photo2.jpg
```

2. **Upload with authentication file**:
```bash
gphotos-upload --auth auth.json --album "My Album" photo1.jpg photo2.jpg
```

3. **Upload with logging**:
```bash
gphotos-upload --log upload.log --album "My Album" photo1.jpg photo2.jpg
```

### As a Python Package

```python
from gphotos_upload import GooglePhotosClient, Config

# Create a client
config = Config.from_env()
client = GooglePhotosClient(config, auth_file="auth.json")

# Upload photos to an album
client.upload_photos(["photo1.jpg", "photo2.jpg"], "My Album")

# Upload from directory structure
client.upload_photos_from_directory("/path/to/photos")
```

## Directory Structure and Album Creation

The script automatically mirrors your local folder structure to create albums in Google Photos. Here's how it works:

1. **Root Directory**: The directory you specify becomes your root directory
2. **Album Creation**: 
   - Each subdirectory becomes a separate album in Google Photos
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

## Environment Variables

You can configure the tool using environment variables:

- `GPHOTOS_API_BASE_URL`: Base URL for the Google Photos API
- `GPHOTOS_AUTH_PORT`: Port for OAuth authentication server (default: 8080)
- `GPHOTOS_AUTH_HOST`: Host for OAuth authentication server (default: localhost)
- `GPHOTOS_MAX_RETRIES`: Maximum number of upload retries (default: 3)
- `GPHOTOS_RETRY_DELAY`: Delay between retries in seconds (default: 5)
- `GPHOTOS_LOG_LEVEL`: Logging level (default: INFO)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
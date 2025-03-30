#!/bin/bash

# Check if client_id.json exists
if [ ! -f "client_id.json" ]; then
    echo "Error: client_id.json not found. Please mount it as a volume or copy it into the container."
    exit 1
fi

# Check if photos directory is mounted
if [ ! -d "/photos" ]; then
    echo "Error: /photos directory not found. Please mount your photos directory."
    exit 1
fi

# Run the script with the mounted photos directory
python gphotos-upload.py "/photos" 
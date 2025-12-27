# Google Photos Unfiled Downloader

A standalone Python script to download photos and videos from Google Photos that aren't in any album ("unfiled" items).

## Features

- No external dependencies (uses Python standard library only)
- OAuth 2.0 authentication with PKCE
- Resumable downloads with state tracking
- Downloads both photos and videos
- Creates a ZIP archive of all unfiled items
- Progress tracking and error handling

## Requirements

- Python 3.6+
- `credentials.json` from Google Cloud Console

## Setup

### 1. Get Google Cloud Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the **Photos Library API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Photos Library API"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as the application type
   - Download the credentials
5. Save the downloaded file as `credentials.json` in the same directory as the script

### 2. Run the Script

```bash
chmod +x gphotosdl.py
./gphotosdl.py
```

Or:

```bash
python3 gphotosdl.py
```

## How It Works

1. **Authentication**: Opens your browser for Google OAuth authentication
2. **Fetch Albums**: Retrieves all your albums and their contents
3. **Fetch All Items**: Gets all media items from your library
4. **Identify Unfiled**: Finds items not in any album
5. **Download**: Downloads unfiled items to a ZIP file

## Output

- `unfiled_photos.zip`: ZIP archive containing all unfiled photos and videos
- `token.pickle`: Saved authentication tokens (reused on subsequent runs)
- `download_state.json`: Download progress (allows resuming interrupted downloads)
- `temp_downloads/`: Temporary directory (automatically cleaned up)

## Resuming Downloads

If the download is interrupted, simply run the script again. It will:
- Skip already downloaded files
- Continue from where it left off
- Append new files to the existing ZIP

## Security Notes

- `credentials.json` contains your OAuth client ID and secret
- `token.pickle` contains your access tokens
- Never commit these files to version control
- The script only requests read-only access to your photos

## Limitations

- Downloads only "unfiled" photos (not in any album)
- Does not preserve folder structure
- Does not download metadata (EXIF data is preserved in the image files)
- Access tokens may expire (script will re-authenticate if needed)

## Privacy Policy

See our [Privacy Policy](PRIVACY.md) for information about how this application handles your data.

**Summary:** This tool runs entirely on your local computer. It accesses your Google Photos in read-only mode to download unfiled items. No data is collected, stored on external servers, or shared with third parties.

## License

This is a standalone script provided as-is. Feel free to modify and use as needed.

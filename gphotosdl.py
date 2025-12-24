#!/usr/bin/env python
"""
Google Photos Unfiled Downloader
Standalone script - no pip install required (except standard library)
Only requirement: credentials.json from Google Cloud Console
"""

import os
import pickle
import json
import urllib.request
import urllib.parse
import urllib.error
import http.server
import webbrowser
import hashlib
import base64
import secrets
import time
from zipfile import ZipFile
from urllib.parse import urlparse, parse_qs

# Configuration
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']
STATE_FILE = 'download_state.json'
TOKEN_FILE = 'token.pickle'
REDIRECT_URI = 'http://localhost:8080'

class OAuthHandler(http.server.BaseHTTPRequestHandler):
    """Handler for OAuth callback"""
    def do_GET(self):
        self.server.auth_code = parse_qs(urlparse(self.path).query).get('code', [None])[0]
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<html><body><h1>Authentication successful!</h1><p>You can close this window.</p></body></html>')

    def log_message(self, format, *args):
        pass  # Suppress log messages

class GoogleAuth:
    """Minimal OAuth 2.0 implementation"""
    def __init__(self, credentials_file):
        with open(credentials_file, 'r') as f:
            creds = json.load(f)
            self.client_id = creds['installed']['client_id']
            self.client_secret = creds['installed']['client_secret']

        self.token = None
        self.refresh_token = None
        self.token_expiry = None
        self.scopes = None

    def authorize(self):
        """Run OAuth flow"""
        # Load saved token if it exists
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as f:
                saved = pickle.load(f)

            self.token = saved.get('token')
            self.refresh_token = saved.get('refresh_token')
            self.token_expiry = saved.get('token_expiry')
            self.scopes = saved.get('scopes', [])

            # Check if scopes match what we need
            if set(self.scopes) != set(SCOPES):
                print("Saved token has different scopes, re-authenticating...")
                os.remove(TOKEN_FILE)
                self.token = None
                self.refresh_token = None
            # Check if token is expired
            elif self.token_expiry and time.time() >= self.token_expiry:
                if self.refresh_token:
                    print("Token expired, refreshing...")
                    try:
                        self._refresh_token()
                        return
                    except Exception as e:
                        print(f"Token refresh failed: {e}, re-authenticating...")
                        os.remove(TOKEN_FILE)
                        self.token = None
                        self.refresh_token = None
                else:
                    print("Token expired and no refresh token, re-authenticating...")
                    os.remove(TOKEN_FILE)
                    self.token = None
                    self.refresh_token = None
            elif self.token:
                print("Using saved credentials")
                return

        if not self.token:
            self._do_auth_flow()

    def _do_auth_flow(self):
        """Perform the OAuth authorization flow"""
        # Generate PKCE verifier and challenge
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')

        # Build authorization URL
        auth_params = {
            'client_id': self.client_id,
            'redirect_uri': REDIRECT_URI,
            'response_type': 'code',
            'scope': ' '.join(SCOPES),
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'access_type': 'offline',
            'prompt': 'consent'
        }

        auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(auth_params)

        print("Opening browser for authentication...")
        webbrowser.open(auth_url)

        # Start local server to catch callback
        server = http.server.HTTPServer(('localhost', 8080), OAuthHandler)
        server.auth_code = None
        server.handle_request()

        if not server.auth_code:
            raise Exception("Failed to get authorization code")

        # Exchange code for token
        token_params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': server.auth_code,
            'code_verifier': code_verifier,
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI
        }

        req = urllib.request.Request(
            'https://oauth2.googleapis.com/token',
            data=urllib.parse.urlencode(token_params).encode('utf-8'),
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        response = urllib.request.urlopen(req)
        token_data = json.loads(response.read().decode('utf-8'))

        self.token = token_data['access_token']
        self.refresh_token = token_data.get('refresh_token')
        expires_in = token_data.get('expires_in', 3600)
        self.token_expiry = time.time() + expires_in

        # Get the scopes that were actually granted
        granted_scopes = token_data.get('scope', '')
        if granted_scopes:
            self.scopes = granted_scopes.split(' ')
            print(f"Granted scopes: {self.scopes}")
        else:
            self.scopes = SCOPES
            print(f"No scope info in token response, assuming: {self.scopes}")

        # Check if we got the scopes we need
        required_scope = 'https://www.googleapis.com/auth/photoslibrary.readonly'
        if required_scope not in self.scopes:
            print(f"\n⚠️  WARNING: Required scope not granted!")
            print(f"   Required: {required_scope}")
            print(f"   Granted:  {self.scopes}")
            print(f"\n   This usually means:")
            print(f"   1. Photos Library API is not enabled in Google Cloud Console")
            print(f"   2. The scope is not added to the OAuth consent screen")
            print(f"\n   Please check your Google Cloud Console setup.")

        # Save tokens
        with open(TOKEN_FILE, 'wb') as f:
            pickle.dump({
                'token': self.token,
                'refresh_token': self.refresh_token,
                'token_expiry': self.token_expiry,
                'scopes': self.scopes
            }, f)

        print("Authentication successful!")

    def _refresh_token(self):
        """Refresh the access token using the refresh token"""
        token_params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }

        req = urllib.request.Request(
            'https://oauth2.googleapis.com/token',
            data=urllib.parse.urlencode(token_params).encode('utf-8'),
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        response = urllib.request.urlopen(req)
        token_data = json.loads(response.read().decode('utf-8'))

        self.token = token_data['access_token']
        expires_in = token_data.get('expires_in', 3600)
        self.token_expiry = time.time() + expires_in

        # Save updated token
        with open(TOKEN_FILE, 'wb') as f:
            pickle.dump({
                'token': self.token,
                'refresh_token': self.refresh_token,
                'token_expiry': self.token_expiry,
                'scopes': self.scopes
            }, f)

        print("Token refreshed successfully!")

class PhotoDownloader:
    def __init__(self):
        self.auth = GoogleAuth('credentials.json')
        self.filed_ids = set()
        self.all_items = []
        self.downloaded = set()
        self.load_state()

    def authenticate(self):
        self.auth.authorize()
        # Validate the token after authentication
        self._validate_token()

    def _validate_token(self):
        """Validate the access token by checking with Google's token info endpoint"""
        print("\nValidating access token...")
        try:
            # Use Google's tokeninfo endpoint to verify the token
            token_info_url = f'https://oauth2.googleapis.com/tokeninfo?access_token={self.auth.token}'
            req = urllib.request.Request(token_info_url)
            response = urllib.request.urlopen(req)
            token_info = json.loads(response.read().decode('utf-8'))

            print(f"✓ Token is valid")
            print(f"  Expires in: {token_info.get('expires_in', 'unknown')} seconds")
            print(f"  Scope: {token_info.get('scope', 'unknown')}")

            # Check if the scope includes photoslibrary
            scope = token_info.get('scope', '')
            if 'photoslibrary' not in scope:
                print(f"\n⚠️  WARNING: Token does not include 'photoslibrary' scope!")
                print(f"  This will cause API calls to fail.")
                print(f"  Please check your OAuth consent screen configuration.")
                return

            # Test if Photos Library API is accessible
            print("\nTesting Photos Library API access...")
            try:
                test_url = 'https://photoslibrary.googleapis.com/v1/mediaItems?pageSize=1'
                headers = {
                    'Authorization': f'Bearer {self.auth.token}',
                    'Content-Type': 'application/json'
                }
                test_req = urllib.request.Request(test_url, headers=headers)
                test_response = urllib.request.urlopen(test_req)
                print(f"✓ Photos Library API is accessible")
            except urllib.error.HTTPError as api_error:
                error_body = api_error.read().decode('utf-8')
                print(f"\n❌ Photos Library API test failed!")
                print(f"   Status: {api_error.code}")
                print(f"   Error: {error_body}")

                if api_error.code == 403:
                    print(f"\n   DIAGNOSIS:")
                    print(f"   Your token has the correct scope, but the API call is being rejected.")
                    print(f"   This usually means:")
                    print(f"   1. Photos Library API is NOT enabled in your Google Cloud project")
                    print(f"   2. You are not added as a test user in the OAuth consent screen")
                    print(f"   3. There's a mismatch between your credentials.json project and API settings")
                    print(f"\n   Please verify:")
                    print(f"   A. Go to: https://console.cloud.google.com/apis/library/photoslibrary.googleapis.com")
                    print(f"      Make sure it shows 'API enabled' (green checkmark)")
                    print(f"   B. Go to: https://console.cloud.google.com/apis/credentials/consent")
                    print(f"      Under 'Test users', make sure your email is listed")
                    print(f"   C. Check that your credentials.json is from the SAME project")

        except Exception as e:
            print(f"⚠️  Token validation failed: {e}")
            print(f"  This might cause issues with API requests.")

    def _api_request(self, url, method='GET', body=None):
        """Make authenticated API request"""
        headers = {
            'Authorization': f'Bearer {self.auth.token}',
            'Content-Type': 'application/json'
        }

        data = json.dumps(body).encode('utf-8') if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            response = urllib.request.urlopen(req)
            return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"API Error: {e.code} - {error_body}")

            # Check for scope/authentication issues
            if e.code == 403 or e.code == 401:
                try:
                    error_data = json.loads(error_body)
                    error_message = error_data.get('error', {}).get('message', '')
                    if 'insufficient authentication scopes' in error_message.lower() or 'invalid' in error_message.lower():
                        print("\nAuthentication issue detected!")
                        print("Deleting saved token and re-authenticating...")
                        if os.path.exists(TOKEN_FILE):
                            os.remove(TOKEN_FILE)
                        print("\nPlease run the script again to re-authenticate with the correct scopes.")
                        exit(1)
                except:
                    pass

            raise

    def load_state(self):
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                self.downloaded = set(state.get('downloaded', []))
                print(f"Resumed: {len(self.downloaded)} files already downloaded")

    def save_state(self):
        with open(STATE_FILE, 'w') as f:
            json.dump({'downloaded': list(self.downloaded)}, f)

    def get_filed_items(self):
        """Fetch all albums and collect media item IDs"""
        print("Fetching albums...")
        url = 'https://photoslibrary.googleapis.com/v1/albums'
        next_page = None
        album_count = 0

        while True:
            params = {'pageSize': 50}
            if next_page:
                params['pageToken'] = next_page

            full_url = url + '?' + urllib.parse.urlencode(params)
            data = self._api_request(full_url)

            albums = data.get('albums', [])
            album_count += len(albums)

            for album in albums:
                self._get_album_items(album['id'])

            next_page = data.get('nextPageToken')
            print(f"Processed {album_count} albums, {len(self.filed_ids)} filed items found")

            if not next_page:
                break

        print(f"\nTotal filed items: {len(self.filed_ids)}")

    def _get_album_items(self, album_id):
        """Get all media items in a specific album"""
        url = 'https://photoslibrary.googleapis.com/v1/mediaItems:search'
        next_page = None

        while True:
            body = {
                'albumId': album_id,
                'pageSize': 100
            }
            if next_page:
                body['pageToken'] = next_page

            data = self._api_request(url, method='POST', body=body)

            items = data.get('mediaItems', [])
            for item in items:
                self.filed_ids.add(item['id'])

            next_page = data.get('nextPageToken')
            if not next_page:
                break

    def get_all_items(self):
        """Fetch all media items from library"""
        print("\nFetching all media items...")
        url = 'https://photoslibrary.googleapis.com/v1/mediaItems'
        next_page = None

        while True:
            params = {'pageSize': 100}
            if next_page:
                params['pageToken'] = next_page

            full_url = url + '?' + urllib.parse.urlencode(params)
            data = self._api_request(full_url)

            items = data.get('mediaItems', [])
            self.all_items.extend(items)

            print(f"Fetched {len(self.all_items)} total items...")

            next_page = data.get('nextPageToken')
            if not next_page:
                break

        print(f"Total items in library: {len(self.all_items)}")

    def download_unfiled(self, output_zip='unfiled_photos.zip'):
        """Download items not in any album"""
        unfiled = [item for item in self.all_items if item['id'] not in self.filed_ids]
        print(f"\nFound {len(unfiled)} unfiled items")

        if not unfiled:
            print("No unfiled items to download!")
            return

        os.makedirs('temp_downloads', exist_ok=True)

        with ZipFile(output_zip, 'a') as zipf:
            for i, item in enumerate(unfiled, 1):
                item_id = item['id']

                if item_id in self.downloaded:
                    print(f"[{i}/{len(unfiled)}] Skipping (already downloaded): {item['filename']}")
                    continue

                try:
                    # Determine download URL based on media type
                    if 'video' in item['mimeType']:
                        download_url = f"{item['baseUrl']}=dv"
                    else:
                        download_url = f"{item['baseUrl']}=d"

                    filename = item['filename']
                    temp_path = os.path.join('temp_downloads', filename)

                    print(f"[{i}/{len(unfiled)}] Downloading: {filename}")

                    # Download file
                    urllib.request.urlretrieve(download_url, temp_path)

                    # Add to zip
                    zipf.write(temp_path, filename)
                    os.remove(temp_path)

                    # Mark as downloaded and save state
                    self.downloaded.add(item_id)
                    self.save_state()

                except Exception as e:
                    print(f"Error downloading {filename}: {e}")
                    continue

        try:
            os.rmdir('temp_downloads')
        except:
            pass

        print(f"\nDownload complete! Saved to {output_zip}")

def main():
    print("=" * 60)
    print("Google Photos Unfiled Downloader")
    print("=" * 60)
    print()

    if not os.path.exists('credentials.json'):
        print("ERROR: credentials.json not found!")
        print("\nPlease follow these steps:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project (or select existing one)")
        print("3. Enable 'Photos Library API':")
        print("   - Go to 'APIs & Services' > 'Library'")
        print("   - Search for 'Photos Library API'")
        print("   - Click 'Enable'")
        print("4. Configure OAuth consent screen:")
        print("   - Go to 'APIs & Services' > 'OAuth consent screen'")
        print("   - Choose 'External' and click 'Create'")
        print("   - Fill in app name and your email")
        print("   - Click 'Add or Remove Scopes'")
        print("   - Add scope: '../auth/photoslibrary.readonly'")
        print("   - Save and continue")
        print("   - IMPORTANT: Add test users!")
        print("     * Click 'Add Users' under Test users")
        print("     * Add your Google account email")
        print("     * This is required for API access in testing mode")
        print("5. Create OAuth 2.0 credentials:")
        print("   - Go to 'APIs & Services' > 'Credentials'")
        print("   - Click 'Create Credentials' > 'OAuth client ID'")
        print("   - Choose 'Desktop app' as application type")
        print("   - Download as 'credentials.json' in this directory")
        return

    downloader = PhotoDownloader()
    downloader.authenticate()
    downloader.get_filed_items()
    downloader.get_all_items()
    downloader.download_unfiled()

if __name__ == '__main__':
    main()

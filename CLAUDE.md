# Google Photos Unfiled Downloader - LLM Context

## Project Overview

A standalone Python script to download "unfiled" photos from Google Photos - photos that exist in your library but aren't in any album. Uses only Python standard library (no pip dependencies required).

**Repository:** https://github.com/thebaysix/gphotosdl
**Current Branch:** `claude/setup-photos-auth-ydYrR`
**Primary Developer:** megha (megabyte31@gmail.com)

## Current Status: BLOCKED on Google Cloud Console Configuration

### What Works ✅

The authentication system is fully implemented and robust:
- ✅ OAuth 2.0 PKCE flow with local callback server
- ✅ Token expiry tracking and automatic refresh
- ✅ Scope validation and mismatch detection
- ✅ Windows file permission handling
- ✅ Token introspection and validation
- ✅ API accessibility testing with detailed diagnostics
- ✅ Comprehensive error messages

### What's Blocking ❌

**Google Cloud Console UI Issue:** When accessing the OAuth consent screen configuration page, the user gets redirected to the auth overview page instead. This prevents:
- Editing the OAuth consent screen
- Verifying/adding the required scope (`photoslibrary.readonly`)
- Completing the setup process

**Symptoms:**
- API enabled: ✅ Photos Library API is enabled in project
- Test user added: ✅ megabyte31@gmail.com is listed as test user
- Token has scope: ✅ Token shows `photoslibrary.readonly` scope
- API calls fail: ❌ 403 "insufficient authentication scopes"

**Root Cause:** The OAuth consent screen likely doesn't have the `photoslibrary.readonly` scope properly configured in the "Scopes" section, even though the API is enabled and the test user is added. The UI redirect bug prevents verification/fixing this.

## Project Roadmap

### Phase 1: Authentication ✅ (Completed)
- [x] OAuth 2.0 PKCE flow implementation
- [x] Token storage and management
- [x] Token refresh logic
- [x] Windows compatibility fixes
- [x] Comprehensive error handling
- [x] Diagnostic tooling

### Phase 2: Google Cloud Setup 🚧 (Blocked)
- [x] Create Google Cloud project
- [x] Enable Photos Library API
- [x] Create OAuth credentials
- [x] Add test user
- [ ] **BLOCKED:** Configure scope in OAuth consent screen (UI redirect issue)

### Phase 3: Core Functionality 📋 (Not Started)
- [ ] Fetch all albums from Google Photos
- [ ] Collect media item IDs from albums (filed items)
- [ ] Fetch all media items from library
- [ ] Identify unfiled items (items not in any album)
- [ ] Download unfiled items with proper handling for photos/videos
- [ ] Create ZIP archive of unfiled items

### Phase 4: Advanced Features 📋 (Planned)
- [ ] Resume capability for interrupted downloads
- [ ] Progress tracking and reporting
- [ ] Filename conflict handling
- [ ] Metadata preservation
- [ ] Filtering options (date range, media type, etc.)

## Technical Architecture

### Authentication Flow (gphotosdl.py:41-179)

```
GoogleAuth.__init__()
  └─> authorize()
      ├─> Load saved token if exists
      ├─> Validate token expiry
      ├─> Validate scopes match
      ├─> Refresh token if expired (has refresh_token)
      └─> _do_auth_flow() if no valid token
          ├─> Generate PKCE challenge
          ├─> Open browser for user consent
          ├─> Start local server on :8080
          ├─> Exchange code for token
          ├─> Validate granted scopes
          └─> Save token to token.pickle
```

### Validation & Diagnostics (gphotosdl.py:194-253)

```
PhotoDownloader.authenticate()
  └─> _validate_token()
      ├─> Query Google's tokeninfo endpoint
      ├─> Verify token validity and expiry
      ├─> Check scope includes 'photoslibrary'
      └─> Test actual API access with mediaItems endpoint
          ├─> SUCCESS: Proceed with download
          └─> FAILURE: Show detailed diagnosis and exit
```

### Download Flow (gphotosdl.py:181-402) - Not Yet Functional

```
main()
  └─> PhotoDownloader()
      ├─> authenticate()
      ├─> get_filed_items()      # Blocked: needs working API access
      │   ├─> Fetch all albums
      │   └─> Collect item IDs from each album
      ├─> get_all_items()        # Blocked: needs working API access
      │   └─> Fetch all media items from library
      └─> download_unfiled()     # Blocked: needs working API access
          ├─> Identify unfiled items (all - filed)
          ├─> Download each item
          └─> Create ZIP archive
```

## Key Files

### gphotosdl.py (502 lines)
Main script containing all functionality:
- `GoogleAuth` (lines 41-179): OAuth authentication and token management
- `PhotoDownloader` (lines 181-402): Main application logic
  - `_validate_token()` (lines 194-253): Token validation and API testing
  - `_api_request()` (lines 255-287): Authenticated API requests with error handling
  - `get_filed_items()` (lines 296-337): Fetch albums and collect filed item IDs
  - `get_all_items()` (lines 339-359): Fetch all library items
  - `download_unfiled()` (lines 361-402): Download and ZIP unfiled items
- `main()` (lines 404-439): Entry point with setup instructions

### credentials.json (Not in repo)
OAuth 2.0 client credentials from Google Cloud Console:
- Required format: Desktop app credentials
- Project: `download-unfiled` (or `gphotosdl-2`)
- Contains: client_id, client_secret, redirect_uris

### token.pickle (Not in repo, auto-generated)
Saved authentication state:
- access_token: Current OAuth token
- refresh_token: Long-lived refresh token
- token_expiry: Unix timestamp of expiration
- scopes: List of granted scopes

### download_state.json (Not in repo, auto-generated)
Download progress tracking:
- downloaded: List of item IDs already downloaded
- Enables resume capability

## Required Google Cloud Configuration

### Project Setup
1. Project name: `download-unfiled` or `gphotosdl-2`
2. APIs enabled:
   - ✅ Photos Library API (`photoslibrary.googleapis.com`)

### OAuth Consent Screen
- Publishing status: **Testing** (not Production)
- User type: **External**
- Test users: **megabyte31@gmail.com**
- **ISSUE:** Scopes section needs `../auth/photoslibrary.readonly` but UI redirects prevent access

### OAuth Credentials
- Type: **OAuth 2.0 Client ID**
- Application type: **Desktop app**
- Authorized redirect URIs: `http://localhost:8080`

## API Scopes

**Required:** `https://www.googleapis.com/auth/photoslibrary.readonly`
- Allows: Read-only access to Google Photos library
- Needed for: Listing albums, fetching media items, accessing media URLs

## Common Issues & Solutions

### Issue: 403 "insufficient authentication scopes"
**Symptoms:** Token has correct scope, API is enabled, test user added, but API calls fail
**Cause:** OAuth consent screen doesn't have scope configured in "Scopes" section
**Solution:** Edit OAuth consent screen → Scopes → Add photoslibrary.readonly
**Current Blocker:** UI redirect prevents accessing consent screen editor

### Issue: Windows "Permission denied" when deleting token.pickle
**Status:** ✅ Fixed (commit 1404b7f)
**Solution:** Close file handle before deletion (lines 56-59)

### Issue: Token expiry causes re-authentication
**Status:** ✅ Fixed (commit 7860567)
**Solution:** Automatic token refresh using refresh_token (lines 148-179)

### Issue: Scope mismatch between saved token and requirements
**Status:** ✅ Fixed (commit 7860567)
**Solution:** Validate scopes on load, force re-auth if mismatch (lines 65-70)

## Next Steps for Resolution

### Immediate (Unblock Development)
1. **Fix OAuth consent screen access:**
   - Try different browser/incognito mode
   - Clear Google Cloud Console cookies
   - Try Firefox/Edge instead of Chrome
   - Access via hamburger menu navigation
   - Use gcloud CLI as workaround
   - Try different Google account to isolate issue

2. **Once unblocked:**
   - Edit OAuth consent screen
   - Navigate to Scopes section
   - Add `../auth/photoslibrary.readonly` scope
   - Save changes
   - Delete token.pickle
   - Run script - should work immediately

### Post-Unblock (Resume Development)
1. Test end-to-end download flow
2. Implement progress reporting
3. Add error handling for network issues
4. Test with large photo libraries
5. Add filtering options
6. Documentation and user guide

## Development Notes

### Testing
- Use a Google account with Photos Library API access
- Test user must be added to OAuth consent screen test users
- First run requires browser authentication
- Subsequent runs use saved token with auto-refresh

### Windows Compatibility
- File paths must use proper quoting in bash commands
- File handles must be closed before deletion (Windows locks open files)
- Use `os.path` for cross-platform path handling

### Error Handling
- All API errors show detailed JSON error messages
- 403/401 errors trigger diagnostic output and exit
- Token validation failures are non-fatal (warnings only)
- Network errors should be caught and retried (TODO)

## Commit History (Recent)

- `ff23775` Exit early when API test fails to avoid confusion
- `39d6ea4` Add Photos Library API accessibility test
- `48b0e89` Add token validation and test user instructions
- `ef39da4` Add scope debugging and improve setup instructions
- `1404b7f` Fix Windows permission error when deleting token file
- `7860567` Fix authentication scope issues with Google Photos API

## Resources

- [Google Photos Library API Documentation](https://developers.google.com/photos/library/guides/get-started)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [PKCE Flow Specification](https://tools.ietf.org/html/rfc7636)
- [Google Cloud Console](https://console.cloud.google.com/)

---

**Last Updated:** 2024-12-16
**Status:** Blocked on Google Cloud Console OAuth consent screen UI issue
**Contact:** megabyte31@gmail.com

# Privacy Policy for Google Photos Unfiled Downloader

**Effective Date:** December 27, 2024

## Overview

Google Photos Unfiled Downloader ("gphotosdl") is a personal, open-source tool that runs locally on your computer to download photos from your Google Photos library that are not organized in albums.

## Data Collection and Usage

### What Data We Access
- **Google Photos Library:** The application accesses your Google Photos library in read-only mode to:
  - List your albums
  - List media items in your library
  - Identify which items are not in any album
  - Download those unfiled items to your local computer

### What We Do NOT Collect
- We do not collect, store, or transmit your personal information to any server
- We do not share your data with any third parties
- We do not use your data for advertising or analytics
- All data processing happens locally on your computer

### Data Storage
- OAuth tokens are stored locally on your computer in a file called `token.pickle`
- Downloaded photos are stored locally in a ZIP file on your computer
- No data is sent to any external servers except Google's APIs for authentication and photo access

### Third-Party Services
This application uses Google APIs to access your Google Photos library. Your use of Google services is subject to Google's Privacy Policy: https://policies.google.com/privacy

## Your Rights

You can:
- Revoke access at any time by visiting: https://myaccount.google.com/permissions
- Delete the local token file (`token.pickle`) to remove stored credentials
- Delete any downloaded photos from your local computer

## Open Source

This application is open source. You can review the code at: https://github.com/thebaysix/gphotosdl

## Contact

For questions or concerns about this privacy policy, please open an issue at: https://github.com/thebaysix/gphotosdl/issues

## Changes to This Policy

We may update this privacy policy from time to time. Changes will be posted in the GitHub repository.

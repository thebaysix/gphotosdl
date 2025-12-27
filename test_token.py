#!/usr/bin/env python
"""Quick script to print the full access token for manual testing"""
import pickle
import os

TOKEN_FILE = 'token.pickle'

if os.path.exists(TOKEN_FILE):
    with open(TOKEN_FILE, 'rb') as f:
        saved = pickle.load(f)
        token = saved.get('token')
        print(f"Full access token:")
        print(token)
        print(f"\nTest with curl:")
        print(f'curl -H "Authorization: Bearer {token}" "https://photoslibrary.googleapis.com/v1/mediaItems?pageSize=1"')
else:
    print("No token.pickle found. Run gphotosdl.py first.")

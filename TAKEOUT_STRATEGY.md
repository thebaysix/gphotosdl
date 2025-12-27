# Google Takeout Strategy for Downloading Unfiled Photos (1TB)

## Overview

Google Takeout will automatically split your 1TB export into multiple 50GB archives (~20 archives). This document outlines a strategy to download everything, then identify and extract only unfiled photos.

## Phase 1: Export from Google Takeout

### Step 1: Request Export

1. Go to: https://takeout.google.com
2. Click "Deselect all"
3. Select only **"Google Photos"**
4. Click "Next step"
5. Configure delivery:
   - **Frequency:** Export once
   - **File type:** .zip (recommended) or .tgz
   - **Size:** 50 GB (maximum)
6. Click "Create export"

**Expected result:** Google will create ~20 archives of 50GB each

**Time estimate:** Several hours to 1-2 days for Google to prepare the archives

### Step 2: Download Archives

Google will email you when the export is ready. You'll get links to download each archive.

**Storage needed:**
- 1TB for downloaded archives
- 1TB for extracted files
- ~500GB-1TB for final unfiled photos (depending on how many are unfiled)
- **Total: ~2.5-3TB free space recommended**

**Download strategy:**
- Download a few archives at a time to manage disk space
- Verify each archive downloads completely (check file size)
- Consider using a download manager for reliability

## Phase 2: Extract and Identify Unfiled Photos

### Understanding Google Takeout Structure

Google Takeout exports include:
```
Google Photos/
├── Photos from 2020/
│   ├── IMG_1234.jpg
│   ├── IMG_1234.jpg.json  # Metadata
│   └── ...
├── Photos from 2021/
├── Albums/
│   ├── Vacation 2020/
│   │   ├── IMG_1234.jpg  # These are DUPLICATES of photos above
│   │   └── IMG_1234.jpg.json
│   └── Family Photos/
└── archive_browser.html
```

**Key insight:** Photos in albums appear TWICE:
1. In the year folders (all photos)
2. In the Albums folder (only filed photos)

### Step 3: Process Archives with Script

Create a Python script to identify unfiled photos by comparing:
- Photos in year folders (all photos)
- Photos in Albums folder (filed photos)
- **Unfiled = All - Filed**

**Script approach:**

```python
#!/usr/bin/env python3
"""
Extract and identify unfiled photos from Google Takeout archives.
"""

import os
import json
import shutil
import zipfile
from pathlib import Path
from collections import defaultdict

def extract_archive(archive_path, extract_to):
    """Extract a Google Takeout zip archive."""
    print(f"Extracting {archive_path}...")
    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def find_all_photos(takeout_root):
    """Find all photos in year folders."""
    all_photos = set()
    photos_root = Path(takeout_root) / "Takeout" / "Google Photos"

    for item in photos_root.iterdir():
        if item.is_dir() and item.name.startswith("Photos from"):
            for photo in item.rglob("*"):
                if photo.is_file() and not photo.name.endswith('.json'):
                    # Use filename + size as unique identifier
                    identifier = (photo.name, photo.stat().st_size)
                    all_photos.add((identifier, photo))

    return all_photos

def find_filed_photos(takeout_root):
    """Find photos that are in albums (filed)."""
    filed_photos = set()
    albums_root = Path(takeout_root) / "Takeout" / "Google Photos" / "Albums"

    if not albums_root.exists():
        return filed_photos

    for album in albums_root.iterdir():
        if album.is_dir():
            for photo in album.rglob("*"):
                if photo.is_file() and not photo.name.endswith('.json'):
                    identifier = (photo.name, photo.stat().st_size)
                    filed_photos.add(identifier)

    return filed_photos

def copy_unfiled_photos(all_photos, filed_identifiers, output_dir):
    """Copy unfiled photos to output directory."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    unfiled_count = 0

    for identifier, photo_path in all_photos:
        if identifier not in filed_identifiers:
            # This photo is unfiled
            dest = output_path / photo_path.name

            # Handle duplicate filenames
            counter = 1
            while dest.exists():
                stem = photo_path.stem
                suffix = photo_path.suffix
                dest = output_path / f"{stem}_{counter}{suffix}"
                counter += 1

            shutil.copy2(photo_path, dest)
            unfiled_count += 1

            if unfiled_count % 100 == 0:
                print(f"Copied {unfiled_count} unfiled photos...")

    return unfiled_count

def main():
    # Configuration
    ARCHIVES_DIR = "./takeout_archives"        # Where you downloaded the zips
    EXTRACT_DIR = "./extracted"                # Temporary extraction location
    OUTPUT_DIR = "./unfiled_photos"            # Final unfiled photos destination

    print("Google Takeout Unfiled Photos Extractor")
    print("=" * 50)

    # Step 1: Extract all archives
    archives = list(Path(ARCHIVES_DIR).glob("*.zip"))
    print(f"\nFound {len(archives)} archives to process")

    for i, archive in enumerate(archives, 1):
        print(f"\n[{i}/{len(archives)}] Processing {archive.name}")
        extract_archive(archive, EXTRACT_DIR)

    # Step 2: Find all photos
    print("\nScanning for all photos...")
    all_photos = find_all_photos(EXTRACT_DIR)
    print(f"Found {len(all_photos)} total photos")

    # Step 3: Find filed photos
    print("\nScanning for filed photos (in albums)...")
    filed_identifiers = find_filed_photos(EXTRACT_DIR)
    print(f"Found {len(filed_identifiers)} filed photos")

    # Step 4: Copy unfiled photos
    print("\nCopying unfiled photos...")
    unfiled_count = copy_unfiled_photos(all_photos, filed_identifiers, OUTPUT_DIR)

    print("\n" + "=" * 50)
    print(f"Complete!")
    print(f"Total photos: {len(all_photos)}")
    print(f"Filed photos: {len(filed_identifiers)}")
    print(f"Unfiled photos: {unfiled_count}")
    print(f"Output directory: {OUTPUT_DIR}")

    # Cleanup suggestion
    print(f"\nTo save space, you can now delete:")
    print(f"  - {EXTRACT_DIR} (extracted archives)")
    print(f"  - {ARCHIVES_DIR} (original archives)")

if __name__ == "__main__":
    main()
```

## Phase 3: Execution Plan

### Timeline and Disk Space Management

**Option A: Process All at Once (Requires 3TB free)**
1. Download all 20 archives (~1TB)
2. Extract all archives (~1TB)
3. Run script to identify and copy unfiled photos
4. Delete extracted files
5. Delete original archives

**Option B: Process in Batches (Requires 500GB free)**
1. Download 5 archives (~250GB)
2. Extract them (~250GB)
3. Run script on first batch, accumulate unfiled photos
4. Delete extracted files
5. Repeat for remaining archives
6. Script modification needed to handle multiple runs

### Batch Processing Script

For Option B, modify the script to append to results:

```python
# At the start of main()
OUTPUT_DIR = "./unfiled_photos"
STATE_FILE = "./processing_state.json"

# Load previous state
if Path(STATE_FILE).exists():
    with open(STATE_FILE) as f:
        state = json.load(f)
    already_filed = set(tuple(x) for x in state.get('filed', []))
else:
    already_filed = set()

# After finding filed photos
all_filed = filed_identifiers | already_filed

# Save state for next batch
with open(STATE_FILE, 'w') as f:
    json.dump({
        'filed': [list(x) for x in all_filed]
    }, f)
```

## Pros and Cons vs API Approach

### Pros of Takeout:
- ✅ No OAuth verification needed
- ✅ No API rate limits
- ✅ Get full-resolution originals
- ✅ Get metadata JSON files
- ✅ One-time download

### Cons of Takeout:
- ❌ Downloads ALL photos (filed + unfiled)
- ❌ Requires 2-3TB disk space
- ❌ Takes hours/days to prepare export
- ❌ Manual download of 20+ archives
- ❌ Post-processing required

## Estimated Timeline

- **Export preparation:** 12-48 hours (Google's processing time)
- **Download (20 archives @ 50GB each):** 10-20 hours (depends on internet speed)
- **Extraction:** 2-4 hours
- **Processing script:** 1-2 hours
- **Total:** 3-5 days

## Recommendations

1. **Start with a test:** Request export for just 2023-2024 photos first to test the workflow
2. **Monitor disk space:** Set up alerts when disk reaches 80% full
3. **Use external drives:** Consider using external SSD/HDD for storage
4. **Verify archives:** Check that each downloaded archive is complete before extracting
5. **Keep original archives:** Don't delete until you've verified unfiled photos are correct

## Alternative: Hybrid Approach

If you only want unfiled photos from recent years:

1. Use Takeout for bulk of old photos (2010-2020)
2. Use Google Photos web interface to manually organize recent photos
3. Request another Takeout export of only recent organized data

This reduces total download size significantly if most unfiled photos are old.

---

**Next Steps:**
1. Decide: Option A (3TB free) or Option B (500GB free)?
2. Test with small export first
3. Set up directory structure
4. Run the processing script

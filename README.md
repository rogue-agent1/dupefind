# dupefind

Find duplicate files by content hash. Zero dependencies.

## Usage

```bash
dupefind find [directory]                # Find dupes
dupefind find ~/Photos --ext .jpg,.png   # Filter by extension
dupefind find . --min 1024               # Min 1KB files only
dupefind json .                          # JSON output
```

## How It Works

1. Groups files by size (fast pre-filter)
2. Quick-hash first 4KB (eliminates most non-dupes)
3. Full MD5 hash only for quick-hash matches
4. Reports wasted space

## Requirements

- Python 3.6+ (stdlib only)

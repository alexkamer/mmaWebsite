# MMA Website Scripts

## Data Update Scripts

### `update_data.py`

A comprehensive Python script that updates the MMA database with the latest data from ESPN API.

**What it updates:**
- New leagues and promotions
- New fighter profiles and information
- New events and fight cards
- New fight results and details
- Betting odds from various providers
- Detailed fight statistics

**Usage:**

```bash
# From project root
uv run python scripts/update_data.py

# Or use the convenient shell wrapper
./update_database.sh
```

**Features:**
- ✅ Automatically detects and adds only new records (no duplicates)
- ✅ Parallel processing with ThreadPoolExecutor for speed
- ✅ Progress tracking with detailed logging
- ✅ Error handling for API failures
- ✅ Works with both Flask and standalone database

**Expected Runtime:**
- Full update: 15-30 minutes (depending on new data volume)
- Incremental update: 2-5 minutes

**Output Example:**
```
🥊🥊🥊 MMA DATABASE UPDATE SCRIPT 🥊🥊🥊

============================================================
UPDATING LEAGUES
============================================================
✅ No new leagues to add

============================================================
UPDATING ATHLETES
============================================================
→ Detected 37 pages of athletes
✔ Retrieved 36746 athlete URLs
→ Found 234 new athletes to add
  → Added 100/234 athletes...
  → Added 200/234 athletes...
✅ Added 234 new athletes

... (continues for each section)
```

## Other Scripts

### `utilities/`
Contains utility scripts for various tasks:
- `accurate_ufc_scraper.py` - Scrapes UFC rankings from UFC.com
- `init_db.py` - Initializes database tables
- `update_ufc_rankings.py` - Updates UFC rankings in database

## Notes

- The update script uses the database models from `archive/db.py` which work without Flask context
- The notebook version `notebooks/updateData.ipynb` is still available for interactive use
- All scripts handle API rate limiting and timeouts gracefully

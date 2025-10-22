# UFC Rankings Utilities

This directory contains scripts for managing UFC rankings data in your Fight Intel application.

## Scripts Overview

### 1. `update_rankings.py` ⭐ **RECOMMENDED**
**Simple, reliable rankings update with current UFC champions and P4P rankings.**

```bash
# Update rankings with current data
uv run python scripts/utilities/update_rankings.py
```

**Features:**
- ✅ Current UFC champions (as of Dec 2024)
- ✅ P4P rankings (Men's & Women's)
- ✅ Top contenders in each division
- ✅ Fast and reliable
- ✅ No external dependencies

---

### 2. `ufc_rankings_scraper.py` 🌐 **ADVANCED**
**Web scraper that attempts to fetch live data from UFC.com/rankings**

```bash
# Scrape live rankings from UFC.com
uv run python scripts/utilities/ufc_rankings_scraper.py
```

**Features:**
- 🌐 Scrapes live UFC website
- 🔄 Automatic fallback to known data
- 📊 Comprehensive parsing attempt
- ⚠️ May need updates if UFC changes their website structure

---

### 3. `schedule_rankings_update.py` ⏰ **AUTOMATION**
**Scheduler and automation tools for keeping rankings current**

```bash
# Manual update
uv run python scripts/utilities/schedule_rankings_update.py --update

# Check if update needed
uv run python scripts/utilities/schedule_rankings_update.py --check

# Show cron job setup
uv run python scripts/utilities/schedule_rankings_update.py --cron

# Development background scheduler
uv run python scripts/utilities/schedule_rankings_update.py --background
```

## Quick Start

### Option 1: Manual Update (Recommended)
```bash
# Run this whenever you want fresh rankings data
uv run python scripts/utilities/update_rankings.py
```

### Option 2: Automated Daily Updates
```bash
# Get cron job instructions
uv run python scripts/utilities/schedule_rankings_update.py --cron

# Then add the generated cron job to update daily at 6 AM
```

### Option 3: Development Mode
```bash
# Run background scheduler (updates every 24 hours)
uv run python scripts/utilities/schedule_rankings_update.py --background
```

## Current Champions (Updated Dec 2024)

### Men's Divisions
- 🥊 **Heavyweight**: Jon Jones
- 🥊 **Light Heavyweight**: Alex Pereira
- 🥊 **Middleweight**: Dricus Du Plessis
- 🥊 **Welterweight**: Belal Muhammad
- 🥊 **Lightweight**: Islam Makhachev
- 🥊 **Featherweight**: Ilia Topuria
- 🥊 **Bantamweight**: Merab Dvalishvili
- 🥊 **Flyweight**: Alexandre Pantoja

### Women's Divisions
- 👑 **Bantamweight**: Raquel Pennington
- 👑 **Flyweight**: Valentina Shevchenko
- 👑 **Strawweight**: Zhang Weili

## Database Schema

The scripts update the `ufc_rankings` table with these columns:

```sql
CREATE TABLE ufc_rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    division TEXT,                    -- e.g., "Heavyweight", "Women's Bantamweight"
    fighter_name TEXT NOT NULL,       -- Fighter's full name
    rank INTEGER,                     -- 0 for champions, 1-15 for ranked fighters
    is_champion BOOLEAN DEFAULT FALSE,
    is_interim_champion BOOLEAN DEFAULT FALSE,
    is_p4p BOOLEAN DEFAULT FALSE,     -- Pound-for-pound rankings
    p4p_rank INTEGER,
    gender TEXT CHECK(gender IN ('M', 'F')),
    ranking_type TEXT NOT NULL,       -- "Division" or "P4P"
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Troubleshooting

### ❌ "Database not found"
Make sure you're running from the project root directory:
```bash
cd /path/to/mmaWebsite
uv run python scripts/utilities/update_rankings.py
```

### ❌ "No champions showing on homepage"
1. Check if rankings were loaded: `sqlite3 data/mma.db "SELECT COUNT(*) FROM ufc_rankings WHERE is_champion = 1;"`
2. Restart your Flask app: `uv run run.py`

### ❌ Web scraper not working
The UFC website structure changes frequently. Use `update_rankings.py` instead for reliable data.

## Manual Updates

To manually update champion data, edit the `rankings_data` list in `update_rankings.py` and run:

```bash
uv run python scripts/utilities/update_rankings.py
```

## Integration

The rankings are automatically displayed on your homepage in the "Current UFC Champions" section. The data is loaded via the `/` route in `mma_website/routes/main.py`.
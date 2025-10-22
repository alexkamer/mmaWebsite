# MMA Database Update Guide

## Overview

This guide explains the efficient data update system for the MMA website database. The system uses two complementary approaches:

1. **Incremental Updates** (Daily/Weekly) - Fast, efficient updates for recent activity
2. **Full Backfill** (Monthly) - Comprehensive sync of all fighter data

## Why This Approach?

### Problem with Old System
The original `update_data.py` script:
- ❌ Processes ALL events chronologically (28K+ events)
- ❌ Takes 15-30 minutes even when there's little new data
- ❌ Misses fighter-specific regional fights
- ❌ Can't catch fights from events that failed to process

### New Fighter-Centric System
Using the ESPN **eventlog endpoint** for each fighter:
- ✅ Fighter-centric view ensures complete fight history
- ✅ Only processes what's missing (targeted updates)
- ✅ Catches ALL promotions automatically (UFC, regional, international)
- ✅ Much faster for incremental updates (2-5 minutes vs 30+ minutes)

## Update Scripts

### 1. Incremental Update (Recommended for Regular Use)

**Script:** `scripts/incremental_update.py`

**What it does:**
- Identifies fighters active in the last N days (default: 90)
- Checks their eventlogs for missing fights
- Processes only the missing data
- Includes odds and fight statistics

**Usage:**

```bash
# Standard incremental update (last 90 days)
uv run python scripts/incremental_update.py

# More frequent updates (last 30 days)
uv run python scripts/incremental_update.py --days 30

# Less frequent but more comprehensive (last 180 days)
uv run python scripts/incremental_update.py --days 180
```

**Performance:**
- Runtime: 2-10 minutes (depending on --days value)
- API calls: 200-500 (vs 30K+ in old system)
- Best for: Daily or weekly updates

**When to use:**
- ✅ Daily/weekly data refreshes
- ✅ After major UFC events
- ✅ When you want quick updates
- ✅ For catching recent fight results

### 2. Full Fighter Backfill (Comprehensive Sync)

**Script:** `scripts/backfill_fighter_events.py`

**What it does:**
- Checks EVERY fighter's complete eventlog (~36K fighters)
- Identifies all missing fights across their entire career
- Processes missing events in batches
- Comprehensive but time-intensive

**Usage:**

```bash
# Full backfill of all fighters
uv run python scripts/backfill_fighter_events.py --mode full

# With custom batch size (default: 100)
uv run python scripts/backfill_fighter_events.py --mode full --batch-size 200

# Run in background with logging
nohup uv run python scripts/backfill_fighter_events.py --mode full > backfill.log 2>&1 &

# Check a specific fighter
uv run python scripts/backfill_fighter_events.py --mode fighter --fighter-id 5311034

# Sample 200 random fighters (for testing)
uv run python scripts/backfill_fighter_events.py --mode sample --sample-size 200
```

**Performance:**
- Runtime: 3-8 hours for all fighters
- API calls: 36K+ (one per fighter + missing events)
- Best for: Monthly comprehensive syncs

**When to use:**
- ✅ Monthly comprehensive updates
- ✅ After adding many new fighters
- ✅ When you suspect missing historical data
- ✅ Initial database population

### 3. Legacy Update Script (For Reference)

**Script:** `scripts/update_data.py`

This is the original event-based update script. It's still functional but **not recommended** for regular use because:
- Slower than incremental updates
- Processes data chronologically instead of by need
- May miss fighter-specific fights

**Keep this for:**
- Adding new athletes in bulk
- Initial database setup
- Reference implementation

## Recommended Update Schedule

### Daily (Automated)
```bash
# Add to crontab or scheduler
0 6 * * * cd /path/to/mmaWebsite && uv run python scripts/incremental_update.py --days 30
```

### Weekly (Manual or Automated)
```bash
# Longer lookback for more comprehensive weekly update
uv run python scripts/incremental_update.py --days 90
```

### Monthly (Manual)
```bash
# Full backfill to catch everything
nohup uv run python scripts/backfill_fighter_events.py --mode full > logs/backfill_$(date +%Y%m%d).log 2>&1 &

# Monitor progress
tail -f logs/backfill_*.log
```

## How the System Works

### Fighter Eventlog Endpoint

ESPN provides a per-fighter eventlog endpoint:
```
https://sports.core.api.espn.com/v2/sports/mma/athletes/{fighter_id}/eventlog
```

This returns a complete list of all fights for a fighter, including:
- UFC fights
- Regional promotion fights
- International fights
- Historical fights

**Example:** Fighter 5311034 has 8 fights in their eventlog:
- 1 UFC fight (Dana White's Contender Series)
- 7 regional fights (UAE Warriors, Eagle FC, etc.)

### Incremental Update Flow

```
1. Query Database
   ↓
2. Find fighters with recent activity (last N days)
   ↓
3. For each fighter:
   - Fetch their eventlog from ESPN
   - Compare with database
   - Identify missing fights
   ↓
4. Process missing events
   - Fetch event details
   - Add cards, fights, odds, stats
   ↓
5. Done! ✅
```

### Full Backfill Flow

```
1. Get all fighter IDs from database (~36K)
   ↓
2. Process in batches (e.g., 200 fighters at a time)
   ↓
3. For each fighter:
   - Fetch eventlog
   - Compare with database
   - Track missing fights
   ↓
4. After batch: Process all missing events
   ↓
5. Repeat for next batch
   ↓
6. Done! ✅
```

## Monitoring & Troubleshooting

### Check if backfill is running
```bash
ps aux | grep backfill_fighter_events
```

### Monitor backfill progress
```bash
tail -f backfill.log

# Or check for specific metrics
grep "Batch" backfill.log
grep "Added" backfill.log
```

### Kill a running backfill (if needed)
```bash
pkill -f backfill_fighter_events
```

### Common Issues

**Issue:** "No missing events to add" but fights are missing
- **Cause:** Events exist in database but specific fights don't
- **Solution:** This is expected - the script processes events to add missing fights

**Issue:** Lots of duplicate warnings
- **Cause:** Duplicate key constraints (expected behavior)
- **Solution:** These are benign - the script skips duplicates automatically

**Issue:** Backfill is very slow
- **Cause:** Too many fighters to check
- **Solution:** Use incremental update for regular updates, backfill only monthly

## Database Coverage Stats

After running the scripts, you can check coverage:

```bash
# Total fights by promotion
sqlite3 data/mma.db "SELECT league, COUNT(*) FROM fights GROUP BY league ORDER BY COUNT(*) DESC;"

# Coverage by year for "other" promotion
sqlite3 data/mma.db "
SELECT
    substr(date, 1, 4) as year,
    COUNT(*) as fight_count
FROM fights f
JOIN cards c ON f.event_id = c.event_id AND f.league = c.league
WHERE f.league = 'other'
GROUP BY year
ORDER BY year DESC;"
```

## Performance Comparison

| Script | Fighters Checked | Runtime | API Calls | Best For |
|--------|-----------------|---------|-----------|----------|
| `incremental_update.py --days 30` | ~200 | 2-5 min | 200-500 | Daily updates |
| `incremental_update.py --days 90` | ~500 | 5-10 min | 500-1000 | Weekly updates |
| `incremental_update.py --days 180` | ~1000 | 10-20 min | 1000-2000 | Bi-weekly comprehensive |
| `backfill_fighter_events.py --mode full` | ~36,000 | 3-8 hours | 36K+ | Monthly full sync |
| `update_data.py` (legacy) | All events | 15-30 min | 30K+ | Initial setup only |

## Tips for Efficiency

1. **Use incremental updates for regular maintenance** - Much faster and catches recent activity
2. **Run full backfill monthly** - Ensures comprehensive coverage
3. **Adjust --days based on update frequency** - More frequent updates = lower --days value
4. **Run backfills overnight** - Use `nohup` and check logs in the morning
5. **Monitor your database size** - The database will grow as more fights are added

## API Rate Limiting

ESPN's API is generally lenient, but to be respectful:
- Incremental script uses 15 workers (moderate)
- Backfill uses batches to avoid overwhelming the API
- Add delays if you notice 429 errors (rare)

## Questions?

- **How often should I update?** Daily with incremental (--days 30), monthly with full backfill
- **Which script should I run?** Start with `incremental_update.py`, it's faster and sufficient for most needs
- **When do I need the full backfill?** Monthly, or when you add many new fighters
- **What about the old update_data.py?** Keep it for reference, but prefer incremental updates

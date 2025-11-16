# MMA Data Collection & Update Strategy

## Overview
This document outlines the comprehensive data collection and update strategy for the MMA website, including how to discover missing events and keep data current.

## Problem Solved
The original data collection approach iterated through league seasons to discover events. However, **some events were missing** because they weren't properly indexed in season listings. The fighter-centric eventlog approach solves this by discovering ALL fights from each fighter's perspective.

## Architecture

### 1. Discovery: Fighter Eventlog Scraper
**Script:** `scripts/scrape_fighter_eventlogs.py`

**What it does:**
- Iterates through all ~36K fighters in the database
- Hits ESPN's eventlog API for each fighter:
  ```
  https://sports.core.api.espn.com/v2/sports/mma/athletes/{id}/eventlog?lang=en&region=us&limit=250
  ```
- Discovers all events, competitions, and fights from fighter perspectives
- Compares against existing database to identify gaps
- Outputs JSON files with missing data

**Output files** (saved to `data/`):
- `eventlog_entries.json` - All discovered events with URLs
- `missing_events.json` - Event IDs not in cards table
- `missing_competitions.json` - Fight IDs not in fights table
- `eventlog_scraping_report.txt` - Summary statistics

**Usage:**
```bash
uv run python scripts/scrape_fighter_eventlogs.py
```

### 2. Backfill: Missing Data Importer
**Script:** `scripts/backfill_missing_data.py`

**What it does:**
- Backfills missing events discovered by eventlog scraper
- Updates incomplete fight results (NULL winners for completed fights)
- Fills in missing odds data
- Fills in missing statistics data
- Fills in missing linescore data

**Usage:**
```bash
# Run all backfill operations
uv run python scripts/backfill_missing_data.py --all

# Or run specific operations
uv run python scripts/backfill_missing_data.py --events    # Missing events
uv run python scripts/backfill_missing_data.py --fights    # Incomplete results
uv run python scripts/backfill_missing_data.py --odds      # Missing odds
uv run python scripts/backfill_missing_data.py --stats     # Missing statistics

# Control concurrency
uv run python scripts/backfill_missing_data.py --all --workers 75
```

### 3. Validation: Data Completeness Checker
**Script:** `scripts/validate_data_completeness.py`

**What it does:**
- Analyzes database for completeness and quality issues
- Identifies missing results, odds, and statistics
- Detects orphaned records (fights without events, etc.)
- Checks data quality (missing names, invalid IDs, duplicates)
- Provides league-specific completeness metrics

**Usage:**
```bash
uv run python scripts/validate_data_completeness.py
```

**Sample output:**
```
DATABASE OVERVIEW
Athletes:     36,809
Events:       15,234
Fights:       142,567
Odds records: 89,234
Statistics:   67,890

MISSING FIGHT RESULTS
⚠️  Fights with missing results (>7 days old): 234

MISSING ODDS DATA
Total fights with odds_url:     45,123
Fights with actual odds data:   42,890
⚠️  Missing odds data:            2,233
Odds coverage: 95.1%

COMPLETENESS BY LEAGUE
📊 UFC:
  Total fights:      45,678
  With results:      44,234 (96.8%)
  With odds:         38,456 (84.2%)
  With statistics:   35,123 (76.9%)
```

## Data Collection Workflow

### Initial Setup (One-time)
```bash
# 1. Scrape all fighter eventlogs to discover gaps
uv run python scripts/scrape_fighter_eventlogs.py

# 2. Validate current database state
uv run python scripts/validate_data_completeness.py

# 3. Backfill all missing data
uv run python scripts/backfill_missing_data.py --all
```

### Regular Maintenance (Weekly/Monthly)
```bash
# 1. Update recent fight results
uv run python scripts/backfill_missing_data.py --fights

# 2. Check for new missing data
uv run python scripts/validate_data_completeness.py

# 3. Backfill any gaps found
uv run python scripts/backfill_missing_data.py --all
```

### After Major Events
```bash
# 1. Update fight results and statistics
uv run python scripts/backfill_missing_data.py --fights --stats

# 2. Refresh odds data
uv run python scripts/backfill_missing_data.py --odds
```

## Data Sources & Structure

### ESPN API Endpoints Used

**Eventlog (per fighter):**
```
GET /v2/sports/mma/athletes/{id}/eventlog
Returns: List of all events fighter participated in
```

**Event Details:**
```
GET /v2/sports/mma/leagues/{league}/events/{event_id}
Returns: Card info + all competitions/fights
```

**Fight Status:**
```
GET /v2/sports/mma/leagues/{league}/events/{event_id}/competitions/{fight_id}/status
Returns: Result, method, round, time
```

**Odds:**
```
GET /v2/sports/mma/leagues/{league}/events/{event_id}/competitions/{fight_id}/odds
Returns: Betting lines from multiple providers
```

**Statistics:**
```
GET /v2/sports/mma/leagues/{league}/events/{event_id}/competitions/{fight_id}/competitors/{athlete_id}/statistics
Returns: Strikes, takedowns, control time, etc.
```

**Linescores:**
```
GET /v2/sports/mma/leagues/{league}/events/{event_id}/competitions/{fight_id}/competitors/{athlete_id}/linescores
Returns: Judge scorecards by round
```

## Database Tables

### Cards (Events)
```sql
- event_id (PRIMARY KEY)
- league, event_name, date
- venue_name, city, state, country
```

### Fights (Competitions)
```sql
- fight_id (PRIMARY KEY)
- event_id (FOREIGN KEY)
- fighter_1_id, fighter_2_id
- fighter_1_winner, fighter_2_winner
- weight_class, end_round, end_time, result_display_name
- odds_url, fighter_1_statistics, fighter_2_statistics
- fighter_1_linescore, fighter_2_linescore
```

### Odds
```sql
- provider_id_fight_id (PRIMARY KEY)
- fight_id (FOREIGN KEY)
- provider_name
- home/away athlete odds (moneyline, victory method)
- rounds over/under
```

### StatisticsForFight
```sql
- event_competition_athlete_id (PRIMARY KEY)
- competition_id (maps to fight_id)
- athlete_id
- Various fight stats (strikes, takedowns, etc.)
```

## Data Update Strategy

### What Gets Stale?

1. **Fight Results** (high priority)
   - Pre-fight: winner/loser = NULL
   - Post-fight: Results added
   - Update window: Within 24 hours of event

2. **Odds** (medium priority)
   - Change constantly until fight time
   - Lock at fight start
   - Update frequency: Daily for upcoming fights

3. **Statistics** (low priority)
   - Only available after fight completes
   - Rarely change once published
   - Update window: Within 48 hours of event

4. **Linescores** (low priority)
   - Only for decision wins
   - Available shortly after fight
   - Update window: Within 48 hours of event

### Update Priorities

**Daily:**
- Upcoming fight odds (next 30 days)
- Recent fight results (last 7 days)

**Weekly:**
- Recent fight statistics (last 30 days)
- Missing odds/stats backfill

**Monthly:**
- Full validation scan
- Historical data cleanup
- Eventlog rescan for new fighters

## Monitoring & Alerts

### Key Metrics to Track

1. **Completeness Ratios:**
   - % of fights with results (target: >98% for past fights)
   - % of fights with odds data (target: >85% for UFC)
   - % of fights with statistics (target: >75% for UFC)

2. **Freshness:**
   - Age of most recent event
   - Lag between fight date and result availability

3. **Data Quality:**
   - Orphaned records
   - Duplicate entries
   - Missing required fields

### Validation Checks

Run validation script weekly:
```bash
uv run python scripts/validate_data_completeness.py > data/validation_$(date +%Y%m%d).txt
```

Review output for:
- High severity issues (orphaned records, invalid IDs)
- Medium severity issues (missing results >7 days)
- Low severity issues (missing odds/stats)

## Best Practices

1. **Always validate before backfilling:**
   ```bash
   uv run python scripts/validate_data_completeness.py
   uv run python scripts/backfill_missing_data.py --all
   ```

2. **Use appropriate concurrency:**
   - Development: `--workers 25`
   - Production: `--workers 75`
   - Avoid >150 workers (may trigger rate limiting)

3. **Backup before major operations:**
   ```bash
   cp data/mma.db data/mma_backup_$(date +%Y%m%d).db
   ```

4. **Monitor for API changes:**
   - ESPN API structure may change
   - Watch for new endpoints or fields
   - Update helper functions accordingly

5. **Handle rate limiting gracefully:**
   - Scripts include retry logic
   - Reduce workers if seeing 429 errors
   - Add delays between requests if needed

## Troubleshooting

### Eventlog scraper stuck
- Check API availability
- Reduce max_workers
- Run in smaller batches

### Backfill failing
- Check eventlog_entries.json exists
- Verify database permissions
- Check for disk space

### Missing data persists
- Verify ESPN has the data (check web UI)
- Check for API endpoint changes
- Review error logs in script output

## Future Enhancements

1. **Incremental updates:**
   - Only scan fighters added recently
   - Track last update timestamp per fighter

2. **Automated scheduling:**
   - Cron jobs for daily/weekly updates
   - Webhooks for event results

3. **Real-time updates:**
   - WebSocket connections for live fights
   - Push notifications for result updates

4. **Data quality automation:**
   - Automatic cleanup of orphaned records
   - Duplicate detection and merging

## Related Files

- `/notebooks/grabData.ipynb` - Original data collection notebook
- `/archive/updateData.ipynb` - Legacy update scripts
- `/mma_website/utils/helpers.py` - Core API helper functions
- `/mma_website/utils/db_utils.py` - Database utilities
- `/scripts/` - New automated update scripts

## Support

For issues or questions:
1. Check validation output first
2. Review script error logs
3. Verify ESPN API availability
4. Check database integrity

---

**Last Updated:** 2025-10-24
**Author:** Claude Code

# Automated UFC Rankings Update System ✅

## Overview
Your MMA website now automatically updates UFC rankings from ESPN's API daily! Rankings are fetched fresh from ESPN and stored in your database.

## What Was Implemented

### 1. Rankings Update Service
**File**: `mma_website/services/rankings_update_service.py`

- Fetches current UFC rankings from ESPN API
- Supports all divisions (13 total):
  - Men's P4P, Women's P4P
  - Heavyweight, Light Heavyweight, Middleweight
  - Welterweight, Lightweight, Featherweight
  - Bantamweight, Flyweight
  - Women's Bantamweight, Flyweight, Strawweight
- Links fighters to existing athlete records
- Tracks update statistics

### 2. Automated Scheduler
**File**: `mma_website/tasks/scheduler.py`

- Runs rankings update **daily at 3 AM UTC**
- Background scheduler using APScheduler
- Configurable via environment variables
- Graceful shutdown on app exit

### 3. Admin API Endpoints
**File**: `mma_website/routes/admin.py`

New endpoints for managing rankings:

#### Manual Update
```bash
POST /admin/rankings/update
POST /admin/rankings/update?force=true  # Force update
```

#### Rankings Status
```bash
GET /admin/rankings/status
```

#### Scheduler Status
```bash
GET /admin/scheduler/status
```

#### Database Stats
```bash
GET /admin/data/stats
```

### 4. Database Schema Update
**File**: `scripts/update_rankings_schema.sql`

Added columns to `ufc_rankings` table:
- `athlete_id` - Links to ESPN athlete ID
- Index for faster lookups

---

## Quick Start

### Check Rankings Status
```bash
curl http://localhost:5004/admin/rankings/status
```

**Response**:
```json
{
  "divisions_count": 15,
  "last_update": "2025-10-24T11:32:19.399071",
  "needs_update": false,
  "total_rankings": 152
}
```

### Manually Trigger Update
```bash
curl -X POST http://localhost:5004/admin/rankings/update
```

**Response**:
```json
{
  "success": true,
  "message": "Rankings updated successfully",
  "stats": {
    "divisions_processed": 13,
    "rankings_updated": 122,
    "new_fighters": 0,
    "errors": 0,
    "duration_seconds": 2.61
  }
}
```

### Check Scheduler Status
```bash
curl http://localhost:5004/admin/scheduler/status
```

**Response**:
```json
{
  "enabled": true,
  "jobs": [
    {
      "id": "update_rankings",
      "name": "Update UFC Rankings",
      "next_run": "2025-10-23T03:00:00-05:00",
      "trigger": "cron[hour='3', minute='0']"
    }
  ]
}
```

---

## Configuration

### Environment Variables (.env)

```bash
# Enable/disable scheduler
SCHEDULER_ENABLED=True

# Cron schedule for rankings update
# Format: minute hour day month day_of_week
RANKINGS_UPDATE_CRON=0 3 * * *  # Daily at 3 AM UTC

# Examples:
# Every 12 hours: 0 */12 * * *
# Every Monday at 6 AM: 0 6 * * 1
# Twice daily (6 AM and 6 PM): 0 6,18 * * *
```

### Disable Scheduler
```bash
SCHEDULER_ENABLED=False
```

---

## Using the Service Programmatically

### In Python Code

```python
from mma_website import create_app, db
from mma_website.services.rankings_update_service import get_rankings_service

app = create_app()
with app.app_context():
    service = get_rankings_service()

    # Check if update needed
    if service.needs_update(hours=24):
        print("Rankings need updating")

    # Get last update time
    last_update = service.get_last_update_time()
    print(f"Last updated: {last_update}")

    # Perform update
    stats = service.update_rankings()
    print(f"Updated {stats['updated_rankings']} rankings")
```

### Manual Script

Create `scripts/update_rankings_manual.py`:

```python
#!/usr/bin/env python3
"""Manually update UFC rankings"""
from mma_website import create_app, db
from mma_website.services.rankings_update_service import get_rankings_service

def main():
    app = create_app()
    with app.app_context():
        service = get_rankings_service()
        print("Updating UFC rankings...")
        stats = service.update_rankings()
        print(f"✅ Complete! Updated {stats['updated_rankings']} rankings")

if __name__ == "__main__":
    main()
```

Run it:
```bash
uv run python scripts/update_rankings_manual.py
```

---

## How It Works

### 1. Fetch Rankings from ESPN
```python
# Service fetches from ESPN API
GET https://sports.core.api.espn.com/v2/sports/mma/leagues/ufc/rankings
```

### 2. Process Each Division
For each division (Lightweight, Heavyweight, etc.):
- Fetch current rankings (1-15 typically)
- Get fighter names from ESPN
- Match to existing fighters in database (by ID)
- Update rankings table

### 3. Update Database
```sql
-- Delete old rankings for division
DELETE FROM ufc_rankings WHERE division = 'Lightweight'

-- Insert new rankings
INSERT INTO ufc_rankings
  (division, fighter_name, rank, is_champion, athlete_id, last_updated)
VALUES
  ('Lightweight', 'Charles Oliveira', 1, 1, '2504169', '2025-10-24T11:32:19')
```

### 4. Track Statistics
- Divisions processed
- Rankings updated
- New fighters discovered
- Errors encountered
- Duration

---

## Querying Updated Rankings

### SQL Examples

```sql
-- Get current P4P rankings
SELECT fighter_name, rank
FROM ufc_rankings
WHERE ranking_type = 'Pound for Pound'
ORDER BY rank;

-- Get Lightweight division
SELECT fighter_name, rank, is_champion
FROM ufc_rankings
WHERE division = 'Lightweight'
ORDER BY rank;

-- Get all champions
SELECT division, fighter_name
FROM ufc_rankings
WHERE is_champion = 1;

-- Check last update time
SELECT MAX(last_updated)
FROM ufc_rankings;

-- Count rankings per division
SELECT division, COUNT(*)
FROM ufc_rankings
GROUP BY division
ORDER BY division;
```

### Python Example

```python
from sqlalchemy import text

with app.app_context():
    # Get P4P rankings
    result = db.session.execute(text("""
        SELECT fighter_name, rank
        FROM ufc_rankings
        WHERE ranking_type = 'Pound for Pound'
        ORDER BY rank
    """))

    for row in result:
        print(f"#{row.rank}: {row.fighter_name}")
```

---

## Testing

### Test Update Service
```bash
uv run python -c "
from mma_website import create_app
from mma_website.services.rankings_update_service import get_rankings_service

app = create_app()
with app.app_context():
    service = get_rankings_service()
    stats = service.update_rankings()
    print(f'Updated {stats[\"updated_rankings\"]} rankings in {stats[\"total_divisions\"]} divisions')
"
```

### Test Admin Endpoints
```bash
# Status
curl http://localhost:5004/admin/rankings/status

# Manual update
curl -X POST http://localhost:5004/admin/rankings/update

# Database stats
curl http://localhost:5004/admin/data/stats

# Scheduler status
curl http://localhost:5004/admin/scheduler/status
```

---

## Monitoring

### Check Logs
```bash
# View recent log entries
tail -f logs/mma_website.log | grep -i ranking

# Check for errors
tail -f logs/mma_website_error.log
```

### Expected Log Output
```
INFO - Starting UFC rankings update
INFO - Fetching UFC rankings from ESPN API
INFO - Fetched 13 division rankings
INFO - Processing rankings for Pound for Pound
INFO - Processing rankings for Lightweight
...
INFO - Rankings update completed successfully
INFO - Rankings update complete: 122 rankings updated in 2.61s
```

---

## Troubleshooting

### Rankings Not Updating

**Check if scheduler is running**:
```bash
curl http://localhost:5004/admin/scheduler/status
```

**Check logs for errors**:
```bash
tail -f logs/mma_website.log | grep ERROR
```

**Manually trigger update**:
```bash
curl -X POST "http://localhost:5004/admin/rankings/update?force=true"
```

### ESPN API Errors

If ESPN API is down or slow:
- Service will log errors but continue
- Rankings will use last successful update
- Check logs for specific API errors

### Database Errors

**Check schema is updated**:
```bash
sqlite3 data/mma.db "PRAGMA table_info(ufc_rankings);"
# Should show athlete_id column
```

**Reapply schema update if needed**:
```bash
sqlite3 data/mma.db < scripts/update_rankings_schema.sql
```

---

## Statistics

### Current Update Results
✅ **13 divisions** fetched
✅ **122 rankings** updated
✅ **0 errors**
✅ **2.61 seconds** duration

### Database Counts
- **152 total rankings** across all divisions
- **15 unique divisions** (including P4P)
- **36,809 fighters** in database
- **75,408 fights** recorded

---

## Next Steps

### Potential Enhancements

1. **Email Notifications**
   - Send email when rankings change
   - Alert on major ranking movements

2. **Ranking History**
   - Track ranking changes over time
   - Show fighter's ranking progression

3. **Webhook Integration**
   - Notify external services when rankings update
   - Trigger social media posts

4. **More Frequent Updates**
   - Update after major UFC events
   - Check for updates multiple times per day

5. **Dashboard**
   - Visual admin dashboard for monitoring
   - Charts showing ranking trends

---

## Files Created/Modified

### New Files
- `mma_website/services/rankings_update_service.py` - Core update service
- `mma_website/tasks/__init__.py` - Task package
- `mma_website/tasks/scheduler.py` - APScheduler setup
- `mma_website/routes/admin.py` - Admin API endpoints
- `scripts/update_rankings_schema.sql` - Database schema updates

### Modified Files
- `mma_website/__init__.py` - Initialize scheduler, register admin blueprint
- `mma_website/config.py` - Add scheduler configuration
- `.env.example` - Add scheduler environment variables
- `pyproject.toml` - Add APScheduler dependency

---

## Dependencies Added

```toml
apscheduler = ">=3.11.0"
```

---

**Status**: ✅ Fully Functional
**Last Updated**: 2025-10-24
**Auto-Update**: Daily at 3 AM UTC

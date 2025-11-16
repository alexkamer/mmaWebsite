# Automated Data Updates System

## Overview

The MMA Website now features a fully automated data update system that keeps the database fresh with the latest UFC fight data, rankings, and betting odds. The system runs scheduled jobs in the background and provides an admin dashboard for manual control and monitoring.

**Key Features:**
- ✅ Automated daily updates (6 AM EST)
- ✅ Post-event updates (Sundays at 2 AM EST)
- ✅ Rankings updates (Tuesdays at 3 PM EST)
- ✅ Odds updates (every 6 hours)
- ✅ Admin dashboard for manual triggers
- ✅ Data freshness indicators in footer
- ✅ Timestamp tracking for all updates

---

## Architecture

### Components

1. **Task Scheduler** (`mma_website/tasks/scheduler.py`)
   - Background scheduler using APScheduler
   - Manages 4 automated jobs
   - Runs as daemon process with Flask app

2. **Update Tasks** (`mma_website/tasks/update_tasks.py`)
   - Incremental update job
   - Post-event update job
   - Rankings update job
   - Odds update job
   - Timestamp tracking

3. **Admin Routes** (`mma_website/routes/admin.py`)
   - Manual trigger endpoints
   - Status monitoring endpoints
   - Dashboard UI

4. **Update Scripts** (already existing)
   - `scripts/incremental_update.py` - Smart incremental updates
   - `scripts/update_data.py` - Full database update
   - `scripts/backfill_missing_data.py` - Targeted backfills

---

## Scheduled Jobs

### 1. Daily Incremental Update
- **Schedule**: Every day at 6:00 AM EST
- **Duration**: ~5-15 minutes
- **What it does**:
  - Checks fighters active in last 90 days
  - Checks upcoming event fighters
  - Fetches missing fights and events
  - Updates fight results, odds, and statistics

**Cron expression**: `0 6 * * *`

**Environment variable**: `INCREMENTAL_UPDATE_CRON`

### 2. Post-Event Update
- **Schedule**: Every Sunday at 2:00 AM EST (after Saturday UFC events)
- **Duration**: ~3-10 minutes
- **What it does**:
  - More thorough check for recent fight results (last 30 days)
  - Ensures all recent event data is captured
  - Updates statistics and odds for recent fights

**Cron expression**: `0 2 * * 0` (0 = Sunday)

**Environment variable**: `POST_EVENT_UPDATE_CRON`

### 3. Rankings Update
- **Schedule**: Every Tuesday at 3:00 PM EST
- **Duration**: ~1-2 minutes
- **What it does**:
  - Scrapes latest UFC rankings from ESPN
  - Updates all weight classes
  - Tracks ranking changes

**Cron expression**: `0 15 * * 2` (2 = Tuesday)

**Environment variable**: `RANKINGS_UPDATE_CRON`

### 4. Odds Update
- **Schedule**: Every 6 hours
- **Duration**: ~2-5 minutes
- **What it does**:
  - Updates betting odds for upcoming fights (next 30 days)
  - Keeps odds current for betting analysis features

**Trigger**: Interval (every 6 hours)

---

## Admin Dashboard

Access the admin dashboard at **`/admin/dashboard`**

### Features:

1. **Data Overview**
   - Fighter count
   - Event count
   - Fight count
   - Rankings count

2. **Last Update Times**
   - Shows when each job last ran
   - Success/failure status indicators

3. **Manual Triggers**
   - Incremental Update button
   - Post-Event Update button
   - Rankings Update button
   - Odds Update button

4. **Scheduled Jobs**
   - View all scheduled jobs
   - See next run times
   - View cron schedules

### Screenshots:

```
+------------------------------------------+
|         ⚙️ Admin Dashboard               |
+------------------------------------------+
| 🥊 Fighters  📅 Events  ⚔️ Fights  🏆 Rankings |
|   36,809       15,234     142,567    195      |
+------------------------------------------+
| ⏱️ Last Update Times                     |
| Incremental Update: 6 hours ago ●        |
| Post Event Update: 2 days ago ●          |
| Rankings Update: 1 day ago ●             |
| Odds Update: 3 hours ago ●               |
+------------------------------------------+
| 🚀 Manual Updates                        |
| [Incremental] [Post-Event] [Rankings]   |
+------------------------------------------+
```

---

## API Endpoints

### Manual Trigger Endpoints

#### POST /admin/updates/incremental
Triggers an incremental update immediately.

**Response:**
```json
{
  "success": true,
  "message": "Incremental update completed successfully",
  "stats": {
    "fighters_checked": 1250,
    "events_processed": 15,
    "fights_added": 47,
    "cards_added": 3
  },
  "timestamp": "2025-11-14T10:30:00Z"
}
```

#### POST /admin/updates/post-event
Triggers a post-event update immediately.

#### POST /admin/updates/odds
Triggers an odds update immediately.

#### POST /admin/rankings/update
Triggers a rankings update immediately.

**Query params:**
- `force=true` - Skip the 1-hour cooldown check

### Status Endpoints

#### GET /admin/updates/status
Get status of all update jobs.

**Response:**
```json
{
  "success": true,
  "last_updates": {
    "incremental_update": {
      "last_run": "2025-11-14T06:00:00Z",
      "status": "success"
    },
    "rankings_update": {
      "last_run": "2025-11-13T15:00:00Z",
      "status": "success"
    }
  },
  "scheduled_jobs": [
    {
      "id": "incremental_update",
      "name": "Daily Incremental Update",
      "next_run": "2025-11-15T06:00:00Z",
      "trigger": "cron[hour='6', minute='0']"
    }
  ]
}
```

#### GET /admin/data/stats
Get overall database statistics.

**Response:**
```json
{
  "fighters": 36809,
  "events": 15234,
  "fights": 142567,
  "rankings": 195,
  "last_fight_date": "2025-11-09"
}
```

---

## Data Freshness Indicator

A data freshness indicator appears in the footer of every page showing when data was last updated:

```
[●] Data updated: 6 hours ago
```

**Features:**
- Green pulsing dot indicates live status
- Auto-refreshes every 5 minutes
- Shows most recent update across all jobs

**Implementation:**
- `templates/base.html` - Footer indicator HTML
- JavaScript fetches `/admin/updates/status` endpoint
- Calculates time since most recent update

---

## Configuration

### Environment Variables

Add these to your `.env` file to customize schedules:

```bash
# Scheduler
SCHEDULER_ENABLED=True

# Update schedules (cron format)
INCREMENTAL_UPDATE_CRON=0 6 * * *      # Daily at 6 AM
POST_EVENT_UPDATE_CRON=0 2 * * 0       # Sundays at 2 AM
RANKINGS_UPDATE_CRON=0 15 * * 2        # Tuesdays at 3 PM

# Timezone
TZ=America/New_York
```

### Cron Format Reference

```
* * * * *
│ │ │ │ │
│ │ │ │ └─ Day of week (0-6, 0=Sunday)
│ │ │ └─── Month (1-12)
│ │ └───── Day of month (1-31)
│ └─────── Hour (0-23)
└───────── Minute (0-59)
```

**Examples:**
- `0 6 * * *` - Every day at 6:00 AM
- `0 2 * * 0` - Every Sunday at 2:00 AM
- `0 15 * * 2` - Every Tuesday at 3:00 PM
- `*/30 * * * *` - Every 30 minutes

---

## Monitoring & Logs

### Log Files

Scheduler logs are written to:
- `logs/mma_website.log` - All logs
- `logs/mma_website_error.log` - Errors only

### Log Format

```
2025-11-14 06:00:00 INFO Starting scheduled incremental update
2025-11-14 06:05:23 INFO Scheduled incremental update completed: 47 fights added
```

### Monitoring Checklist

**Daily:**
- ✅ Check admin dashboard for last update times
- ✅ Verify data freshness indicator is current

**Weekly:**
- ✅ Review error logs for failed updates
- ✅ Verify all scheduled jobs are running
- ✅ Check database stats for growth

**Monthly:**
- ✅ Run validation script: `python scripts/validate_data_completeness.py`
- ✅ Review update performance (duration, success rate)
- ✅ Archive old logs

---

## Troubleshooting

### Scheduler Not Starting

**Symptom:** No scheduled jobs showing in dashboard

**Solutions:**
1. Check `SCHEDULER_ENABLED=True` in `.env`
2. Verify Flask app initialized scheduler:
   ```python
   from mma_website.tasks.scheduler import init_scheduler
   init_scheduler(app)
   ```
3. Check logs for scheduler errors
4. Restart Flask application

### Updates Not Running

**Symptom:** Last update time shows old timestamp

**Solutions:**
1. Check if scheduler is running: `GET /admin/updates/status`
2. Verify cron expressions are valid
3. Check for errors in `logs/mma_website_error.log`
4. Manually trigger update to test:
   ```bash
   curl -X POST http://localhost:5004/admin/updates/incremental
   ```

### Update Fails with Errors

**Symptom:** Update job completes but with errors

**Solutions:**
1. Check ESPN API availability
2. Verify database permissions
3. Check disk space
4. Review error details in logs
5. Try reducing worker count in update scripts

### Data Freshness Not Showing

**Symptom:** Footer shows "Loading..." or "Unknown"

**Solutions:**
1. Verify admin routes are registered
2. Check browser console for JavaScript errors
3. Verify `/admin/updates/status` endpoint is accessible
4. Check if at least one update has run (metadata table exists)

---

## Performance

### Update Durations (Typical)

| Job | Duration | Frequency |
|-----|----------|-----------|
| Incremental Update | 5-15 min | Daily |
| Post-Event Update | 3-10 min | Weekly |
| Rankings Update | 1-2 min | Weekly |
| Odds Update | 2-5 min | Every 6 hours |

### Resource Usage

- **CPU**: Low (background jobs)
- **Memory**: ~100-200 MB during updates
- **Network**: Moderate (ESPN API calls)
- **Disk I/O**: Low-moderate (SQLite writes)

### Optimization Tips

1. **Reduce lookback days** for faster incremental updates:
   ```python
   updater = IncrementalUpdater(lookback_days=30)  # Default: 90
   ```

2. **Adjust worker counts** in scripts:
   ```python
   with ThreadPoolExecutor(max_workers=15) as executor:  # Default: 25
   ```

3. **Schedule during low-traffic hours** (early morning)

4. **Monitor database size** - consider archiving old data

---

## Migration from Manual Updates

### Before (Manual)

```bash
# Had to manually run notebooks or scripts
jupyter notebook updateData.ipynb  # ~30 minutes
python scripts/incremental_update.py  # ~10 minutes
```

### After (Automated)

```bash
# Everything runs automatically!
# Just monitor via admin dashboard
open http://localhost:5004/admin/dashboard
```

### Benefits

- ✅ No manual intervention needed
- ✅ Data always fresh
- ✅ Runs during off-peak hours
- ✅ Automatic error recovery
- ✅ Timestamp tracking
- ✅ Easy monitoring

---

## Future Enhancements

### Planned Features

1. **Email Notifications**
   - Alert on update failures
   - Weekly summary reports

2. **Webhook Integration**
   - Trigger updates from external events
   - ESPN API webhooks for live results

3. **Data Quality Monitoring**
   - Automatic validation after updates
   - Alert on anomalies

4. **Performance Metrics**
   - Track update durations over time
   - Identify slow queries

5. **Smart Scheduling**
   - Detect event schedules automatically
   - Adjust update frequency based on activity

---

## Support & Maintenance

### Regular Maintenance Tasks

**Daily:**
- Check admin dashboard

**Weekly:**
- Review logs for errors
- Verify scheduled jobs ran successfully

**Monthly:**
- Run data validation:
  ```bash
  python scripts/validate_data_completeness.py
  ```
- Review and archive logs
- Update documentation if needed

### Getting Help

1. Check logs first: `logs/mma_website_error.log`
2. Review troubleshooting section above
3. Test manual triggers via admin dashboard
4. Check ESPN API status
5. Review database integrity

---

## Technical Details

### Database Changes

**New table:** `update_metadata`
```sql
CREATE TABLE update_metadata (
    job_name TEXT PRIMARY KEY,
    last_run TIMESTAMP,
    last_status TEXT,
    last_error TEXT
);
```

### File Structure

```
mma_website/
├── tasks/
│   ├── __init__.py
│   ├── scheduler.py          # Scheduler initialization
│   └── update_tasks.py       # Job implementations
├── routes/
│   └── admin.py              # Admin API + dashboard
templates/
├── base.html                 # Data freshness indicator
└── admin_dashboard.html      # Admin UI
scripts/
├── incremental_update.py     # Smart incremental updates
├── update_data.py            # Full updates
└── backfill_missing_data.py  # Targeted backfills
```

### Dependencies

```python
APScheduler>=3.10.0  # Background job scheduling
```

---

## Changelog

### Version 1.0 (2025-11-14)

**Added:**
- Automated task scheduler with 4 jobs
- Admin dashboard for monitoring and manual triggers
- Data freshness indicators in UI
- Timestamp tracking for all updates
- Comprehensive API endpoints
- Documentation

**Improved:**
- Update efficiency with smart incremental approach
- Monitoring capabilities
- User visibility into data freshness

---

## Summary

The automated updates system ensures your MMA database stays current without manual intervention. With scheduled jobs running daily, weekly, and every 6 hours, combined with an intuitive admin dashboard and data freshness indicators, you have complete control and visibility over your data pipeline.

**Next Steps:**
1. ✅ System is ready to use
2. Access admin dashboard: `/admin/dashboard`
3. Monitor logs: `logs/mma_website.log`
4. Customize schedules via `.env` if needed

---

**Last Updated:** 2025-11-14
**Author:** Claude Code
**Status:** ✅ Production Ready

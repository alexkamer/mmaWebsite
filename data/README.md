# Data Directory

This directory contains the SQLite database for the MMA Website.

## Database File

- `mma.db` - Main SQLite database (94MB, not tracked in git)

## Database Schema

### Main Tables

- **athletes** - Fighter profiles (17,000+ records)
  - Personal information, photos, stats, records

- **cards** - Event information
  - Event name, date, venue, league

- **fights** - Individual fight details
  - Fighter IDs, results, methods, odds

- **odds** - Betting odds from multiple providers
  - Provider-specific odds data

- **statistics_for_fights** - Detailed fight statistics
  - Strikes, takedowns, control time, etc.

- **ufc_rankings** - Current UFC rankings
  - Division, rank, fighter

- **leagues** - Promotion information
  - UFC, Bellator, PFL, ONE, regional promotions

- **fighter_events** - Many-to-many relationship
  - Links fighters to events they participated in

## Setup

The database is not included in the repository due to its size (94MB).

### Initialize Database

**Quick Setup (Testing)**
```bash
uv run python scripts/update_data.py
# Takes 15-30 minutes
```

**Full Setup (Production)**
```bash
# Step 1: Initial data
uv run python scripts/update_data.py

# Step 2: Backfill historical data (run overnight)
uv run python scripts/backfill_fighter_events.py --mode full
# Takes 3-8 hours
```

## Maintenance

### Regular Updates

**Daily/Weekly**
```bash
uv run python scripts/incremental_update.py --days 30
```

**Monthly Full Sync**
```bash
uv run python scripts/backfill_fighter_events.py --mode full
```

### Backup

```bash
# Create backup
cp data/mma.db data/mma.db.backup

# Or use SQLite dump
sqlite3 data/mma.db .dump > backup.sql
```

### Optimization

```bash
# Add database indexes
uv run python scripts/add_database_indexes.py

# Vacuum database (reclaim space)
sqlite3 data/mma.db "VACUUM;"
```

## Size Information

- **Current Size**: ~94MB
- **Record Counts**:
  - Fighters: 17,000+
  - Events: 5,000+
  - Fights: 100,000+
  - Odds: Multiple providers
  - Statistics: Detailed metrics

## Notes

- Database uses SQLite for simplicity
- Foreign key constraints enabled
- Indexes on commonly queried fields
- Full-text search on fighter names
- Normalized international character support

## Troubleshooting

### "Database is locked"
Multiple processes accessing database. Close other connections.

### "Database file not found"
Run setup scripts to create database.

### "Disk space full"
Requires ~10GB free space for operations.

### Corrupted database
```bash
# Check integrity
sqlite3 data/mma.db "PRAGMA integrity_check;"

# If corrupted, restore from backup or rebuild
rm data/mma.db
uv run python scripts/update_data.py
```

For more information, see [docs/DATA_UPDATE_GUIDE.md](../docs/DATA_UPDATE_GUIDE.md)

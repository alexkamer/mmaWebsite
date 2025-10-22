# Notebooks Directory

## Active Notebooks

### `grabData.ipynb`
**Status**: ✅ Active (for initial data collection)
**Purpose**: Initial data exploration and collection from ESPN API
**Usage**: One-time or exploratory data gathering

### `analyze_data.ipynb`
**Status**: ✅ Active (for analysis)
**Purpose**: Data analysis and exploration of the MMA database
**Usage**: Ad-hoc analysis, statistical exploration, database queries

---

## Deprecated Notebooks

### `updateData.ipynb` → **ARCHIVED**
**Status**: ⚠️ Deprecated (moved to `archive/updateData.ipynb`)
**Reason**: Replaced by production-ready Python scripts

**Use these scripts instead:**

1. **Daily/Weekly Updates** (2-10 minutes)
   ```bash
   uv run python scripts/incremental_update.py --days 30
   ```

2. **Monthly Full Sync** (3-8 hours)
   ```bash
   uv run python scripts/backfill_fighter_events.py --mode full
   ```

3. **Initial Setup** (15-30 minutes)
   ```bash
   uv run python scripts/update_data.py
   ```

---

## Why Scripts Over Notebooks?

The data update functionality has been moved from Jupyter notebooks to dedicated Python scripts for several reasons:

1. **Production Ready**: Scripts are easier to automate and schedule
2. **Error Handling**: Better error handling and logging
3. **Performance**: Optimized for speed and efficiency
4. **Maintainability**: Cleaner code structure, easier to debug
5. **Version Control**: Better git diffs and code review
6. **Automation**: Can be run via cron jobs or CI/CD

---

## Development Workflow

**For Data Exploration**: Use notebooks (`grabData.ipynb`, `analyze_data.ipynb`)

**For Data Updates**: Use scripts in `scripts/` directory

**For Reference**: Check `archive/updateData.ipynb` to see the original implementation

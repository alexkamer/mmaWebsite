# MMA Website - Project Status & Current Capabilities

**Last Updated**: October 2025
**Status**: ✅ Production-Ready (Modular Architecture)

---

## 🎯 What This Project Accomplishes

A comprehensive MMA (Mixed Martial Arts) web application that provides:

### Core Capabilities
1. **Fighter Database** - 17,000+ fighters with detailed profiles, fight history, and career analytics
2. **Event Management** - Complete UFC and regional promotion event tracking with fight cards
3. **Rankings System** - Real-time UFC rankings across all divisions
4. **Interactive Games** - Fighter Wordle and Tale of the Tape comparison tools
5. **Analytics Dashboard** - Betting system analysis and performance metrics
6. **Live Data** - ESPN API integration for upcoming events and real-time fight data

---

## 📊 Database Stats
- **Size**: 82MB SQLite database
- **Fighters**: 17,000+ athlete profiles
- **Events**: Thousands of historical and upcoming events
- **Fights**: Complete fight history with statistics and odds
- **Odds Data**: Multi-provider betting odds integration

---

## 🏗️ Architecture

### ✅ Current: Modular Flask Application (PRODUCTION)
**Entry Point**: `uv run run.py`

```
mma_website/
├── __init__.py              # Application factory with create_app()
├── config/                  # Configuration management
├── models/
│   ├── database.py          # SQLAlchemy ORM models
│   └── pydantic_models.py   # Pydantic schemas for validation
├── routes/                  # Blueprint-based routing
│   ├── main.py              # Home, fighters list, career timeline
│   ├── events.py            # Event listings and details
│   ├── games.py             # Fighter Wordle, Tale of Tape, Next Event
│   └── api.py               # RESTful API endpoints
├── services/                # Business logic layer
│   └── fighter_service.py   # Fighter data processing
└── utils/                   # Helper utilities
    ├── helpers.py           # General helpers
    └── text_utils.py        # Text normalization
```

### ⚠️ Legacy: Monolithic app.py (DEPRECATED)
- **Status**: Archived in `archive/app.py` (1800+ lines)
- **Usage**: Reference only, not for active development
- **Note**: Fully migrated to modular structure

---

## 🌐 Web Application Routes

### Main Pages
- `/` - Home page with recent events and featured content
- `/fighters` - Fighter search and browse
- `/fighter/<id>` - Detailed fighter profile with fight history
- `/career-timeline/<id>` - Visual career timeline with ranking changes
- `/events` - Event listings by year
- `/events/<event_id>` - Detailed event page with fight card
- `/rankings` - Current UFC rankings by division

### Interactive Games
- `/fighter-wordle` - Guess UFC fighters with hints
- `/tale-of-tape` - Side-by-side fighter comparisons
- `/next-event` - Live upcoming UFC event with ESPN API integration
- `/fight-preview/<fighter1>/<fighter2>` - Detailed fight preview

### Analytics & Tools
- `/system-checker` - Betting system analysis
- `/query` - MMA question answering (experimental)

### API Endpoints
- `GET /api/fighter/<id>` - Fighter data
- `GET /api/fighters/search?q=<query>` - Search fighters
- `GET /api/fight-stats/<fight_id>` - Fight statistics
- `GET /rankings/api` - Rankings data

---

## 🗄️ Database Schema

### Key Tables
- `athletes` - Fighter profiles (name, stats, photos, records)
- `cards` - Event information (name, date, venue, promotion)
- `fights` - Fight details (result, method, round, time, odds)
- `odds` - Betting odds from multiple providers
- `statistics_for_fights` - Detailed fight metrics (strikes, takedowns, etc.)
- `ufc_rankings` - Current UFC rankings by division
- `leagues` - Promotion information (UFC, Bellator, etc.)
- `fighter_events` - Many-to-many relationship for fighter participation

---

## 🔄 Data Update System

### Active Scripts
1. **`scripts/incremental_update.py`** (RECOMMENDED)
   - Purpose: Daily/weekly updates
   - Runtime: 2-10 minutes
   - Usage: `uv run python scripts/incremental_update.py --days 30`

2. **`scripts/backfill_fighter_events.py`** (MONTHLY)
   - Purpose: Comprehensive sync of all fighter events
   - Runtime: 3-8 hours
   - Usage: `nohup uv run python scripts/backfill_fighter_events.py --mode full > backfill.log 2>&1 &`

3. **`scripts/update_data.py`** (LEGACY)
   - Purpose: Initial setup only
   - Runtime: 15-30 minutes

### Update Capabilities
- ✅ New fighter profiles
- ✅ New events and fight cards
- ✅ Fight results and statistics
- ✅ Betting odds updates
- ✅ Regional and international fights
- ✅ UFC rankings

---

## 📁 Directory Structure

### Active Directories
```
/
├── mma_website/              # Main application package (ACTIVE)
├── templates/                # Jinja2 HTML templates
├── static/                   # CSS, JS, images
├── data/                     # SQLite database
├── scripts/                  # Data update scripts (PRODUCTION)
├── notebooks/                # Jupyter notebooks for exploration (see notebooks/README.md)
├── docs/                     # Documentation (organized)
├── archive/                  # Deprecated code (app.py, db.py, models.py, updateData.ipynb)
├── utils/                    # Standalone utility functions (legacy)
├── instance/                 # Flask instance folder
└── logs/                     # Application logs
```

### Root Files
- `run.py` - ✅ Application entry point (CURRENT)
- `pyproject.toml` - Python project configuration (uv)
- `requirements.txt` - Pip dependencies
- `uv.lock` - Locked dependencies
- `.env` / `.env.example` - Environment configuration
- `quick_update.sh` - Quick update wrapper script
- `update_database.sh` - Database update wrapper script

### Documentation Files (Organized in `docs/`)
- `README.md` - User-facing documentation (root)
- `CLAUDE.md` - Development notes and architecture (root)
- `PROJECT_STATUS.md` - This file (root)
- `docs/CHANGELOG.md` - Change log (formerly IMPROVEMENTS_COMPLETED.md)
- `docs/UPDATE_NOTES.md` - Data update notes (formerly UPDATE_SUMMARY.md)
- `docs/UI_CHANGES.md` - UI/UX changes (formerly VISUAL_IMPROVEMENTS.md)
- `docs/DATA_UPDATE_GUIDE.md` - Comprehensive data update guide
- `docs/MMA_QUERY_SETUP.md` - Query feature setup
- `docs/QUESTION_ANALYSIS.md` - Question analysis documentation
- `docs/SETUP_STATUS.md` - Setup status and configuration

### Shell Scripts
- `quick_update.sh` - Quick data update wrapper
- `update_database.sh` - Database update wrapper

---

## 🔧 Development Tools

### Jupyter Notebooks (Active)
- `notebooks/grabData.ipynb` - ✅ Initial data collection from ESPN
- `notebooks/analyze_data.ipynb` - ✅ Data analysis and exploration
- ~~`notebooks/updateData.ipynb`~~ - ⚠️ **DEPRECATED** (moved to `archive/`, replaced by scripts)

**For data updates, use production scripts instead:**
- `scripts/incremental_update.py` - Daily/weekly updates
- `scripts/backfill_fighter_events.py` - Monthly full sync
- `scripts/update_data.py` - Legacy full update

See `notebooks/README.md` for details.

### Utility Scripts
- `scripts/utilities/accurate_ufc_scraper.py` - UFC rankings scraper
- `scripts/utilities/update_ufc_rankings.py` - Update rankings in DB
- `scripts/add_database_indexes.py` - Database optimization
- `scripts/debug/` - Various debugging scripts

---

## 🚀 Running the Application

### Development
```bash
# Install dependencies
uv sync

# Run the application
uv run run.py

# Access at http://127.0.0.1:5000
```

### Data Updates
```bash
# Quick daily update
uv run python scripts/incremental_update.py --days 7

# Full monthly backfill
uv run python scripts/backfill_fighter_events.py --mode full
```

---

## 📦 Dependencies

### Core
- Flask 3.1+ - Web framework
- SQLAlchemy 2.0+ - ORM
- Flask-SQLAlchemy - Flask integration
- Flask-Caching - Caching layer
- Pydantic 2.11+ - Data validation

### Data Collection
- requests - HTTP client
- beautifulsoup4 - HTML parsing
- pandas - Data manipulation

### AI/ML (Optional)
- openai - GPT integration for query feature
- agno - AI agent framework
- crawl4ai - Web scraping

---

## ✅ Completed Features

### Architecture
- ✅ Migrated from monolithic to modular structure
- ✅ Blueprint-based routing
- ✅ Service layer separation
- ✅ Pydantic models for validation
- ✅ Application factory pattern

### Features
- ✅ ESPN API integration for live events
- ✅ Fight preview with detailed stats
- ✅ Career timeline visualization
- ✅ Fighter name normalization (international characters)
- ✅ Advanced fighter search
- ✅ Betting system analysis
- ✅ Tale of the Tape comparisons
- ✅ Fighter Wordle game

### Data
- ✅ Incremental update system
- ✅ Backfill script for historical data
- ✅ Database indexes for performance
- ✅ Multi-provider odds integration

---

## 🎯 Future Enhancements

### Features
- [ ] User authentication and favorites
- [ ] Fight predictions and picks
- [ ] Advanced analytics dashboard
- [ ] Fighter comparison tools
- [ ] Email notifications for events
- [ ] Mobile-responsive design improvements

### Technical
- [ ] Redis caching layer
- [ ] GraphQL API
- [ ] Automated testing suite
- [ ] CI/CD pipeline
- [ ] Docker containerization
- [ ] Production deployment configuration

### Data
- [ ] Real-time odds updates
- [ ] Fighter social media integration
- [ ] Video highlights integration
- [ ] Advanced statistics (ELO ratings, etc.)

---

## 📝 Notes

- The application is fully functional and production-ready
- All legacy code has been archived
- The modular architecture allows for easy feature additions
- Data updates are semi-automated (manual trigger required)
- Database is version-controlled (schema changes tracked)
- Documentation is comprehensive and up-to-date

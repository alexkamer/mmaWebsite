# MMA Website - Claude Code Analysis

## Overview
A comprehensive MMA (Mixed Martial Arts) Flask web application featuring fighter profiles, event management, rankings, and interactive games. The app currently uses the older Flask structure (single app.py) but has a newer modular structure available in the `mma_website/` package.

## Current Webapp Capabilities

### Core Features
1. **Fighter Database & Profiles** (`/fighter/<id>`)
   - Detailed fighter information with photos, stats, records
   - Fight history with filtering by promotion, rounds, fight type, weight class, odds
   - Career timeline visualization with fights and ranking changes
   - Fighter search functionality with normalized name matching

2. **Event Management** (`/events`)
   - Event listings by year with fight cards
   - Detailed event pages showing all fights with fighter photos and odds
   - Fight statistics when available
   - Recent and upcoming events on homepage

3. **UFC Rankings** (`/rankings`)
   - Current UFC rankings by division (men's and women's)
   - Pound-for-pound rankings
   - Champion and interim champion tracking

4. **Interactive Games**
   - **Fighter Wordle** (`/fighter-wordle`): Guess UFC fighters with hints
   - **Tale of the Tape** (`/tale-of-tape`): Side-by-side fighter comparisons

5. **Analytics Tools**
   - **Next Event** (`/next-event`): Live upcoming UFC event data from ESPN API
   - **System Checker** (`/system-checker`): Betting system analysis (age gaps, favorites, etc.)

### Technical Features
- SQLite database with comprehensive MMA data (82MB database)
- Real-time odds integration from multiple providers
- Fighter name normalization for international characters
- Responsive design with Tailwind CSS
- Search functionality across fighters

## Database Schema
Key tables:
- `athletes`: Fighter profiles, stats, photos
- `cards`: Event information 
- `fights`: Fight results, statistics, odds
- `odds`: Betting odds from multiple providers
- `statistics_for_fights`: Detailed fight metrics
- `ufc_rankings`: Current UFC rankings

## Architecture Status

### ✅ Current Implementation (Modular - MIGRATED!)
- **Structure**: Clean modular Flask app using blueprints
- **Entry Point**: `uv run run.py` (uses application factory pattern)
- **Blueprints**: Organized routes in `mma_website/routes/`
  - `main.py`: Home, fighters list, career timeline, system checker
  - `events.py`: Event listings and details with services
  - `games.py`: Fighter Wordle, Tale of Tape, **Next Event with ESPN API**
  - `api.py`: RESTful API endpoints
- **Services**: Business logic separated in `services/`
- **Models**: Database models and Pydantic schemas
- **Utils**: Helper functions and text processing
- **Templates**: Updated to use blueprint URL routing

### ⚠️ Legacy Implementation (app.py - DEPRECATED)
- Single monolithic Flask app (~1800 lines)  
- **Status**: Still works but should not be used for new development
- **Usage**: `uv run app.py` (for reference only)

## What's Next

### ✅ COMPLETED: Architecture Migration
- ✅ **Migrated to Modular Structure**: Fully functional blueprint-based app
- ✅ **Next Event ESPN Integration**: Working in modular structure with Fight Preview
- ✅ **Template Updates**: All navigation uses blueprint URLs
- ✅ **Testing**: Confirmed working on `http://127.0.0.1:5000`

### Feature Enhancements
1. **Data Updates**: Implement automated data refresh from ESPN API
2. **User Features**: 
   - Favorite fighters
   - Fight predictions/picks
   - Fighter comparison tools
3. **Analytics**: 
   - Advanced betting system analysis
   - Fighter performance trends
   - Historical data visualization

### Technical Improvements
1. **API Enhancement**: RESTful API endpoints for external consumption
2. **Performance**: Database optimization and caching
3. **Testing**: Add test suite for reliability
4. **Deployment**: Production configuration and deployment setup

## Development Commands
```bash
# Run modular app (CURRENT - RECOMMENDED)
uv run run.py

# Run legacy app (DEPRECATED - for reference only)
uv run app.py

# Database operations (Jupyter notebooks)
# updateData.ipynb - Main data updates
# grabData.ipynb - Initial data collection
```

## Key Files
- `run.py`: **CURRENT** Entry point for modular app
- `mma_website/`: **CURRENT** Modular application structure (blueprints, services, models)
- `app.py`: **LEGACY** Monolithic application (1800+ lines) - for reference only
- `requirements.txt`: Python dependencies
- `data/mma.db`: Main SQLite database (82MB)
- `templates/`: Jinja2 HTML templates (updated for blueprint routing)
- `updateData.ipynb`: Data update scripts
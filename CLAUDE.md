# MMA Website - Claude Code Analysis

## Overview
A comprehensive MMA (Mixed Martial Arts) web application featuring fighter profiles, event management, rankings, and interactive games. The application uses a **FastAPI backend** with a **Next.js frontend** for a modern, professional architecture.

## Current Webapp Capabilities

### Core Features
1. **Fighter Database & Profiles**
   - **Fighters List** (`/fighters`) ✅ **MIGRATED TO NEXT.JS**
     - Searchable database of 36,847+ fighters with infinite scroll
     - Alphabet filter (A-Z) for quick navigation
     - Weight class filtering with fighter counts
     - Fighter cards displaying photos, nicknames, records, weight class
     - Compare mode for side-by-side fighter analysis
     - Responsive grid layout (1-4 columns based on screen size)
   - **Fighter Detail** (`/fighters/{id}`) ✅ **MIGRATED TO NEXT.JS**
     - Premium split-screen hero design with gradient backgrounds
     - Large fighter image with country flag overlay
     - Comprehensive fighter stats (record, height, weight, reach, stance, nationality, team)
     - Win/loss streak indicators with visual badges
     - Interactive fight statistics cards (finish rate, KO/TKO, submissions, decisions, avg fight time, R1 finishes)
     - Complete fight history table with result filters (All/Wins/Losses/Draws)
     - Promotion filtering (UFC, Bellator, PFL, etc.)
     - Clickable opponents linking to their profiles
     - Event links, title fight badges, betting odds display
     - Compare functionality with searchable fighter modal
     - Hover effects and smooth transitions throughout

2. **Event Management**
   - **Events List** (`/events`) ✅ **MIGRATED TO NEXT.JS**
     - Premium hero section with grid background pattern
     - Year filtering with horizontal scroll buttons (2025, 2024, 2023, etc.)
     - Promotion tabs with event counts (All/UFC/Other)
     - Responsive event cards grid (1-3 columns)
     - Event cards display: promotion badge, event name, date, location
     - Hover effects with red glow on cards
     - Direct links to event detail pages
     - Loading skeletons for smooth UX
     - Empty state when no events found
   - **Event Detail** (`/events/{id}`) ✅ **MIGRATED TO NEXT.JS**
     - Premium event detail pages with dramatic gradient headers
     - Championship main event showcase with large fighter photos (160px)
     - Main card, prelims, and early prelims sections with progressive visual hierarchy
     - Fighter records calculated at fight time (W-L-D format)
     - Title fight indicators with gold borders and championship badges
     - Fight results, methods, rounds, and timing
     - Winner/loser badges with color coding
     - Responsive design with shadcn/ui components

3. **UFC Rankings** (`/rankings`)
   - Current UFC rankings by division (men's and women's)
   - Pound-for-pound rankings
   - Champion and interim champion tracking

4. **Interactive Games**
   - **Fighter Wordle**: Guess UFC fighters with hints
   - **Tale of the Tape**: Side-by-side fighter comparisons

5. **Analytics Tools**
   - **Next Event**: Live upcoming UFC event data from ESPN API
   - **System Checker**: Betting system analysis (age gaps, favorites, etc.)

### Technical Features
- **FastAPI Backend**: Async Python API with Pydantic models
- **Next.js 16 Frontend**: React 19 with App Router and server components
- **shadcn/ui Components**: Premium UI components (New York style)
- **Tailwind CSS 4**: Modern utility-first CSS framework
- **SQLite Database**: Comprehensive MMA data (82MB database)
- Real-time odds integration from multiple providers
- Fighter name normalization for international characters
- Responsive design optimized for all devices
- Fighter search functionality

## Database Schema
Key tables:
- `athletes`: Fighter profiles, stats, photos
- `cards`: Event information 
- `fights`: Fight results, statistics, odds
- `odds`: Betting odds from multiple providers
- `statistics_for_fights`: Detailed fight metrics
- `ufc_rankings`: Current UFC rankings

## Architecture Status

### ✅ Current Implementation (FastAPI + Next.js)

**Backend - FastAPI** (`backend/`)
- **Entry Point**: `cd backend && python run.py` (Port 8000)
- **Structure**: Clean async API with Pydantic models
- **API Routes**: Organized in `backend/api/`
  - `events.py`: Event listings and detailed event data with fighter records
  - `fighters.py`: Fighter profiles and statistics
  - `rankings.py`: UFC rankings by division
- **Services**: Business logic separated for maintainability
- **Database**: SQLite with async support
- **Features**: CORS enabled, automatic API docs at `/docs`

**Frontend - Next.js** (`frontend/`)
- **Entry Point**: `cd frontend && npm run dev` (Port 3000)
- **Structure**: Next.js 16 App Router with React 19
- **Pages**: Organized in `frontend/app/`
  - `events/[id]/page.tsx`: ✅ Enhanced event detail pages (MIGRATED)
  - Other pages: Still need migration from Flask
- **Components**: Reusable React components with shadcn/ui
  - `FighterCard`: Display fighter info with photos and records
  - `MainEventCard`: Premium main event showcase
  - `FightCard`: Regular fight display for main card/prelims
- **Styling**: Tailwind CSS 4 with shadcn/ui (New York style)
- **API Integration**: TanStack React Query for data fetching

### ⚠️ Legacy Implementation (Flask - DEPRECATED)
- **Status**: Flask templates in `templates/` and `mma_website/` are deprecated
- **Migration**: Gradually moving all features to Next.js frontend
- **Note**: Flask app (`run.py`, `app.py`) should not be used for new development
- **Reference**: Available at `http://127.0.0.1:5004` for comparison only

## What's Next

### ✅ COMPLETED: FastAPI + Next.js Migration
- ✅ **Homepage** (`/`): Professional analytics-style dashboard with champions, events, and featured fighters
- ✅ **Events List Page** (`/events`): Year-based filtering (2015-2025), promotion tabs (All/UFC/Other), responsive event cards with dates and locations
- ✅ **Events Detail Page** (`/events/{id}`): Migrated with enhanced premium design
- ✅ **Rankings Page** (`/rankings`): UFC rankings by division with champion spotlights, fighter photos, stats, search, and tabbed navigation
- ✅ **Fighters List Page** (`/fighters`): Searchable database with 36,847+ fighters, alphabet navigation, weight class filters, infinite scroll, compare mode
- ✅ **Fighter Detail Page** (`/fighters/{id}`): Premium split-screen design with comprehensive stats, fight history with filters, win streaks, fight statistics, and compare functionality
- ✅ **shadcn/ui Setup**: Component library configured (New York style)
- ✅ **FastAPI Backend**: Complete events, homepage, rankings, and fighters APIs with pagination and filtering
- ✅ **Main Event Display**: Fixed fight ordering by match_number
- ✅ **Image Configuration**: ESPN CDN configured for Next.js Image component

### 🚧 Pages to Migrate from Flask
1. **Fighter Compare** (`/fighters/compare`) - Side-by-side fighter comparison with head-to-head records
2. **Games** - Fighter Wordle, Tale of the Tape
3. **Analytics Tools** - Next Event, System Checker

### Feature Enhancements
1. **Data Updates**: Automated data refresh from ESPN API
2. **User Features**:
   - Favorite fighters
   - Fight predictions/picks
   - Enhanced fighter comparison tools
3. **Analytics**:
   - Advanced betting system analysis
   - Fighter performance trends
   - Historical data visualization

### Technical Improvements
1. **Testing**: Add test suite for frontend and backend
2. **Performance**: Database optimization and caching
3. **Deployment**: Production configuration for FastAPI and Next.js
4. **API Docs**: Enhance FastAPI automatic documentation

## Known Issues & Limitations

### Chrome DevTools MCP
⚠️ **CRITICAL**: When using chrome-devtools MCP tools for testing/screenshots:
- **DO NOT use `fullPage: true` on `take_screenshot`** for long pages
- Full-page screenshots can exceed the 8000px dimension limit
- Error: `messages.3.content.2.image.source.base64.data: At least one of the image dimensions exceed max allowed size: 8000 pixels`
- **Solution**: Use viewport screenshots only (default behavior without `fullPage: true`)
- For long pages, take multiple viewport screenshots while scrolling instead

## Development Commands

### Current Stack (FastAPI + Next.js)
```bash
# Start FastAPI backend (Port 8000)
cd backend && python run.py

# Start Next.js frontend (Port 3000)
cd frontend && npm run dev

# View FastAPI docs
open http://localhost:8000/docs

# View Next.js app
open http://localhost:3000
```

### Database Operations
```bash
# Data updates (Jupyter notebooks)
# scripts/update_data.py - Main data updates via CLI
# updateData.ipynb - Interactive data updates
# grabData.ipynb - Initial data collection
```

### Legacy (DEPRECATED - DO NOT USE)
```bash
# Flask app (for reference only)
uv run run.py  # Port 5004
```

## Key Files & Directories

### Current Stack
- **`backend/`**: FastAPI application
  - `backend/run.py`: FastAPI entry point
  - `backend/api/`: API route handlers
  - `backend/services/`: Business logic layer
  - `backend/models/`: Pydantic models
- **`frontend/`**: Next.js application
  - `frontend/app/`: Next.js pages (App Router)
  - `frontend/components/`: React components
  - `frontend/lib/`: Utilities and API client
  - `frontend/components.json`: shadcn/ui configuration
- **`data/mma.db`**: Main SQLite database (82MB)
- **`scripts/`**: Data update scripts

### Legacy (DEPRECATED)
- `mma_website/`: Flask blueprints and templates
- `templates/`: Jinja2 HTML templates
- `app.py`: Monolithic Flask app
- `run.py`: Modular Flask app
# MMA Website - Project Overview

## Purpose
A comprehensive MMA (Mixed Martial Arts) web application featuring:
- 36,847+ fighter profiles with detailed stats and fight history
- Complete UFC and regional promotion event tracking
- Real-time UFC rankings
- Interactive games (Fighter Wordle)
- Betting analytics and system checker
- Live ESPN API integration for upcoming events
- Side-by-side fighter comparisons

## Architecture

### Current Stack (Production)
**Backend - FastAPI** (Port 8000)
- Modern async Python API with Pydantic models
- Entry point: `backend/run.py` 
- Clean separation: API routes, services layer, models
- SQLite database (82MB) with async support
- CORS enabled, automatic API docs at `/docs`

**Frontend - Next.js** (Port 3000)
- Next.js 16 with React 19 and App Router
- Entry point: `cd frontend && npm run dev`
- shadcn/ui components (New York style)
- Tailwind CSS 4 for styling
- TanStack React Query for data fetching

### Legacy Stack (OBSOLETE - Safe to Delete)
⛔ Flask application (Port 5004) - **MIGRATION COMPLETE**
- Files to delete: `mma_website/`, `templates/`, `app.py`, `run.py` (Flask entry point)
- All features migrated to Next.js with enhanced designs

## Migration Status
✅ **COMPLETE** - All Flask pages successfully migrated to Next.js:
- Homepage, Events (list & detail), Rankings
- Fighters (list, detail, compare)
- Next Event (ESPN API), System Checker (betting analytics)
- Fighter Wordle game

## Database
- **Location**: `data/mma.db` (SQLite, 82MB)
- **Key Tables**: athletes, cards, fights, odds, statistics_for_fights, ufc_rankings
- **Data Source**: ESPN API
- **Not in repo**: Database excluded due to size (must be initialized via scripts)

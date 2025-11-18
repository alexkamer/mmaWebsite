# MMA Website - Codebase Structure

## Directory Layout

```
mmaWebsite/
├── backend/                 # FastAPI backend (Port 8000)
│   ├── api/                # API route handlers
│   │   ├── main.py        # FastAPI app entry point, CORS, routes
│   │   ├── events.py      # Event listings and details
│   │   ├── fighters.py    # Fighter profiles and stats
│   │   ├── rankings.py    # UFC rankings
│   │   ├── betting.py     # Betting analytics (System Checker)
│   │   ├── espn.py        # ESPN API integration (Next Event)
│   │   ├── homepage.py    # Homepage data
│   │   ├── wordle.py      # Fighter Wordle game
│   │   └── query.py       # General query endpoint
│   ├── services/          # Business logic layer
│   ├── models/            # Pydantic models and schemas
│   ├── database/          # SQLAlchemy models, DB connection
│   └── run.py             # Backend entry point
│
├── frontend/               # Next.js frontend (Port 3000)
│   ├── app/               # Next.js App Router pages
│   │   ├── page.tsx       # Homepage (/)
│   │   ├── layout.tsx     # Root layout
│   │   ├── globals.css    # Global styles
│   │   ├── events/        # Events list and detail pages
│   │   ├── fighters/      # Fighters list, detail, compare
│   │   ├── rankings/      # Rankings page
│   │   ├── next-event/    # Live ESPN event data
│   │   ├── tools/         # Tool pages (system-checker)
│   │   └── games/         # Game pages (wordle)
│   ├── components/        # Reusable React components
│   │   ├── ui/           # shadcn/ui components
│   │   └── *.tsx         # Custom components (FighterCard, etc.)
│   ├── lib/              # Utilities and API client
│   ├── public/           # Static assets
│   └── package.json      # Frontend dependencies
│
├── data/                  # Database (NOT in repo)
│   └── mma.db            # SQLite database (82MB)
│
├── scripts/               # Data update and management scripts
│   ├── update_data.py            # Initial data setup
│   ├── create_seed_db.py         # Quick seed database
│   ├── incremental_update.py     # Daily/weekly updates
│   └── backfill_fighter_events.py # Full data sync
│
├── notebooks/             # Jupyter notebooks for data exploration
│   ├── updateData.ipynb          # Interactive data updates
│   └── grabData.ipynb            # Initial data collection
│
├── tests/                 # Test suite (pytest)
│
├── docs/                  # Documentation
│
├── ⛔ mma_website/        # OBSOLETE - Flask blueprints (safe to delete)
├── ⛔ templates/          # OBSOLETE - Jinja2 templates (safe to delete)
├── ⛔ static/             # OBSOLETE - Flask static files (safe to delete)
├── ⛔ app.py              # OBSOLETE - Flask app (safe to delete)
├── ⛔ run.py              # OBSOLETE - Flask entry (Port 5004, safe to delete)
│
├── CLAUDE.md              # ⭐ Main project documentation for Claude
├── README.md              # User-facing documentation
├── pyproject.toml         # Python project config (uv)
├── requirements.txt       # Python dependencies
├── pytest.ini             # Pytest configuration
└── .gitignore            # Git ignore rules
```

## Key Files

### Backend Entry Points
- **`backend/run.py`**: Starts FastAPI backend on port 8000 with uvicorn
- **`backend/api/main.py`**: FastAPI app instance, CORS config, route includes

### Frontend Entry Points
- **`frontend/app/layout.tsx`**: Root layout with Providers, fonts
- **`frontend/app/page.tsx`**: Homepage (/)
- **`frontend/package.json`**: Scripts (dev, build, start, lint)

### Configuration Files
- **`pyproject.toml`**: Python dependencies (uv package manager)
- **`frontend/package.json`**: Node dependencies and scripts
- **`frontend/components.json`**: shadcn/ui configuration (New York style)
- **`frontend/tailwind.config.ts`**: Tailwind CSS configuration
- **`pytest.ini`**: Testing configuration
- **`.gitignore`**: Excluded files (database, .env, cache)
- **`.python-version`**: Python version (3.12)

### Documentation Files
- **`CLAUDE.md`**: ⭐ PRIMARY - Complete project overview for AI assistants
- **`README.md`**: User-facing getting started guide
- **`SETUP.md`**: Detailed setup instructions
- **`PROJECT_STATUS.md`**: Project capabilities and status
- **`MIGRATION_PLAN.md`**: Flask to Next.js migration details
- **`NEXT_SESSION.md`**: Next steps and tasks

## Database Schema

**Location**: `data/mma.db` (SQLite, 82MB)

**Key Tables**:
- `athletes`: Fighter profiles (36,847+ fighters)
- `cards`: Event information
- `fights`: Fight results and statistics
- `odds`: Betting odds from multiple providers
- `statistics_for_fights`: Detailed fight metrics
- `ufc_rankings`: Current UFC rankings by division

## API Structure

### Backend API Routes (Port 8000)
- `GET /` - Health check
- `GET /api/homepage` - Homepage data
- `GET /api/events` - Events list with filters
- `GET /api/events/{id}` - Event details
- `GET /api/fighters` - Fighters list with pagination
- `GET /api/fighters/{id}` - Fighter profile
- `GET /api/fighters/compare` - Compare fighters
- `GET /api/rankings` - UFC rankings
- `GET /api/espn/next-event` - Live ESPN event data
- `GET /api/betting/system-checker` - Betting analytics
- `GET /api/wordle/daily-fighter` - Wordle game data
- `GET /docs` - Auto-generated API documentation

### Frontend Pages (Port 3000)
- `/` - Homepage
- `/events` - Events list
- `/events/{id}` - Event detail
- `/fighters` - Fighters list
- `/fighters/{id}` - Fighter profile
- `/fighters/compare?fighter1=X&fighter2=Y` - Fighter comparison
- `/rankings` - UFC rankings
- `/next-event` - Live ESPN event
- `/tools/system-checker` - Betting analytics
- `/games/wordle` - Fighter Wordle game

## Component Organization

### Frontend Components
- **`components/ui/`**: shadcn/ui base components (Button, Card, Avatar, etc.)
- **`components/FighterCard.tsx`**: Fighter display card (reusable)
- **`components/MainEventCard.tsx`**: Premium main event showcase
- **`components/FightCard.tsx`**: Regular fight display
- **`lib/api.ts`**: API client for backend communication
- **`lib/utils.ts`**: Utility functions

## Data Flow
1. **Backend**: FastAPI serves JSON data from SQLite database
2. **Frontend**: Next.js fetches data via TanStack React Query
3. **Database**: SQLite with ESPN API as data source
4. **Updates**: Scripts fetch and update database from ESPN API

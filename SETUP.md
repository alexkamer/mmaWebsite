# Setup Guide

Complete setup instructions for the MMA Website.

## Quick Start

```bash
# 1. Install dependencies
uv sync                          # Backend (Python)
cd frontend && npm install       # Frontend (Node.js)

# 2. Set up database
uv run python scripts/update_data.py

# 3. Start backend (Terminal 1)
cd backend && python run.py      # Runs on http://localhost:8000

# 4. Start frontend (Terminal 2)
cd frontend && npm run dev       # Runs on http://localhost:3000

# 5. Visit http://localhost:3000
```

## Prerequisites

- **Python 3.12+**
- **Node.js 18+** and npm
- **Git**
- **10GB free disk space** (for database)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd mmaWebsite
```

### 2. Install Dependencies

**Backend Dependencies (Python)**

Using uv (Recommended):
```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install backend dependencies
uv sync
```

**Frontend Dependencies (Node.js)**

```bash
# Install Node.js dependencies
cd frontend
npm install
cd ..
```

### 3. Environment Configuration

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Optional: Azure OpenAI for query feature
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_DEPLOYMENT=gpt-4-1
```

**Note:** The Azure OpenAI configuration is only needed if you want to use the experimental MMA query feature (`/api/query` endpoint). The rest of the application works without it.

**Frontend Environment:**

Create `frontend/.env.local`:
```bash
# API endpoint (points to FastAPI backend)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Database Setup

The database is not included in the repository due to its size (94MB). You'll need to create it:

**Option A: Quick Setup (Recommended for Testing)**
```bash
# This will take 15-30 minutes and fetch recent data
uv run python scripts/update_data.py
```

**Option B: Comprehensive Setup (Recommended for Production)**
```bash
# Step 1: Initial data collection (15-30 minutes)
uv run python scripts/update_data.py

# Step 2: Backfill historical data (3-8 hours, run overnight)
uv run python scripts/backfill_fighter_events.py --mode full
```

**Option C: Minimal Setup (Development Only)**
```bash
# Creates an empty database with schema only
# You'll need to manually add data
python -c "
from mma_website.models.database import db
from mma_website import create_app
app = create_app()
with app.app_context():
    db.create_all()
"
```

### 5. Run the Application

The application consists of two servers that must both be running:

**Terminal 1 - Start FastAPI Backend (Port 8000):**
```bash
cd backend
python run.py
```

The backend API will be available at `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

**Terminal 2 - Start Next.js Frontend (Port 3000):**
```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 6. Verify Setup

Visit `http://localhost:3000` in your browser. You should see:
- **Homepage** with champions, recent events, and upcoming fights
- **Fighters** (`/fighters`) - Searchable database with 36,847+ fighters
- **Events** (`/events`) - UFC, Bellator, PFL event listings
- **Rankings** (`/rankings`) - Current UFC rankings by division
- **Next Event** (`/next-event`) - Upcoming UFC event with betting odds
- **System Checker** (`/tools/system-checker`) - Betting analytics dashboard
- **Fighter Wordle** (`/games/wordle`) - Daily fighter guessing game

## Database Updates

### Daily/Weekly Updates
```bash
# Fast incremental update (2-10 minutes)
uv run python scripts/incremental_update.py --days 30
```

### Monthly Full Sync
```bash
# Comprehensive backfill (3-8 hours)
uv run python scripts/backfill_fighter_events.py --mode full
```

## Directory Structure

After setup, your directory should look like:

```
mmaWebsite/
├── .env                      # Backend environment configuration
├── backend/                  # FastAPI backend (Port 8000)
│   ├── api/                 # API routes
│   ├── models/              # Pydantic models
│   ├── services/            # Business logic
│   └── run.py              # FastAPI entry point
├── frontend/                 # Next.js frontend (Port 3000)
│   ├── .env.local           # Frontend environment configuration
│   ├── app/                 # Next.js pages (App Router)
│   ├── components/          # React components
│   ├── lib/                 # Utilities and API client
│   └── __tests__/           # Jest tests
├── data/
│   └── mma.db               # SQLite database (82MB, you create this)
├── scripts/                 # Data update scripts
└── docs/                    # Documentation
```

## Troubleshooting

### Backend won't start
```bash
# Make sure you're in the backend directory
cd backend
python run.py

# Check if port 8000 is already in use
lsof -ti:8000 | xargs kill -9
```

### Frontend won't start
```bash
# Make sure dependencies are installed
cd frontend
npm install

# Check if port 3000 is already in use
lsof -ti:3000 | xargs kill -9

# Or run on a different port
cd frontend
PORT=3001 npm run dev
```

### Frontend can't connect to backend
```bash
# Verify backend is running on port 8000
curl http://localhost:8000/health

# Check frontend/.env.local has correct API URL
cat frontend/.env.local
# Should show: NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Database errors
```bash
# Reset the database
rm data/mma.db
uv run python scripts/update_data.py
```

### "Module not found" errors (Backend)
```bash
# Make sure you've run uv sync
uv sync

# Or use uv run for commands
uv run python backend/run.py
```

## Next Steps

- Read [PROJECT_STATUS.md](PROJECT_STATUS.md) for project overview
- Check [docs/DATA_UPDATE_GUIDE.md](docs/DATA_UPDATE_GUIDE.md) for data management
- See [CONTRIBUTING.md](.github/CONTRIBUTING.md) if you want to contribute
- Explore the [docs/](docs/) directory for more documentation

## Getting Help

- Check existing [documentation](docs/)
- Open an issue on GitHub
- Review [PROJECT_STATUS.md](PROJECT_STATUS.md) for architecture details

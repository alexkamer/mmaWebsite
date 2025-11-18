# MMA Website - Suggested Commands

## Development Commands

### Starting the Application

**Backend (FastAPI - Port 8000)**
```bash
cd backend && python run.py
# OR
cd backend && uv run run.py
# API docs: http://localhost:8000/docs
```

**Frontend (Next.js - Port 3000)**
```bash
cd frontend && npm run dev
# App: http://localhost:3000
```

**Both Required**: Run both backend and frontend for full functionality

### Frontend Commands
```bash
cd frontend

# Development server
npm run dev

# Production build
npm run build

# Start production server
npm start

# Linting
npm run lint
```

### Backend Commands
```bash
cd backend

# Run server
python run.py
# OR
uv run run.py

# Install dependencies
uv sync
# OR
pip install -r requirements.txt
```

## Testing

### Python Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_filename.py

# Run specific test
pytest tests/test_filename.py::test_function_name

# Skip slow tests
pytest -m "not slow"

# Run only unit tests
pytest -m unit
```

### Frontend Tests
```bash
cd frontend
npm run lint  # ESLint checking
```

## Database Commands

### Data Updates
```bash
# Initial setup (use seed for quick setup)
uv run python scripts/create_seed_db.py  # Fast (2-3 min, 100 fighters)

# Full data update
uv run python scripts/update_data.py  # Slow (15-30 min, 17K+ fighters)

# Daily/weekly incremental updates
uv run python scripts/incremental_update.py --days 30

# Monthly full sync
uv run python scripts/backfill_fighter_events.py --mode full

# Quick update script
./quick_update.sh
```

### Database Operations
```bash
# SQLite CLI
sqlite3 data/mma.db

# View tables
sqlite3 data/mma.db ".tables"

# Query example
sqlite3 data/mma.db "SELECT * FROM athletes LIMIT 10;"
```

## Git Commands (macOS/Darwin)
```bash
# Status
git status

# Stage changes
git add .
git add <file>

# Commit
git commit -m "message"

# Push
git push origin <branch>

# Pull
git pull origin <branch>

# Create branch
git checkout -b <branch-name>

# Switch branch
git checkout <branch-name>

# View branches
git branch -a

# Create backup tag (before cleanup)
git tag flask-backup-$(date +%Y%m%d)
```

## File System Commands (macOS/Darwin)
```bash
# List files
ls -la

# Find files
find . -name "*.py"
find . -type f -name "package.json"

# Search in files
grep -r "search_term" .
grep -r "search_term" --include="*.py" .

# File operations
cp source dest
mv source dest
rm file
rm -rf directory

# Directory operations
mkdir directory
cd directory
pwd
```

## Cleanup Commands

### Remove Obsolete Flask Files (Optional)
```bash
# Create backup first!
git tag flask-backup-$(date +%Y%m%d)

# Then remove obsolete files
rm -rf mma_website/  # Flask blueprints
rm -rf templates/    # Jinja2 templates
rm app.py           # Monolithic Flask app
rm run.py           # Flask entry point (Port 5004)

# Note: backend/run.py is FastAPI and should NOT be deleted
```

## Package Management

### Python (uv - recommended)
```bash
# Sync dependencies
uv sync

# Add package
uv add <package>

# Remove package
uv remove <package>

# Run command
uv run <command>
```

### Python (pip - alternative)
```bash
# Install dependencies
pip install -r requirements.txt

# Add package
pip install <package>
# Then: pip freeze > requirements.txt

# Virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
```

### Node.js (npm)
```bash
cd frontend

# Install dependencies
npm install

# Add package
npm install <package>

# Add dev dependency
npm install --save-dev <package>

# Update packages
npm update
```

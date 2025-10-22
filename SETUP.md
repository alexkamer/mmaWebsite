# Setup Guide

Complete setup instructions for the MMA Website.

## Prerequisites

- Python 3.12+
- Git
- 10GB free disk space (for database)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd mmaWebsite
```

### 2. Install Dependencies

**Option A: Using uv (Recommended)**
```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

**Option B: Using pip**
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
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

# Flask configuration
FLASK_ENV=development
FLASK_DEBUG=1
```

**Note:** The Azure OpenAI configuration is only needed if you want to use the experimental MMA query feature (`/query` route). The rest of the application works without it.

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

### 5. Verify Setup

Run the application:

```bash
uv run run.py
```

Visit `http://127.0.0.1:5000` in your browser. You should see:
- Home page with events (if database is populated)
- Fighter search functionality
- Rankings page
- Interactive games

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
├── .env                      # Your environment configuration
├── .venv/                    # Virtual environment (if using pip)
├── data/
│   └── mma.db               # SQLite database (94MB, you create this)
├── mma_website/             # Main application
├── scripts/                 # Data update scripts
├── templates/               # HTML templates
├── static/                  # CSS, JS, images
├── docs/                    # Documentation
└── run.py                   # Application entry point
```

## Troubleshooting

### "Module not found" errors
```bash
# Make sure you're using the virtual environment
source .venv/bin/activate  # or: uv run <command>
```

### Database errors
```bash
# Reset the database
rm data/mma.db
uv run python scripts/update_data.py
```

### Port already in use
```bash
# Kill the process using port 5000
lsof -ti:5000 | xargs kill -9

# Or run on a different port
FLASK_RUN_PORT=5001 uv run run.py
```

### "No module named 'mma_website'"
```bash
# Make sure you're in the project root directory
cd /path/to/mmaWebsite
uv run run.py
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

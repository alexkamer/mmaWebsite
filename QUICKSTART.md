# Quick Start Guide

## 🎯 Fastest Way to Get Started

```bash
git clone https://github.com/yourusername/mmaWebsite.git
cd mmaWebsite
python setup.py
```

**That's it!** Visit `http://127.0.0.1:5000` when done.

---

## 📋 What the Setup Script Does

The automated `setup.py` script handles:

1. ✅ **Checks Python 3.12+** - Verifies you have the right version
2. ✅ **Installs uv** - Fast package manager (optional, falls back to pip)
3. ✅ **Installs dependencies** - All required packages
4. ✅ **Creates .env file** - Configuration from template
5. ✅ **Sets up database** - Choice of seed (fast) or full (comprehensive)
6. ✅ **Verifies installation** - Ensures everything works

**Time:** 2-3 minutes for seed database, 15-30 for full

---

## 🎮 Database Options

When you run `setup.py`, you'll choose:

### Option 1: Seed Database (Recommended for First Time)
- ⏱️ **Time:** 2-3 minutes
- 📦 **Size:** ~5MB
- 👥 **Fighters:** Top 100 UFC fighters
- 🎫 **Events:** Last 2 UFC events
- 🏆 **Rankings:** Current UFC rankings
- ✅ **Perfect for:** Testing, development, trying the app

### Option 2: Full Database
- ⏱️ **Time:** 15-30 minutes
- 📦 **Size:** ~94MB
- 👥 **Fighters:** 17,000+ fighters
- 🎫 **Events:** All historical events
- 🏆 **Rankings:** Complete data
- ✅ **Perfect for:** Production, full features

💡 **Tip:** Start with seed database, upgrade to full later!

---

## 🚀 Running the Application

After setup:

```bash
# If using uv (recommended)
uv run run.py

# If using pip
python run.py
```

Then open: **http://127.0.0.1:5000**

---

## 🔄 Upgrading from Seed to Full Database

Started with seed database and want more data?

```bash
# Get recent data (2-10 minutes)
uv run python scripts/incremental_update.py --days 90

# Get all historical data (3-8 hours, run overnight)
uv run python scripts/backfill_fighter_events.py --mode full
```

---

## ⚙️ Configuration (Optional)

The `.env` file is created automatically with defaults. Edit it only if you want:

```env
# Optional: Azure OpenAI for /query feature
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_DEPLOYMENT=gpt-4-1

# Flask settings (auto-configured)
FLASK_ENV=development
FLASK_DEBUG=1
```

**Note:** The app works fine without Azure OpenAI (only needed for experimental query feature)

---

## 🛠️ Troubleshooting

### "Python 3.12+ required"
```bash
# Install Python 3.12+
# macOS: brew install python@3.12
# Windows: Download from python.org
# Linux: Use your package manager
```

### "Command not found: uv"
The setup script will offer to install it, or use pip instead.

### "Port 5000 already in use"
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Or use different port
FLASK_RUN_PORT=5001 python run.py
```

### Database errors
```bash
# Reset and recreate
rm data/mma.db
python setup.py
```

---

## 📚 What's Next?

After setup:
- 🌐 Explore the app at `http://127.0.0.1:5000`
- 📖 Read [README.md](README.md) for features
- 🔧 Check [SETUP.md](SETUP.md) for detailed docs
- 🤝 See [CONTRIBUTING.md](.github/CONTRIBUTING.md) to contribute

---

## 🎯 Common Commands

```bash
# Start application
uv run run.py

# Update data (daily/weekly)
uv run python scripts/incremental_update.py --days 30

# Full data sync (monthly)
uv run python scripts/backfill_fighter_events.py --mode full

# Create seed database from scratch
uv run python scripts/create_seed_db.py

# Get full database from scratch
uv run python scripts/update_data.py
```

---

## ✅ You're Ready!

That's all you need to get started. Enjoy the app! 🥊

# MMA Website 🥊

A comprehensive MMA (Mixed Martial Arts) web application built with Flask, featuring 17,000+ fighter profiles, event management, live rankings, and interactive games powered by ESPN API data.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.1+-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ Features

### Core Features
- **🥊 Fighter Database** - 17,000+ fighters with detailed profiles, fight history, and career statistics
- **📅 Event Management** - Complete UFC and regional promotion event tracking with live updates
- **🏆 UFC Rankings** - Real-time rankings across all divisions
- **⚔️ Tale of the Tape** - Side-by-side fighter comparisons with advanced filtering
- **🎮 Fighter Wordle** - Interactive game to guess UFC fighters
- **📊 Analytics Dashboard** - Betting systems analysis and performance metrics
- **🔴 Live Events** - ESPN API integration for upcoming UFC events

### Technical Features
- Modular Flask application with blueprints
- SQLite database (94MB) with 17K+ fighters
- ESPN API integration for real-time data
- RESTful API endpoints
- Responsive Tailwind CSS design
- Advanced text normalization for international fighters

## 🚀 Quick Start

### One-Command Setup ⚡

```bash
# Clone and set up everything automatically
git clone https://github.com/yourusername/mmaWebsite.git
cd mmaWebsite
python setup.py
```

That's it! The setup script will:
- ✅ Install dependencies
- ✅ Configure environment
- ✅ Set up seed database (2-3 minutes)
- ✅ Verify installation

Then visit `http://127.0.0.1:5000` 🎉

### Manual Setup (Alternative)

<details>
<summary>Click to expand manual installation steps</summary>

**Prerequisites:** Python 3.12+

```bash
# 1. Clone repository
git clone https://github.com/yourusername/mmaWebsite.git
cd mmaWebsite

# 2. Install dependencies (choose one)
uv sync          # Recommended (faster)
# OR
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env

# 4. Create database (choose one)
uv run python scripts/create_seed_db.py      # Fast (2-3 min, 100 fighters)
# OR
uv run python scripts/update_data.py         # Full (15-30 min, 17K+ fighters)

# 5. Run application
uv run run.py
```

</details>

**📖 For detailed information, see [SETUP.md](SETUP.md)**

## 📊 Project Stats

- **Fighters**: 17,000+ athlete profiles
- **Events**: Thousands of historical and upcoming events
- **Fights**: Complete fight history with statistics
- **Database**: 94MB SQLite with multi-provider odds
- **Code**: Modular architecture with blueprints

## 🗂️ Project Structure

```
mmaWebsite/
├── mma_website/              # Main Flask application (modular)
│   ├── routes/              # Blueprint-based routing
│   ├── services/            # Business logic layer
│   ├── models/              # Database models & schemas
│   └── utils/               # Helper functions
├── scripts/                 # Data update scripts
│   ├── incremental_update.py      # Daily updates (2-10 min)
│   ├── backfill_fighter_events.py # Full sync (3-8 hours)
│   └── update_data.py             # Initial setup
├── templates/               # Jinja2 HTML templates
├── static/                  # CSS, JavaScript, images
├── docs/                    # Documentation
└── data/                    # SQLite database (not in repo)
```

## 🔄 Data Updates

### Daily/Weekly Updates (Recommended)
```bash
uv run python scripts/incremental_update.py --days 30
```

### Monthly Full Sync
```bash
uv run python scripts/backfill_fighter_events.py --mode full
```

See [docs/DATA_UPDATE_GUIDE.md](docs/DATA_UPDATE_GUIDE.md) for details.

## 🌐 Routes

### Main Pages
- `/` - Home with recent events
- `/fighters` - Fighter search and browse
- `/fighter/<id>` - Fighter profile
- `/events` - Event listings
- `/rankings` - UFC rankings

### Interactive Features
- `/fighter-wordle` - Fighter guessing game
- `/tale-of-tape` - Fighter comparisons
- `/next-event` - Live UFC event data
- `/system-checker` - Betting analytics

### API Endpoints
- `GET /api/fighter/<id>` - Fighter data
- `GET /api/fighters/search?q=<query>` - Search
- `GET /api/fight-stats/<id>` - Fight statistics
- `GET /rankings/api` - Rankings data

## 📚 Documentation

- [SETUP.md](SETUP.md) - Complete setup guide
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Project overview & capabilities
- [CONTRIBUTING.md](.github/CONTRIBUTING.md) - Contribution guidelines
- [docs/DATA_UPDATE_GUIDE.md](docs/DATA_UPDATE_GUIDE.md) - Data management
- [docs/CHANGELOG.md](docs/CHANGELOG.md) - Change history

## 🛠️ Tech Stack

- **Backend**: Flask 3.1+, SQLAlchemy 2.0+
- **Database**: SQLite (94MB)
- **Frontend**: Jinja2, Tailwind CSS
- **Data Source**: ESPN API
- **Validation**: Pydantic 2.11+
- **Package Manager**: uv / pip

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](.github/CONTRIBUTING.md) for guidelines.

### Priority Areas
- [ ] Add automated tests (pytest)
- [ ] Mobile responsiveness improvements
- [ ] User authentication & profiles
- [ ] Advanced analytics features
- [ ] Deployment configuration

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Data provided by ESPN API
- Built with Flask and SQLAlchemy
- Inspired by the MMA community

## 📧 Contact

For questions or suggestions:
- Open an [issue](https://github.com/yourusername/mmaWebsite/issues)
- Check [PROJECT_STATUS.md](PROJECT_STATUS.md) for architecture details

---

**Note**: The database is not included in the repository due to its size (94MB). You'll need to initialize it using the setup scripts. See [SETUP.md](SETUP.md) for instructions.

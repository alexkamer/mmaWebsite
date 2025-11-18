# MMA Website - Tech Stack

## Backend (FastAPI)
- **Framework**: FastAPI 0.121+
- **Runtime**: Python 3.12+
- **Server**: Uvicorn with auto-reload
- **Database**: SQLite with SQLAlchemy 2.0+ (async)
- **Validation**: Pydantic 2.11+
- **Package Manager**: uv (recommended) or pip

### Backend Dependencies
- fastapi, uvicorn[standard]
- sqlalchemy, aiosqlite
- pydantic, pydantic-settings
- httpx, aiohttp, requests
- beautifulsoup4, lxml
- pandas
- python-dotenv
- pytest, pytest-cov

## Frontend (Next.js)
- **Framework**: Next.js 16.0.3 (App Router)
- **Runtime**: React 19.2.0
- **UI Components**: shadcn/ui (New York style)
  - @radix-ui/react-avatar, tabs, slot
  - lucide-react icons
- **Styling**: Tailwind CSS 4 with @tailwindcss/postcss
- **Data Fetching**: @tanstack/react-query 5.90+
- **Animations**: framer-motion
- **Utilities**: class-variance-authority, clsx, tailwind-merge
- **TypeScript**: 5.x with strict typing
- **Package Manager**: npm

## Data Sources
- **ESPN API**: Live event data, fighter info, odds
- **Web Scraping**: BeautifulSoup4, Selenium, Crawl4AI
- **Data Processing**: Pandas for analysis

## Development Tools
- **Testing**: pytest with coverage (pytest-cov)
- **Linting**: ESLint (frontend)
- **Version Control**: Git
- **Python Version Management**: pyenv (.python-version file)

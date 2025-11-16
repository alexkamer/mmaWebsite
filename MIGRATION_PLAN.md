# MMA Website Migration Plan

## Stack Decision ✅
- **Frontend**: Next.js 15 (App Router) + TypeScript
- **Backend**: FastAPI (Python) - async REST API
- **Styling**: Tailwind CSS + shadcn/ui components
- **Theme**: Dark/Light mode with toggle
- **Database**: SQLite (existing) → can migrate to PostgreSQL later

## Project Structure

```
mma-website/
├── frontend/                    # Next.js application
│   ├── app/
│   │   ├── layout.tsx          # Root layout with theme provider
│   │   ├── page.tsx            # Home page
│   │   ├── fighters/
│   │   │   ├── page.tsx        # Fighters list
│   │   │   └── [id]/
│   │   │       └── page.tsx    # Fighter profile
│   │   ├── events/
│   │   │   ├── page.tsx        # Events list
│   │   │   └── [id]/
│   │   │       └── page.tsx    # Event details
│   │   ├── rankings/
│   │   │   └── page.tsx        # UFC Rankings
│   │   ├── games/
│   │   │   ├── wordle/
│   │   │   ├── tale-of-tape/
│   │   │   └── next-event/
│   │   └── system-checker/
│   ├── components/
│   │   ├── ui/                 # shadcn/ui components
│   │   ├── fighters/           # Fighter-specific components
│   │   ├── events/             # Event components
│   │   ├── layout/             # Nav, Footer, etc.
│   │   └── theme/              # Theme provider, toggle
│   ├── lib/
│   │   ├── api.ts             # API client for FastAPI
│   │   ├── types.ts           # TypeScript types
│   │   └── utils.ts           # Utilities
│   ├── public/                # Static assets
│   └── styles/
│       └── globals.css        # Tailwind + custom styles
│
├── backend/                    # FastAPI application
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI app with CORS
│   │   ├── fighters.py       # Fighter endpoints
│   │   ├── events.py         # Event endpoints
│   │   ├── rankings.py       # Rankings endpoints
│   │   ├── games.py          # Games endpoints
│   │   └── analytics.py      # System checker endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   ├── fighter.py        # Pydantic models
│   │   ├── event.py
│   │   └── ranking.py
│   ├── services/              # Reuse existing services
│   │   ├── fighter_service.py
│   │   ├── event_service.py
│   │   └── ranking_service.py
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py     # SQLite connection
│   └── requirements.txt       # FastAPI, uvicorn, etc.
│
├── data/
│   └── mma.db                 # Existing database
│
└── shared/                     # Shared configs
    ├── .env.example
    └── docker-compose.yml      # Optional: containerize both apps
```

## Migration Steps

### Phase 1: Backend Setup (FastAPI)
1. Create FastAPI app structure
2. Set up CORS for Next.js communication
3. Create REST endpoints mirroring Flask routes:
   - GET /api/fighters - List fighters
   - GET /api/fighters/{id} - Fighter details
   - GET /api/events - List events
   - GET /api/events/{id} - Event details
   - GET /api/rankings - UFC rankings
   - GET /api/games/wordle - Wordle data
   - GET /api/analytics/system-checker - System checker
4. Reuse existing services/database code
5. Test with curl/Postman

### Phase 2: Frontend Setup (Next.js)
1. Initialize Next.js 15 with TypeScript
2. Install Tailwind CSS
3. Install and configure shadcn/ui
4. Set up dark mode with next-themes
5. Create layout with navigation
6. Create API client for FastAPI

### Phase 3: Page Migration (Priority Order)
1. **Home page** - Dashboard with recent events
2. **Fighter list** - Searchable fighter directory
3. **Fighter profile** - Detailed fighter page with timeline
4. **Events list** - Event listings by year
5. **Event details** - Fight card with odds
6. **Rankings** - UFC rankings by division
7. **Games** - Fighter Wordle, Tale of Tape
8. **System Checker** - Analytics dashboard

### Phase 4: Professional UI/UX
1. Implement consistent color scheme
2. Add smooth animations (Framer Motion)
3. Better typography (Inter, Geist Sans)
4. Responsive design (mobile-first)
5. Loading states and skeletons
6. Error handling

### Phase 5: Testing & Optimization
1. Test all features
2. Add loading states
3. Optimize images
4. SEO optimization
5. Performance tuning

## Development Commands

### Backend (FastAPI)
```bash
cd backend
uvicorn api.main:app --reload --port 8000
```

### Frontend (Next.js)
```bash
cd frontend
npm run dev  # runs on port 3000
```

## Deployment Options
- **Frontend**: Vercel (free, optimized for Next.js)
- **Backend**: Railway, Render, or Fly.io (free tiers available)
- **Database**: Can migrate to PostgreSQL on deployment

## Rollback Plan
If migration fails or needs to be paused:
```bash
git checkout 4d90b57  # Return to Flask version
```

## Timeline Estimate
- Backend setup: 2-3 hours
- Frontend setup: 1-2 hours
- Page migration: 8-12 hours (1-2 hours per major page)
- UI polish: 3-4 hours
- Testing: 2-3 hours
**Total: ~20-25 hours** (can be done incrementally)

## Next Steps
1. Create backend/ directory with FastAPI structure
2. Create frontend/ directory with Next.js
3. Start with backend API endpoints
4. Build frontend pages one by one

# MMA Website - Code Style & Conventions

## Python (Backend)

### General Style
- **Python Version**: 3.12+
- **Style Guide**: PEP 8 compliant
- **Package Manager**: uv (preferred) or pip
- **Type Hints**: Used throughout (Pydantic models)
- **Async/Await**: FastAPI routes use async functions
- **Docstrings**: Present but not universally enforced

### Backend Structure
- **API Routes**: `backend/api/` - One file per resource (events.py, fighters.py, etc.)
- **Services**: `backend/services/` - Business logic layer
- **Models**: `backend/models/` - Pydantic models and schemas
- **Database**: `backend/database/` - SQLAlchemy models and connection

### Naming Conventions
- **Files**: snake_case (e.g., `fighters.py`, `main.py`)
- **Functions**: snake_case (e.g., `get_fighter_by_id`)
- **Classes**: PascalCase (e.g., `FighterModel`, `EventResponse`)
- **Constants**: UPPER_SNAKE_CASE
- **Variables**: snake_case

## TypeScript/React (Frontend)

### General Style
- **TypeScript**: Strict mode enabled
- **React Version**: 19.2.0 with hooks
- **Next.js**: App Router pattern (not Pages Router)

### Frontend Structure
- **Pages**: `frontend/app/` - File-based routing
- **Components**: `frontend/components/` - Reusable React components
- **UI Components**: shadcn/ui (New York style) - `frontend/components/ui/`
- **Lib**: `frontend/lib/` - Utilities and API client
- **Styles**: Tailwind CSS classes, `globals.css` for global styles

### Naming Conventions
- **Files**: kebab-case for pages (e.g., `page.tsx`), PascalCase for components (e.g., `FighterCard.tsx`)
- **Components**: PascalCase (e.g., `FighterCard`, `MainEventCard`)
- **Functions**: camelCase (e.g., `getFighterData`)
- **Hooks**: camelCase starting with `use` (e.g., `useQuery`)
- **Constants**: UPPER_SNAKE_CASE
- **Types/Interfaces**: PascalCase (e.g., `FighterData`, `EventResponse`)

### React Patterns
- **Server Components**: Default in Next.js 16 App Router
- **Client Components**: Mark with `"use client"` directive when needed
- **Data Fetching**: TanStack React Query for client-side, fetch for server components
- **Styling**: Tailwind utility classes, shadcn/ui components

## Database Conventions
- **Tables**: Lowercase with underscores (e.g., `athletes`, `ufc_rankings`)
- **Foreign Keys**: Convention follows SQLAlchemy patterns
- **Queries**: SQLAlchemy ORM (backend), async where possible

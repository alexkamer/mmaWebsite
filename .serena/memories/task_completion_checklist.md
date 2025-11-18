# MMA Website - Task Completion Checklist

## When a Task is Complete

### General Workflow
1. **Code Quality**: Ensure code follows style conventions
2. **Testing**: Run appropriate tests (see below)
3. **Linting**: Check for linting errors
4. **Documentation**: Update relevant docs if needed
5. **Git**: Commit changes with clear message
6. **Verification**: Test in browser if UI changes

### Backend Changes (FastAPI)

**Run These Commands:**
```bash
cd backend

# 1. Test the backend
pytest tests/  # If tests exist

# 2. Verify backend runs
python run.py  # Should start on port 8000 without errors

# 3. Check API docs (optional)
# Open http://localhost:8000/docs in browser
```

**Checklist:**
- [ ] Backend starts without errors
- [ ] API endpoints return expected data
- [ ] No Python syntax/import errors
- [ ] Type hints are correct (Pydantic models validate)
- [ ] Database queries work correctly

### Frontend Changes (Next.js)

**Run These Commands:**
```bash
cd frontend

# 1. Lint check
npm run lint

# 2. Build check (optional but recommended)
npm run build

# 3. Run dev server
npm run dev  # Should start on port 3000
```

**Checklist:**
- [ ] No ESLint errors
- [ ] Build completes without errors
- [ ] Page renders correctly in browser
- [ ] No console errors in browser DevTools
- [ ] Responsive design works (test different screen sizes)
- [ ] TypeScript types are correct

### Full Stack Changes

**Run Both:**
```bash
# Terminal 1 - Backend
cd backend && python run.py

# Terminal 2 - Frontend
cd frontend && npm run dev
```

**Test in Browser:**
1. Navigate to http://localhost:3000
2. Test the modified functionality
3. Check browser console for errors
4. Verify API calls work (Network tab in DevTools)

### Database Changes

**Commands:**
```bash
# Test database operations
sqlite3 data/mma.db "SELECT * FROM <table> LIMIT 5;"

# If schema changed, may need to regenerate DB
uv run python scripts/create_seed_db.py
```

**Checklist:**
- [ ] Database schema is correct
- [ ] Queries return expected results
- [ ] No missing columns/tables
- [ ] Indexes are appropriate

### Before Committing

**Commands:**
```bash
# Check what changed
git status
git diff

# Stage changes
git add .

# Commit with clear message
git commit -m "feat: Add new feature X"
# OR
git commit -m "fix: Fix bug in Y"
# OR
git commit -m "docs: Update documentation for Z"

# Push to remote
git push origin <branch>
```

**Commit Message Conventions:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style/formatting (no logic change)
- `refactor:` - Code refactoring
- `test:` - Adding/updating tests
- `chore:` - Maintenance tasks

### Production Deployment (Future)

**Not Yet Configured** - but when ready:
1. Run full test suite: `pytest`
2. Build frontend: `cd frontend && npm run build`
3. Set environment variables for production
4. Configure production database
5. Set up reverse proxy (nginx)
6. Enable HTTPS
7. Monitor logs

## Quick Testing Scripts

### Test All
```bash
# Backend
cd backend && pytest && python run.py &

# Frontend
cd frontend && npm run lint && npm run build && npm run dev
```

### Test Specific Feature
```bash
# Example: Testing fighters endpoint
cd backend && python run.py &
curl http://localhost:8000/api/fighters/1  # Should return fighter data
```

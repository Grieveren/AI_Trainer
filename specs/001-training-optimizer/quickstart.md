# Developer Quickstart: Intelligent Training Optimizer

**Feature**: 001-training-optimizer
**Last Updated**: 2025-10-24

## Overview

This guide gets you up and running with the AI Trainer development environment in 15 minutes.

**What You'll Set Up**:
- Python 3.11+ backend with FastAPI
- PostgreSQL 15+ database
- Redis 7+ for caching and job queue
- Celery workers for background tasks
- React 18+ frontend with TypeScript
- Development tools (linting, testing, pre-commit hooks)

## Prerequisites

**Required**:
- Python 3.11 or higher
- Node.js 18+ and npm
- Docker and Docker Compose (for PostgreSQL and Redis)
- Git

**Recommended**:
- pyenv (Python version management)
- nvm (Node version management)
- VS Code with Python and TypeScript extensions

**Accounts** (for full functionality):
- Garmin Developer Account (https://developerportal.garmin.com)
- Anthropic API Key (https://console.anthropic.com)

---

## Quick Setup (15 minutes)

### Step 1: Clone and Initialize (2 minutes)

```bash
git clone <repository-url> ai-trainer
cd ai-trainer

# Checkout feature branch
git checkout 001-training-optimizer
```

### Step 2: Start Infrastructure (3 minutes)

Start PostgreSQL and Redis using Docker Compose:

```bash
# Start services in background
docker-compose up -d postgres redis

# Verify services are running
docker-compose ps

# Expected output:
# NAME                 SERVICE    STATUS
# ai-trainer-postgres  postgres   Up 30 seconds
# ai-trainer-redis     redis      Up 30 seconds
```

### Step 3: Backend Setup (5 minutes)

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Create environment file
cp .env.example .env

# Edit .env with your configuration:
# - ANTHROPIC_API_KEY=your_key_here
# - GARMIN_CLIENT_ID=your_client_id
# - GARMIN_CLIENT_SECRET=your_client_secret
# - DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/aitrainer
# - REDIS_URL=redis://localhost:6379/0

# Run database migrations
alembic upgrade head

# Verify backend starts
uvicorn src.main:app --reload --port 8000

# Visit http://localhost:8000/docs to see API documentation
```

### Step 4: Frontend Setup (3 minutes)

Open a new terminal window:

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local

# Edit .env.local:
# VITE_API_URL=http://localhost:8000/api/v1

# Start development server
npm run dev

# Visit http://localhost:5173 to see the app
```

### Step 5: Start Celery Workers (2 minutes)

Open a new terminal window:

```bash
cd backend
source venv/bin/activate

# Start Celery worker
celery -A src.celery_app worker --loglevel=info

# In another terminal, start Celery Beat (scheduler)
celery -A src.celery_app beat --loglevel=info
```

---

## Development Workflow

### Running Tests

**Backend Tests**:
```bash
cd backend
source venv/bin/activate

# Run all tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_recovery_calculator.py -v

# Run tests matching pattern
pytest -k "test_recovery" -v

# Run with watch mode (auto-rerun on changes)
pytest-watch

# View coverage report
open htmlcov/index.html
```

**Frontend Tests**:
```bash
cd frontend

# Run all tests
npm test

# Run with watch mode
npm test -- --watch

# Run with coverage
npm test -- --coverage
```

### Code Quality

**Backend Linting and Formatting**:
```bash
cd backend
source venv/bin/activate

# Format code with Black
black src/ tests/

# Lint with Ruff
ruff check src/ tests/

# Type check with mypy
mypy src/

# Run all checks
./scripts/check-quality.sh
```

**Frontend Linting and Formatting**:
```bash
cd frontend

# Format code with Prettier
npm run format

# Lint with ESLint
npm run lint

# Type check
npm run type-check

# Run all checks
npm run check
```

### Pre-commit Hooks

Install pre-commit hooks to automatically check code quality:

```bash
# Install pre-commit (if not already installed)
pip install pre-commit

# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

---

## Project Structure

```
ai-trainer/
├── backend/
│   ├── src/
│   │   ├── models/              # SQLAlchemy models (User, HealthMetrics, etc.)
│   │   ├── services/
│   │   │   ├── garmin/         # Garmin API integration
│   │   │   ├── ai/             # Claude AI integration
│   │   │   ├── recovery/       # Recovery score calculation
│   │   │   ├── recommendations/ # Workout recommendation engine
│   │   │   └── training_plan/  # Training plan generation
│   │   ├── api/
│   │   │   ├── routes/         # FastAPI route handlers
│   │   │   ├── middleware/     # Auth, error handling
│   │   │   └── schemas/        # Pydantic request/response models
│   │   ├── jobs/               # Celery background tasks
│   │   ├── database/           # Database connection and migrations
│   │   └── utils/              # Shared utilities
│   ├── tests/
│   │   ├── contract/           # API contract tests
│   │   ├── integration/        # Integration tests
│   │   └── unit/               # Unit tests
│   ├── alembic/                # Database migrations
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── dashboard/
│   │   │   ├── recovery/
│   │   │   ├── insights/
│   │   │   └── plans/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Insights.tsx
│   │   │   └── Plans.tsx
│   │   ├── services/           # API client
│   │   ├── hooks/              # Custom React hooks
│   │   └── utils/
│   ├── tests/
│   └── package.json
│
├── specs/
│   └── 001-training-optimizer/
│       ├── spec.md             # Feature specification
│       ├── plan.md             # Implementation plan
│       ├── research.md         # Technology research
│       ├── data-model.md       # Database schema
│       ├── contracts/          # API contracts
│       └── tasks.md            # Implementation tasks (generated)
│
├── docker-compose.yml          # Local development services
└── .specify/                   # SpecKit configuration
```

---

## Common Development Tasks

### Create a Database Migration

```bash
cd backend
source venv/bin/activate

# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add workout_notes column"

# Review generated migration in alembic/versions/

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Add a New API Endpoint

1. **Define Pydantic schemas** in `backend/src/api/schemas/`
2. **Implement route handler** in `backend/src/api/routes/`
3. **Write contract test** in `backend/tests/contract/`
4. **Write integration test** in `backend/tests/integration/`
5. **Document in API contract** in `specs/001-training-optimizer/contracts/`

Example:
```python
# backend/src/api/routes/recovery.py
from fastapi import APIRouter, Depends
from src.api.schemas.recovery import RecoveryScoreResponse
from src.services.recovery import RecoveryService

router = APIRouter()

@router.get("/{date}", response_model=RecoveryScoreResponse)
async def get_recovery_score(
    date: str,
    current_user: User = Depends(get_current_user),
    recovery_service: RecoveryService = Depends()
):
    """Get recovery score and recommendation for a specific date."""
    return await recovery_service.get_recovery_score(current_user.id, date)
```

### Add a Background Job

1. **Define task** in `backend/src/jobs/`
2. **Register in Celery app** in `backend/src/celery_config.py`
3. **Add to beat schedule** if recurring
4. **Write unit test** in `backend/tests/unit/test_jobs.py`

Example:
```python
# backend/src/jobs/garmin_sync.py
from src.celery_app import celery_app
from src.services.garmin import GarminService

@celery_app.task(bind=True, max_retries=5)
def sync_user_garmin_data(self, user_id: str):
    """Sync Garmin data for a single user."""
    try:
        service = GarminService()
        service.sync_health_metrics(user_id)
        service.sync_workouts(user_id)
    except GarminAPIError as e:
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
```

### Monitor Background Jobs

Access Flower dashboard (Celery monitoring):
```bash
# In a new terminal
cd backend
source venv/bin/activate

celery -A src.celery_app flower

# Visit http://localhost:5555
```

---

## Troubleshooting

### PostgreSQL Connection Error

**Error**: `could not connect to server: Connection refused`

**Solution**:
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Restart PostgreSQL
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

### Redis Connection Error

**Error**: `redis.exceptions.ConnectionError: Error connecting to Redis`

**Solution**:
```bash
# Check if Redis is running
docker-compose ps redis

# Restart Redis
docker-compose restart redis

# Test connection
redis-cli ping  # Should return "PONG"
```

### Celery Worker Not Starting

**Error**: `kombu.exceptions.OperationalError: [Errno 111] Connection refused`

**Solution**:
```bash
# Ensure Redis is running
docker-compose ps redis

# Verify REDIS_URL in .env
echo $REDIS_URL  # Should be redis://localhost:6379/0

# Restart worker
celery -A src.celery_app worker --loglevel=info
```

### Migration Conflicts

**Error**: `alembic.util.exc.CommandError: Target database is not up to date.`

**Solution**:
```bash
# Check current migration status
alembic current

# View migration history
alembic history

# Downgrade to specific revision
alembic downgrade <revision_id>

# Re-apply migrations
alembic upgrade head
```

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'src'`

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Add backend directory to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/ai-trainer/backend"
```

---

## Useful Commands Cheatsheet

### Backend
```bash
# Start API server
uvicorn src.main:app --reload --port 8000

# Run tests
pytest

# Run specific test
pytest tests/unit/test_recovery.py::test_high_hrv_scores_100 -v

# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type check
mypy src/

# Database migrations
alembic upgrade head       # Apply all migrations
alembic downgrade -1       # Rollback one migration
alembic revision --autogenerate -m "description"  # Create migration

# Celery
celery -A src.celery_app worker --loglevel=info  # Start worker
celery -A src.celery_app beat --loglevel=info    # Start scheduler
celery -A src.celery_app flower                   # Start monitoring UI
```

### Frontend
```bash
# Start dev server
npm run dev

# Run tests
npm test

# Build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint

# Format
npm run format

# Type check
npm run type-check
```

### Docker
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f postgres
docker-compose logs -f redis

# Restart service
docker-compose restart postgres

# Remove volumes (⚠️ deletes all data)
docker-compose down -v
```

---

## Next Steps

1. **Read the Specification**: Review `specs/001-training-optimizer/spec.md` to understand requirements
2. **Review Data Model**: Study `specs/001-training-optimizer/data-model.md` to understand database schema
3. **Explore API Contracts**: Check `specs/001-training-optimizer/contracts/` for API endpoint specifications
4. **Run the Test Suite**: Ensure all tests pass with `pytest` and `npm test`
5. **Review TDD Workflow**: Read the constitution's TDD requirements in `.specify/memory/constitution.md`
6. **Pick Your First Task**: Check `specs/001-training-optimizer/tasks.md` (generated by `/speckit.tasks`)

---

## Getting Help

- **Documentation**: See `specs/001-training-optimizer/` for detailed specifications
- **API Docs**: Visit http://localhost:8000/docs for interactive API documentation
- **Research Findings**: Review `specs/001-training-optimizer/research.md` for technology decisions
- **Project Constitution**: Read `.specify/memory/constitution.md` for coding standards

---

## Development Guidelines

### TDD Workflow (Required by Constitution)

1. **Red**: Write failing test first
2. **Green**: Implement minimum code to pass
3. **Refactor**: Improve code quality while keeping tests green

Example:
```bash
# 1. Red: Write test
# tests/unit/test_recovery_calculator.py
def test_high_hrv_scores_100():
    calculator = RecoveryCalculator()
    result = calculator.calculate_hrv_component(65, 59)  # 10% above avg
    assert result == 100

# Run test (should fail)
pytest tests/unit/test_recovery_calculator.py::test_high_hrv_scores_100

# 2. Green: Implement
# src/services/recovery/calculator.py
def calculate_hrv_component(self, current_hrv, avg_hrv):
    deviation = (current_hrv - avg_hrv) / avg_hrv
    if deviation >= 0.1:
        return 100
    # ... rest of implementation

# Run test (should pass)
pytest tests/unit/test_recovery_calculator.py::test_high_hrv_scores_100

# 3. Refactor: Improve while tests stay green
```

### Code Quality Standards (Required by Constitution)

- **Coverage Target**: 80% minimum for critical paths
- **Linting**: Zero warnings before commit
- **Type Hints**: All functions must have type annotations
- **Documentation**: Public APIs must have docstrings
- **Pre-commit Hooks**: Must pass all checks

---

## Environment Variables Reference

### Backend (.env)
```bash
# Application
ENV=development
DEBUG=true
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/aitrainer

# Redis
REDIS_URL=redis://localhost:6379/0

# External APIs
ANTHROPIC_API_KEY=your_anthropic_key_here
GARMIN_CLIENT_ID=your_garmin_client_id
GARMIN_CLIENT_SECRET=your_garmin_client_secret
GARMIN_CALLBACK_URL=http://localhost:8000/api/v1/garmin/callback

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Logging
LOG_LEVEL=INFO
```

### Frontend (.env.local)
```bash
VITE_API_URL=http://localhost:8000/api/v1
VITE_ENV=development
```

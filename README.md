# AI Trainer - Intelligent Training Optimization System

An intelligent fitness training optimization system that automatically fetches Garmin health and training data, analyzes patterns using Claude AI, and generates personalized workout recommendations based on recovery status.

## Features

- **Daily Recovery Scoring**: AI-powered analysis of HRV, resting heart rate, sleep, and stress
- **Personalized Recommendations**: Daily workout suggestions based on your body's readiness
- **AI-Powered Insights**: Pattern recognition and training optimization advice
- **Adaptive Training Plans**: Multi-week plans that adjust based on actual recovery
- **Garmin Integration**: Automatic data synchronization from your Garmin devices

## Project Status

**Current Phase**: Initial Setup & Infrastructure
**Branch**: `001-training-optimizer`
**MVP Target**: User Story 1 (Daily Recovery & Recommendations)

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Garmin Developer Account (for API access)
- Anthropic API Key (for Claude AI)

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ai-trainer
   git checkout 001-training-optimizer
   ```

2. **Start infrastructure services**:
   ```bash
   docker-compose up -d
   ```

3. **Backend setup**:
   ```bash
   cd backend
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt

   # Create .env file
   cp .env.example .env
   # Edit .env with your API keys

   # Run migrations
   alembic upgrade head

   # Start API server
   uvicorn src.main:app --reload --port 8000
   ```

4. **Frontend setup** (in a new terminal):
   ```bash
   cd frontend
   npm install
   cp .env.example .env.local
   npm run dev
   ```

5. **Access the application**:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Frontend: http://localhost:5173

## Project Structure

```
ai-trainer/
├── backend/              # Python FastAPI backend
│   ├── src/
│   │   ├── models/      # SQLAlchemy models
│   │   ├── services/    # Business logic
│   │   ├── api/         # API routes and schemas
│   │   ├── database/    # Database configuration
│   │   ├── jobs/        # Celery background jobs
│   │   └── utils/       # Utilities
│   ├── tests/           # Test suite
│   └── alembic/         # Database migrations
│
├── frontend/            # React + TypeScript frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── services/    # API clients
│   │   └── hooks/       # Custom hooks
│   └── tests/           # Frontend tests
│
├── specs/               # Feature specifications
│   └── 001-training-optimizer/
│       ├── spec.md      # Feature specification
│       ├── plan.md      # Implementation plan
│       ├── tasks.md     # Task breakdown
│       ├── data-model.md
│       ├── contracts/   # API contracts
│       └── research.md  # Technical decisions
│
└── docker-compose.yml   # PostgreSQL + Redis services
```

## Development

### Running Tests

**Backend**:
```bash
cd backend
pytest                    # Run all tests
pytest --cov              # With coverage
pytest tests/unit         # Unit tests only
pytest -k "recovery"      # Tests matching pattern
```

**Frontend**:
```bash
cd frontend
npm test                  # Run tests
npm test -- --coverage    # With coverage
```

### Code Quality

**Backend**:
```bash
black src/ tests/         # Format code
ruff check src/ tests/    # Lint
mypy src/                 # Type check
```

**Frontend**:
```bash
npm run lint              # ESLint
npm run format            # Prettier
npm run type-check        # TypeScript check
```

### Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
alembic downgrade -1
```

## Documentation

- **Feature Spec**: `specs/001-training-optimizer/spec.md`
- **Implementation Plan**: `specs/001-training-optimizer/plan.md`
- **Task Breakdown**: `specs/001-training-optimizer/tasks.md`
- **API Contracts**: `specs/001-training-optimizer/contracts/`
- **Quickstart Guide**: `specs/001-training-optimizer/quickstart.md`

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 15+ (asyncpg)
- **ORM**: SQLAlchemy 2.0+
- **Caching**: Redis 7+
- **Background Jobs**: Celery 5+
- **Testing**: pytest

### Frontend
- **Framework**: React 18+
- **Language**: TypeScript 5+
- **Build Tool**: Vite 5+
- **Styling**: Tailwind CSS 3+
- **State**: React Query

### External APIs
- **Garmin**: python-garminconnect (OAuth2 PKCE)
- **AI**: Anthropic Claude Haiku 4.5

## Contributing

This project follows Test-Driven Development (TDD):
1. Write tests first (Red phase)
2. Implement to make tests pass (Green phase)
3. Refactor for quality (Refactor phase)

All code must pass linting, type checking, and maintain 80%+ test coverage.

## License

MIT License

## Contact

For questions or issues, please open an issue on the GitHub repository.

# Implementation Plan: Intelligent Training Optimizer

**Branch**: `001-training-optimizer` | **Date**: 2025-10-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-training-optimizer/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build an intelligent fitness training optimization system that automatically fetches Garmin health and training data, analyzes patterns using Claude AI, generates daily workout recommendations based on recovery status, creates adaptive training plans aligned with goals, and prevents overtraining through smart load management. The system will provide actionable insights through AI-powered analysis to help athletes train effectively without risking injury.

## Technical Context

**Language/Version**: Python 3.11+ with FastAPI 0.104+
**Primary Dependencies**:
- Backend: FastAPI, SQLAlchemy 2.0+, Pydantic V2, Celery 5+, Redis 7+
- AI: Anthropic Python SDK (Claude Haiku 4.5 with prompt caching + batch processing)
- Garmin: python-garminconnect library with OAuth 2.0 PKCE
- Testing: pytest, pytest-asyncio, pytest-httpx, pytest-cov
- Frontend: TypeScript 5+, React 18+, Vite 5+, Tailwind CSS 3+, React Query

**Storage**: PostgreSQL 15+ (production), SQLite (development), Redis 7+ (caching + message broker)
**Testing**: pytest with three-layer approach (contract tests for APIs, integration tests for user journeys, unit tests for logic)
**Target Platform**: Web application (Linux/macOS server, browser-based responsive UI)
**Project Type**: Web application (backend API + frontend web UI)

**Performance Goals**:
- API responses within 200ms (p95) per constitution - achieved via FastAPI + Redis caching + asyncpg
- Recovery score calculation within 5 seconds per spec SC-006 - Python + pandas + database indexes
- AI insights generation within 30 seconds per spec SC-007 - Claude Haiku 4.5 (2x faster than Sonnet)
- Training plan generation within 10 seconds per spec SC-008 - Python algorithms + cached data
- Garmin data sync within 2 minutes per spec SC-005 - Celery background jobs + async httpx + 24h caching

**Constraints**:
- Garmin API rate limits: Evaluation keys rate-limited (100-500 req/hr), production keys require verification - Mitigation: 24h caching, webhook-based updates (future)
- Claude AI API costs: Optimized to $0.65/month for 1000 users (85% savings via prompt caching + batch processing)
- Claude AI response times: <5s typical with prompt caching (within 30s requirement)
- Offline capability for cached data viewing with "last updated" timestamps
- Privacy requirement: no third-party data sharing per FR-036, AES-256 encryption for tokens

**Scale/Scope**:
- Initial: Single-user pilot deployment
- Target: 100-1000 users with daily active usage
- Data volume: ~365 days of metrics per user, ~5-10 workouts per week per user = ~3.6M rows/year
- 4 priority levels of user stories with 15 acceptance scenarios total
- Estimated monthly costs at 1000 users: $85-195 (scales to $400-800 at 10K users)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Development Gates (from Constitution)

- [x] Feature specification reviewed and approved (spec.md exists and is complete)
- [x] Technical approach documented and reviewed (documented in Technical Context above)
- [x] Dependencies and risks identified (Garmin API, Claude AI, listed above)
- [x] Test strategy defined (three-layer testing: contract, integration, unit tests with pytest)
- [x] Constitution compliance verified (checked with justified complexity violations)

### Constitution Principle Compliance

**I. Code Quality First** ✅
- Will use linting (to be specified in research: ESLint/Pylint)
- Will follow style guides (to be specified in research)
- Self-documenting code standards will be enforced
- No violations anticipated

**II. Test-Driven Development (TDD)** ✅
- TDD will be followed for all features per constitution
- Contract tests required for Garmin API and Claude AI integrations (FR-002, FR-003, FR-016)
- Integration tests required for critical user journeys (4 user stories with 15 acceptance scenarios)
- Unit test coverage >80% for critical paths (recovery scoring, recommendation generation)
- No violations anticipated

**III. User Experience Consistency** ✅
- FR-032: Plain language throughout, no jargon
- FR-033: Web interface with mobile-friendly design
- FR-034: Contextual help for all metrics
- Error messages must be clear and actionable (FR-009, FR-013)
- Loading states required for all async operations (Garmin sync, AI insights)
- Accessibility standards WCAG 2.1 AA must be met
- No violations anticipated

**IV. Performance Requirements** ⚠️
- API endpoints MUST respond within 200ms (p95) per constitution
- **POTENTIAL VIOLATION**: Recovery score calculation (5s per SC-006) and AI insights (30s per SC-007) exceed 200ms
- **JUSTIFICATION REQUIRED**: See Complexity Tracking section

### Initial Assessment

**Status**: ⚠️ CONDITIONAL PASS - Requires justification for performance violations

All constitution principles align with feature requirements EXCEPT performance timing. The feature inherently requires longer processing times for AI-powered analysis and complex calculations. This must be justified in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/              # Data models (User, HealthMetrics, Workout, RecoveryScore, etc.)
│   ├── services/            # Business logic services
│   │   ├── garmin/         # Garmin API integration
│   │   ├── ai/             # Claude AI integration for insights
│   │   ├── recovery/       # Recovery score calculation
│   │   ├── recommendations/ # Workout recommendation engine
│   │   └── training_plan/  # Training plan generation and adaptation
│   ├── api/                # REST API endpoints
│   │   ├── routes/         # Route handlers
│   │   ├── middleware/     # Auth, error handling, etc.
│   │   └── schemas/        # Request/response validation schemas
│   ├── database/           # Database migrations and setup
│   ├── jobs/               # Background jobs (Garmin sync, AI insights generation)
│   └── utils/              # Shared utilities
├── tests/
│   ├── contract/           # Contract tests for external APIs (Garmin, Claude)
│   ├── integration/        # Integration tests for user journeys
│   └── unit/               # Unit tests for models, services
└── config/                 # Configuration files

frontend/
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── dashboard/     # Dashboard widgets
│   │   ├── recovery/      # Recovery score display
│   │   ├── recommendations/ # Workout recommendation cards
│   │   ├── insights/      # AI insights display
│   │   └── plans/         # Training plan views
│   ├── pages/             # Page components
│   │   ├── Dashboard.tsx  # Main dashboard (User Story 1)
│   │   ├── Insights.tsx   # AI insights (User Story 2)
│   │   ├── Plans.tsx      # Training plans (User Story 3)
│   │   └── Goals.tsx      # Goal tracking (User Story 4)
│   ├── services/          # API client services
│   ├── hooks/             # Custom React hooks
│   ├── utils/             # Shared utilities
│   └── styles/            # Global styles and theme
└── tests/
    ├── integration/       # E2E tests for user flows
    └── unit/              # Component unit tests
```

**Structure Decision**: Web application structure (Option 2) selected because:
- FR-033 specifies "web interface and mobile-friendly design"
- System requires both backend API (for data processing, external integrations) and frontend UI (for user interaction)
- Clear separation enables independent scaling and deployment
- Backend handles compute-intensive operations (recovery scoring, AI insights) asynchronously
- Frontend provides responsive, mobile-friendly interface for cross-device access

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| API response times exceed 200ms for recovery scoring (5s) and AI insights (30s) | Recovery scoring requires fetching and analyzing multiple time-series metrics (HRV, resting HR, sleep, stress, training load). AI insights require Claude API calls for pattern analysis of historical data. Both are computationally intensive and involve external API dependencies. | Simple caching or pre-computation insufficient because: (1) Recovery score needs latest overnight data each morning (FR-002), (2) AI insights must analyze evolving patterns across weeks/months (FR-016, FR-017), (3) External API calls (Garmin, Claude) have inherent latency beyond our control. Real-time data freshness is core to feature value (SC-001, SC-002). |
| Long-running operations (Garmin sync up to 2 minutes, SC-005) | Garmin API requires multiple paginated requests to fetch complete workout history and daily health metrics across multiple endpoints. Must respect API rate limits to avoid account throttling. | Simplified sync insufficient because: (1) Initial sync requires fetching historical data for baseline establishment (Assumption #6: 7-14 days minimum), (2) Complete workout details needed for accurate training load calculation (FR-003), (3) Incomplete syncs would produce inaccurate recovery scores and recommendations, violating core feature promise (SC-010: 80% alignment with perceived readiness). |

**Mitigation Strategy**:
- Use async/background jobs for Garmin sync (FR-002: "automatically fetch", implies scheduled background process)
- Implement loading states with progress indicators per UX consistency principle (constitution III)
- Cache recovery scores with TTL to serve fast responses for repeated requests
- Pre-compute AI insights on schedule (nightly) rather than on-demand where possible
- Show "last updated" timestamps when serving cached data (acceptance scenario 5 of User Story 1)
- Prioritize p95 latency <200ms for simple CRUD endpoints (user profile, goal management)
- Accept longer latency for compute-intensive operations with clear user expectations set

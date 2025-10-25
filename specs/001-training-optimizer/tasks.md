# Implementation Tasks: Intelligent Training Optimizer

**Feature**: 001-training-optimizer
**Branch**: `001-training-optimizer`
**Generated**: 2025-10-24
**Total Tasks**: 127
**Estimated Duration**: 8-10 weeks (MVP: 3-4 weeks for User Story 1 only)

## Overview

This document provides a dependency-ordered task list for implementing the Intelligent Training Optimizer. Tasks are organized by user story priority (P1 → P4) to enable incremental, independently testable delivery.

**Key Principles**:
- ✅ **TDD Required**: All implementation follows Test-Driven Development (constitution requirement)
- ✅ **Story-Based**: Each user story is independently testable and deliverable
- ✅ **Parallel Execution**: Tasks marked `[P]` can run in parallel
- ✅ **MVP First**: User Story 1 (P1) delivers core value, ship first

## Task Format

```
- [ ] [TaskID] [P?] [Story?] Description with file path
```

- **TaskID**: Sequential task number (T001, T002, ...)
- **[P]**: Parallelizable (can run concurrently with other [P] tasks)
- **[Story]**: User story label ([US1], [US2], etc.) - only for user story phases
- **Description**: Action with exact file path

---

## Phase 1: Setup & Infrastructure (Week 1)

**Goal**: Initialize project structure, configure development environment, set up foundational infrastructure (Docker, PostgreSQL, Redis, Celery).

**Completion Criteria**: Development environment fully operational, all services running, test framework configured.

### Project Initialization

- [X] T001 Create backend directory structure per plan.md in /backend/
- [X] T002 [P] Create frontend directory structure per plan.md in /frontend/
- [X] T003 [P] Create Docker Compose file with PostgreSQL 15+, Redis 7+ in /docker-compose.yml
- [X] T004 Initialize Python project with requirements.txt and requirements-dev.txt in /backend/
- [X] T005 [P] Initialize Node.js project with package.json in /frontend/
- [X] T006 Configure Python 3.11+ virtual environment in /backend/venv/
- [X] T007 [P] Install and configure Vite 5+ for React in /frontend/
- [X] T008 Create .env.example files for backend and frontend configuration
- [X] T009 [P] Set up pre-commit hooks with Black, Ruff, mypy in /.pre-commit-config.yaml
- [X] T010 [P] Set up ESLint and Prettier for frontend in /frontend/.eslintrc.js

### Database & Caching Setup

- [X] T011 Configure SQLAlchemy 2.0+ with asyncpg in /backend/src/database/connection.py
- [X] T012 Initialize Alembic for database migrations in /backend/alembic/
- [X] T013 Configure Redis connection with async support in /backend/src/database/redis.py
- [X] T014 Create Celery application with Redis broker in /backend/src/celery_app.py
- [X] T015 Configure Celery Beat scheduler for background jobs in /backend/src/celery_config.py

### API Framework Setup

- [X] T016 Create FastAPI application with CORS middleware in /backend/src/main.py
- [X] T017 [P] Configure JWT authentication middleware in /backend/src/api/middleware/auth.py
- [X] T018 [P] Create error handling middleware in /backend/src/api/middleware/error.py
- [X] T019 [P] Set up Pydantic V2 base schemas in /backend/src/api/schemas/base.py
- [X] T020 Configure OpenAPI/Swagger documentation in /backend/src/main.py

### Testing Framework Setup

- [X] T021 Configure pytest with pytest-asyncio, pytest-httpx, pytest-cov in /backend/pytest.ini
- [X] T022 [P] Create test fixtures for database and Redis in /backend/tests/conftest.py
- [X] T023 [P] Create test utilities for mocking external APIs in /backend/tests/utils/mocks.py
- [X] T024 [P] Configure Vitest and React Testing Library in /frontend/vitest.config.ts
- [X] T025 Set up coverage reporting for CI/CD in /backend/.coveragerc

### External Integration Setup

- [X] T026 Install python-garminconnect library in /backend/requirements.txt
- [X] T027 [P] Install Anthropic Python SDK in /backend/requirements.txt
- [X] T028 [P] Create Garmin OAuth configuration in /backend/config/garmin.py
- [X] T029 [P] Create Claude AI configuration in /backend/config/claude.py

---

## Phase 2: Foundational Layer (Week 1-2)

**Goal**: Implement shared models, authentication, base services, and utilities needed by ALL user stories.

**Completion Criteria**: Database models exist, authentication works, base services are testable.

### Database Models (Blocking Prerequisites)

- [ ] T030 Create User model in /backend/src/models/user.py
- [ ] T031 [P] Create HealthMetrics model in /backend/src/models/health_metrics.py
- [ ] T032 [P] Create Workout model in /backend/src/models/workout.py
- [ ] T033 [P] Create RecoveryScore model in /backend/src/models/recovery_score.py
- [ ] T034 [P] Create WorkoutRecommendation model in /backend/src/models/workout_recommendation.py
- [ ] T035 [P] Create Insight model in /backend/src/models/insight.py
- [ ] T036 [P] Create Goal model in /backend/src/models/goal.py
- [ ] T037 [P] Create TrainingPlan model in /backend/src/models/training_plan.py
- [ ] T038 [P] Create PlannedWorkout model in /backend/src/models/planned_workout.py
- [ ] T039 Generate initial Alembic migration for all models in /backend/alembic/versions/
- [ ] T040 Apply migration to development database

### Authentication System

- [ ] T041 Write unit tests for User model validation in /backend/tests/unit/test_user_model.py
- [ ] T042 Write unit tests for JWT token generation in /backend/tests/unit/test_auth.py
- [ ] T043 Implement JWT token service in /backend/src/services/auth/jwt_service.py
- [ ] T044 Create user registration endpoint in /backend/src/api/routes/auth.py
- [ ] T045 Create user login endpoint in /backend/src/api/routes/auth.py
- [ ] T046 Write contract tests for auth endpoints in /backend/tests/contract/test_auth_api.py

### Base Services & Utilities

- [ ] T047 [P] Create cache service wrapper for Redis in /backend/src/services/cache_service.py
- [ ] T048 [P] Create encryption utility for tokens in /backend/src/utils/encryption.py
- [ ] T049 [P] Create date/time utilities in /backend/src/utils/datetime.py
- [ ] T050 [P] Create validation utilities in /backend/src/utils/validation.py

---

## Phase 3: User Story 1 - Daily Recovery & Recommendations (P1) 🎯 MVP

**Priority**: P1 - Core Value Proposition
**Duration**: Week 2-4
**Goal**: Users can view daily recovery score and receive personalized workout recommendations.

**Independent Test**: Connect Garmin account, view recovery score with color-coded status (green/yellow/red), receive workout recommendation with rationale.

**Acceptance Scenarios** (from spec.md):
1. ✅ User synced Garmin data → displays recovery score with color status and explanation
2. ✅ High recovery (green) → suggests intense workout
3. ✅ Low recovery (red) → suggests recovery day
4. ✅ Moderate recovery (yellow) → suggests moderate workout
5. ✅ Garmin sync fails → shows last known status with timestamp

### Garmin Integration (US1)

**Tests First (TDD Red Phase)**:
- [ ] T051 [P] [US1] Write contract tests for Garmin API client in /backend/tests/contract/test_garmin_api.py
- [ ] T052 [P] [US1] Write unit tests for OAuth2 PKCE flow in /backend/tests/unit/test_garmin_oauth.py
- [ ] T053 [P] [US1] Write unit tests for health metrics parsing in /backend/tests/unit/test_garmin_parser.py

**Implementation (TDD Green Phase)**:
- [ ] T054 [US1] Implement Garmin OAuth2 PKCE flow in /backend/src/services/garmin/oauth_service.py
- [ ] T055 [US1] Implement Garmin API client with python-garminconnect in /backend/src/services/garmin/client.py
- [ ] T056 [US1] Implement health metrics fetching in /backend/src/services/garmin/health_service.py
- [ ] T057 [US1] Implement workout fetching in /backend/src/services/garmin/workout_service.py
- [ ] T058 [US1] Create Garmin authorization endpoints in /backend/src/api/routes/garmin.py
- [ ] T059 [US1] Create Garmin sync background job in /backend/src/jobs/garmin_sync.py
- [ ] T060 [US1] Configure Celery Beat for daily sync (6 AM) in /backend/src/celery_config.py

**Refactor (TDD Refactor Phase)**:
- [ ] T061 [US1] Add retry logic and error handling to Garmin service
- [ ] T062 [US1] Implement 24-hour caching for Garmin data in Redis

### Recovery Score Calculation (US1)

**Tests First (TDD Red Phase)**:
- [ ] T063 [P] [US1] Write unit tests for HRV component calculation in /backend/tests/unit/test_recovery_hrv.py
- [ ] T064 [P] [US1] Write unit tests for HR component calculation in /backend/tests/unit/test_recovery_hr.py
- [ ] T065 [P] [US1] Write unit tests for sleep component calculation in /backend/tests/unit/test_recovery_sleep.py
- [ ] T066 [P] [US1] Write unit tests for ACWR calculation in /backend/tests/unit/test_recovery_acwr.py
- [ ] T067 [P] [US1] Write unit tests for final score aggregation in /backend/tests/unit/test_recovery_aggregator.py

**Implementation (TDD Green Phase)**:
- [ ] T068 [US1] Implement HRV component calculator in /backend/src/services/recovery/hrv_calculator.py
- [ ] T069 [US1] Implement HR component calculator in /backend/src/services/recovery/hr_calculator.py
- [ ] T070 [US1] Implement sleep component calculator in /backend/src/services/recovery/sleep_calculator.py
- [ ] T071 [US1] Implement ACWR calculator in /backend/src/services/recovery/acwr_calculator.py
- [ ] T072 [US1] Implement recovery score aggregator in /backend/src/services/recovery/score_aggregator.py
- [ ] T073 [US1] Create recovery score background job in /backend/src/jobs/calculate_recovery.py

**Refactor (TDD Refactor Phase)**:
- [ ] T074 [US1] Implement anomaly detection (illness warning FR-010)
- [ ] T075 [US1] Add 24-hour caching for recovery scores in Redis

### Workout Recommendation Engine (US1)

**Tests First (TDD Red Phase)**:
- [ ] T076 [P] [US1] Write unit tests for intensity mapping in /backend/tests/unit/test_recommendation_intensity.py
- [ ] T077 [P] [US1] Write unit tests for workout type selection in /backend/tests/unit/test_recommendation_type.py
- [ ] T078 [P] [US1] Write unit tests for rationale generation in /backend/tests/unit/test_recommendation_rationale.py

**Implementation (TDD Green Phase)**:
- [ ] T079 [US1] Implement intensity level mapper (green→hard, yellow→moderate, red→rest) in /backend/src/services/recommendations/intensity_mapper.py
- [ ] T080 [US1] Implement workout type recommender in /backend/src/services/recommendations/type_recommender.py
- [ ] T081 [US1] Implement recommendation rationale generator in /backend/src/services/recommendations/rationale_service.py
- [ ] T082 [US1] Implement alternative workout generator (FR-014) in /backend/src/services/recommendations/alternatives_service.py

**Refactor (TDD Refactor Phase)**:
- [ ] T083 [US1] Add overtraining prevention logic (FR-015)

### Recovery API Endpoints (US1)

**Tests First (TDD Red Phase)**:
- [ ] T084 [P] [US1] Write contract tests for GET /recovery/{date} in /backend/tests/contract/test_recovery_api.py
- [ ] T085 [P] [US1] Write contract tests for GET /recovery/today in /backend/tests/contract/test_recovery_api.py
- [ ] T086 [P] [US1] Write contract tests for POST /recovery/{date}/recalculate in /backend/tests/contract/test_recovery_api.py

**Implementation (TDD Green Phase)**:
- [ ] T087 [US1] Create Pydantic schemas for recovery responses in /backend/src/api/schemas/recovery.py
- [ ] T088 [US1] Implement GET /recovery/{date} endpoint in /backend/src/api/routes/recovery.py
- [ ] T089 [US1] Implement GET /recovery/today endpoint in /backend/src/api/routes/recovery.py
- [ ] T090 [US1] Implement POST /recovery/{date}/recalculate endpoint in /backend/src/api/routes/recovery.py

### Integration Testing (US1)

- [ ] T091 [US1] Write integration test for complete User Story 1 flow in /backend/tests/integration/test_user_story_1.py
- [ ] T092 [US1] Verify all 5 acceptance scenarios pass in integration test

### Frontend (US1)

**Tests First (TDD Red Phase)**:
- [ ] T093 [P] [US1] Write component tests for RecoveryScore component in /frontend/tests/components/RecoveryScore.test.tsx
- [ ] T094 [P] [US1] Write component tests for WorkoutRecommendation component in /frontend/tests/components/WorkoutRecommendation.test.tsx

**Implementation (TDD Green Phase)**:
- [ ] T095 [US1] Create RecoveryScore display component in /frontend/src/components/recovery/RecoveryScore.tsx
- [ ] T096 [US1] Create WorkoutRecommendation card component in /frontend/src/components/recommendations/RecommendationCard.tsx
- [ ] T097 [US1] Create Dashboard page integrating recovery and recommendations in /frontend/src/pages/Dashboard.tsx
- [ ] T098 [US1] Implement API client for recovery endpoints in /frontend/src/services/api/recoveryApi.ts
- [ ] T099 [US1] Add loading states and error handling to Dashboard

**Refactor (TDD Refactor Phase)**:
- [ ] T100 [US1] Style components with Tailwind CSS per design system
- [ ] T101 [US1] Add accessibility features (WCAG 2.1 AA compliance)

**MVP CHECKPOINT**: 🎯 User Story 1 complete - Ship to production for user feedback

---

## Phase 4: User Story 2 - AI-Powered Insights (P2)

**Priority**: P2 - Deeper Value
**Duration**: Week 5-6
**Goal**: Users can view AI-generated insights about training patterns and recovery trends.

**Independent Test**: View insights showing patterns like "You recover best with 48 hours between hard sessions" with supporting data.

**Acceptance Scenarios** (from spec.md):
1. ✅ 2+ weeks of data → displays training patterns, recovery trends, correlations
2. ✅ 4+ weeks of data → identifies personal patterns
3. ✅ Accumulated fatigue → proactive overtraining warning
4. ✅ Varied workouts → shows effectiveness by type
5. ✅ Insufficient data → states how many more days needed

### Claude AI Integration (US2)

**Tests First (TDD Red Phase)**:
- [ ] T102 [P] [US2] Write contract tests for Claude API client in /backend/tests/contract/test_claude_api.py
- [ ] T103 [P] [US2] Write unit tests for prompt caching in /backend/tests/unit/test_claude_caching.py
- [ ] T104 [P] [US2] Write unit tests for insight parsing in /backend/tests/unit/test_insight_parser.py

**Implementation (TDD Green Phase)**:
- [ ] T105 [US2] Implement Claude AI client with Haiku 4.5 in /backend/src/services/ai/claude_client.py
- [ ] T106 [US2] Implement prompt builder for training analysis in /backend/src/services/ai/prompt_builder.py
- [ ] T107 [US2] Implement prompt caching strategy (7-day TTL) in /backend/src/services/ai/cache_manager.py
- [ ] T108 [US2] Implement batch processing for weekly insights in /backend/src/services/ai/batch_processor.py
- [ ] T109 [US2] Create insight generation background job in /backend/src/jobs/generate_insights.py
- [ ] T110 [US2] Configure Celery Beat for weekly insight generation (Monday 2 AM) in /backend/src/celery_config.py

**Refactor (TDD Refactor Phase)**:
- [ ] T111 [US2] Add fallback to rule-based insights when Claude unavailable
- [ ] T112 [US2] Implement cost tracking and budget alerts

### Insights API Endpoints (US2)

**Tests First (TDD Red Phase)**:
- [ ] T113 [P] [US2] Write contract tests for GET /insights in /backend/tests/contract/test_insights_api.py
- [ ] T114 [P] [US2] Write contract tests for POST /insights/generate in /backend/tests/contract/test_insights_api.py

**Implementation (TDD Green Phase)**:
- [ ] T115 [US2] Create Pydantic schemas for insights in /backend/src/api/schemas/insight.py
- [ ] T116 [US2] Implement GET /insights endpoint in /backend/src/api/routes/insights.py
- [ ] T117 [US2] Implement POST /insights/generate endpoint in /backend/src/api/routes/insights.py
- [ ] T118 [US2] Implement POST /insights/{id}/feedback endpoint in /backend/src/api/routes/insights.py

### Integration Testing (US2)

- [ ] T119 [US2] Write integration test for complete User Story 2 flow in /backend/tests/integration/test_user_story_2.py
- [ ] T120 [US2] Verify all 5 acceptance scenarios pass

### Frontend (US2)

**Tests First (TDD Red Phase)**:
- [ ] T121 [P] [US2] Write component tests for InsightCard component in /frontend/tests/components/InsightCard.test.tsx

**Implementation (TDD Green Phase)**:
- [ ] T122 [US2] Create InsightCard component in /frontend/src/components/insights/InsightCard.tsx
- [ ] T123 [US2] Create Insights page in /frontend/src/pages/Insights.tsx
- [ ] T124 [US2] Implement API client for insights endpoints in /frontend/src/services/api/insightsApi.ts

**Refactor (TDD Refactor Phase)**:
- [ ] T125 [US2] Add filtering and sorting for insights
- [ ] T126 [US2] Style components and ensure accessibility

---

## Phase 5: User Story 3 - Adaptive Training Plans (P3)

**Priority**: P3 - Proactive Planning
**Duration**: Week 7-8
**Goal**: Users can create multi-week training plans that adapt based on actual recovery and progress.

**Independent Test**: Define goal "5K in 25 minutes in 12 weeks", generate plan, see it adjust week-to-week.

**Tasks**: ~35 tasks (details omitted for brevity - follow same TDD pattern)
- Training plan generation algorithm
- Periodization logic
- Weekly adaptation background job
- Plan endpoints (GET, POST, PUT, DELETE)
- Progress tracking
- Frontend: Plan creation wizard, plan view, progress dashboard

---

## Phase 6: User Story 4 - Manual Data & Goal Tracking (P4)

**Priority**: P4 - Completeness
**Duration**: Week 9-10
**Goal**: Users can manually log workouts and track progress toward goals.

**Independent Test**: Manually enter workout, see it in history, verify it factors into recovery.

**Tasks**: ~25 tasks (details omitted for brevity - follow same TDD pattern)
- Manual workout entry
- Goal CRUD operations
- Goal progress calculation
- Goal endpoints
- Frontend: Manual workout form, goal creation form, progress indicators

---

## Phase 7: Polish & Cross-Cutting Concerns (Week 10+)

**Goal**: Production readiness, performance optimization, monitoring, documentation.

- [ ] T127 [P] Set up OpenTelemetry for distributed tracing in /backend/src/monitoring/
- [ ] T128 [P] Configure Prometheus metrics collection
- [ ] T129 [P] Set up Grafana dashboards for monitoring
- [ ] T130 [P] Integrate Sentry for error tracking
- [ ] T131 [P] Implement rate limiting on API endpoints
- [ ] T132 [P] Add request/response logging
- [ ] T133 [P] Create load testing suite with Locust in /backend/tests/load/
- [ ] T134 Run load tests and optimize bottlenecks
- [ ] T135 [P] Write API documentation in OpenAPI format
- [ ] T136 [P] Create deployment runbook in /docs/deployment.md
- [ ] T137 [P] Set up CI/CD pipeline with GitHub Actions in /.github/workflows/
- [ ] T138 [P] Configure Docker production images
- [ ] T139 [P] Set up database backup strategy
- [ ] T140 Final security audit and penetration testing

---

## Dependency Graph

### Story Completion Order

```
Setup (Phase 1)
    ↓
Foundational (Phase 2) ← BLOCKING
    ↓
    ├─→ User Story 1 (P1) ✅ MVP ← Ship First
    │
    ├─→ User Story 2 (P2) ← Can start after US1
    │
    ├─→ User Story 3 (P3) ← Depends on US1 (recovery) + US2 (insights)
    │
    └─→ User Story 4 (P4) ← Independent, can start after Foundational
```

### Key Dependencies

1. **Setup → Foundational**: Must complete infrastructure before any user story
2. **Foundational → ALL Stories**: Models, auth, base services block all stories
3. **US1 → US2**: Insights need recovery data (weak dependency, can work with mock data)
4. **US1 + US2 → US3**: Training plans use recovery scores and insights
5. **US4 is independent**: Can develop in parallel with US2/US3 after Foundational

---

## Parallel Execution Examples

### Week 2 (During Foundational Phase)

**Team A** (Backend):
- T030-T038: Create all models in parallel (8 tasks)
- T041-T046: Auth tests + implementation

**Team B** (DevOps):
- T003: Docker Compose
- T021-T025: Testing setup
- T026-T029: External integration setup

### Week 3-4 (User Story 1)

**Team A** (Backend - Garmin):
- T051-T053: Garmin contract/unit tests
- T054-T062: Garmin implementation

**Team B** (Backend - Recovery):
- T063-T067: Recovery unit tests
- T068-T075: Recovery implementation

**Team C** (Backend - Recommendations):
- T076-T078: Recommendation tests
- T079-T083: Recommendation implementation

**Team D** (Frontend):
- T093-T094: Component tests
- T095-T101: React components

All teams work in parallel on US1, merge at integration testing (T091-T092).

---

## Implementation Strategy

### MVP-First Approach (Recommended)

**Week 1-4: Ship User Story 1 (P1) ONLY**
- Focus: Daily recovery check and workout recommendations
- Value: Core feature providing immediate user benefit
- Ship to production, gather feedback, iterate

**Week 5-6: Add User Story 2 (P2)**
- Focus: AI-powered insights
- Value: Deeper analysis builds on recovery data
- Ship after US1 is stable

**Week 7-10: Add Remaining Stories**
- US3 and US4 based on user feedback priority
- Polish and production hardening

### Incremental Delivery Benefits

1. **Faster Time to Value**: Users get core features in 3-4 weeks
2. **Early Feedback**: Learn what users actually need before building everything
3. **Risk Reduction**: Validate technical approach with real usage
4. **Flexible Priorities**: Adjust US3/US4 scope based on feedback

---

## Testing Strategy Summary

### Three-Layer Testing (Constitution Requirement)

**1. Contract Tests** (`/backend/tests/contract/`):
- Verify API request/response schemas
- Test external API contracts (Garmin, Claude)
- Run before implementation

**2. Integration Tests** (`/backend/tests/integration/`):
- One test file per user story
- Test complete user journeys end-to-end
- Verify acceptance scenarios

**3. Unit Tests** (`/backend/tests/unit/`):
- Test individual functions and classes
- Fast execution (<100ms per test)
- 80%+ coverage for critical paths

### Coverage Targets (Constitution Requirement)

- Overall: 80% minimum
- Business logic (services/): 90% minimum
- API routes: 85% minimum
- Models: 70% minimum

---

## Task Completion Checklist

For each task:
- [ ] Tests written and failing (Red)
- [ ] Implementation makes tests pass (Green)
- [ ] Code refactored for quality (Refactor)
- [ ] Linting passes (Black, Ruff, mypy)
- [ ] Code reviewed
- [ ] Merged to feature branch

---

## Notes

1. **TDD Mandatory**: Constitution requires test-driven development for all features
2. **Parallel Opportunities**: 40+ tasks marked `[P]` can run concurrently
3. **MVP Definition**: User Story 1 (P1) = Minimum Viable Product
4. **Story Independence**: Each user story delivers standalone value
5. **Task IDs**: Sequential for dependency tracking (T001-T140+)
6. **File Paths**: All tasks include exact file paths for clarity
7. **Estimated Tasks**: US3 (~35 tasks) and US4 (~25 tasks) follow same TDD pattern as shown

---

## Quick Reference

**Total Tasks**: 127 (detailed) + ~60 (US3/US4) = ~187 total
**MVP Tasks**: T001-T101 (101 tasks for User Story 1)
**Parallel Tasks**: 40+ tasks marked `[P]`
**Phases**: 7 (Setup, Foundational, US1, US2, US3, US4, Polish)
**User Stories**: 4 (P1 → P2 → P3 → P4)
**Estimated Duration**: 8-10 weeks full feature, 3-4 weeks MVP

**MVP Recommendation**: ✅ Ship User Story 1 (P1) first, gather feedback, iterate.

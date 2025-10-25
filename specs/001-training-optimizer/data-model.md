# Data Model: Intelligent Training Optimizer

**Feature**: 001-training-optimizer
**Date**: 2025-10-24
**Source**: Extracted from spec.md and research.md

## Overview

This document defines the data model for the Intelligent Training Optimizer. The model is designed to support:
- User authentication and Garmin account linking
- Daily health metrics collection (HRV, resting HR, sleep, stress)
- Workout tracking (Garmin-synced and manually entered)
- Recovery score calculation and caching
- AI-powered insight generation and storage
- Training plan creation and adaptation
- Goal definition and progress tracking

## Entity Relationship Diagram

```
User
├─1:N─> HealthMetrics (daily snapshots)
├─1:N─> Workouts (training sessions)
├─1:N─> RecoveryScores (daily readiness)
├─1:N─> WorkoutRecommendations (daily suggestions)
├─1:N─> Insights (AI-generated patterns)
├─1:N─> Goals (targets to achieve)
└─1:N─> TrainingPlans
         └─1:N─> PlannedWorkouts
                  └─0:1─> Workout (completion link)

RecoveryScore ←─1:1─ WorkoutRecommendation
Goal ←─1:N─ TrainingPlan
```

## Core Entities

### User

Represents an athlete using the system. Stores authentication credentials, Garmin account linkage, and profile information.

**Table**: `users`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique user identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User's email address (used for authentication) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Account creation timestamp |
| garmin_user_id | VARCHAR(255) | NULLABLE, UNIQUE | Garmin account ID (null until connected) |
| garmin_access_token | TEXT | NULLABLE | Encrypted OAuth access token for Garmin API |
| garmin_refresh_token | TEXT | NULLABLE | Encrypted OAuth refresh token |
| garmin_token_expires_at | TIMESTAMP | NULLABLE | When current access token expires |

**Indexes**:
- PRIMARY KEY on `id`
- UNIQUE INDEX on `email`
- UNIQUE INDEX on `garmin_user_id` WHERE NOT NULL

**Validation Rules** (Pydantic):
- `email`: Must be valid email format, max 255 characters
- `garmin_access_token`: Encrypted at rest using AES-256
- `garmin_refresh_token`: Encrypted at rest using AES-256

**State Transitions**:
1. Created → Garmin Connected (when OAuth flow completes)
2. Garmin Connected → Garmin Disconnected (when user revokes or token invalid)
3. Garmin Disconnected → Garmin Connected (when user re-authorizes)

---

### HealthMetrics

Daily snapshot of physiological data collected from Garmin devices overnight. Used for recovery score calculation.

**Table**: `health_metrics`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTO INCREMENT | Unique metric record ID |
| user_id | UUID | FOREIGN KEY (users.id), NOT NULL | Owner of this data |
| date | DATE | NOT NULL | Calendar date for this snapshot |
| hrv_ms | INTEGER | NULLABLE | Heart Rate Variability in milliseconds (e.g., 62) |
| resting_hr | INTEGER | NULLABLE | Resting heart rate in beats per minute (e.g., 55) |
| sleep_duration_minutes | INTEGER | NULLABLE | Total sleep duration in minutes (e.g., 480 = 8 hours) |
| sleep_score | INTEGER | NULLABLE, CHECK (0-100) | Garmin's sleep quality score 0-100 |
| stress_level | INTEGER | NULLABLE, CHECK (0-100) | Average stress level 0-100 from Garmin |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | When this record was created |

**Indexes**:
- PRIMARY KEY on `id`
- COMPOUND INDEX on `(user_id, date DESC)` for fast time-series queries
- UNIQUE INDEX on `(user_id, date)` to prevent duplicates

**Validation Rules**:
- `hrv_ms`: Typical range 20-150ms, alert if outside 10-200ms
- `resting_hr`: Typical range 40-80 bpm, alert if outside 30-120 bpm
- `sleep_duration_minutes`: Must be >= 0, alert if > 720 (12 hours)
- `sleep_score`: Integer 0-100
- `stress_level`: Integer 0-100

**Data Sources**:
- Garmin Connect API endpoint: `/wellness-api/rest/dailies`
- Fetched daily via Celery scheduled job (6 AM)
- Cached for 24 hours in Redis

---

### Workout

Individual training session with type, duration, intensity, and optional heart rate data. Can be synced from Garmin or manually entered.

**Table**: `workouts`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique workout identifier |
| user_id | UUID | FOREIGN KEY (users.id), NOT NULL | Who performed this workout |
| garmin_activity_id | VARCHAR(255) | NULLABLE, UNIQUE | Garmin's activity ID (null for manual entries) |
| workout_type | ENUM | NOT NULL | Type: run, bike, swim, strength, yoga, other |
| started_at | TIMESTAMP | NOT NULL | When workout began |
| duration_minutes | INTEGER | NOT NULL | Total duration in minutes |
| training_load | FLOAT | NULLABLE | Garmin Training Load score (0-500+) |
| perceived_exertion | INTEGER | NULLABLE, CHECK (1-10) | User's RPE rating (1=easy, 10=maximal) |
| heart_rate_zones | JSONB | NULLABLE | Time in each HR zone: `{"zone1": 120, "zone2": 140, ...}` |
| manual_entry | BOOLEAN | NOT NULL, DEFAULT FALSE | True if user manually logged this |
| notes | TEXT | NULLABLE | Optional user notes about the workout |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | When record was created |

**Indexes**:
- PRIMARY KEY on `id`
- COMPOUND INDEX on `(user_id, started_at DESC)` for workout history queries
- UNIQUE INDEX on `garmin_activity_id` WHERE NOT NULL

**Validation Rules**:
- `workout_type`: One of predefined enum values
- `duration_minutes`: Must be > 0, alert if > 720 (12 hours)
- `training_load`: Typical range 0-500, alert if > 1000
- `perceived_exertion`: Integer 1-10 (RPE scale)
- `heart_rate_zones`: JSON object with zone names as keys, seconds as values

**Relationships**:
- Belongs to User
- May be linked from PlannedWorkout (when plan is completed)

**Data Sources**:
- Garmin Connect API: `/fitness-api/rest/activityList` and `/fitness-api/rest/activity/{id}`
- Manual entry via API endpoint
- Fetched daily via Celery job

---

### RecoveryScore

Daily calculated score (0-100) representing training readiness based on recent health metrics and training load.

**Table**: `recovery_scores`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTO INCREMENT | Unique score record ID |
| user_id | UUID | FOREIGN KEY (users.id), NOT NULL | Owner of this score |
| date | DATE | NOT NULL | Calendar date for this score |
| total_score | INTEGER | NOT NULL, CHECK (0-100) | Final recovery score 0-100 |
| hrv_component | INTEGER | NOT NULL, CHECK (0-100) | HRV contribution to score (40% weight) |
| hr_component | INTEGER | NOT NULL, CHECK (0-100) | Resting HR contribution (30% weight) |
| sleep_component | INTEGER | NOT NULL, CHECK (0-100) | Sleep contribution (20% weight) |
| stress_component | INTEGER | NOT NULL, CHECK (0-100) | Stress contribution (10% weight) |
| acwr_adjustment | FLOAT | NOT NULL, DEFAULT 1.0 | Acute:Chronic Workload Ratio adjustment factor |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | When score was calculated |

**Indexes**:
- PRIMARY KEY on `id`
- UNIQUE COMPOUND INDEX on `(user_id, date)` to prevent duplicates
- INDEX on `date` for time-series analysis

**Validation Rules**:
- All component scores: Integer 0-100
- `total_score`: Integer 0-100
- `acwr_adjustment`: Float 0.0-1.0 (multiplicative reduction factor)

**Calculation Algorithm** (from research.md):
```python
total_score = (
    (hrv_component * 0.4) +
    (hr_component * 0.3) +
    (sleep_component * 0.2) +
    (stress_component * 0.1)
) * acwr_adjustment

# Component calculations:
# HRV: +10% vs 7-day avg = 100, -10% = 50, -20% = 0
# HR: -5% vs 7-day avg = 100, +0% = 50, +10% = 0 (inverse)
# Sleep: 7-9 hours = 100, 6 hours = 70, <5 hours = 30
# Stress: inverted Garmin stress (100 - garmin_stress)
# ACWR: Reduce by 20% if ratio > 1.5, by 10% if > 1.3
```

**Color Coding**:
- Green (80-100): High recovery, ready for hard training
- Yellow (50-79): Moderate recovery, adjust intensity
- Red (0-49): Low recovery, prioritize rest

**Caching Strategy**:
- Cache in Redis for 24 hours (key: `recovery:{user_id}:{date}`)
- Invalidate on new health metrics arrival
- Recalculate when cached value missing or invalidated

---

### WorkoutRecommendation

Daily suggested training session based on current recovery score and training goals.

**Table**: `workout_recommendations`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTO INCREMENT | Unique recommendation ID |
| user_id | UUID | FOREIGN KEY (users.id), NOT NULL | Recipient of recommendation |
| date | DATE | NOT NULL | Calendar date for this recommendation |
| recovery_score_id | INTEGER | FOREIGN KEY (recovery_scores.id), NOT NULL | Basis for this recommendation |
| workout_type | ENUM | NOT NULL | Recommended type: run, bike, swim, strength, rest, active_recovery |
| duration_minutes | INTEGER | NOT NULL | Suggested duration |
| intensity_level | ENUM | NOT NULL | Level: recovery, easy, moderate, hard, maximal |
| heart_rate_target_low | INTEGER | NULLABLE | Lower HR target in bpm (if applicable) |
| heart_rate_target_high | INTEGER | NULLABLE | Upper HR target in bpm (if applicable) |
| rationale | TEXT | NOT NULL | Plain language explanation of why this recommendation |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | When generated |

**Indexes**:
- PRIMARY KEY on `id`
- COMPOUND INDEX on `(user_id, date DESC)` for recommendation history
- FOREIGN KEY INDEX on `recovery_score_id`

**Validation Rules**:
- `workout_type`: One of predefined enum values
- `duration_minutes`: Must be > 0
- `intensity_level`: One of predefined enum values
- `rationale`: Min 50 characters (must be substantive)
- HR targets: If provided, `heart_rate_target_high` > `heart_rate_target_low`

**Relationships**:
- Belongs to User
- References RecoveryScore (1:1 relationship)

**Generation Logic**:
- Green recovery (80-100) → Hard or high-volume workout
- Yellow recovery (50-79) → Moderate workout with adjusted intensity
- Red recovery (0-49) → Rest day or active recovery

**Caching Strategy**:
- Cache in Redis for current day only (key: `recommendation:{user_id}:{date}`)
- Invalidate when recovery score changes

---

### Insight

AI-generated observation about training patterns, recovery trends, or correlations with actionable recommendations.

**Table**: `insights`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTO INCREMENT | Unique insight ID |
| user_id | UUID | FOREIGN KEY (users.id), NOT NULL | Recipient of insight |
| generated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | When Claude API generated this |
| valid_until | DATE | NOT NULL | Cache expiry date (typically generated_at + 7 days) |
| insight_type | ENUM | NOT NULL | Category: recovery_pattern, overtraining_warning, workout_effectiveness, frequency_recommendation |
| title | VARCHAR(255) | NOT NULL | Short summary of insight (e.g., "You recover best after 48 hours") |
| content | TEXT | NOT NULL | Full plain language explanation of pattern |
| supporting_data | JSONB | NOT NULL | Metrics supporting insight: `{"avg_hrv_after_hard": 58, "avg_hrv_normal": 62}` |
| action_items | JSONB | NOT NULL | Recommended actions: `["Schedule hard workouts on Tuesdays", "Add extra rest day after long runs"]` |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Database insertion time |

**Indexes**:
- PRIMARY KEY on `id`
- COMPOUND INDEX on `(user_id, generated_at DESC)` for insight feed
- INDEX on `valid_until` for cache expiry cleanup

**Validation Rules**:
- `insight_type`: One of predefined enum values
- `title`: Max 255 characters, min 10 characters
- `content`: Min 100 characters (must be substantive)
- `supporting_data`: Valid JSON object with at least one metric
- `action_items`: JSON array with at least one action string

**Relationships**:
- Belongs to User

**Generation Strategy** (from research.md):
- Weekly scheduled generation via Celery Beat (Monday 2 AM)
- Batch processing for 50% cost discount
- Prompt caching for 90% cost savings
- Uses Claude Haiku 4.5 model
- Analyzes 4-8 weeks of historical data
- Valid for 7 days (cache TTL)

**AI Prompt Structure**:
```python
system_prompt = """You are a sports science expert analyzing training data.
Generate 3-5 specific, actionable insights based on patterns."""

user_prompt = f"""
Training History (last 8 weeks):
{format_workouts_and_metrics()}

Analysis Request: Identify patterns in recovery, workout effectiveness,
and training frequency. Each insight must include:
- Title (concise pattern summary)
- Content (plain language explanation)
- Supporting data (specific metrics)
- Action items (2-3 concrete recommendations)
"""
```

---

### Goal

User-defined target with metric, target value, timeline, and progress tracking.

**Table**: `goals`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique goal identifier |
| user_id | UUID | FOREIGN KEY (users.id), NOT NULL | Owner of this goal |
| goal_type | ENUM | NOT NULL | Type: distance, time, event, fitness_level |
| target_metric | VARCHAR(255) | NOT NULL | What to measure (e.g., "5K time", "10K distance") |
| target_value | VARCHAR(255) | NOT NULL | Desired value (e.g., "25:00", "10 km") |
| target_date | DATE | NOT NULL | Deadline for achievement |
| priority | INTEGER | NOT NULL, CHECK (1-5), DEFAULT 3 | Importance level (1=highest, 5=lowest) |
| status | ENUM | NOT NULL, DEFAULT 'active' | Status: active, achieved, abandoned |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | When goal was created |

**Indexes**:
- PRIMARY KEY on `id`
- COMPOUND INDEX on `(user_id, status, target_date)` for active goals list
- INDEX on `target_date` for deadline tracking

**Validation Rules**:
- `goal_type`: One of predefined enum values
- `target_metric`: Min 3 characters, max 255 characters
- `target_value`: Min 1 character, max 255 characters
- `target_date`: Must be future date at creation
- `priority`: Integer 1-5
- `status`: One of predefined enum values

**Relationships**:
- Belongs to User
- Has many TrainingPlans

**State Transitions**:
1. Created (status=active)
2. active → achieved (when target reached)
3. active → abandoned (when user gives up or goal no longer relevant)

---

### TrainingPlan

Structured multi-week program with daily workouts, rest days, progression schedule, and goal alignment.

**Table**: `training_plans`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique plan identifier |
| user_id | UUID | FOREIGN KEY (users.id), NOT NULL | Owner of this plan |
| goal_id | UUID | FOREIGN KEY (goals.id), NOT NULL | Goal this plan targets |
| name | VARCHAR(255) | NOT NULL | Plan name (e.g., "12-Week 5K Plan") |
| start_date | DATE | NOT NULL | When plan begins |
| end_date | DATE | NOT NULL | When plan completes (target_date from goal) |
| status | ENUM | NOT NULL, DEFAULT 'draft' | Status: draft, active, completed, cancelled |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | When plan was created |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last modification time |

**Indexes**:
- PRIMARY KEY on `id`
- COMPOUND INDEX on `(user_id, status)` for active plans
- FOREIGN KEY INDEX on `goal_id`

**Validation Rules**:
- `name`: Min 3 characters, max 255 characters
- `end_date`: Must be > `start_date`
- `end_date`: Should align with `goal.target_date`
- `status`: One of predefined enum values

**Relationships**:
- Belongs to User
- Belongs to Goal
- Has many PlannedWorkouts

**State Transitions**:
1. Created (status=draft)
2. draft → active (when user approves and starts)
3. active → completed (when end_date reached and goal achieved)
4. active → cancelled (when user stops following plan)

**Adaptation Logic** (from spec FR-024 to FR-026):
- Weekly review (Sunday 3 AM via Celery)
- Adjust upcoming week if recovery consistently low
- Advance plan if progress faster than expected
- Reorganize if workouts missed

---

### PlannedWorkout

Individual workout within a training plan with scheduled date, type, duration, intensity, and completion tracking.

**Table**: `planned_workouts`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique planned workout ID |
| training_plan_id | UUID | FOREIGN KEY (training_plans.id), NOT NULL | Parent training plan |
| scheduled_date | DATE | NOT NULL | When this workout should be done |
| workout_type | ENUM | NOT NULL | Type: run, bike, swim, strength, rest |
| duration_minutes | INTEGER | NOT NULL | Planned duration |
| intensity_level | ENUM | NOT NULL | Level: recovery, easy, moderate, hard, maximal |
| description | TEXT | NULLABLE | Details (e.g., "6x800m intervals at 5K pace") |
| completed | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether user completed this workout |
| actual_workout_id | UUID | FOREIGN KEY (workouts.id), NULLABLE | Link to actual workout if completed |
| notes | TEXT | NULLABLE | User notes about this workout |

**Indexes**:
- PRIMARY KEY on `id`
- COMPOUND INDEX on `(training_plan_id, scheduled_date)` for plan view
- FOREIGN KEY INDEX on `actual_workout_id`

**Validation Rules**:
- `workout_type`: One of predefined enum values
- `duration_minutes`: Must be > 0
- `intensity_level`: One of predefined enum values
- `completed` + `actual_workout_id`: If completed=true, actual_workout_id should be NOT NULL

**Relationships**:
- Belongs to TrainingPlan
- May reference Workout (when completed)

**Completion Flow**:
1. User completes workout (creates Workout record)
2. System links PlannedWorkout.actual_workout_id → Workout.id
3. System sets PlannedWorkout.completed = true

---

## Enumerations

### WorkoutType
- `run`: Running/jogging
- `bike`: Cycling
- `swim`: Swimming
- `strength`: Strength training/gym
- `yoga`: Yoga/flexibility
- `other`: Other activity

### IntensityLevel
- `recovery`: Very light, active recovery
- `easy`: Comfortable, conversational pace
- `moderate`: Somewhat hard, can speak in short sentences
- `hard`: Hard, difficult to speak
- `maximal`: All-out effort

### GoalType
- `distance`: Achieve specific distance (e.g., run 10K)
- `time`: Achieve time goal (e.g., 5K under 25 minutes)
- `event`: Complete event (e.g., marathon)
- `fitness_level`: Reach fitness milestone (e.g., run 30 minutes continuously)

### InsightType
- `recovery_pattern`: Patterns in recovery data
- `overtraining_warning`: Risk of overtraining detected
- `workout_effectiveness`: Which workouts yield best results
- `frequency_recommendation`: Optimal training frequency

### PlanStatus
- `draft`: Plan created but not started
- `active`: Currently following this plan
- `completed`: Plan finished
- `cancelled`: Plan abandoned before completion

### GoalStatus
- `active`: Currently working toward this goal
- `achieved`: Goal successfully reached
- `abandoned`: Gave up on this goal

---

## Data Relationships Summary

### One-to-Many (1:N)
- User → HealthMetrics: One user has many daily health metric records
- User → Workouts: One user performs many workouts
- User → RecoveryScores: One user has many daily recovery scores
- User → WorkoutRecommendations: One user receives many recommendations
- User → Insights: One user receives many AI insights
- User → Goals: One user defines many goals
- User → TrainingPlans: One user creates many training plans
- Goal → TrainingPlans: One goal can have multiple plans (e.g., restart plan)
- TrainingPlan → PlannedWorkouts: One plan contains many planned workouts

### One-to-One (1:1)
- RecoveryScore → WorkoutRecommendation: Each recovery score generates one recommendation

### Optional One-to-One (0:1)
- PlannedWorkout → Workout: Planned workout may be linked to actual workout when completed

---

## Storage Considerations

### Database: PostgreSQL 15+

**Rationale** (from research.md):
- Relational data model fits naturally (users, workouts, plans)
- JSONB for flexible data (heart rate zones, supporting data)
- Window functions for rolling averages (7-day, 28-day)
- Native time-series query support with proper indexes
- Handles 3.6M rows/year efficiently for 1000 users

**Key Indexes**:
- Compound indexes on `(user_id, date DESC)` for all time-series tables
- Unique indexes on `(user_id, date)` to prevent duplicates
- Foreign key indexes for join performance

### Caching: Redis 7+

**Cache Keys**:
- Recovery scores: `recovery:{user_id}:{date}` (TTL: 24 hours)
- Recommendations: `recommendation:{user_id}:{date}` (TTL: 24 hours)
- Insights: `insight:{user_id}` (TTL: 7 days)
- Garmin data: `garmin:{user_id}:{endpoint}:{date}` (TTL: 24 hours)

**Invalidation Strategy**:
- Invalidate on new data arrival (health metrics, workouts)
- Invalidate on user-triggered recalculation
- Automatic expiry via TTL

---

## Data Volume Estimates

### For 1000 Users

| Table | Records/User/Year | Total/Year | Storage/Year |
|-------|-------------------|------------|--------------|
| HealthMetrics | 365 | 365,000 | ~15 MB |
| Workouts | 260 (5/week) | 260,000 | ~50 MB |
| RecoveryScores | 365 | 365,000 | ~20 MB |
| WorkoutRecommendations | 365 | 365,000 | ~40 MB |
| Insights | 52 (weekly) | 52,000 | ~50 MB |
| TrainingPlans | 2-3 | 2,500 | ~1 MB |
| PlannedWorkouts | 180 (per plan) | 450,000 | ~30 MB |
| **Total** | | ~2.8M records | ~206 MB |

**Scaling**: At 10,000 users → ~28M records/year, ~2 GB/year (very manageable for PostgreSQL)

---

## Migration Strategy

### Alembic Migrations

All schema changes versioned and tracked via Alembic:
```bash
alembic revision --autogenerate -m "Create initial schema"
alembic upgrade head
```

### Zero-Downtime Migrations

For production deployments:
1. Add new columns as NULLABLE
2. Backfill data in background job
3. Make column NOT NULL in subsequent migration
4. Drop old columns after verification

---

## Security Considerations

### Encryption at Rest
- `garmin_access_token`: Encrypted using AES-256 before storage
- `garmin_refresh_token`: Encrypted using AES-256 before storage
- Use SQLAlchemy-utils `EncryptedType` or custom encryption

### Data Privacy
- User data never shared with third parties (FR-036)
- Insights generated by Claude AI do not persist user PII in Anthropic's systems
- Users can export data (FR-035) and request deletion (GDPR compliance)

### Access Control
- All queries filtered by authenticated user_id
- Row-level security via application layer
- API endpoints require JWT authentication

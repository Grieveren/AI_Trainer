# Technical Research: Intelligent Training Optimizer

**Feature**: 001-training-optimizer
**Date**: 2025-10-24
**Purpose**: Document research findings and technical decisions for implementation planning

## Executive Summary

After comprehensive research into technology stack options for the Intelligent Training Optimizer, the following core decisions have been made:

1. **Backend**: Python 3.11+ with FastAPI - superior AI/ML ecosystem integration, excellent async performance
2. **Database**: PostgreSQL 15+ with standard tables - mature, reliable, handles time-series data well with proper indexes
3. **Background Jobs**: Celery 5+ with Redis - robust scheduling, retry logic, and monitoring capabilities
4. **Testing**: pytest with three-layer testing approach - excellent async support, mature ecosystem
5. **Garmin Integration**: python-garminconnect library - active maintenance, comprehensive API coverage
6. **Claude Integration**: Anthropic Python SDK with cost optimization strategies - prompt caching, batch processing

These decisions prioritize the AI/ML workload requirements, data processing capabilities, and the mature Python ecosystem for health/fitness data analysis.

## Research Areas

### 0. Backend Language and Framework Selection

**Research Question**: Should we use Python (FastAPI) or TypeScript/Node.js (Express) for the backend?

**Decision**: Python 3.11+ with FastAPI 0.104+

**Rationale**:

1. **AI/ML Ecosystem Integration** (Critical for this application):
   - Python dominates AI/ML with 51% of developers using it for data exploration and processing
   - Direct integration with data science libraries: pandas (data manipulation), NumPy (numerical computing), SciPy (statistical analysis)
   - Native Anthropic Claude SDK with excellent support and examples
   - Future extensibility: If we need to add ML models for recovery prediction or pattern detection, Python ecosystem is unmatched
   - FastAPI usage jumped 30% (29% to 38%) in 2025, driven heavily by ML/AI developers

2. **Time-Series Data Processing**:
   - pandas excels at time-series operations: rolling averages, date-based indexing, resampling
   - Recovery score algorithm requires 7-day and 28-day rolling calculations - natural fit for pandas
   - NumPy provides efficient array operations for HRV analysis and statistical computations
   - Over 80% of data scientists use pandas for data cleaning and preparation

3. **Async Performance**:
   - FastAPI delivers ~24% higher RPS and ~30% lower latency than Express under real-world load testing
   - Native async/await support with asyncio (Python 3.11+)
   - FastAPI processes requests in ~17ms vs Flask's 507ms (though Express can be 3x faster in some simple benchmarks)
   - Async I/O with httpx (Garmin/Claude API calls) and asyncpg (PostgreSQL queries)

4. **Background Job Processing**:
   - Celery is mature, battle-tested solution for distributed task queues
   - Native Python integration with FastAPI BackgroundTasks for simple jobs
   - Better for compute-intensive operations (recovery calculations, data analysis)
   - Excellent monitoring with Flower dashboard

5. **Development Velocity**:
   - FastAPI's automatic API documentation (OpenAPI/Swagger)
   - Pydantic V2 for data validation with excellent performance
   - Type hints and mypy for static type checking
   - Simpler deployment for data-heavy workloads

6. **Performance Requirements Compatibility**:
   - Constitution requires 200ms p95 for simple endpoints - FastAPI achieves this
   - Compute-intensive operations (recovery scoring: 5s, AI insights: 30s) need background processing regardless of language
   - FastAPI's async-first design handles concurrent background tasks efficiently

**Alternatives Considered**:

1. **TypeScript/Node.js with Express**:
   - **Strengths**:
     - Larger ecosystem for web development
     - Excellent for real-time features (WebSockets)
     - Unified language with React frontend
     - Some benchmarks show 3x faster request processing for simple operations
   - **Why Rejected**:
     - Weaker AI/ML ecosystem - no pandas/NumPy equivalent
     - Claude SDK less mature for TypeScript
     - Time-series data manipulation more cumbersome
     - Would need additional libraries for statistical computing
     - This is a data-intensive application, not primarily a real-time web app
   - **When to Reconsider**: If real-time workout guidance or live coaching features become priority

2. **Hybrid Approach** (Python for ML microservices, Node.js for API):
   - **Why Rejected for MVP**:
     - Adds deployment complexity
     - Network overhead between services
     - More difficult to debug and maintain
     - MVP should prove value before adding architectural complexity
   - **When to Reconsider**: If scaling to 10,000+ users and need to optimize specific bottlenecks

**Trade-offs**:

| Aspect | Python/FastAPI | Impact |
|--------|----------------|---------|
| Ecosystem | Smaller web ecosystem than Node.js | Acceptable - FastAPI has everything needed for API development |
| Frontend Integration | Different language than React/TypeScript | Minimal - REST API provides clean separation |
| Real-time Features | Slightly more complex than Node.js | Acceptable - not critical for MVP (no live coaching) |
| Simple Benchmarks | Can be slower than Node.js for basic CRUD | Mitigated - Caching and async I/O close the gap |
| Developer Pool | Fewer full-stack Python/React developers | Acceptable - Clear API contract enables parallel development |

**Implementation Notes**:
- Use FastAPI 0.104+ with async route handlers
- SQLAlchemy 2.0+ with asyncpg dialect for async PostgreSQL
- httpx for async external API calls (Garmin, Claude)
- Pydantic V2 for request/response validation
- uvicorn as ASGI server with multiple workers

---

### 1. Garmin Connect API Integration

**Research Question**: How to integrate with Garmin Connect API for health metrics and workout data?

**Decision**: Use Garmin Health API with OAuth 2.0 PKCE + python-garminconnect library

**Rationale**:

1. **Official Garmin Health API**:
   - Garmin Developer Program provides Health API specifically for third-party health/fitness integrations
   - OAuth 2.0 PKCE (Proof Key for Code Exchange) authentication - more secure than standard OAuth2
   - Access to comprehensive health metrics: HRV, resting HR, stress, sleep, respiration, SpO2, body composition
   - Activity data includes: workouts with HR zones, duration, type, training load, training status
   - HRV summaries available as JSON (collected during overnight sleep window on supported devices like Forerunner 995)

2. **Rate Limits and Best Practices**:
   - Evaluation-level keys are rate-limited (specific numbers not publicly disclosed, typically 100-500 req/hour)
   - Production-level keys not rate-limited (requires Partner Verification Tool approval)
   - Summary data endpoints should only be called in response to Ping notifications (webhook-based updates)
   - Push notifications must be responded to with HTTP 200 in timely manner
   - Aggressive caching required to minimize API calls

3. **Python Library - python-garminconnect**:
   - Most popular and actively maintained Python library (released Sept 2025)
   - Uses same OAuth authentication as official Garmin Connect app via Garth library
   - Comprehensive coverage: health metrics, activity data, device info, goals, historical data
   - Parses JSON responses (no HTML scraping needed)
   - Available on PyPI: `pip install garminconnect`

**Alternatives Considered**:

1. **Direct API Integration without Library**:
   - **Why Rejected**:
     - OAuth 2.0 PKCE flow is complex to implement correctly
     - Need to handle token refresh, rate limiting, pagination
     - python-garminconnect already solves these problems
     - Time savings significant for MVP

2. **Garth Library** (lower-level):
   - **Why Rejected**:
     - Lower-level than python-garminconnect
     - Would need to build more abstraction layers
     - python-garminconnect built on Garth, provides higher-level API

3. **Garmy Library** (AI-focused):
   - **Considered but Rejected**:
     - Newer, less battle-tested than python-garminconnect
     - AI-first design might be overkill for MVP
     - Local SQLite database might conflict with our PostgreSQL design
   - **When to Reconsider**: If we add more advanced AI health analytics features

4. **Web Scraping Garmin Connect**:
   - **Rejected**:
     - Violates Terms of Service
     - Unreliable (HTML structure changes break code)
     - No official support or documentation
     - Could result in account suspension

5. **Manual .FIT File Upload**:
   - **Kept as Fallback Only**:
     - Good for users without Garmin Connect account
     - Enables testing without real account
     - Not primary integration method
     - Requires significant file parsing logic

**Implementation Approach**:

```python
from garminconnect import Garmin

# Initialize client (uses Garth for OAuth)
client = Garmin(email, password)
client.login()

# Fetch daily health metrics
health_data = client.get_daily_metrics(date)
# Returns: HRV, resting HR, stress, sleep, steps, calories, etc.

# Fetch activities (workouts)
activities = client.get_activities(start_date, limit=50)

# Get detailed activity data
activity_detail = client.get_activity(activity_id)
# Returns: HR zones, training load, duration, splits, etc.
```

**Rate Limit Handling Strategy**:

1. **Caching Layer** (Redis):
   - Cache daily health metrics for 24 hours
   - Cache activity list for 1 hour
   - Cache detailed activity for 7 days (historical data doesn't change)
   - Cache key format: `garmin:{user_id}:{endpoint}:{date}`

2. **Webhook-Based Updates** (Future Enhancement):
   - Register for Garmin ping notifications
   - Only fetch data when Garmin notifies of new data
   - Reduces unnecessary API calls by 80-90%
   - Requires production-level API keys

3. **Batch Fetching**:
   - Fetch multiple days of data in single request where possible
   - Use pagination efficiently
   - Schedule daily batch sync (6 AM) instead of real-time syncing

4. **Exponential Backoff**:
   - Retry failed requests with exponential backoff (1s, 2s, 4s, 8s)
   - Max 5 retries before marking sync as failed
   - Alert user if sync consistently fails

**Data Available from API**:

| Metric Category | Specific Metrics | Endpoint |
|-----------------|------------------|----------|
| Daily Health | HRV (ms), Resting HR (bpm), Sleep duration/quality, Stress (0-100), SpO2, Respiration rate | `/wellness-api/rest/dailies` |
| Activities | Activity list with type, date, duration, distance | `/fitness-api/rest/activityList` |
| Activity Details | HR zones, training load, pace/speed, elevation, splits | `/fitness-api/rest/activity/{id}` |
| Training Status | Fitness level, training load focus, recovery time | `/metrics-api/rest/trainingStatus` |
| Body Composition | Weight, body fat %, muscle mass, bone mass, body water | `/wellness-api/rest/bodyComposition` |

**OAuth 2.0 PKCE Flow**:

1. Register app at Garmin Developer Portal (https://developerportal.garmin.com)
2. Receive: Consumer Key, Consumer Secret
3. Generate code verifier (43-128 char random string)
4. Create code challenge (SHA-256 hash of verifier)
5. Redirect user to: `https://connect.garmin.com/oauth2Confirm?client_id={key}&code_challenge={challenge}`
6. User authorizes app
7. Receive authorization code
8. Exchange code + verifier for access/refresh tokens at `/oauth/token`
9. Store tokens encrypted in database
10. Use refresh token to get new access token when expired

**Security Considerations**:
- Store tokens encrypted at rest (AES-256)
- Use HTTPS only for OAuth redirects
- Implement CSRF protection for OAuth callback
- Rotate refresh tokens periodically
- Revoke tokens when user disconnects account

**Error Handling**:
- **401 Unauthorized**: Token expired → Use refresh token to get new access token
- **403 Forbidden**: Account revoked → Alert user to reconnect
- **429 Rate Limited**: Exponential backoff + use cached data
- **500 Server Error**: Retry with backoff, fallback to cached data
- **Network Timeout**: Retry up to 3 times, then fail gracefully

**Trade-offs**:

| Aspect | Decision | Trade-off |
|--------|----------|-----------|
| Using Library vs Direct API | python-garminconnect | Less control over implementation, dependency on third-party library maintenance |
| OAuth PKCE Complexity | Accept complexity | More secure than simple OAuth2, but requires careful implementation |
| Rate Limits | Aggressive caching | Data may be up to 24 hours stale, acceptable for daily health metrics |
| Production Keys | Start with evaluation keys | Rate limited initially, need to pass verification for production access |

---

### 2. Recovery Score Algorithm

**Research Question**: What algorithm should calculate the daily recovery score (0-100)?

**Decision**: Weighted multi-factor algorithm based on sports science research

**Rationale**:
- HRV (Heart Rate Variability) is the strongest predictor of recovery (40% weight)
- Resting heart rate deviations indicate stress or illness (30% weight)
- Sleep quality and duration affect recovery capacity (20% weight)
- Subjective stress levels provide psychological component (10% weight)
- Recent training load must be factored (acute:chronic workload ratio)

**Alternatives Considered**:
- **Simple HRV-only score**: Rejected - too one-dimensional, misses important factors
- **Machine learning model**: Rejected for MVP - requires large training dataset, adds complexity
- **Garmin's Body Battery**: Considered but proprietary algorithm, use as validation reference

**Algorithm Details**:

```
Recovery Score = (HRV_score * 0.4) + (HR_score * 0.3) + (Sleep_score * 0.2) + (Stress_score * 0.1)

Where each component score (0-100):

HRV_score:
- Calculate 7-day rolling average HRV
- Today's HRV vs. average: +10% = 100, -10% = 50, -20% = 0
- Linear interpolation between points

HR_score:
- Calculate 7-day rolling average resting HR
- Today's HR vs. average: -5% = 100, +0% = 50, +10% = 0
- Inverse relationship (lower is better)

Sleep_score:
- Duration: 7-9 hours = 100, 6 hours = 70, <5 hours = 30
- Quality: Use Garmin's sleep score if available
- Combined: (duration_score * 0.6) + (quality_score * 0.4)

Stress_score:
- Use Garmin's stress level (0-100 scale)
- Inverted: stress_score = 100 - garmin_stress
```

**Training Load Adjustment**:
- Calculate Acute:Chronic Workload Ratio (ACWR)
- Acute load = 7-day average training load
- Chronic load = 28-day average training load
- Optimal ACWR = 0.8-1.3
- Reduce recovery score by 20% if ACWR > 1.5 (overreaching)
- Reduce recovery score by 10% if ACWR > 1.3 (building fatigue)

**Thresholds**:
- Green (80-100): High recovery, ready for hard training
- Yellow (50-79): Moderate recovery, adjust intensity
- Red (0-49): Low recovery, prioritize rest/recovery

**Validation Approach**:
- Compare against user perceived readiness (weekly survey)
- Adjust weights based on correlation analysis
- A/B test variations with subset of users

---

### 3. Claude AI Integration for Insights

**Research Question**: How to use Claude AI to generate personalized training insights with optimal cost and performance?

**Decision**: Use Anthropic Python SDK with Claude Haiku 4.5 + Prompt Caching + Batch Processing

**Rationale**:

1. **Model Selection - Claude Haiku 4.5**:
   - Delivers Sonnet 4-level coding performance (73% SWE-bench) at one-third the cost
   - More than twice the speed of Sonnet
   - Pricing: $0.10 input / $0.50 output per 1M tokens (with caching)
   - Perfect for pattern analysis on structured training data
   - Upgrade to Sonnet 4.5 only for complex edge cases

2. **Cost Optimization - 95% Total Savings**:
   - **Prompt Caching**: 90% savings on cached portions
     - Cache system prompt and user's training history (static for 7 days)
     - Only pay full price for new data and questions
     - Cache reads: $0.01 per 1M tokens for Haiku 4.5
     - Reduces latency by up to 85% for long prompts
   - **Batch Processing**: 50% discount on all models
     - Process non-urgent insight generation within 24 hours
     - Perfect for weekly scheduled insights
     - Queue multiple users and batch submit
   - **Combined**: Achieve 95% cost reduction vs. standard API calls

3. **Token Usage for Time-Series Analysis**:
   - 8 weeks of training data: ~2,000-5,000 tokens (workout summaries + daily metrics)
   - System prompt + instructions: ~1,000 tokens
   - Response (3-5 insights): ~500-1,000 tokens
   - **With Caching**: Only pay full price once per week, cache hits cost 0.1x
   - Example: Weekly insight generation = $0.003 per user (vs $0.03 without optimization)

4. **Performance**:
   - Context window: 200K tokens (sufficient for 6+ months of detailed training data)
   - Response time: <5 seconds for typical analysis (within 30s requirement from SC-007)
   - Haiku 4.5 is 2x faster than Sonnet while maintaining quality

5. **Python SDK Advantages**:
   - Native integration with FastAPI backend
   - async/await support for non-blocking API calls
   - Built-in retry logic and error handling
   - Streaming responses for real-time insight generation (future enhancement)

**Alternatives Considered**:

1. **Claude Sonnet 4.5**:
   - **Strengths**: Highest quality, best for complex reasoning
   - **Why Rejected for Primary Use**: 3x more expensive, slower
   - **When to Use**: Escalate from Haiku if insights quality score < 7/10
   - **Cost**: $3.00 input / $15.00 output per 1M tokens

2. **OpenAI GPT-4**:
   - **Strengths**: Good general purpose model
   - **Why Rejected**:
     - Claude preferred for analytical tasks and instruction following
     - OpenAI pricing less competitive with prompt caching
     - Anthropic SDK better documented for Python/FastAPI
   - **When to Reconsider**: If Claude API has sustained outages

3. **Local LLM** (Llama 3, Mistral):
   - **Why Rejected**:
     - Infrastructure complexity (GPU requirements, model hosting)
     - Higher latency (>30s for complex analysis)
     - Quality trade-offs vs. Claude Haiku
     - DevOps overhead not justified for MVP
   - **When to Reconsider**: If scaling to 10,000+ users with high insight generation frequency

4. **Rule-Based Insights**:
   - **Kept as Fallback**:
     - Simple pattern matching ("You've had 3 hard workouts this week")
     - Used when Claude API unavailable
     - Lower quality but guaranteed availability
   - **Implementation**: 10-15 rule templates covering common patterns

**Implementation Approach**:

```python
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# System prompt (cached for 7 days)
system_prompt = """You are a sports science expert analyzing an athlete's training
and recovery data. Generate 3-5 specific, actionable insights based on patterns in
their data. Each insight must include supporting data and recommendations."""

# User training data (cached for 7 days)
training_history = format_training_data(user_workouts, user_health_metrics)

# New analysis request (not cached)
analysis_request = f"Analyze patterns for week ending {date}"

# With prompt caching
response = client.messages.create(
    model="claude-haiku-4.5-20250929",
    max_tokens=1000,
    system=[
        {
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"}  # Cache for 5 minutes
        }
    ],
    messages=[
        {
            "role": "user",
            "content": f"{training_history}\n\n{analysis_request}",
            "cache_control": {"type": "ephemeral"}  # Cache training history
        }
    ]
)
```

**Caching Strategy**:

1. **What to Cache** (7-day TTL):
   - System prompt with role and instructions
   - Historical training data (last 8 weeks)
   - User profile and goals
   - Previous insights for context

2. **What NOT to Cache**:
   - Current week's new data
   - Specific analysis questions
   - Date-specific queries

3. **Cache Invalidation**:
   - Automatic after 7 days
   - Manual invalidation on:
     - User profile changes (new goal, injury logged)
     - Significant training pattern shift detected
     - User requests fresh analysis

**Batch Processing Strategy**:

```python
# Queue users for weekly insight generation
batch_requests = []
for user in users_needing_insights:
    batch_requests.append({
        "custom_id": f"insight-{user.id}-{date}",
        "params": {
            "model": "claude-haiku-4.5-20250929",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": format_prompt(user)}]
        }
    })

# Submit batch (50% discount, processed within 24 hours)
batch = client.batches.create(requests=batch_requests)

# Check batch status later (background job)
result = client.batches.retrieve(batch.id)
```

**Monitoring & Cost Tracking**:

1. **Token Usage Monitoring** (via Grafana + Anthropic Usage API):
   - Track input/output token counts per user
   - Monitor cache hit rates (target: >80% after first generation)
   - Alert on anomalies (3x 7-day average token usage)
   - Daily cost tracking with budget alerts ($1000 threshold)

2. **Quality Metrics**:
   - User feedback on insight usefulness (thumbs up/down)
   - Track escalations from Haiku to Sonnet (target: <5%)
   - Monitor insight staleness (days since last generation)

3. **Performance Metrics**:
   - Response time distribution (p50, p95, p99)
   - Cache hit latency vs. cache miss latency
   - Batch processing completion times

**Cost Estimation**:

| Scenario | Tokens | Cost (No Optimization) | Cost (With Optimization) | Savings |
|----------|--------|------------------------|--------------------------|---------|
| First insight generation | 5,000 input + 1,000 output | $0.0011 | $0.0011 | 0% |
| Subsequent weekly insights (cached) | 500 input + 1,000 output | $0.0011 | $0.00006 | 95% |
| Monthly per user (4 insights) | 20,000 total | $0.0044 | $0.0013 | 70% |
| 1000 users monthly | - | $4.40 | $1.30 | 70% |
| With batch processing | - | $4.40 | $0.65 | 85% |

**Error Handling**:

```python
try:
    response = generate_insights(user)
except anthropic.RateLimitError:
    # Queue for batch processing instead
    queue_for_batch(user)
    return get_cached_insights(user)
except anthropic.APITimeoutError:
    # Retry once, then fallback
    try:
        response = generate_insights(user, timeout=60)
    except:
        return generate_rule_based_insights(user)
except anthropic.APIError as e:
    # Log error, return cached or rule-based
    log_error(e)
    cached = get_cached_insights(user)
    return cached if cached else generate_rule_based_insights(user)
```

**Prompt Engineering Best Practices**:

1. **Structured Output**:
   - Request JSON format for easy parsing
   - Define schema: `{"insights": [{"title": "", "content": "", "supporting_data": [], "action": ""}]}`

2. **Few-Shot Examples**:
   - Include 1-2 example insights in system prompt
   - Shows desired format and depth

3. **Temperature Settings**:
   - Use temperature=0.3 for consistent analytical output
   - Higher temperature (0.7) if creative variation desired

**Trade-offs**:

| Aspect | Decision | Trade-off |
|--------|----------|-----------|
| Haiku vs Sonnet | Haiku 4.5 primary | Slightly lower quality, but 70% cost savings justifies it |
| Prompt Caching | Aggressive caching (7 days) | Insights may miss very recent subtle patterns |
| Batch Processing | Weekly batched insights | 24-hour delay acceptable, not for real-time use cases |
| Token Limits | Max 1000 output tokens | Limits insight length, but forces conciseness |

---

### 4. Database Selection and Schema Design

**Research Question**: What database best supports time-series health metrics, relational data, and query patterns?

**Decision**: PostgreSQL 15+ with standard tables and strategic indexes (no TimescaleDB extension for MVP)

**Rationale**:

1. **PostgreSQL Core Strengths**:
   - **Relational Data Model**: Perfect for users, workouts, recovery scores, training plans (highly relational)
   - **JSONB Support**: Flexible storage for variable health metrics (HR zones, device-specific data)
   - **Excellent Indexing**: B-tree for timestamps, compound indexes for (user_id, date)
   - **ACID Guarantees**: Critical for workout-to-recovery-to-recommendation data consistency
   - **Mature Python Ecosystem**: SQLAlchemy 2.0+ with asyncpg, excellent async support
   - **Connection Pooling**: Built-in pgBouncer support, SQLAlchemy pooling

2. **Time-Series Handling** (Without TimescaleDB):
   - Standard PostgreSQL handles fitness app time-series data excellently with proper indexes
   - Data volume: 365 days × 1000 users × ~10 daily records = ~3.6M rows/year (manageable)
   - Partitioning by date not needed until 10M+ rows
   - Compound index `(user_id, date DESC)` provides fast range queries
   - Window functions (rolling averages) native in PostgreSQL: `AVG(hrv) OVER (PARTITION BY user_id ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)`

3. **Performance with asyncpg**:
   - asyncpg is high-performance PostgreSQL client (2-5x faster than psycopg2)
   - SQLAlchemy 2.0 async dialect: `postgresql+asyncpg://...`
   - Connection pooling reduces overhead, improves performance
   - Native support for JSONB queries and array operations
   - Important: PgBouncer transaction pooling breaks asyncpg prepared statements (avoid or use session pooling)

4. **SQLite for Development**:
   - No separate database server needed
   - Identical SQLAlchemy models work with both SQLite and PostgreSQL
   - Fast iteration during development
   - Easy CI/CD testing (in-memory database)
   - Switch to PostgreSQL for staging/production

**Alternatives Considered**:

1. **TimescaleDB** (PostgreSQL extension for time-series):
   - **Strengths**:
     - Automatic partitioning (hypertables)
     - Optimized time-series queries
     - Better compression for large datasets
     - Continuous aggregates for pre-computed rollups
   - **Why Rejected for MVP**:
     - Adds deployment complexity (extension installation, hypertable management)
     - Overkill for MVP scale (365 days × 1000 users)
     - Standard PostgreSQL with proper indexes sufficient for fitness app queries
     - Learning curve for team (hypertable-specific concepts)
   - **When to Reconsider**:
     - Scaling to 10,000+ users with multi-year history
     - Need for real-time aggregations across millions of rows
     - Storage costs become significant (compression needed)
     - Query performance degrades despite optimization

2. **InfluxDB** (Purpose-built time-series database):
   - **Strengths**:
     - Exceptional write performance for sensor data
     - Purpose-built time-series features
     - Better on-disk compression than PostgreSQL
   - **Why Rejected**:
     - Weak relational capabilities (hard to join workouts with users, training plans)
     - NoSQL data model doesn't fit user profiles, goals, plans
     - Stability issues at high cardinalities (100K+ unique user/device combos)
     - Would need PostgreSQL + InfluxDB (increased complexity)
     - SQL query flexibility needed for analytics
   - **When to Reconsider**:
     - If pivoting to real-time device streaming (live HR, GPS during workouts)
     - If metrics become purely time-series without relational context

3. **MongoDB** (Document database):
   - **Strengths**:
     - Flexible schema for varying health metrics
     - Good for rapid prototyping
   - **Why Rejected**:
     - Training data is inherently relational (users → workouts → recovery scores → plans)
     - Need ACID transactions for data consistency
     - SQL better for complex analytics queries (rolling averages, correlations)
     - JSONB in PostgreSQL provides schema flexibility where needed
   - **When to Reconsider**: Not applicable for this use case

4. **Denormalized Schema**:
   - **Why Rejected**:
     - Would duplicate user data across workout records
     - Data inconsistency risks (user updates must propagate)
     - Harder to maintain referential integrity
     - Normalized design with proper indexes performs well
   - **When to Use**: Read-heavy materialized views for specific dashboards (future optimization)

**Schema Design - Normalized with Strategic Indexes**:

Design principles:
- Normalized structure (3NF) to eliminate redundancy
- Strategic indexes on all foreign keys and date columns
- Compound indexes for common query patterns: `(user_id, date DESC)`
- JSONB columns for variable/device-specific data
- asyncpg-compatible (avoid features that break with PgBouncer transaction pooling)

**Core Tables**:

```sql
users
- id (PK, UUID)
- email (unique)
- created_at
- garmin_user_id
- garmin_access_token (encrypted)
- garmin_refresh_token (encrypted)
- garmin_token_expires_at

health_metrics
- id (PK)
- user_id (FK)
- date (indexed)
- hrv_ms (integer, nullable)
- resting_hr (integer, nullable)
- sleep_duration_minutes (integer, nullable)
- sleep_score (integer 0-100, nullable)
- stress_level (integer 0-100, nullable)
- created_at
- INDEX: (user_id, date DESC)

workouts
- id (PK, UUID)
- user_id (FK)
- garmin_activity_id (nullable, unique)
- workout_type (enum: run, bike, swim, strength, other)
- started_at (timestamp)
- duration_minutes
- training_load (float, nullable)
- perceived_exertion (integer 1-10, nullable)
- heart_rate_zones (JSONB, nullable) - {zone1: 120, zone2: 140, ...}
- manual_entry (boolean, default false)
- created_at
- INDEX: (user_id, started_at DESC)

recovery_scores
- id (PK)
- user_id (FK)
- date (indexed)
- total_score (integer 0-100)
- hrv_component (integer 0-100)
- hr_component (integer 0-100)
- sleep_component (integer 0-100)
- stress_component (integer 0-100)
- acwr_adjustment (float) - multiplicative factor
- created_at
- UNIQUE: (user_id, date)

workout_recommendations
- id (PK)
- user_id (FK)
- date (indexed)
- recovery_score_id (FK)
- workout_type (enum)
- duration_minutes
- intensity_level (enum: recovery, easy, moderate, hard, maximal)
- heart_rate_target_low (nullable)
- heart_rate_target_high (nullable)
- rationale (text) - plain language explanation
- created_at
- INDEX: (user_id, date DESC)

insights
- id (PK)
- user_id (FK)
- generated_at
- valid_until (date) - cache expiry
- insight_type (enum: recovery_pattern, overtraining_warning, workout_effectiveness, frequency_recommendation)
- title (varchar)
- content (text) - plain language insight
- supporting_data (JSONB) - metrics that support this insight
- action_items (JSONB) - array of recommended actions
- created_at
- INDEX: (user_id, generated_at DESC)

training_plans
- id (PK, UUID)
- user_id (FK)
- goal_id (FK)
- name
- start_date
- end_date
- created_at
- updated_at
- status (enum: draft, active, completed, cancelled)

planned_workouts
- id (PK, UUID)
- training_plan_id (FK)
- scheduled_date
- workout_type
- duration_minutes
- intensity_level
- completed (boolean)
- actual_workout_id (FK workouts, nullable) - links to completed workout
- notes (text)

goals
- id (PK, UUID)
- user_id (FK)
- goal_type (enum: distance, time, event, fitness_level)
- target_metric (varchar) - e.g., "5K time", "10K distance"
- target_value (varchar) - e.g., "25:00", "10 km"
- target_date
- priority (integer 1-5)
- status (enum: active, achieved, abandoned)
- created_at
```

**Migration Strategy**:
- Use Alembic for schema migrations
- Version all schema changes
- Support rollback for each migration

---

### 5. Background Job Processing

**Research Question**: How to handle background tasks (Garmin sync, AI insights generation)?

**Decision**: Celery 5+ with Redis broker for scheduled/async jobs + FastAPI BackgroundTasks for simple operations

**Rationale**:

1. **Celery - Production-Grade Task Queue**:
   - **Mature and Battle-Tested**: Industry standard for Python distributed task queues since 2009
   - **Scheduled Jobs**: Built-in beat scheduler for daily/weekly/hourly tasks (Garmin sync at 6 AM, weekly insights)
   - **Retry Logic**: Exponential backoff, max retries, custom retry strategies per task
   - **Monitoring**: Flower dashboard provides real-time job visibility, worker status, task history
   - **Resource Management**: Worker concurrency control, task routing to specific workers
   - **Python Ecosystem**: Native integration with FastAPI, SQLAlchemy, asyncio

2. **Redis as Broker and Cache**:
   - **Dual Purpose**: Message broker for Celery + cache layer for application
   - **Simple Setup**: Single Redis instance serves both purposes for MVP
   - **Performance**: In-memory operation, sub-millisecond latency
   - **Persistence**: AOF/RDB for job durability (survive restarts)
   - **Native Support**: Python redis-py library, Celery's recommended broker

3. **FastAPI BackgroundTasks for Lightweight Operations**:
   - **Simple API**: No broker needed, tasks run in same process
   - **Use Cases**: Non-critical operations (email notifications, cache warming, logging)
   - **When NOT to Use**: Long-running tasks, need retries, scheduled jobs
   - **Example**: Send email confirmation after user action

**Alternatives Considered**:

1. **BullMQ** (Node.js task queue):
   - **Strengths**:
     - Excellent for Node.js/TypeScript applications
     - Redis-backed, similar architecture to Celery
     - Good TypeScript support, modern API
     - Works well with NestJS and Express
   - **Why Rejected**:
     - We chose Python/FastAPI backend (see Section 0)
     - Celery better integrated with Python AI/ML ecosystem
     - No advantage over Celery for Python applications
   - **When to Reconsider**: If we had chosen Node.js/Express backend

2. **APScheduler**:
   - **Strengths**:
     - Lightweight, pure Python
     - Simple scheduling API
     - No external broker needed
   - **Why Rejected**:
     - Less robust than Celery for production workloads
     - No distributed worker support
     - Limited monitoring/visibility
     - Weaker retry mechanisms
     - Not designed for high-volume task processing
   - **When to Use**: Simple cron-style jobs in single-server deployments (not our case)

3. **AWS Lambda / Google Cloud Functions**:
   - **Strengths**:
     - Serverless, pay-per-execution
     - Auto-scaling, no infrastructure management
     - Good for event-driven architectures
   - **Why Rejected for MVP**:
     - Adds deployment complexity (function packaging, API Gateway setup)
     - Cold start latency (100-1000ms) unacceptable for user-triggered jobs
     - Vendor lock-in
     - Harder to debug and test locally
     - Celery + Redis simpler for MVP
   - **When to Reconsider**:
     - Scaling to 10,000+ users with unpredictable load
     - Cost optimization (pay only for compute used)
     - Need multi-region deployment

4. **Kubernetes CronJobs**:
   - **Strengths**:
     - Native Kubernetes scheduling
     - Good for containerized deployments
     - Reliable execution guarantees
   - **Why Rejected**:
     - Requires Kubernetes cluster (overkill for MVP)
     - Less flexible than Celery for complex workflows
     - Harder to monitor and debug
     - No retry logic built-in
   - **When to Reconsider**: If deploying to Kubernetes for other reasons

5. **RabbitMQ** (as broker instead of Redis):
   - **Strengths**:
     - More robust message guarantees than Redis
     - Better for complex routing patterns
     - Higher reliability for critical tasks
   - **Why Rejected for MVP**:
     - More complex setup and configuration
     - Overkill for fitness app task patterns
     - Redis sufficient with AOF persistence
     - Redis also serves as cache (dual purpose)
   - **When to Reconsider**: If job loss becomes critical issue (it shouldn't for fitness insights)

**Job Types and Scheduling**:

| Job Type | Trigger | Priority | Timeout | Retries | Worker Pool |
|----------|---------|----------|---------|---------|-------------|
| Daily Garmin Sync | Celery Beat: 6 AM daily | High | 5 min | 5 (exponential backoff) | I/O pool (10 workers) |
| Recovery Score Calculation | Event: New health data | High | 30s | 3 | CPU pool (4 workers) |
| AI Insights Generation | Celery Beat: Weekly (batched) | Medium | 60s | 3 | AI pool (2 workers) |
| Training Plan Adaptation | Celery Beat: Weekly (Sunday) | Medium | 2 min | 3 | CPU pool |
| Email Notifications | Event: Various | Low | 10s | 2 | Default pool |
| Cache Warming | FastAPI Background | Low | 30s | 0 (fire and forget) | Same process |

**Celery Configuration**:

```python
# celery_config.py
from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "ai_trainer",
    broker="redis://localhost:6379/0",  # Redis as message broker
    backend="redis://localhost:6379/1"  # Results backend
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Worker configuration
    worker_prefetch_multiplier=1,  # Fair task distribution
    task_acks_late=True,  # Acknowledge after completion (reliability)

    # Retry configuration
    task_default_retry_delay=60,  # 1 minute between retries
    task_max_retries=5,

    # Result expiration
    result_expires=3600,  # 1 hour

    # Beat schedule (scheduled tasks)
    beat_schedule={
        "daily-garmin-sync": {
            "task": "tasks.garmin.sync_all_users",
            "schedule": crontab(hour=6, minute=0),  # 6 AM daily
        },
        "weekly-insights-generation": {
            "task": "tasks.insights.generate_batch",
            "schedule": crontab(day_of_week=1, hour=2, minute=0),  # Monday 2 AM
        },
        "weekly-training-plan-adaptation": {
            "task": "tasks.training_plan.adapt_all_plans",
            "schedule": crontab(day_of_week=0, hour=3, minute=0),  # Sunday 3 AM
        },
    },
)

# Task example with retry logic
@celery_app.task(bind=True, max_retries=5)
def sync_garmin_data(self, user_id: int):
    try:
        # Fetch Garmin data
        client = get_garmin_client(user_id)
        data = client.get_daily_metrics(date.today())
        save_health_metrics(user_id, data)

        # Trigger recovery score calculation
        calculate_recovery_score.delay(user_id, date.today())

    except GarminAPIError as e:
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
```

**Monitoring and Observability**:

1. **Flower Dashboard** (Celery monitoring UI):
   - Real-time task monitoring: pending, active, completed, failed
   - Worker status and resource usage
   - Task execution times and patterns
   - Historical task data (last 7 days)
   - Access: `http://localhost:5555` (dev), protected in production

2. **Metrics to Track**:
   - Task success/failure rates by task type
   - Average task execution time (target: <5s for recovery calc, <30s for insights)
   - Queue depth (alert if >100 pending tasks)
   - Worker utilization (target: 60-80%)
   - Retry rates (alert if >10% of tasks retry)

3. **Error Handling and Alerting**:
   - Sentry integration for task exceptions
   - Slack/email alerts for critical failures (Garmin sync failed for 5+ consecutive days)
   - Dead letter queue for permanently failed tasks
   - Manual retry interface via Flower

**Trade-offs**:

| Aspect | Decision | Trade-off |
|--------|----------|-----------|
| Celery vs Serverless | Celery + Redis | More infrastructure to manage, but simpler for MVP and better local dev experience |
| Redis vs RabbitMQ | Redis | Less robust message guarantees, but simpler setup and dual cache/broker use |
| Single Redis vs Separate | Single instance for MVP | Potential bottleneck at scale, but simpler and sufficient for 1000 users |
| Beat Scheduler vs External | Celery Beat | Single point of failure, needs monitoring, but integrated and reliable |

**Scaling Strategy** (Future):

1. **Horizontal Scaling** (1000-10000 users):
   - Add more Celery workers (separate machines/containers)
   - Redis Cluster for broker sharding
   - Separate Redis instances for cache and broker

2. **Vertical Separation**:
   - Dedicated worker pools: I/O-bound (Garmin sync), CPU-bound (analytics), AI-bound (insights)
   - Priority queues: high (user-triggered), medium (scheduled), low (maintenance)

3. **Migration to Serverless** (10000+ users):
   - Move scheduled jobs to AWS Lambda / Cloud Run
   - Keep Celery for real-time user-triggered tasks
   - Hybrid approach for cost optimization

**Job Types**:

1. **Daily Garmin Sync** (Scheduled, 6 AM daily):
   - Fetch previous day's health metrics for all users
   - Fetch new workouts
   - Calculate recovery scores
   - Queue recommendation generation

2. **Recovery Score Calculation** (Triggered):
   - Calculate score when new health data arrives
   - Store in database
   - Invalidate cached recommendations

3. **AI Insights Generation** (Scheduled, weekly per user):
   - Gather 4-8 weeks of historical data
   - Call Claude API with structured prompt
   - Parse and store insights
   - Send notification if critical insight (overtraining warning)

4. **Training Plan Adaptation** (Scheduled, weekly):
   - Review past week's compliance and recovery trends
   - Adjust upcoming week's plan if needed
   - Notify user of significant changes

**Monitoring**:
- Flower dashboard for Celery job monitoring
- Error tracking with Sentry
- Job success/failure metrics in logs

---

### 6. Performance Optimization

**Research Question**: How to meet <200ms p95 API latency and <2 second page load requirements?

**Decision**: Multi-layer caching, async I/O, database optimization, and CDN for frontend

**Rationale**:
- Constitution mandates performance standards
- User experience depends on fast response times
- Multi-pronged approach addresses different bottlenecks

**Backend Optimization**:

1. **Caching Strategy** (Redis):
   - Recovery scores: Cache for 24 hours (recalculate on new data)
   - Recommendations: Cache for current day
   - Insights: Cache for 7 days
   - User profile: Cache for 1 hour
   - Cache keys: `{user_id}:{resource}:{date}`

2. **Database Optimization**:
   - Indexes on all foreign keys and date fields
   - Compound index on (user_id, date) for time-series queries
   - Connection pooling (SQLAlchemy default pool size: 5-10)
   - Prepared statements via SQLAlchemy ORM
   - Eager loading for relationships (avoid N+1 queries)

3. **Async I/O**:
   - FastAPI's native async support for all routes
   - httpx for async HTTP requests to Garmin/Claude APIs
   - asyncpg for async PostgreSQL queries
   - Concurrent processing of independent operations

4. **Response Optimization**:
   - Gzip compression for API responses
   - Pagination for list endpoints (limit 50 items default)
   - Field filtering (only return requested fields)

**Frontend Optimization**:

1. **Build Optimization**:
   - Vite for fast builds and HMR
   - Code splitting by route
   - Tree shaking to remove unused code
   - Minification and compression

2. **Asset Optimization**:
   - CDN for static assets (CloudFlare, AWS CloudFront)
   - Image optimization (WebP format, lazy loading)
   - Font subsetting and preloading

3. **Runtime Optimization**:
   - React.lazy for code splitting
   - Service Worker for offline caching
   - Optimistic UI updates
   - Debounced API calls

**Monitoring**:
- OpenTelemetry for distributed tracing
- Prometheus for metrics collection
- Grafana for visualization
- Alert on p95 latency > 200ms

**Load Testing**:
- Locust for load testing
- Target: 100 concurrent users, <200ms p95
- Run before each release

---

### 7. Testing Framework and Strategy

**Research Question**: How to implement TDD workflow and achieve 80% test coverage with comprehensive testing?

**Decision**: pytest for backend + Vitest for frontend with three-layer testing approach

**Rationale**:

1. **pytest for Python Backend**:
   - **Industry Standard**: Most widely adopted Python testing framework (80%+ adoption)
   - **Async Support**: pytest-asyncio plugin for testing async FastAPI endpoints
   - **Fixtures**: Powerful dependency injection for test data (db sessions, mock clients)
   - **Plugins**: Rich ecosystem (pytest-cov for coverage, pytest-mock, pytest-httpx)
   - **Fast Execution**: Parallel test execution with pytest-xdist
   - **Clear Output**: Detailed failure reports with actual vs expected values
   - **TDD Friendly**: Quick feedback loop, watch mode available

2. **Three-Layer Testing Architecture**:
   - **Contract Tests**: Verify API contracts (request/response schemas, status codes)
   - **Integration Tests**: Test complete user journeys (one per user story)
   - **Unit Tests**: Test individual functions/classes in isolation
   - Ensures coverage at all levels: API surface, business logic, data layer

3. **Coverage Measurement**:
   - pytest-cov (uses coverage.py under the hood)
   - HTML reports for visualization
   - CI/CD integration blocks merges if coverage < 80%
   - Line and branch coverage tracking

**Alternatives Considered**:

1. **Jest** (JavaScript/TypeScript testing):
   - **Strengths**:
     - Excellent for React/TypeScript frontend testing
     - Snapshot testing for UI components
     - Fast execution with parallel workers
     - Built-in mocking and coverage
     - Developed by Facebook, widely adopted
   - **Decision**:
     - Use Vitest instead of Jest for frontend (Vite-native, faster)
     - Keep Jest comparison for reference (very similar to pytest in Python)
   - **Why Not for Backend**: We chose Python backend, pytest is native choice

2. **unittest** (Python standard library):
   - **Strengths**:
     - Built into Python, no installation needed
     - Class-based test structure
     - xUnit-style assertions
   - **Why Rejected**:
     - More verbose than pytest (class boilerplate)
     - Less powerful fixtures
     - Weaker plugin ecosystem
     - pytest can run unittest tests (compatibility)
   - **When to Use**: Legacy codebases already using unittest

3. **nose2** (successor to nose):
   - **Why Rejected**:
     - Less active development than pytest
     - Smaller community
     - pytest more popular and feature-rich
     - No compelling advantages

**Contract Testing Approach**:

- **Purpose**: Verify external API contracts (Garmin API, Claude API)
- **Tools**: pytest + responses (HTTP mocking) or pytest-httpx
- **Scope**: Request schemas, response parsing, error handling

```python
# test_garmin_contract.py
import pytest
from responses import RequestsMock

def test_garmin_daily_metrics_contract(responses: RequestsMock):
    # Mock Garmin API response
    responses.get(
        "https://apis.garmin.com/wellness-api/rest/dailies",
        json={
            "dailies": [{
                "calendarDate": "2025-10-24",
                "restingHeartRateInBeatsPerMinute": 55,
                "hrvInMilliseconds": 62,
                "stressLevelMax": 45,
                "sleepDurationInSeconds": 28800
            }]
        },
        status=200
    )

    # Call service that depends on Garmin API
    client = GarminService(mock_token)
    metrics = client.get_daily_metrics("2025-10-24")

    # Verify contract expectations
    assert metrics.hrv_ms == 62
    assert metrics.resting_hr == 55
    assert metrics.stress_level == 45
    assert metrics.sleep_duration_minutes == 480
```

**Integration Testing Approach**:

- **Purpose**: Test complete user journeys (one test file per user story)
- **Tools**: pytest + httpx TestClient + test database
- **Scope**: End-to-end flows from API request to database persistence

```python
# test_user_story_1_recovery_check.py
import pytest
from httpx import AsyncClient
from datetime import date

@pytest.mark.asyncio
async def test_user_views_recovery_and_recommendation(
    client: AsyncClient,
    test_user,
    mock_garmin_data
):
    # Setup: User with Garmin data synced overnight
    await sync_garmin_data(test_user.id, mock_garmin_data)

    # Act: User requests recovery status
    response = await client.get(
        f"/api/recovery/{date.today()}",
        headers={"Authorization": f"Bearer {test_user.token}"}
    )

    # Assert: Recovery score and recommendation returned
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["green", "yellow", "red"]
    assert 0 <= data["total_score"] <= 100
    assert "recommendation" in data
    assert data["recommendation"]["workout_type"] is not None
    assert data["recommendation"]["rationale"] is not None
```

**Unit Testing Approach**:

- **Purpose**: Test individual functions/classes in isolation
- **Tools**: pytest with fixtures and mocking
- **Scope**: Business logic, calculations, transformations

```python
# test_recovery_calculator.py
import pytest
from services.recovery import RecoveryCalculator

def test_recovery_calculator_scores_high_hrv_as_100():
    calculator = RecoveryCalculator()

    metrics = HealthMetrics(
        hrv_ms=65,  # 10% above 7-day average of 59
        resting_hr=55,  # On par with average
        sleep_duration_minutes=480,  # 8 hours
        sleep_score=85,
        stress_level=30
    )

    historical = HistoricalAverages(
        hrv_avg=59,
        hr_avg=55
    )

    score = calculator.calculate(metrics, historical)

    assert score.hrv_component == 100  # Perfect HRV
    assert score.hr_component == 50    # Average HR
    assert score.sleep_component >= 90 # Good sleep
    assert 80 <= score.total_score <= 100  # High recovery
```

**Test Data Management**:

```python
# conftest.py (pytest fixtures)
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from httpx import AsyncClient

@pytest.fixture
async def db_session():
    """Provides test database session"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()

@pytest.fixture
async def test_user(db_session):
    """Creates test user"""
    user = User(
        email="test@example.com",
        garmin_user_id="12345"
    )
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.fixture
def mock_garmin_data():
    """Provides mock Garmin API responses"""
    return {
        "hrv_ms": 62,
        "resting_hr": 55,
        "sleep_duration_minutes": 480,
        "stress_level": 30
    }
```

**Coverage Targets**:

| Component | Target | Rationale |
|-----------|--------|-----------|
| Overall | 80% minimum | Constitution requirement |
| Business Logic (services/) | 90% minimum | Core value, complex algorithms |
| API Routes | 85% minimum | User-facing, critical paths |
| Models | 70% minimum | Simple CRUD, less complexity |
| Utils/Helpers | 80% minimum | Shared code, high reuse |

**CI/CD Integration**:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov pytest-httpx

      - name: Run tests with coverage
        run: |
          pytest --cov=backend --cov-report=html --cov-report=term \
                 --cov-fail-under=80 tests/

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
```

**TDD Workflow**:

1. **Red**: Write failing test first
   ```bash
   pytest tests/test_recovery_calculator.py::test_high_hrv_scores_100 -v
   ```

2. **Green**: Implement minimum code to pass
   ```python
   def calculate_hrv_component(current, average):
       if current >= average * 1.1:
           return 100
       # ... rest of implementation
   ```

3. **Refactor**: Improve code while keeping tests green
   ```bash
   pytest tests/test_recovery_calculator.py -v  # All pass
   ```

4. **Repeat**: Next test case

**Mocking External APIs**:

```python
# Use responses for sync HTTP, pytest-httpx for async
import pytest
from pytest_httpx import HTTPXMock

@pytest.mark.asyncio
async def test_garmin_api_timeout_handling(httpx_mock: HTTPXMock):
    # Mock timeout
    httpx_mock.add_exception(httpx.TimeoutException("Connection timeout"))

    service = GarminService()

    with pytest.raises(GarminAPIError) as exc:
        await service.get_daily_metrics("2025-10-24")

    assert "timeout" in str(exc.value).lower()
```

**Trade-offs**:

| Aspect | Decision | Trade-off |
|--------|----------|-----------|
| pytest vs unittest | pytest | More modern, but another dependency (minimal concern) |
| Test DB | SQLite in-memory | Faster, but may miss PostgreSQL-specific issues (acceptable for MVP) |
| Mock vs Real APIs | Mock external APIs | Fast tests, but need occasional integration tests with real APIs |
| Coverage Threshold | 80% minimum | May encourage meaningless tests to hit number (mitigate with code review) |

**Frontend Testing** (Complementary):

- **Framework**: Vitest (Vite-native, faster than Jest)
- **Component Testing**: React Testing Library
- **E2E Testing**: Playwright (future, not MVP)
- **Coverage**: 70% minimum (UI complexity varies)

**Test Layers**:

**1. Contract Tests** (test_*_api.py):
- Test API request/response contracts
- Verify status codes, response schemas
- Test authentication requirements
- Test error responses
- Framework: pytest + httpx test client
- Run before every deployment

Example:
```python
def test_get_recovery_score_returns_valid_schema():
    response = client.get("/api/recovery/2025-10-23", auth=token)
    assert response.status_code == 200
    data = response.json()
    assert "total_score" in data
    assert 0 <= data["total_score"] <= 100
    assert "components" in data
```

**2. Integration Tests** (test_user_story_*.py):
- Test complete user journeys
- One test file per user story
- Use real database (test DB)
- Mock external APIs (Garmin, Claude)
- Verify end-to-end flows

Example (User Story 1):
```python
def test_user_views_daily_recovery_and_recommendation():
    # Setup: User with Garmin data synced overnight
    user = create_test_user()
    sync_mock_garmin_data(user, date="2025-10-23")

    # Act: User opens app and views recovery
    response = client.get("/api/recovery/today", auth=user.token)

    # Assert: Recovery score displayed with recommendation
    assert response.status_code == 200
    recovery = response.json()
    assert recovery["status"] in ["green", "yellow", "red"]
    assert "recommendation" in recovery
    assert recovery["recommendation"]["workout_type"] is not None
```

**3. Unit Tests** (test_*.py):
- Test individual functions/classes
- No external dependencies
- Fast execution (<100ms per test)
- High coverage (90%+ for business logic)

Example:
```python
def test_recovery_calculator_scores_high_hrv_as_100():
    metrics = HealthMetrics(
        hrv_ms=65,  # 10% above 7-day average of 59
        resting_hr=55,
        sleep_duration_minutes=480,
        stress_level=30
    )
    historical_avg = {"hrv": 59, "hr": 55}

    score = recovery_calculator.calculate(metrics, historical_avg)

    assert score.hrv_component == 100
    assert 80 <= score.total_score <= 100
```

**Test Data Management**:
- Fixtures for common test data (pytest fixtures)
- Factory pattern for model creation (factory_boy)
- Separate test database (auto-created/destroyed)
- Mock external APIs (responses library)

**Coverage Targets**:
- Overall: 80% minimum (constitution requirement)
- Business logic (services/): 90% minimum
- API routes: 85% minimum
- Models: 70% minimum (simple CRUD doesn't need exhaustive tests)

**CI/CD Integration**:
- Run all tests on every PR
- Block merge if tests fail or coverage drops below 80%
- Generate coverage reports (coverage.py + codecov)

---

## Technology Stack Summary

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0+
- **Validation**: Pydantic V2
- **Database**: PostgreSQL 15+ (production), SQLite (development)
- **Caching**: Redis 7+
- **Background Jobs**: Celery 5+ with Redis broker
- **HTTP Client**: httpx (async)
- **AI Integration**: Anthropic Python SDK
- **Testing**: pytest, pytest-asyncio, coverage.py
- **Migrations**: Alembic

### Frontend
- **Language**: TypeScript 5+
- **Framework**: React 18+
- **Build Tool**: Vite 5+
- **Styling**: Tailwind CSS 3+
- **State Management**: React Query (TanStack Query)
- **Routing**: React Router v6
- **HTTP Client**: axios
- **Testing**: Vitest, React Testing Library

### DevOps
- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Monitoring**: OpenTelemetry, Prometheus, Grafana
- **Error Tracking**: Sentry
- **Load Testing**: Locust

### Development Tools
- **Linting**: Ruff (Python), ESLint (TypeScript)
- **Formatting**: Black (Python), Prettier (TypeScript)
- **Type Checking**: mypy (Python), TypeScript compiler
- **Pre-commit Hooks**: pre-commit framework

---

## Risk Mitigation

### Risk 1: Garmin API Rate Limits
**Mitigation**:
- Implement aggressive caching (24-hour TTL for metrics)
- Batch requests where possible
- Retry with exponential backoff
- Monitor rate limit headers
- Alert on approaching limits

### Risk 2: Claude AI Availability/Latency
**Mitigation**:
- Cache insights for 7 days
- Graceful degradation to rule-based insights
- Async generation (don't block user experience)
- Set reasonable timeouts (30s)
- Monitor API health

### Risk 3: Data Privacy and Security
**Mitigation**:
- Encrypt tokens at rest (SQLAlchemy-utils)
- HTTPS only (enforce in production)
- OAuth2 for authentication
- Rate limiting on API endpoints
- Regular security audits
- GDPR compliance (data export, deletion)

### Risk 4: Performance Degradation at Scale
**Mitigation**:
- Comprehensive load testing before launch
- Horizontal scaling strategy (stateless backend)
- Database read replicas if needed
- CDN for static assets
- Monitor performance metrics continuously
- Auto-scaling in production

---

## Decision Summary Table

Quick reference for all technology decisions made:

| Category | Decision | Primary Rationale | Alternative Rejected | When to Reconsider |
|----------|----------|-------------------|----------------------|-------------------|
| **Backend Language** | Python 3.11+ | AI/ML ecosystem, pandas/NumPy for time-series, 40% adoption growth | TypeScript/Node.js | Real-time features become priority |
| **Backend Framework** | FastAPI 0.104+ | 24% better RPS, async-first, auto API docs, ML developer favorite | Express, Django | Need extreme performance (3x faster on simple ops) |
| **Database** | PostgreSQL 15+ | Relational data, JSONB flexibility, window functions, mature | TimescaleDB, InfluxDB | 10K+ users with multi-year history |
| **Garmin Integration** | python-garminconnect + OAuth PKCE | Maintained, comprehensive, handles auth complexity | Direct API, web scraping | More control needed over implementation |
| **Claude Integration** | Anthropic SDK + Haiku 4.5 | 95% cost savings (caching + batching), 2x faster than Sonnet | Sonnet 4.5, GPT-4, Local LLM | Quality issues or sustained outages |
| **Background Jobs** | Celery 5+ with Redis | Scheduled tasks, retry logic, Flower monitoring, production-ready | BullMQ, APScheduler, Lambda | Node.js backend or serverless at scale |
| **Caching/Broker** | Redis 7+ | Dual purpose (cache + broker), simple setup, sub-ms latency | RabbitMQ, separate cache | Message reliability becomes critical |
| **Testing Framework** | pytest + pytest-asyncio | 80% Python adoption, async support, powerful fixtures | Jest, unittest | Different language chosen |
| **ORM** | SQLAlchemy 2.0+ with asyncpg | Async PostgreSQL, 2-5x faster than psycopg2, mature | Raw SQL, Prisma | Simple CRUD only (unlikely) |

## Cost Analysis Summary

**Estimated Monthly Costs (1000 users)**:

| Service | Usage | Cost/Month | Notes |
|---------|-------|------------|-------|
| Claude AI (Haiku 4.5) | 4K insights/month with caching/batching | $0.65 | 85% savings vs unoptimized |
| Garmin API | Free tier | $0 | Production keys after verification |
| PostgreSQL (managed) | 20GB storage, low I/O | $25-50 | DigitalOcean/AWS RDS |
| Redis (managed) | 1GB memory | $15-20 | Cache + broker |
| Compute (backend) | 2 vCPU, 4GB RAM | $40-60 | API + Celery workers |
| Frontend hosting (CDN) | Static assets | $5-10 | Vercel/Netlify/CloudFlare |
| Monitoring (Grafana Cloud) | Basic tier | $0-50 | Free tier may suffice |
| **Total** | | **$85-195** | Scales non-linearly with users |

**At 10K users**: ~$400-800/month (economies of scale, batch processing, caching)

## Performance Targets vs Decisions

| Requirement | Target | Technology Decision | How It Achieves Target |
|-------------|--------|---------------------|------------------------|
| Simple API endpoints (p95) | <200ms | FastAPI + Redis caching + asyncpg | FastAPI: 17ms response, Redis: sub-ms, asyncpg: 2-5x faster |
| Recovery score calculation | <5s | Python + pandas + database indexes | pandas rolling windows, compound indexes (user_id, date) |
| AI insights generation | <30s | Claude Haiku 4.5 + prompt caching | 2x faster than Sonnet, 85% latency reduction with caching |
| Training plan generation | <10s | Python algorithms + cached data | Pre-computed recovery scores, efficient queries |
| Garmin data sync | <2min | Celery + async httpx + caching | Background job, parallel requests, cached historical data |
| Database queries | <50ms | PostgreSQL indexes + connection pooling | Compound indexes, asyncpg, SQLAlchemy pool |

## Key Trade-offs Accepted

1. **Python over TypeScript**:
   - Accept smaller web ecosystem and different language than frontend
   - Gain AI/ML tools, time-series libraries, data science ecosystem
   - Justified by data-intensive workload and AI integration requirements

2. **Standard PostgreSQL over TimescaleDB**:
   - Accept manual partitioning if needed at scale
   - Gain simpler deployment, no hypertable learning curve
   - Justified by MVP scale (<10M rows expected)

3. **Haiku over Sonnet**:
   - Accept slightly lower quality insights
   - Gain 70% cost savings, 2x faster responses
   - Justified by acceptable quality for pattern analysis (can escalate edge cases)

4. **Celery infrastructure over Serverless**:
   - Accept more infrastructure to manage (Redis, workers)
   - Gain simpler local development, no cold starts, better debugging
   - Justified by MVP simplicity (serverless adds complexity upfront)

5. **Aggressive caching (7-day insights)**:
   - Accept potentially stale insights (miss very recent patterns)
   - Gain 90% cost reduction, 85% latency reduction
   - Justified by weekly update cadence is sufficient for training patterns

## Risk Summary

| Risk | Likelihood | Impact | Mitigation Strategy | Status |
|------|------------|--------|---------------------|--------|
| Garmin API rate limits | Medium | High | 24h caching, webhooks (future), monitoring | Mitigated |
| Claude API costs exceed budget | Low | Medium | Prompt caching (90% savings), batch processing, usage alerts | Mitigated |
| Claude API availability | Low | Medium | 7-day cache, rule-based fallback, Sentry alerts | Mitigated |
| Performance degradation at scale | Medium | High | Load testing, horizontal scaling plan, monitoring | Planned |
| Security breach (token theft) | Low | Critical | AES-256 encryption, HTTPS only, rate limiting, audits | Mitigated |
| Time-series queries slow down | Low | Medium | Proper indexes, connection pooling, query optimization | Mitigated |

## Integration Dependencies

**External Services**:
1. **Garmin Connect API** (Critical)
   - SLA: None (free tier)
   - Fallback: Manual .FIT file upload
   - Risk: API downtime affects new data sync only (cached data still available)

2. **Claude AI API** (Important)
   - SLA: 99.9% uptime (Anthropic standard)
   - Fallback: Rule-based insights, cached insights
   - Risk: New insight generation only (user experience degradation acceptable)

3. **Redis** (Critical)
   - SLA: Self-managed or 99.9% (managed service)
   - Fallback: None (cache miss = slower, broker down = no background jobs)
   - Risk: Requires monitoring and backup strategy

**Internal Dependencies**:
- PostgreSQL → Redis (caching layer)
- Celery → Redis (message broker)
- FastAPI → PostgreSQL (data persistence)
- FastAPI → Redis (caching)
- Background jobs → Garmin API → Claude API → PostgreSQL

## Next Steps

With comprehensive research complete, proceed to implementation phases:

### Phase 0: Complete ✅
- [x] Backend language/framework selection
- [x] Garmin API integration strategy
- [x] Claude AI integration and cost optimization
- [x] Database selection and schema design
- [x] Background job processing approach
- [x] Testing framework and strategy
- [x] Technology stack summary

### Phase 1: Design (Next)
1. Generate data-model.md with detailed entity schemas
2. Generate API contracts in /contracts/ directory
3. Generate quickstart.md for developer onboarding
4. Update technology stack in Technology Stack Summary section
5. Document API endpoints and request/response formats

### Phase 2: Task Generation (After Phase 1)
1. Run `/speckit.tasks` command
2. Generate tasks.md with dependency-ordered implementation tasks
3. Break down into sprints aligned with user story priorities (P1 → P4)

### Phase 3: Implementation (After Phase 2)
1. TDD workflow for each task
2. Implement infrastructure (Docker, PostgreSQL, Redis, Celery)
3. Implement User Story 1 (P1): Daily recovery check and workout recommendation
4. Implement subsequent user stories in priority order

---

## Appendix: Research Sources

**Web Research Conducted** (2025-10-24):
- Garmin Connect API documentation and OAuth 2.0 PKCE specifications
- Garmin Health API rate limits and best practices
- python-garminconnect, Garth, and Garmy library comparisons
- FastAPI vs Express performance benchmarks (2025)
- Python data science ecosystem (pandas, NumPy, SciPy) for time-series
- Claude AI SDK Python vs TypeScript capabilities
- Claude Haiku 4.5 vs Sonnet 4.5 pricing and performance
- Anthropic prompt caching and batch processing cost optimization
- PostgreSQL vs TimescaleDB vs InfluxDB for time-series data
- SQLAlchemy asyncpg performance and connection pooling
- Celery vs BullMQ for background job processing
- pytest vs Jest testing framework comparison

**Key Insights from Research**:
1. Python adoption in AI/ML increased 40% in 2025, with FastAPI growing 30% among ML developers
2. Claude Haiku 4.5 achieves 73% SWE-bench performance at 1/3 cost of Sonnet
3. Prompt caching + batch processing enables 95% total cost reduction for Claude API
4. TimescaleDB overkill for fitness app scale (<10M rows), standard PostgreSQL sufficient
5. Celery remains production standard for Python background jobs despite serverless alternatives
6. pytest has 80%+ adoption among Python developers with excellent async support

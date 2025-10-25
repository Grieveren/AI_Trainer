# Recovery & Recommendations API Contract

**User Story**: User Story 1 - Daily Recovery Check and Workout Recommendation (Priority P1)
**Endpoints**: `/api/v1/recovery/*`

## GET /recovery/{date}

Get recovery score and workout recommendation for a specific date.

**Priority**: P1 - Core value proposition
**Success Criteria**: SC-001 (recommendations within 30 seconds of opening app)

### Request

**Method**: `GET`
**Path**: `/api/v1/recovery/{date}`
**Path Parameters**:
- `date` (required): ISO 8601 date format `YYYY-MM-DD`

**Headers**:
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Example**:
```http
GET /api/v1/recovery/2025-10-24 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Response

**Status**: `200 OK`

**Body**:
```json
{
  "date": "2025-10-24",
  "recovery_score": {
    "total_score": 85,
    "status": "green",
    "components": {
      "hrv": {
        "score": 95,
        "weight": 0.4,
        "value_ms": 65,
        "seven_day_avg_ms": 59,
        "explanation": "Your HRV is 10% above your 7-day average, indicating excellent recovery"
      },
      "resting_heart_rate": {
        "score": 80,
        "weight": 0.3,
        "value_bpm": 53,
        "seven_day_avg_bpm": 55,
        "explanation": "Your resting heart rate is slightly below average, a positive sign"
      },
      "sleep": {
        "score": 90,
        "weight": 0.2,
        "duration_minutes": 480,
        "quality_score": 85,
        "explanation": "You got 8 hours of good quality sleep"
      },
      "stress": {
        "score": 70,
        "weight": 0.1,
        "garmin_stress_level": 30,
        "explanation": "Your stress levels are moderate"
      }
    },
    "acwr": {
      "acute_load": 280,
      "chronic_load": 320,
      "ratio": 0.875,
      "adjustment_factor": 1.0,
      "explanation": "Your training load is well-balanced"
    }
  },
  "recommendation": {
    "workout_type": "run",
    "duration_minutes": 60,
    "intensity_level": "hard",
    "heart_rate_target": {
      "low_bpm": 155,
      "high_bpm": 170,
      "zone": "Zone 3-4"
    },
    "rationale": "Your recovery score is excellent (85/100) with strong HRV and good sleep. This is an ideal day for a hard training session. Your training load ratio (0.88) shows you're not overtrained. Consider a tempo run or interval workout to build fitness.",
    "alternatives": [
      {
        "workout_type": "bike",
        "duration_minutes": 75,
        "intensity_level": "moderate",
        "rationale": "If running feels too hard, a bike session provides similar cardiovascular benefit with lower impact"
      }
    ]
  },
  "data_freshness": {
    "health_metrics_updated_at": "2025-10-24T06:15:00Z",
    "garmin_last_sync": "2025-10-24T06:15:00Z",
    "score_calculated_at": "2025-10-24T06:16:30Z",
    "is_stale": false
  }
}
```

**Response Fields**:
- `date`: Date for this recovery score (ISO 8601)
- `recovery_score.total_score`: Overall score 0-100 (FR-007)
- `recovery_score.status`: Color-coded status - `"green"` (80-100), `"yellow"` (50-79), `"red"` (0-49) (FR-008)
- `recovery_score.components`: Breakdown of score components with explanations (FR-009)
- `recovery_score.acwr`: Acute:Chronic Workload Ratio analysis
- `recommendation.workout_type`: Suggested workout type (FR-011, FR-012)
- `recommendation.intensity_level`: Suggested intensity (FR-012)
- `recommendation.rationale`: Plain language explanation (FR-013)
- `recommendation.alternatives`: Alternative workout options (FR-014)
- `data_freshness`: Timestamps for data provenance (acceptance scenario 5)

### Error Responses

**404 Not Found** - No health metrics for this date:
```json
{
  "error": {
    "code": "NO_HEALTH_METRICS",
    "message": "No health metrics available for date 2025-10-24. Garmin data sync may be pending.",
    "details": {
      "date": "2025-10-24",
      "last_sync": "2025-10-23T06:15:00Z",
      "suggestion": "Try syncing Garmin data or check back later"
    },
    "timestamp": "2025-10-24T10:30:00Z"
  }
}
```

**503 Service Unavailable** - Cannot calculate score:
```json
{
  "error": {
    "code": "RECOVERY_CALCULATION_FAILED",
    "message": "Unable to calculate recovery score due to insufficient historical data",
    "details": {
      "date": "2025-10-24",
      "days_of_data": 3,
      "required_days": 7,
      "suggestion": "Continue syncing Garmin data for 4 more days to enable recovery scoring"
    },
    "timestamp": "2025-10-24T10:30:00Z"
  }
}
```

### Acceptance Criteria Mapping

1. ✅ **Given** user has synced Garmin data overnight, **When** user opens app, **Then** displays recovery score with color status and explanation
   - Response includes `total_score`, `status` (green/yellow/red), and component explanations

2. ✅ **Given** high recovery score (green), **When** viewing recommendation, **Then** suggests intense workout
   - `status: "green"` → `intensity_level: "hard"` with specific zones

3. ✅ **Given** low recovery score (red), **When** viewing recommendation, **Then** suggests recovery day
   - Tested separately (see Red Score example below)

4. ✅ **Given** moderate recovery score (yellow), **When** viewing recommendation, **Then** suggests moderate workout
   - Tested separately (see Yellow Score example below)

5. ✅ **Given** Garmin sync fails, **When** user opens app, **Then** displays last known status with timestamp
   - `data_freshness.is_stale: true` with `garmin_last_sync` timestamp

---

## GET /recovery/today

Convenience endpoint for getting today's recovery score.

**Method**: `GET`
**Path**: `/api/v1/recovery/today`
**Behavior**: Redirects to `/api/v1/recovery/{current_date}`

**Response**: Same as `/recovery/{date}` with `date` set to today's date in user's timezone.

---

## POST /recovery/{date}/recalculate

Force recalculation of recovery score (e.g., after manual data entry).

### Request

**Method**: `POST`
**Path**: `/api/v1/recovery/{date}/recalculate`

**Headers**:
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Body** (optional):
```json
{
  "invalidate_cache": true
}
```

### Response

**Status**: `202 Accepted` - Calculation queued

**Body**:
```json
{
  "status": "queued",
  "job_id": "calc_550e8400_2025-10-24",
  "estimated_completion_seconds": 3,
  "poll_url": "/api/v1/jobs/calc_550e8400_2025-10-24"
}
```

**After Completion**: GET `/recovery/{date}` returns updated score

---

## Additional Scenarios

### Yellow Score Example (Moderate Recovery)

**Request**: `GET /api/v1/recovery/2025-10-20`

**Response**: `200 OK`
```json
{
  "date": "2025-10-20",
  "recovery_score": {
    "total_score": 65,
    "status": "yellow",
    "components": {
      "hrv": {"score": 60, "explanation": "HRV is 5% below average"},
      "resting_heart_rate": {"score": 70, "explanation": "Resting HR is slightly elevated"},
      "sleep": {"score": 60, "duration_minutes": 390, "explanation": "Only 6.5 hours of sleep"},
      "stress": {"score": 75, "explanation": "Stress levels are acceptable"}
    }
  },
  "recommendation": {
    "workout_type": "run",
    "duration_minutes": 40,
    "intensity_level": "easy",
    "heart_rate_target": {"low_bpm": 120, "high_bpm": 140, "zone": "Zone 2"},
    "rationale": "Your recovery is moderate (65/100). Your HRV is below average and you got less sleep than optimal. Today is best for an easy workout to maintain fitness without adding stress. Keep the effort conversational."
  }
}
```

### Red Score Example (Low Recovery)

**Request**: `GET /api/v1/recovery/2025-10-18`

**Response**: `200 OK`
```json
{
  "date": "2025-10-18",
  "recovery_score": {
    "total_score": 38,
    "status": "red",
    "components": {
      "hrv": {"score": 30, "explanation": "HRV is 15% below average - significant fatigue"},
      "resting_heart_rate": {"score": 35, "explanation": "Resting HR is elevated by 8 bpm"},
      "sleep": {"score": 40, "duration_minutes": 300, "explanation": "Only 5 hours of sleep"},
      "stress": {"score": 50, "explanation": "Stress levels are high"}
    },
    "acwr": {
      "ratio": 1.45,
      "adjustment_factor": 0.9,
      "explanation": "Your training load is approaching overreaching territory"
    }
  },
  "recommendation": {
    "workout_type": "rest",
    "duration_minutes": 0,
    "intensity_level": "recovery",
    "rationale": "⚠️ Your recovery is poor (38/100) with low HRV, elevated heart rate, insufficient sleep, and high training load. Your body needs rest. Take today off or do very light activity (20-minute walk). This rest will help you train harder in the coming days. Prioritize sleep tonight.",
    "alternatives": [
      {
        "workout_type": "walk",
        "duration_minutes": 20,
        "intensity_level": "recovery",
        "rationale": "If you need to move, a short, easy walk is acceptable. Keep it very light."
      }
    ]
  }
}
```

---

## Performance Requirements

- **Response Time**: < 200ms (p95) for cached scores (constitution requirement)
- **Initial Calculation**: < 5 seconds for uncached score (SC-006)
- **Cache Strategy**:
  - Redis cache with 24-hour TTL
  - Cache key: `recovery:{user_id}:{date}`
  - Invalidate on new health metrics arrival
- **Fallback**: If calculation exceeds 5s, return 202 with job ID for polling

---

## Validation Rules

### Path Parameters
- `date`: Must be valid ISO 8601 date (YYYY-MM-DD)
- `date`: Cannot be more than 7 days in the future
- `date`: Can be up to 365 days in the past

### Business Rules
- Requires at least 7 days of historical data for accurate recovery scoring (Assumption #6)
- If < 7 days available, return 503 with explanation
- Red recovery score (0-49) triggers overtraining prevention logic (FR-015)
- Anomaly detection: If resting HR > 10% above average + poor HRV, warn of potential illness (FR-010)

---

## Testing Checklist

### Contract Tests
- [ ] Verify response schema matches specification
- [ ] Test with green/yellow/red score scenarios
- [ ] Test with stale Garmin data
- [ ] Test with insufficient historical data
- [ ] Test caching behavior (hit vs miss performance)

### Integration Tests
- [ ] Complete User Story 1 acceptance scenarios (1-5)
- [ ] Verify recovery score calculation algorithm
- [ ] Verify recommendation logic based on score
- [ ] Test cache invalidation on new data
- [ ] Test anomaly detection (illness warning)

### Performance Tests
- [ ] Verify < 200ms p95 for cached scores
- [ ] Verify < 5s for fresh calculation
- [ ] Load test with 100 concurrent users
- [ ] Verify Redis cache hit rate > 80%

"""Create test user and recovery data for manual testing."""
import sys
from datetime import date, datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Use sync database connection
DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5433/aitrainer"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def create_test_data():
    """Create test user and recovery data."""
    with SessionLocal() as db:
        try:
            # Check if test user exists
            result = db.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": "test@example.com"},
            )
            user = result.fetchone()

            if user:
                user_id = user[0]
                print(f"✓ Test user already exists (ID: {user_id})")
            else:
                # Create test user (use gen_random_uuid() for id)
                result = db.execute(
                    text(
                        """
                        INSERT INTO users (id, email, hashed_password, is_active, is_verified, created_at, updated_at)
                        VALUES (gen_random_uuid(), :email, :password, true, true, :now, :now)
                        RETURNING id
                    """
                    ),
                    {
                        "email": "test@example.com",
                        "password": "$2b$12$test_hashed_password",  # Not a real hash, but good enough for testing
                        "now": datetime.utcnow(),
                    },
                )
                user_id = result.fetchone()[0]
                print(f"✓ Created test user (ID: {user_id})")

            # Create recovery score for today
            today = date.today()
            result = db.execute(
                text(
                    "SELECT id FROM recovery_scores WHERE user_id = :user_id AND date = :date"
                ),
                {"user_id": user_id, "date": today},
            )

            if result.fetchone():
                print("✓ Recovery score for today already exists")
            else:
                cached_at = datetime.utcnow()
                cache_expires_at = cached_at + timedelta(hours=24)
                db.execute(
                    text(
                        """
                        INSERT INTO recovery_scores (
                            user_id, date, overall_score, status,
                            hrv_component, hr_component, sleep_component, acwr_component,
                            explanation, cached_at, cache_expires_at, created_at
                        )
                        VALUES (
                            :user_id, :date, :overall_score, :status,
                            :hrv_component, :hr_component, :sleep_component, :acwr_component,
                            :explanation, :cached_at, :cache_expires_at, :now
                        )
                    """
                    ),
                    {
                        "user_id": user_id,
                        "date": today,
                        "overall_score": 85,
                        "status": "green",
                        "hrv_component": 90.0,
                        "hr_component": 85.0,
                        "sleep_component": 80.0,
                        "acwr_component": 85.0,
                        "explanation": "✓ Excellent recovery (Score: 85/100)\n\nYou're well-recovered and ready for high-intensity training. All metrics look great!",
                        "cached_at": cached_at,
                        "cache_expires_at": cache_expires_at,
                        "now": datetime.utcnow(),
                    },
                )
                print(f"✓ Created recovery score for {today}")

            # Create a few historical scores
            for days_ago in [1, 2, 3]:
                hist_date = today - timedelta(days=days_ago)
                result = db.execute(
                    text(
                        "SELECT id FROM recovery_scores WHERE user_id = :user_id AND date = :date"
                    ),
                    {"user_id": user_id, "date": hist_date},
                )

                if not result.fetchone():
                    score = 75 + (days_ago * 2)  # Gradually improving recovery
                    cached_at = datetime.utcnow()
                    cache_expires_at = cached_at + timedelta(hours=24)
                    db.execute(
                        text(
                            """
                            INSERT INTO recovery_scores (
                                user_id, date, overall_score, status,
                                hrv_component, hr_component, sleep_component, acwr_component,
                                explanation, cached_at, cache_expires_at, created_at
                            )
                            VALUES (
                                :user_id, :date, :overall_score, :status,
                                :hrv_component, :hr_component, :sleep_component, :acwr_component,
                                :explanation, :cached_at, :cache_expires_at, :now
                            )
                        """
                        ),
                        {
                            "user_id": user_id,
                            "date": hist_date,
                            "overall_score": score,
                            "status": "yellow" if score < 80 else "green",
                            "hrv_component": float(score - 5),
                            "hr_component": float(score),
                            "sleep_component": float(score + 5),
                            "acwr_component": float(score),
                            "explanation": f"Recovery score: {score}/100",
                            "cached_at": cached_at,
                            "cache_expires_at": cache_expires_at,
                            "now": datetime.utcnow(),
                        },
                    )
            print(f"✓ Created {days_ago} historical recovery scores")

            db.commit()

            print("\n" + "=" * 60)
            print("✅ TEST DATA CREATED SUCCESSFULLY!")
            print("=" * 60)
            print("\nUser Email: test@example.com")
            print(f"User ID: {user_id}")
            print("\nRecovery scores created for:")
            print(f"  - Today ({today}): 85/100 (green)")
            for days_ago in range(1, 4):
                hist_date = today - timedelta(days=days_ago)
                score = 75 + (days_ago * 2)
                print(f"  - {hist_date}: {score}/100")
            print("\n" + "=" * 60)

        except Exception as e:
            print(f"\n❌ Error creating test data: {e}")
            db.rollback()
            sys.exit(1)


if __name__ == "__main__":
    create_test_data()

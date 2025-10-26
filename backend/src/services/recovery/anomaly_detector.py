"""
Anomaly Detection for Health Metrics.

Detects abnormal patterns in health metrics that may indicate:
- Illness (sudden HRV drop, HR spike)
- Overtraining (persistent HRV suppression)
- Poor recovery (multiple warning signals)

Used to provide early warnings and training recommendations.
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detects health metric anomalies and provides warnings.

    Detection criteria:
    - HRV Drop: >20% below 7-day average (illness warning)
    - HR Spike: >10% above 7-day average (illness/stress warning)
    - Persistent Low HRV: 3+ consecutive days <-15% (overtraining)
    - Multiple Warning Signals: HRV drop + HR spike + poor sleep (critical)
    """

    # Thresholds for anomaly detection
    HRV_CRITICAL_DROP_THRESHOLD = -20  # % below baseline
    HRV_WARNING_DROP_THRESHOLD = -15  # % below baseline
    HR_CRITICAL_SPIKE_THRESHOLD = 10  # % above baseline
    HR_WARNING_SPIKE_THRESHOLD = 7  # % above baseline

    # Persistence thresholds
    OVERTRAINING_DAYS_THRESHOLD = 3  # Days with warning signals

    def detect_anomalies(
        self,
        today_metrics: Dict[str, any],
        historical_metrics: List[Dict[str, any]],
        component_scores: Dict[str, Optional[int]],
    ) -> Dict[str, any]:
        """
        Detect anomalies in health metrics.

        Args:
            today_metrics: Today's metrics (hrv_ms, resting_hr, etc.)
            historical_metrics: Historical metrics for baseline comparison
            component_scores: Calculated component scores

        Returns:
            Dict with anomaly information:
            {
                "has_anomalies": bool,
                "severity": str,  # "none", "warning", "critical"
                "warnings": List[str],
                "recommendations": List[str]
            }
        """
        warnings = []
        recommendations = []
        severity = "none"

        # Calculate baselines
        hrv_baseline = self._calculate_baseline_hrv(historical_metrics)
        hr_baseline = self._calculate_baseline_hr(historical_metrics)

        # Detect HRV anomalies
        if today_metrics.get("hrv_ms") and hrv_baseline:
            hrv_deviation = (
                (today_metrics["hrv_ms"] - hrv_baseline) / hrv_baseline
            ) * 100

            if hrv_deviation <= self.HRV_CRITICAL_DROP_THRESHOLD:
                warnings.append(
                    f"Critical HRV drop detected: {hrv_deviation:.1f}% below baseline. "
                    "Possible illness or severe fatigue."
                )
                recommendations.append(
                    "Consider complete rest. Monitor for illness symptoms."
                )
                severity = "critical"

            elif hrv_deviation <= self.HRV_WARNING_DROP_THRESHOLD:
                warnings.append(
                    f"HRV below normal: {hrv_deviation:.1f}% below baseline. "
                    "Recovery may be compromised."
                )
                recommendations.append("Easy training or active recovery only.")
                if severity != "critical":
                    severity = "warning"

        # Detect HR anomalies
        if today_metrics.get("resting_hr") and hr_baseline:
            hr_deviation = (
                (today_metrics["resting_hr"] - hr_baseline) / hr_baseline
            ) * 100

            if hr_deviation >= self.HR_CRITICAL_SPIKE_THRESHOLD:
                warnings.append(
                    f"Elevated resting HR: {hr_deviation:.1f}% above baseline. "
                    "Possible illness, stress, or overtraining."
                )
                recommendations.append(
                    "Prioritize rest and stress management. Monitor symptoms."
                )
                severity = "critical"

            elif hr_deviation >= self.HR_WARNING_SPIKE_THRESHOLD:
                warnings.append(
                    f"Resting HR elevated: {hr_deviation:.1f}% above baseline. "
                    "Increased stress or fatigue."
                )
                if "Easy training" not in " ".join(recommendations):
                    recommendations.append("Reduce training intensity.")
                if severity == "none":
                    severity = "warning"

        # Detect sleep anomalies
        sleep_score = component_scores.get("sleep_score")
        if sleep_score is not None and sleep_score < 40:
            warnings.append(
                f"Poor sleep detected: Sleep score {sleep_score}/100. "
                "Inadequate recovery."
            )
            recommendations.append("Prioritize sleep hygiene and earlier bedtime.")
            if severity == "none":
                severity = "warning"

        # Detect multiple warning signals (critical combination)
        hrv_score = component_scores.get("hrv_score")
        hr_score = component_scores.get("hr_score")

        if (
            hrv_score is not None
            and hrv_score < 25
            and hr_score is not None
            and hr_score < 25
            and sleep_score is not None
            and sleep_score < 50
        ):
            if "illness" not in " ".join(warnings).lower():
                warnings.append(
                    "Multiple warning signals: Low HRV + Elevated HR + Poor sleep. "
                    "High risk of illness or overtraining."
                )
            recommendations.append("PRIORITY: Complete rest until metrics improve.")
            severity = "critical"

        # Detect ACWR overload
        acwr_score = component_scores.get("acwr_score")
        if acwr_score is not None and acwr_score < 30:
            warnings.append(
                f"Training load warning: ACWR score {acwr_score}/100. "
                "Risk of injury from excessive training spike or detraining."
            )
            if acwr_score == 0:
                recommendations.append(
                    "Immediately reduce training load to prevent injury."
                )
            else:
                recommendations.append("Adjust training volume to safer levels.")
            if severity == "none":
                severity = "warning"

        # Check for overtraining pattern (persistent suppression)
        overtraining_risk = self._check_overtraining_pattern(historical_metrics)
        if overtraining_risk:
            warnings.append(
                "Overtraining pattern detected: Persistent HRV suppression over multiple days."
            )
            recommendations.append(
                "Schedule recovery week with reduced volume/intensity."
            )
            severity = "critical"

        return {
            "has_anomalies": len(warnings) > 0,
            "severity": severity,
            "warnings": warnings,
            "recommendations": recommendations,
        }

    def _calculate_baseline_hrv(
        self, historical_metrics: List[Dict[str, any]]
    ) -> Optional[float]:
        """Calculate 7-day baseline HRV."""
        valid_values = [
            m.get("hrv_ms")
            for m in historical_metrics[-7:]
            if m.get("hrv_ms") is not None
        ]

        if len(valid_values) >= 4:
            return sum(valid_values) / len(valid_values)
        return None

    def _calculate_baseline_hr(
        self, historical_metrics: List[Dict[str, any]]
    ) -> Optional[float]:
        """Calculate 7-day baseline resting HR."""
        valid_values = [
            m.get("resting_hr")
            for m in historical_metrics[-7:]
            if m.get("resting_hr") is not None
        ]

        if len(valid_values) >= 4:
            return sum(valid_values) / len(valid_values)
        return None

    def _check_overtraining_pattern(
        self, historical_metrics: List[Dict[str, any]]
    ) -> bool:
        """
        Check for overtraining pattern (persistent HRV suppression).

        Returns True if HRV has been suppressed for 3+ consecutive days.
        """
        if len(historical_metrics) < 7:
            return False

        # Get last 7 days
        recent_metrics = historical_metrics[-7:]

        # Calculate baseline from first 4 days
        baseline_values = [
            m.get("hrv_ms") for m in recent_metrics[:4] if m.get("hrv_ms") is not None
        ]

        if len(baseline_values) < 3:
            return False

        baseline = sum(baseline_values) / len(baseline_values)

        # Check last 3 days for suppression
        suppressed_days = 0
        for m in recent_metrics[-3:]:
            hrv = m.get("hrv_ms")
            if hrv is not None:
                deviation = ((hrv - baseline) / baseline) * 100
                if deviation <= self.HRV_WARNING_DROP_THRESHOLD:
                    suppressed_days += 1

        return suppressed_days >= self.OVERTRAINING_DAYS_THRESHOLD

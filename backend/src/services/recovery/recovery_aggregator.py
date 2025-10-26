"""
Recovery Score Aggregator.

Combines multiple component scores into final recovery score with graceful degradation.

Algorithm:
- Component weights (when all available):
  - HRV: 40% (strongest physiological indicator)
  - HR: 30% (secondary physiological indicator)
  - Sleep: 20% (important for recovery but less immediate)
  - ACWR: 10% (training load management)

- Graceful degradation:
  - If component missing (None), re-weight remaining components proportionally
  - Minimum 2 components required for valid score
  - If <2 components available, return None

- Final score interpretation:
  - 90-100: Excellent recovery (train hard/race ready)
  - 70-89: Good recovery (normal training)
  - 50-69: Moderate recovery (easy training only)
  - 30-49: Poor recovery (active recovery/rest)
  - 0-29: Critical (complete rest required)
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class RecoveryAggregator:
    """Aggregates component scores into final recovery score."""

    # Component weights (must sum to 1.0)
    DEFAULT_WEIGHTS = {
        "hrv_score": 0.40,  # 40% - HRV is primary recovery indicator
        "hr_score": 0.30,  # 30% - Resting HR is secondary
        "sleep_score": 0.20,  # 20% - Sleep quality/duration
        "acwr_score": 0.10,  # 10% - Training load management
    }

    # Minimum number of components required
    MIN_COMPONENTS_REQUIRED = 2

    def calculate_final_score(
        self, components: Optional[Dict[str, Optional[int]]]
    ) -> Optional[int]:
        """
        Calculate final recovery score from component scores.

        Args:
            components: Dict of component scores:
                - hrv_score: HRV component score (0-100 or None)
                - hr_score: HR component score (0-100 or None)
                - sleep_score: Sleep component score (0-100 or None)
                - acwr_score: ACWR component score (0-100 or None)

        Returns:
            Final recovery score (0-100), or None if insufficient data

        Example:
            components = {
                "hrv_score": 85,
                "hr_score": 75,
                "sleep_score": 90,
                "acwr_score": 100
            }
        """
        if components is None or not components:
            logger.debug("No component scores provided")
            return None

        # Filter out missing components and clamp valid ones to 0-100
        valid_components = {}
        for key, score in components.items():
            if score is not None:
                # Clamp score to valid range
                clamped_score = max(0, min(100, score))
                valid_components[key] = clamped_score

        # Check minimum components requirement
        if len(valid_components) < self.MIN_COMPONENTS_REQUIRED:
            logger.debug(
                f"Insufficient components: {len(valid_components)} < {self.MIN_COMPONENTS_REQUIRED}"
            )
            return None

        # Calculate re-weighted scores
        weighted_score = self._calculate_weighted_score(valid_components)

        # Round to integer
        final_score = int(round(weighted_score))

        logger.debug(
            f"Recovery score: {final_score} from components: "
            f"{', '.join(f'{k}={v}' for k, v in valid_components.items())}"
        )

        return final_score

    def _calculate_weighted_score(self, valid_components: Dict[str, int]) -> float:
        """
        Calculate weighted score with proportional re-weighting.

        If components are missing, their weights are redistributed
        proportionally among remaining components.

        Args:
            valid_components: Dict of valid (non-None) component scores

        Returns:
            Weighted score (0-100, may be fractional)
        """
        # Calculate total weight of available components
        total_weight = sum(
            self.DEFAULT_WEIGHTS[key]
            for key in valid_components.keys()
            if key in self.DEFAULT_WEIGHTS
        )

        if total_weight == 0:
            logger.warning("Total weight is zero - should not happen")
            return 50.0  # Return neutral score as fallback

        # Calculate weighted sum with re-normalized weights
        weighted_sum = 0.0

        for key, score in valid_components.items():
            if key in self.DEFAULT_WEIGHTS:
                # Re-normalized weight = original_weight / total_available_weight
                normalized_weight = self.DEFAULT_WEIGHTS[key] / total_weight
                weighted_sum += score * normalized_weight

                logger.debug(
                    f"  {key}: {score} * {normalized_weight:.3f} = {score * normalized_weight:.2f}"
                )

        return weighted_sum

"""Claude AI configuration."""

import os


class ClaudeConfig:
    """Configuration for Anthropic Claude AI integration."""

    def __init__(self):
        """Initialize Claude configuration from environment."""
        self.api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

        # Model configuration
        self.model: str = os.getenv("CLAUDE_MODEL", "claude-haiku-4.5")

        # API configuration
        self.api_version: str = "2023-06-01"
        self.base_url: str = "https://api.anthropic.com"

        # Request configuration
        self.max_tokens: int = int(os.getenv("CLAUDE_MAX_TOKENS", "1024"))
        self.temperature: float = float(os.getenv("CLAUDE_TEMPERATURE", "0.7"))
        self.timeout: int = int(os.getenv("CLAUDE_TIMEOUT", "60"))

        # Retry configuration
        self.max_retries: int = 3
        self.retry_delay: int = 5  # seconds

        # Prompt caching configuration
        self.enable_prompt_caching: bool = (
            os.getenv("CLAUDE_ENABLE_CACHING", "true").lower() == "true"
        )
        self.cache_ttl: int = 3600  # 1 hour in seconds

        # Batch processing configuration
        self.enable_batch_processing: bool = (
            os.getenv("CLAUDE_ENABLE_BATCH", "true").lower() == "true"
        )
        self.batch_size: int = int(os.getenv("CLAUDE_BATCH_SIZE", "10"))

        # Cost optimization
        self.use_haiku_for_simple_tasks: bool = (
            os.getenv("CLAUDE_USE_HAIKU", "true").lower() == "true"
        )

    def validate(self) -> bool:
        """Validate that required configuration is present."""
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        return True

    def get_system_prompt(self, task_type: str) -> str:
        """Get system prompt for specific task type.

        Args:
            task_type: Type of task (insight, recommendation, plan)

        Returns:
            System prompt optimized for the task
        """
        prompts = {
            "insight": (
                "You are an expert sports scientist and training advisor. "
                "Analyze the provided health and training data to generate "
                "actionable insights. Focus on patterns, trends, and specific "
                "recommendations for improvement. Be concise and clear."
            ),
            "recommendation": (
                "You are an expert endurance coach specializing in personalized "
                "training recommendations. Based on the recovery score and recent "
                "training history, recommend an appropriate workout for today. "
                "Include workout type, intensity, duration, and clear rationale."
            ),
            "plan": (
                "You are an expert training plan designer. Create a structured "
                "multi-week training plan that progresses appropriately, includes "
                "recovery periods, and aligns with the athlete's goals. Balance "
                "volume, intensity, and recovery."
            ),
            "adjustment": (
                "You are an expert at adaptive training planning. Analyze the "
                "athlete's actual performance versus planned workouts and adjust "
                "the upcoming training plan accordingly. Maintain progression "
                "while respecting recovery needs."
            ),
        }

        return prompts.get(
            task_type,
            "You are a helpful AI assistant specialized in sports training and health optimization.",
        )

    def get_request_params(self, task_type: str) -> dict:
        """Get optimized request parameters for task type.

        Args:
            task_type: Type of task

        Returns:
            Dictionary of request parameters
        """
        # Use Haiku for simpler tasks if enabled
        model = self.model
        if self.use_haiku_for_simple_tasks and task_type in [
            "insight",
            "recommendation",
        ]:
            model = "claude-haiku-4.5"

        return {
            "model": model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }


# Global configuration instance
claude_config = ClaudeConfig()

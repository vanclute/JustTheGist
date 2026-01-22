"""Model Router with Automatic Fallback for JustTheGist.

Routes tasks to cheaper models with automatic fallback when rate-limited.
Leverages CommittAI's universal model caller.

Usage:
    from scripts.model_router import ModelRouter

    router = ModelRouter()
    result = router.call("Extract transcript from: {url}", task_type="extraction")
"""

import sys
import os
from pathlib import Path
from typing import Optional, List, Tuple
import time

# Add CommittAI to path and load its .env
COMMITTAI_PATH = Path("D:/Projects/committai")
sys.path.insert(0, str(COMMITTAI_PATH))

# Load CommittAI's .env for ENCRYPTION_KEY and API keys
_env_file = COMMITTAI_PATH / ".env"
if _env_file.exists():
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                if key not in os.environ:  # Don't override existing vars
                    os.environ[key] = value

from core.lib.model_caller import call_model, ModelCallError


# Fallback chains by task type
# Order: cheapest first, more expensive as fallback
# Based on models configured in CommittAI's .model-configs.json
FALLBACK_CHAINS = {
    "extraction": [
        # Prioritize subscription models, then cheap APIs
        "gemini",        # Free tier, fast
        "codex",         # GPT subscription - use what you're paying for
        "deepseek",      # Dirt cheap API
        "glm",           # Cheap API fallback
        "kimi",          # Another cheap option
    ],
    "synthesis": [
        # For report generation - need reasoning capability + large context
        "gemini",        # Massive context window (1-2M tokens), excellent for synthesis
        "codex",         # GPT subscription - capable reasoning
        "deepseek",      # Cheap fallback, good reasoning
        "glm",           # Cheap API fallback
        "kimi",          # Final backup, 32k context
    ],
    "default": [
        "deepseek",
        "glm",
        "kimi",
        "gemini",
    ]
}

# Error patterns that indicate rate limiting
RATE_LIMIT_PATTERNS = [
    "429",
    "rate limit",
    "too many requests",
    "quota exceeded",
    "capacity",
    "overloaded",
]


def is_rate_limited(error: Exception) -> bool:
    """Check if error indicates rate limiting."""
    error_str = str(error).lower()
    return any(pattern in error_str for pattern in RATE_LIMIT_PATTERNS)


class ModelRouter:
    """Routes tasks to models with automatic fallback on rate limiting."""

    def __init__(
        self,
        extraction_chain: Optional[List[str]] = None,
        synthesis_chain: Optional[List[str]] = None,
        retry_delay: float = 2.0,
        verbose: bool = True
    ):
        """Initialize router with optional custom fallback chains.

        Args:
            extraction_chain: Custom chain for extraction tasks
            synthesis_chain: Custom chain for synthesis tasks
            retry_delay: Seconds to wait between fallback attempts
            verbose: Print status messages
        """
        self.chains = {
            "extraction": extraction_chain or FALLBACK_CHAINS["extraction"],
            "synthesis": synthesis_chain or FALLBACK_CHAINS["synthesis"],
            "default": FALLBACK_CHAINS["default"],
        }
        self.retry_delay = retry_delay
        self.verbose = verbose

        # Track which models are currently rate-limited
        self._rate_limited: dict[str, float] = {}  # model -> timestamp when limit expires
        self._rate_limit_duration = 300  # 5 minutes cooldown

    def _log(self, msg: str):
        """Print if verbose mode enabled."""
        if self.verbose:
            print(f"[ModelRouter] {msg}", file=sys.stderr)

    def _is_model_cooled_down(self, model: str) -> bool:
        """Check if a previously rate-limited model has cooled down."""
        if model not in self._rate_limited:
            return True
        if time.time() > self._rate_limited[model]:
            del self._rate_limited[model]
            return True
        return False

    def _mark_rate_limited(self, model: str):
        """Mark a model as rate-limited."""
        self._rate_limited[model] = time.time() + self._rate_limit_duration
        self._log(f"{model} rate-limited, cooling down for {self._rate_limit_duration}s")

    def call(
        self,
        prompt: str,
        task_type: str = "default",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        timeout: int = 300,
    ) -> Tuple[str, str]:
        """Route task to available model with fallback.

        Args:
            prompt: The task prompt
            task_type: "extraction", "synthesis", or "default"
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Max response tokens
            timeout: Timeout per attempt

        Returns:
            Tuple of (response, model_used)

        Raises:
            ModelCallError: If all models in chain fail
        """
        chain = self.chains.get(task_type, self.chains["default"])
        errors = []

        for model in chain:
            # Skip models still in cooldown
            if not self._is_model_cooled_down(model):
                self._log(f"Skipping {model} (still in cooldown)")
                continue

            self._log(f"Trying {model}...")

            try:
                # Change to CommittAI dir so config provider finds .model-configs.json
                original_dir = os.getcwd()
                os.chdir(COMMITTAI_PATH)
                try:
                    response = call_model(
                        model_name=model,
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        system_prompt=system_prompt,
                        timeout=timeout,
                        skip_health_check=False,
                    )
                finally:
                    os.chdir(original_dir)

                # Prominent success message
                print(f"✓ {task_type.upper()} completed using: {model.upper()}", file=sys.stderr)
                return response, model

            except ModelCallError as e:
                error_msg = str(e)
                errors.append(f"{model}: {error_msg}")

                if is_rate_limited(e):
                    self._mark_rate_limited(model)
                else:
                    self._log(f"{model} failed (not rate limit): {error_msg[:100]}")

                # Brief delay before trying next model
                if self.retry_delay > 0:
                    time.sleep(self.retry_delay)

        # All models failed
        raise ModelCallError(
            f"All models in {task_type} chain failed:\n" +
            "\n".join(f"  - {e}" for e in errors)
        )

    def extract(self, prompt: str, **kwargs) -> Tuple[str, str]:
        """Convenience method for extraction tasks."""
        return self.call(prompt, task_type="extraction", **kwargs)

    def synthesize(self, prompt: str, **kwargs) -> Tuple[str, str]:
        """Convenience method for synthesis tasks."""
        return self.call(prompt, task_type="synthesis", **kwargs)


# Quick test
if __name__ == "__main__":
    router = ModelRouter()

    print("Testing extraction chain...")
    try:
        response, model = router.extract("What is 2+2? Reply with just the number.")
        print(f"Response from {model}: {response}")
    except ModelCallError as e:
        print(f"All models failed: {e}")

    print("\nTesting synthesis chain...")
    try:
        response, model = router.synthesize("Summarize: The quick brown fox jumps over the lazy dog.")
        print(f"Response from {model}: {response}")
    except ModelCallError as e:
        print(f"All models failed: {e}")

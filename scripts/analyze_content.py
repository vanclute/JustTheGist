#!/usr/bin/env python3
"""
Wrapper script for analyzing content using ModelRouter.

Usage:
    python scripts/analyze_content.py extract "url or content"
    python scripts/analyze_content.py synthesize "content to analyze" "user goal"
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try importing ModelRouter from clautonomous (when running under claude-auto)
# Fall back to local scripts/ folder if not available
try:
    # When running under claude-auto, clautonomous/src is in sys.path
    from model_router import ModelRouter
except ImportError:
    try:
        # Fall back to local scripts folder
        from scripts.model_router import ModelRouter
    except ImportError:
        print("⚠ The ModelRouter dependency isn't available. I'll synthesize directly.", file=sys.stderr)
        print("  ModelRouter requires clautonomous to be configured.", file=sys.stderr)
        sys.exit(1)


def extract_content(source: str) -> dict:
    """Extract content using router (Gemini → Codex → DeepSeek → GLM → Kimi)."""
    router = ModelRouter()

    extraction_prompt = f"""Extract key content and metadata from: {source}

If YouTube URL: Get metadata (yt-dlp) and transcript (youtube-transcript-api)
If web URL: Extract main article content
If file path: Read and extract key content

Return structured data with title, content, metadata."""

    result, model = router.extract(extraction_prompt, timeout=600)

    return {
        "content": result,
        "extraction_model": model,
        "source": source
    }


def synthesize_content(content: str, goal: str) -> dict:
    """Synthesize analysis using router (Gemini → Codex → DeepSeek → GLM → Kimi)."""
    router = ModelRouter()

    synthesis_prompt = f"""Analyze this content based on the user's goal.

User's Goal: {goal}

Content:
{content}

Provide:
- Key insights relevant to the goal
- Resources mentioned (URLs, tools, repos, references)
- Notable quotes or important points
- Assessment of whether this content is valuable for the goal
- Connections to related topics

Format as markdown."""

    result, model = router.synthesize(synthesis_prompt, max_tokens=8000, timeout=600)

    return {
        "analysis": result,
        "synthesis_model": model
    }


def main():
    if len(sys.argv) < 3:
        print("Usage:", file=sys.stderr)
        print("  extract: python scripts/analyze_content.py extract <source>", file=sys.stderr)
        print("  synthesize: python scripts/analyze_content.py synthesize <content> <goal>", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    if command == "extract":
        source = sys.argv[2]
        result = extract_content(source)
        print(json.dumps(result, indent=2))

    elif command == "synthesize":
        content = sys.argv[2]
        goal = sys.argv[3] if len(sys.argv) > 3 else "understand this content"
        result = synthesize_content(content, goal)
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

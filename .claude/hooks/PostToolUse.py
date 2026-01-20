#!/usr/bin/env python3
"""Auto-ingest reports into Knowledge Base when written to docs/"""

import sys
import json
import subprocess
from pathlib import Path

def main():
    # Read tool use from stdin
    tool_data = json.loads(sys.stdin.read())

    # Only trigger on Write tool
    if tool_data.get("tool") != "Write":
        sys.exit(0)

    file_path = tool_data.get("params", {}).get("file_path", "")

    # Only trigger for markdown files anywhere under docs/
    if not file_path.endswith(".md"):
        sys.exit(0)

    # Check if file is under docs/ directory (including subdirectories)
    path_obj = Path(file_path)
    if "docs" not in path_obj.parts:
        sys.exit(0)

    # Get project root (hook runs in cwd)
    project_root = Path.cwd()
    ingest_script = project_root / "scripts" / "ingest_report.py"

    if not ingest_script.exists():
        sys.exit(0)  # Silently skip if script not found

    # Run ingestion
    try:
        result = subprocess.run(
            ["python", str(ingest_script), file_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print(f"[KB] Ingested: {Path(file_path).name}", file=sys.stderr)
        else:
            print(f"[KB] Ingest failed: {result.stderr}", file=sys.stderr)

    except Exception as e:
        print(f"[KB] Ingest error: {e}", file=sys.stderr)

    sys.exit(0)  # Never block

if __name__ == "__main__":
    main()

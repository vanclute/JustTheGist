#!/usr/bin/env python3
"""Archive completed tasks from backlog after each session"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

try:
    from backlog_manager import load_backlog, save_backlog
    USE_MANAGER = True
except ImportError:
    USE_MANAGER = False

def main():
    backlog_path = Path("backlog.json")
    if not backlog_path.exists():
        sys.exit(0)  # No backlog, nothing to do

    # Load backlog with automatic deduplication if available
    if USE_MANAGER:
        data = load_backlog(backlog_path)
    else:
        with open(backlog_path, "r", encoding="utf-8") as f:
            data = json.load(f)

    tasks = data.get("tasks", [])
    # Accept both "done" and "completed" status
    completed = [t for t in tasks if t.get("status") in ("done", "completed")]
    active = [t for t in tasks if t.get("status") not in ("done", "completed")]

    if not completed:
        sys.exit(0)  # Nothing to archive

    # Archive completed tasks
    history_path = Path("backlog_history.json")
    if history_path.exists():
        with open(history_path, "r", encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = {"archived_sessions": []}

    # Add new archive entry
    history["archived_sessions"].append({
        "date": datetime.now().isoformat(),
        "tasks": completed
    })

    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    # Update backlog with only active tasks
    data["tasks"] = active
    if USE_MANAGER:
        save_backlog(data, backlog_path)
    else:
        with open(backlog_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    print(f"[Backlog] Archived {len(completed)} completed task(s)", file=sys.stderr)
    sys.exit(0)

if __name__ == "__main__":
    main()

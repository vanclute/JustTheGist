#!/usr/bin/env python3
"""Archive completed tasks from backlog after each session"""

import sys
import json
from pathlib import Path
from datetime import datetime

def main():
    backlog_path = Path("backlog.json")
    if not backlog_path.exists():
        sys.exit(0)  # No backlog, nothing to do

    # Read current backlog
    with open(backlog_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tasks = data.get("tasks", [])
    completed = [t for t in tasks if t.get("status") == "completed"]
    active = [t for t in tasks if t.get("status") != "completed"]

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
    with open(backlog_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"[Backlog] Archived {len(completed)} completed task(s)", file=sys.stderr)
    sys.exit(0)

if __name__ == "__main__":
    main()

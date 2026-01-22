#!/usr/bin/env python3
"""Backlog management with automatic deduplication and safe updates"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional


def load_backlog(backlog_path: Path = Path("backlog.json")) -> Dict[str, Any]:
    """Load backlog with automatic deduplication

    Deduplicates by task ID, keeping the most recent version of each task.
    """
    if not backlog_path.exists():
        return {
            "version": "1.1",
            "description": "Domain-anchored learning backlog",
            "tasks": [],
            "config": {"auto_pick": True, "max_tasks_per_session": 3}
        }

    with open(backlog_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Deduplicate tasks by ID (keep last occurrence)
    seen_ids = {}
    for i, task in enumerate(data.get("tasks", [])):
        task_id = task.get("id")
        if task_id:
            seen_ids[task_id] = i  # Track last index of each ID

    # Rebuild tasks list with only unique IDs (preserving order of last occurrence)
    unique_tasks = []
    for i, task in enumerate(data.get("tasks", [])):
        task_id = task.get("id")
        if task_id and seen_ids[task_id] == i:  # Keep only last occurrence
            unique_tasks.append(task)

    original_count = len(data.get("tasks", []))
    if len(unique_tasks) < original_count:
        print(f"[Backlog] Deduplicated: {original_count} tasks → {len(unique_tasks)} unique tasks")

    data["tasks"] = unique_tasks
    return data


def save_backlog(data: Dict[str, Any], backlog_path: Path = Path("backlog.json")) -> None:
    """Save backlog to file"""
    with open(backlog_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_next_learn_id(data: Dict[str, Any]) -> int:
    """Get next available LEARN-XXX number"""
    existing_ids = [t.get("id", "") for t in data.get("tasks", [])]
    learn_ids = [int(id.split("-")[1]) for id in existing_ids if id.startswith("LEARN-")]
    return max(learn_ids, default=0) + 1


def add_task(
    topic: str,
    reason: str,
    backlog_path: Path = Path("backlog.json"),
    domain_score: Optional[str] = None
) -> Optional[str]:
    """Add a single task to backlog with duplicate prevention

    Returns:
        Task ID if added, None if duplicate detected
    """
    data = load_backlog(backlog_path)

    # Check if task with same description already exists
    existing_descriptions = {t.get("description", "").lower() for t in data.get("tasks", [])}
    if f"research: {topic.lower()}" in existing_descriptions:
        print(f"[Backlog] Skipped duplicate: {topic}")
        return None

    next_num = get_next_learn_id(data)
    today = datetime.now().strftime("%Y-%m-%d")

    new_task = {
        "id": f"LEARN-{next_num:03d}",
        "description": f"Research: {topic}",
        "reason": reason,
        "status": "queued",
        "type": "learning",
        "source": "curiosity",
        "created": today
    }

    if domain_score:
        new_task["domain_score"] = domain_score

    data["tasks"].append(new_task)
    save_backlog(data, backlog_path)

    print(f"[Backlog] Added: {new_task['id']} - {topic}")
    return new_task["id"]


def mark_complete(task_id: str, backlog_path: Path = Path("backlog.json")) -> bool:
    """Mark a task as done

    Returns:
        True if task was found and marked complete
    """
    data = load_backlog(backlog_path)
    today = datetime.now().strftime("%Y-%m-%d")

    for task in data.get("tasks", []):
        if task.get("id") == task_id:
            task["status"] = "done"
            task["completed"] = today
            task["last_updated"] = datetime.now().isoformat()
            save_backlog(data, backlog_path)
            print(f"[Backlog] Marked complete: {task_id}")
            return True

    print(f"[Backlog] Task not found: {task_id}")
    return False


def mark_in_progress(task_id: str, backlog_path: Path = Path("backlog.json")) -> bool:
    """Mark a task as in_progress

    Returns:
        True if task was found and marked in_progress
    """
    data = load_backlog(backlog_path)
    today = datetime.now().strftime("%Y-%m-%d")

    for task in data.get("tasks", []):
        if task.get("id") == task_id:
            task["status"] = "in_progress"
            task["started"] = today
            task["last_updated"] = datetime.now().isoformat()
            save_backlog(data, backlog_path)
            print(f"[Backlog] Marked in_progress: {task_id}")
            return True

    print(f"[Backlog] Task not found: {task_id}")
    return False


def get_queued_tasks(backlog_path: Path = Path("backlog.json")) -> List[Dict[str, Any]]:
    """Get all queued tasks"""
    data = load_backlog(backlog_path)
    return [t for t in data.get("tasks", []) if t.get("status") == "queued"]


def get_task_count(backlog_path: Path = Path("backlog.json")) -> Dict[str, int]:
    """Get counts of tasks by status"""
    data = load_backlog(backlog_path)
    tasks = data.get("tasks", [])

    return {
        "total": len(tasks),
        "queued": sum(1 for t in tasks if t.get("status") == "queued"),
        "in_progress": sum(1 for t in tasks if t.get("status") == "in_progress"),
        "done": sum(1 for t in tasks if t.get("status") == "done")
    }


if __name__ == "__main__":
    # Test deduplication
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "deduplicate":
        print("Running backlog deduplication...")
        data = load_backlog()
        save_backlog(data)
        counts = get_task_count()
        print(f"\nBacklog status:")
        print(f"  Total: {counts['total']}")
        print(f"  Queued: {counts['queued']}")
        print(f"  In Progress: {counts['in_progress']}")
        print(f"  Done: {counts['done']}")
    else:
        print("Usage:")
        print("  python backlog_manager.py deduplicate  # Clean up backlog")
        print("\nOr import as module for programmatic access")

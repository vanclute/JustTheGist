#!/usr/bin/env python3
"""
Stop dispatcher - SIMPLIFIED VERSION

Changes from original:
1. classify_response() - Only checks for explicit completion signals
2. handle_autonomous_stop() - Everything else → restart with tickler
3. Removed: Pattern matching for "waiting" and "working"
4. Removed: Circuit breaker logic

This eliminates false positives from question marks, section headers, etc.
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude" / "hooks"))

try:
    from hook_state import set_global, is_autonomous_mode, reset_circuit_breaker, log_event
except ImportError:
    def is_autonomous_mode(): return False
    def set_global(key, value): pass
    def reset_circuit_breaker(): pass
    def log_event(event_type, source, data=None): pass

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from claude_hooks.paths import HOOKS_DATA
except ImportError:
    HOOKS_DATA = Path.home() / ".claude" / "hooks_data"

LOG_FILE = HOOKS_DATA / "stop_dispatcher.log"
MARKER_FILE = HOOKS_DATA / "task_complete.marker"

STRUCTURED_SIGNAL_PATTERN = re.compile(r'\[\[SIGNAL:(\w+)(?::([^\]]+))?\]\]')
VALID_SIGNAL_STATUSES = {'task_complete', 'blocked', 'error', 'needs_input'}
TICKLER_MESSAGE = "If there is unfinished work, continue. If all tasks are complete, use: [[SIGNAL:task_complete]]"


def parse_structured_signal(text):
    if not text: return None, None
    match = STRUCTURED_SIGNAL_PATTERN.search(text)
    if match:
        status, message = match.group(1).lower(), match.group(2) or ""
        return (status, message) if status in VALID_SIGNAL_STATUSES else (None, None)
    return None, None


def log(msg):
    try:
        HOOKS_DATA.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except: pass


def get_last_assistant_message(transcript_path):
    try:
        file_path = Path(transcript_path)
        file_size = file_path.stat().st_size
        read_size = min(file_size, 8 * 1024)
        with open(transcript_path, "rb") as f:
            if file_size > read_size: f.seek(file_size - read_size)
            lines = f.read().decode("utf-8", errors="ignore").split("\n")
        if file_size > read_size: lines = lines[1:]
        for line in reversed(lines):
            if not line.strip(): continue
            try:
                entry = json.loads(line.strip())
                if entry.get("type") == "assistant":
                    cont = entry.get("message", {}).get("content", [])
                    if isinstance(cont, list):
                        return " ".join([c.get("text", "") for c in cont if c.get("type") == "text"])
                    elif isinstance(cont, str): return cont
            except: continue
        return None
    except Exception as e:
        log(f"Error reading transcript: {e}")
        return None


def classify_response(text):
    """SIMPLIFIED: Only check explicit signals, no pattern matching"""
    if not text: return "continue_working", "no text found"

    signal_status, signal_message = parse_structured_signal(text)
    if signal_status:
        msg = f"structured signal: {signal_status}"
        if signal_message: msg += f" ({signal_message})"
        return f"signal_{signal_status}", msg

    if "TASK_COMPLETE" in text: return "task_complete", "explicit TASK_COMPLETE keyword"
    if "WORK_COMPLETE" in text: return "work_complete", "explicit WORK_COMPLETE keyword (legacy)"

    return "continue_working", "no explicit completion signal - will restart"


def handle_autonomous_stop(classification, reason):
    log_event("response_classified", "stop_hook", {"classification": classification, "reason": reason})

    # Structured signal: task_complete
    if classification == "signal_task_complete":
        log("Setting task_complete_detected signal (structured)")
        set_global("task_complete_detected", {"timestamp": datetime.now().isoformat(), "reason": reason, "signal_type": "structured"})
        MARKER_FILE.write_text(json.dumps({"timestamp": datetime.now().isoformat(), "signal": "structured", "reason": reason}))
        reset_circuit_breaker()
        log_event("signal_detected", "stop_hook", {"signal": "task_complete", "type": "structured"})
        print("[Stop] [[SIGNAL:task_complete]] - inception restart", file=sys.stderr)
        return 1

    # Structured signal: blocked
    if classification == "signal_blocked":
        log("Setting task_blocked signal (structured)")
        set_global("task_blocked", {"timestamp": datetime.now().isoformat(), "reason": reason, "signal_type": "structured"})
        MARKER_FILE.write_text(json.dumps({"timestamp": datetime.now().isoformat(), "signal": "blocked", "reason": reason}))
        print("[Stop] [[SIGNAL:blocked]] - task blocked, logging", file=sys.stderr)
        return 1

    # Structured signal: error
    if classification == "signal_error":
        log("Setting task_error signal (structured)")
        set_global("task_error", {"timestamp": datetime.now().isoformat(), "reason": reason, "signal_type": "structured"})
        MARKER_FILE.write_text(json.dumps({"timestamp": datetime.now().isoformat(), "signal": "error", "reason": reason}))
        print("[Stop] [[SIGNAL:error]] - task error, logging", file=sys.stderr)
        return 1

    # Structured signal: needs_input
    if classification == "signal_needs_input":
        log("Setting dropout_restart signal (structured needs_input)")
        set_global("dropout_restart", {"message": TICKLER_MESSAGE, "timestamp": datetime.now().isoformat()})
        MARKER_FILE.unlink(missing_ok=True)
        print("[Stop] [[SIGNAL:needs_input]] - triggering restart (autonomous mode)", file=sys.stderr)
        return 1

    # TASK_COMPLETE keyword
    if classification == "task_complete":
        log("Setting task_complete_detected signal (keyword)")
        set_global("task_complete_detected", {"timestamp": datetime.now().isoformat(), "reason": reason, "signal_type": "keyword"})
        MARKER_FILE.write_text(json.dumps({"timestamp": datetime.now().isoformat(), "signal": "TASK_COMPLETE", "reason": reason}))
        reset_circuit_breaker()
        print("[Stop] TASK_COMPLETE - inception restart", file=sys.stderr)
        return 1

    # WORK_COMPLETE keyword (legacy)
    if classification == "work_complete":
        log("Setting work_complete_detected signal (keyword legacy)")
        set_global("work_complete_detected", {"timestamp": datetime.now().isoformat(), "reason": reason, "signal_type": "keyword"})
        MARKER_FILE.write_text(json.dumps({"timestamp": datetime.now().isoformat(), "signal": "WORK_COMPLETE", "reason": reason}))
        print("[Stop] WORK_COMPLETE - checking for more work (legacy)", file=sys.stderr)
        return 1

    # Everything else: restart with tickler
    log(f"Setting dropout_restart signal (continue_working): {reason}")
    set_global("dropout_restart", {"message": TICKLER_MESSAGE, "timestamp": datetime.now().isoformat()})
    MARKER_FILE.unlink(missing_ok=True)
    print("[Stop] No explicit completion signal - restarting with tickler", file=sys.stderr)
    return 1


def main():
    import os
    if not is_autonomous_mode(os.getcwd()): sys.exit(0)

    HOOKS_DATA.mkdir(parents=True, exist_ok=True)
    stdin_data = {}
    try:
        if not sys.stdin.isatty():
            raw = sys.stdin.read()
            if raw.strip(): stdin_data = json.loads(raw)
    except Exception as e:
        stdin_data = {"error": str(e)}

    transcript_path = stdin_data.get("transcript_path")
    last_message, classification, reason = None, "unknown", "no transcript"

    if transcript_path and Path(transcript_path).exists():
        last_message = get_last_assistant_message(transcript_path)
        if last_message:
            analysis_text = last_message[-500:] if len(last_message) > 500 else last_message
            classification, reason = classify_response(analysis_text)

    log(f"Stop: classification={classification}, reason={reason}")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({"timestamp": datetime.now().isoformat(), "classification": classification,
                           "reason": reason, "autonomous_mode": True}, default=str) + "\n")

    exit_code = handle_autonomous_stop(classification, reason)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

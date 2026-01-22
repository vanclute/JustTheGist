#!/usr/bin/env python3
"""Domain anchoring for curiosity learning - keeps topics coherent with original goal"""

import json
from pathlib import Path
from typing import Tuple, Optional


# Domain configuration - defines core topics and allowed expansion paths
DOMAIN_CONFIG = {
    "core_domain": "Tickblaze WPF testing automation and accessibility",
    "core_keywords": [
        "WPF", "UI Automation", "TestComplete", "FlaUI", "accessibility",
        "AutomationPeer", "testing", "trading UI", "custom controls",
        "XAML", ".NET", "C#", "Windows automation"
    ],
    # Adjacent topics that are OK to explore (1 hop away from core)
    "adjacent_keywords": {
        # Performance/optimization tier - relevant for UI performance
        "performance": ["profiling", "diagnostics", "optimization", "rendering", "layout"],
        # Synchronization tier - relevant for real-time UI updates
        "synchronization": ["threading", "reactive", "event handling", "data binding", "throttling"],
        # Architecture tier - relevant for testing complex UIs
        "architecture": ["patterns", "MVVM", "state management", "design patterns"],
        # Related tools - tools that work with WPF testing
        "tools": ["CI/CD", "automation frameworks", "test frameworks", "monitoring"]
    },
    # Off-topic keywords that indicate drift
    "off_topic_keywords": [
        # Infrastructure/network layers not relevant to WPF testing
        "dpdk", "smartnic", "dpu", "kernel bypass", "roce", "dcqcn",
        "data center networking", "collective communication",
        # ML/AI optimization (not testing-related)
        "machine learning", "parameter tuning", "adaptive congestion",
        # Frontend web (RxJS, Angular, React Web, etc - not WPF)
        "rxjs", "angular", "react web", "vue.js",
        # General infrastructure (not Tickblaze-specific)
        "aws", "kubernetes", "containerization"
    ],
    "max_drift_hops": 2  # Max 2 hops from core domain
}


def get_research_context() -> dict:
    """Get original research context from backlog.json if it exists"""
    backlog_path = Path("backlog.json")
    if backlog_path.exists():
        with open(backlog_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "research_context" in data:
                return data["research_context"]

    # Fall back to config
    return {
        "original_goal": DOMAIN_CONFIG["core_domain"],
        "core_keywords": DOMAIN_CONFIG["core_keywords"],
        "adjacent_keywords": DOMAIN_CONFIG["adjacent_keywords"],
        "off_topic_keywords": DOMAIN_CONFIG["off_topic_keywords"],
    }


def score_topic_relevance(topic: str, reason: str = "") -> Tuple[int, str]:
    """Score how relevant a topic is to the original domain

    Returns:
        (score, explanation) where score is:
        - 8-10: Core domain (stays focused on WPF testing automation)
        - 6-7:  Adjacent/adjacent-adjacent (related but expanding scope)
        - 3-5:  Tangential (loosely related, risk of drift)
        - 0-2:  Off-topic (should be filtered out)
    """
    context = get_research_context()
    core_keywords = context.get("core_keywords", DOMAIN_CONFIG["core_keywords"])
    adjacent = context.get("adjacent_keywords", DOMAIN_CONFIG["adjacent_keywords"])
    off_topic = context.get("off_topic_keywords", DOMAIN_CONFIG["off_topic_keywords"])

    combined = f"{topic} {reason}".lower()

    # Check for off-topic keywords first (hard filter)
    for keyword in off_topic:
        if keyword in combined:
            return 0, f"Off-topic keyword detected: '{keyword}'"

    # Score core relevance
    core_matches = sum(1 for kw in core_keywords if kw.lower() in combined)
    if core_matches >= 2:
        return 10, f"Strong core domain relevance ({core_matches} core keywords)"
    if core_matches == 1:
        score = 8
        explanation = f"Core domain focus (mentions: {[kw for kw in core_keywords if kw.lower() in combined][0]})"
        return score, explanation

    # Score adjacent relevance
    adjacent_matches = {}
    for category, keywords in adjacent.items():
        matches = [kw for kw in keywords if kw.lower() in combined]
        if matches:
            adjacent_matches[category] = matches

    if adjacent_matches:
        num_categories = len(adjacent_matches)
        if num_categories >= 2:
            categories = ", ".join(adjacent_matches.keys())
            return 7, f"Multiple adjacent domains: {categories}"
        elif num_categories == 1:
            category = list(adjacent_matches.keys())[0]
            keywords = adjacent_matches[category]
            return 6, f"Related via {category}: {', '.join(keywords)}"

    # Check for tangential relevance
    if "trading" in combined or "tickblaze" in combined or "wpf" in combined:
        return 5, "Mentions trading/WPF context but not directly testing-related"

    if "test" in combined or "automation" in combined or "validation" in combined:
        return 4, "General testing/automation keywords without domain specificity"

    # Complete drift
    return 1, "Too distant from original research goal"


def should_add_topic(topic: str, reason: str = "", position_in_backlog: int = 0) -> Tuple[bool, str]:
    """Decide whether to add a topic to the backlog

    Args:
        topic: The topic to evaluate
        reason: The reason given for adding it
        position_in_backlog: How many topics are already queued (0 = first, 1 = second, etc)

    Returns:
        (should_add, explanation)
    """
    score, explanation = score_topic_relevance(topic, reason)

    # Stricter filters for later topics to prevent drift
    if position_in_backlog < 3:
        # First few topics: must score >= 6 (adjacent relevance minimum)
        threshold = 6
        phase = "Core learning (first 3 topics)"
    else:
        # Later topics: must score >= 5 (tangential minimum)
        threshold = 5
        phase = "Extended exploration (topic 4+)"

    if score >= threshold:
        return True, f"[{phase}] Score {score}/10 - {explanation}"
    else:
        return False, f"[{phase}] Score {score}/10 (threshold: {threshold}) - {explanation}"


def estimate_drift_distance(topic: str, reason: str = "") -> int:
    """Estimate how many hops away from core domain

    0 hops = core domain
    1 hop = directly adjacent to core
    2 hops = adjacent to adjacent topics
    3+ hops = significant drift
    """
    context = get_research_context()
    core_keywords = context.get("core_keywords", DOMAIN_CONFIG["core_keywords"])
    adjacent = context.get("adjacent_keywords", DOMAIN_CONFIG["adjacent_keywords"])

    combined = f"{topic} {reason}".lower()

    # 0 hops: mentions core
    if any(kw.lower() in combined for kw in core_keywords):
        return 0

    # 1 hop: mentions adjacent
    if any(
        any(adj_kw.lower() in combined for adj_kw in keywords)
        for keywords in adjacent.values()
    ):
        return 1

    # Mention of testing/trading generically
    if any(kw in combined for kw in ["test", "trading", "automation"]):
        return 2

    # Everything else is distant
    return 3


if __name__ == "__main__":
    # Test the scoring
    test_topics = [
        ("AutomationPeer implementation for custom WPF controls", "Needed for trading UI"),
        ("UI Automation synchronization patterns", "Real-time updates"),
        ("Reactive Extensions (Rx) patterns", "For streaming data"),
        ("DPDK and kernel bypass", "Network optimization"),
        ("SmartNIC hardware acceleration", "Networking layer"),
        ("WPF Performance Profiling", "Measure bottlenecks"),
        ("RxJS state management", "Observable patterns"),
    ]

    print("Domain Anchor Test Results")
    print("=" * 80)
    for topic, reason in test_topics:
        score, explanation = score_topic_relevance(topic, reason)
        should_add, verdict = should_add_topic(topic, reason, position_in_backlog=0)
        distance = estimate_drift_distance(topic, reason)
        print(f"\nTopic: {topic}")
        print(f"  Reason: {reason}")
        print(f"  Score: {score}/10 - {explanation}")
        print(f"  Distance: {distance} hops from core")
        print(f"  Should add: {should_add} - {verdict}")

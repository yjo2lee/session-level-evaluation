"""
Pilot Study Configuration

This file contains the predefined queries and participant-session assignments
for the controlled pilot study.
"""

# Predefined queries for pilot study
PILOT_QUERIES = {
    "Q1": "I'm planning a 3-day trip to Sapporo. Can you help me plan an itinerary?",
    "Q2": "I'd like to explore Seoul for 3 days. Can you suggest a travel plan?",
    "Q3": "I'm thinking about a 5-6 day trip to Los Angeles. Can you help me plan what to do?",
    "Q4": "I want to visit Paris for 6 days. What should I see and do?"
}

# Participant-session assignment mapping
# Each participant (P1-P4) completes 4 sessions:
# - Sessions 1-2: Comparison Pair 1
# - Sessions 3-4: Comparison Pair 2
# 
# After each pair, participants compare the two sessions and select their preferred one.
PILOT_ASSIGNMENTS = {
    "P1": [
        {"session": 1, "query": "Q1", "assistant": "A", "pair": 1},
        {"session": 2, "query": "Q2", "assistant": "B", "pair": 1},
        {"session": 3, "query": "Q3", "assistant": "B", "pair": 2},
        {"session": 4, "query": "Q4", "assistant": "A", "pair": 2}
    ],
    "P2": [
        {"session": 1, "query": "Q1", "assistant": "B", "pair": 1},
        {"session": 2, "query": "Q2", "assistant": "A", "pair": 1},
        {"session": 3, "query": "Q3", "assistant": "A", "pair": 2},
        {"session": 4, "query": "Q4", "assistant": "B", "pair": 2}
    ],
    "P3": [
        {"session": 1, "query": "Q1", "assistant": "A", "pair": 1},
        {"session": 2, "query": "Q2", "assistant": "B", "pair": 1},
        {"session": 3, "query": "Q3", "assistant": "A", "pair": 2},
        {"session": 4, "query": "Q4", "assistant": "B", "pair": 2}
    ],
    "P4": [
        {"session": 1, "query": "Q1", "assistant": "B", "pair": 1},
        {"session": 2, "query": "Q2", "assistant": "A", "pair": 1},
        {"session": 3, "query": "Q3", "assistant": "B", "pair": 2},
        {"session": 4, "query": "Q4", "assistant": "A", "pair": 2}
    ]
}


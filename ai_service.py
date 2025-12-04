"""
AI service for generating responses from two different assistants using Anthropic Claude API.
Uses ANTHROPIC_API_KEY from Streamlit Secrets (Cloud) or environment variable (local).
"""

import os
from typing import List, Dict
import anthropic
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# Get API key from Streamlit Secrets (Cloud) or environment variable (local)
def get_anthropic_api_key():
    """Get Anthropic API key from Streamlit Secrets or environment variable."""
    # Try Streamlit Secrets first (for Cloud deployment)
    try:
        if hasattr(st, 'secrets') and 'ANTHROPIC_API_KEY' in st.secrets:
            return st.secrets['ANTHROPIC_API_KEY']
    except Exception:
        pass
    
    # Fall back to environment variable (for local development)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        st.error(
            "Anthropic API key is not set. "
            "Set ANTHROPIC_API_KEY in Streamlit Secrets (on Cloud) or as an environment variable locally."
        )
        st.stop()
    return api_key

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=get_anthropic_api_key())

# System prompts for each assistant

# superficial stylistic differences
# SYSTEM_PROMPT_A = """You are a helpful assistant. When responding to the user's messages, always include shiny and interesting emojis that make the conversation feel lively and engaging. Use emojis that match the tone and content of your response (for example ✨, 💡, 🤩, 🎯, 🚀, 🧠). Keep them natural and expressive, not excessive — just enough to make the answer visually fun and emotionally appealing. Do not exceed 100 words in your response."""

# SYSTEM_PROMPT_B = """You are a helpful and friendly assistant. When responding to the user, ask clarifying questions to understand their goals and context, then provide organized, practical, and accurate information tailored to their needs. Offer clear explanations, relevant examples, and, when appropriate, present options or trade-offs to help the user make informed decisions. Keep your tone engaging, concise, and respectful. Do not exceed 100 words in your response."""

# model differences
# SYSTEM_PROMPT_A = """You are a helpful assistant. Do not answer at once. Do not exceed 100 words in your response."""
# SYSTEM_PROMPT_B = """You are a helpful assistant. Do not answer at once. Do not exceed 100 words in your response."""

# superficial stylistic differences
# SYSTEM_PROMPT_A = """You are a travel assistant optimized for quick starting points. Provide a concise, high-level outline without collecting too many details. When the user asks for a travel plan, avoid asking too many questions. Prioritize low friction and simplicity over personalization and optimization. Stay within 100 words. """
SYSTEM_PROMPT_A = """You are a travel assistant optimized for fast, actionable plans.

**APPROACH:**
- Ask at most 1 quick question if essential (otherwise, just start)
- Provide a ready-to-use plan based on smart defaults
- Make reasonable assumptions for typical travelers

**OUTPUT STYLE:**
- Lead with your top recommendation, not options
- Brief day structure (morning/afternoon/evening)
- Include 1-2 insider tips that add real value
- Mention one alternative only if highly relevant

**TONE:**
- Confident and helpful
- Sound like a friend who's been there

**CONSTRAINTS:**
- Stay within 100 words
- Prioritize speed and clarity over completeness
"""

SYSTEM_PROMPT_B = """You are an interactive travel-planning assistant focused on creating 
personalized, executable itineraries.

**INTERACTION STYLE:**
- Turn 1: When user requests a plan, immediately provide 1-2 sentence "preview" of what you're thinking + 1-2 focused questions
- Turn 2: Provide partial plan, rather than a full, detailed plan. 
- From the second turn, ask 1 **specific** follow-up to refine the user's travel style as the chat goes on
- Reveal the plan gradually—never dump a complete itinerary at once
- Each response should move the plan forward AND invite input

**QUESTIONS:**
- You need to ask questions that can identify each user's travel style.
- Make choices easy: "packed days or breathing room?" not "what is your preferred pace?"
- Cover:
- Travel pace preferences (relaxed vs. packed schedule)
- Specific interests (culture, food, nature, adventure, relaxation, etc.)
- Important constraints (budget level, mobility considerations, dietary restrictions, travel companions)
- Priorities or must-see/must-do items

**PROVIDING THE ITINERARY:**
Your itinerary should include:
- **Day-by-day structure**: Organize activities chronologically by day
- **Options and alternatives**: Offer 1-2 alternatives inline, explaining trade-offs if relevant. When explaining each option, a bit of explanation can help users understand new places.
- **Clear sequencing**: Show logical flow and timing (morning, afternoon, evening)
- **Contextual tips**: Weave practical advice into the narrative (booking tips, timing, what to bring, how to get there)
- **Realistic pacing**: Account for travel time, meals, and rest

**IMPORTANT CONSTRAINTS:**
- Keep responses not too verbose (if needed, you can use bullet points or emojis)
- Expand only as needed to cover specifics
- Respond in ≤100 words unless the user provides extensive details requiring a full itinerary ("looks good" or "finalize")
- Provide accurate, factual information only
- If you don't know specific details (prices, hours, current conditions), acknowledge this
- Stay focused on the destination and dates mentioned by the user"""

# """You are a helpful assistant. When helping the user with travel planning, act as a friendly and knowledgeable assistant who asks clarifying questions to understand their goals—such as budget, duration, interests, and travel companions—then provides organized and practical suggestions including itineraries, local highlights, transportation tips, and safety information. Whenever relevant, offer options and trade-offs (for example, noting that one route may be faster while another is more scenic) to help the user make informed decisions. Do not exceed 100 words in your response."""


# Model configuration - Using Claude Sonnet 4
MODEL_A = "claude-sonnet-4-20250929"  # Model name for Assistant A
MODEL_B = "claude-sonnet-4-20250929"  # Model name for Assistant B

def generate_response_a(conversation_history: List[Dict[str, str]], user_message: str) -> str:
    """
    Generate a response from Assistant A using Anthropic Claude API.

    Args:
        conversation_history: List of previous messages [{'role': 'user'/'assistant', 'content': '...'}]
        user_message: The current user message

    Returns:
        The assistant's response
    """
    # Build messages list (Anthropic format)
    messages = []
    
    # Add conversation history
    for msg in conversation_history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Add current user message
    messages.append({"role": "user", "content": user_message})

    # Call Anthropic API
    response = client.messages.create(
        model=MODEL_A,
        max_tokens=1024,
        system=SYSTEM_PROMPT_A,
        messages=messages
    )

    return response.content[0].text

def generate_response_b(conversation_history: List[Dict[str, str]], user_message: str) -> str:
    """
    Generate a response from Assistant B using Anthropic Claude API.

    Args:
        conversation_history: List of previous messages [{'role': 'user'/'assistant', 'content': '...'}]
        user_message: The current user message

    Returns:
        The assistant's response
    """
    # Build messages list (Anthropic format)
    messages = []
    
    # Add conversation history
    for msg in conversation_history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Add current user message
    messages.append({"role": "user", "content": user_message})

    # Call Anthropic API
    response = client.messages.create(
        model=MODEL_B,
        max_tokens=1024,
        system=SYSTEM_PROMPT_B,
        messages=messages
    )

    return response.content[0].text

def get_assistant_response(assistant_name: str, conversation_history: List[Dict[str, str]], user_message: str) -> str:
    """
    Get a response from the specified assistant.

    Args:
        assistant_name: Either 'A' or 'B'
        conversation_history: List of previous messages
        user_message: The current user message

    Returns:
        The assistant's response
    """
    if assistant_name == 'A':
        return generate_response_a(conversation_history, user_message)
    elif assistant_name == 'B':
        return generate_response_b(conversation_history, user_message)
    else:
        raise ValueError(f"Unknown assistant: {assistant_name}")

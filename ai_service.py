"""
AI service for generating responses from two different assistants using OpenAI API.
Uses environment variable OPENAI_API_KEY for authentication.
"""

import os
from typing import List, Dict
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# System prompts for each assistant
SYSTEM_PROMPT_A = """You are a helpful assistant. When responding to the user’s messages, always include shiny and interesting emojis that make the conversation feel lively and engaging. Use emojis that match the tone and content of your response (for example ✨, 💡, 🤩, 🎯, 🚀, 🧠). Keep them natural and expressive, not excessive — just enough to make the answer visually fun and emotionally appealing. Do not exceed 100 words in your response."""

SYSTEM_PROMPT_B = """You are a helpful and friendly assistant. When responding to the user, ask clarifying questions to understand their goals and context, then provide organized, practical, and accurate information tailored to their needs. Offer clear explanations, relevant examples, and, when appropriate, present options or trade-offs to help the user make informed decisions. Keep your tone engaging, concise, and respectful. Do not exceed 100 words in your response."""

# """You are a helpful assistant. When helping the user with travel planning, act as a friendly and knowledgeable assistant who asks clarifying questions to understand their goals—such as budget, duration, interests, and travel companions—then provides organized and practical suggestions including itineraries, local highlights, transportation tips, and safety information. Whenever relevant, offer options and trade-offs (for example, noting that one route may be faster while another is more scenic) to help the user make informed decisions. Do not exceed 100 words in your response."""


# Model configuration
MODEL_A = "gpt-4o"  # Model name for Assistant A
MODEL_B = "gpt-4o"  # Model name for Assistant B

def generate_response_a(conversation_history: List[Dict[str, str]], user_message: str) -> str:
    """
    Generate a response from Assistant A using OpenAI API.

    Args:
        conversation_history: List of previous messages [{'role': 'user'/'assistant', 'content': '...'}]
        user_message: The current user message

    Returns:
        The assistant's response
    """
    # Build messages list with system prompt
    messages = [{"role": "system", "content": SYSTEM_PROMPT_A}]

    # Add conversation history
    messages.extend(conversation_history)

    # Add current user message
    messages.append({"role": "user", "content": user_message})

    # Call OpenAI API
    response = client.chat.completions.create(
        model=MODEL_A,
        messages=messages,
        temperature=0.7
    )

    return response.choices[0].message.content

def generate_response_b(conversation_history: List[Dict[str, str]], user_message: str) -> str:
    """
    Generate a response from Assistant B using OpenAI API.

    Args:
        conversation_history: List of previous messages [{'role': 'user'/'assistant', 'content': '...'}]
        user_message: The current user message

    Returns:
        The assistant's response
    """
    # Build messages list with system prompt
    messages = [{"role": "system", "content": SYSTEM_PROMPT_B}]

    # Add conversation history
    messages.extend(conversation_history)

    # Add current user message
    messages.append({"role": "user", "content": user_message})

    # Call OpenAI API
    response = client.chat.completions.create(
        model=MODEL_B,
        messages=messages,
        temperature=0.7
    )

    return response.choices[0].message.content

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

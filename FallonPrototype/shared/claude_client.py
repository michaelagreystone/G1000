"""
Shared LLM API client for all Fallon sub-agents.
Uses Nvidia NIM API with Kimi K2 model (OpenAI-compatible endpoint).
Every agent imports call_claude() from here — never calls the API directly.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load .env from project root (G1000/.env has the NVIDIA_API_KEY)
_root_env = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=_root_env)

# Nvidia NIM API configuration
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL = "moonshotai/kimi-k2-instruct"  # Kimi K2 model on Nvidia NIM

# Single shared client — initialized once at import time
_client = OpenAI(
    base_url=NVIDIA_BASE_URL,
    api_key=os.environ.get("NVIDIA_API_KEY"),
)

# Session-level token usage tracker — accumulated across all calls in one run
_session_usage = {
    "input_tokens": 0,
    "output_tokens": 0,
}

# Nvidia NIM is free tier, but track usage anyway
_PRICE_PER_M_INPUT = 0.0
_PRICE_PER_M_OUTPUT = 0.0


def call_claude(system_prompt: str, user_message: str, max_tokens: int = 2048) -> str:
    """
    Send a message to the LLM and return the response text as a plain string.
    
    Note: Function name kept as call_claude() for backward compatibility,
    but now uses Nvidia NIM API with Kimi K2 model.

    All sub-agents call this function. It handles:
    - API errors with a clean message (no stack traces in the UI)
    - Token usage tracking for the session cost display

    Args:
        system_prompt: The system-level instruction for the model's role/behavior.
        user_message:  The user's query or content to process.
        max_tokens:    Maximum tokens in the response. Default 2048 is sufficient
                       for most contract answers and financial summaries. Increase
                       to 4096 for full pro forma JSON generation.

    Returns:
        The response text as a plain string, or an error message string if the
        API call fails. Callers should check for strings starting with "ERROR:"
        if they need to distinguish failures from valid responses.
    """
    try:
        response = _client.chat.completions.create(
            model=MODEL,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )

        # Accumulate token usage for the session cost tracker
        if response.usage:
            _session_usage["input_tokens"] += response.usage.prompt_tokens or 0
            _session_usage["output_tokens"] += response.usage.completion_tokens or 0

        return response.choices[0].message.content

    except Exception as e:
        error_str = str(e)
        if "401" in error_str or "authentication" in error_str.lower():
            return "ERROR: Invalid API key. Check your NVIDIA_API_KEY in .env"
        elif "429" in error_str or "rate" in error_str.lower():
            return "ERROR: Rate limit reached. Wait a moment and try again."
        else:
            return f"ERROR: Unexpected error calling Nvidia NIM API — {error_str}"


def get_session_usage() -> dict:
    """
    Return total token usage and estimated cost for the current session.
    Called by the Streamlit sidebar to display live cost tracking.

    Returns a dict:
        {
            "input_tokens":  int,
            "output_tokens": int,
            "total_tokens":  int,
            "estimated_cost_usd": float  (rounded to 4 decimal places)
        }
    """
    input_t = _session_usage["input_tokens"]
    output_t = _session_usage["output_tokens"]
    cost = (input_t / 1_000_000 * _PRICE_PER_M_INPUT) + (
        output_t / 1_000_000 * _PRICE_PER_M_OUTPUT
    )
    return {
        "input_tokens": input_t,
        "output_tokens": output_t,
        "total_tokens": input_t + output_t,
        "estimated_cost_usd": round(cost, 4),
    }


def reset_session_usage() -> None:
    """Reset the session token counter. Called by the 'Clear Session' button in the UI."""
    _session_usage["input_tokens"] = 0
    _session_usage["output_tokens"] = 0

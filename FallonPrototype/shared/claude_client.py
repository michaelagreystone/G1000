"""
Shared Claude API client for all Fallon sub-agents.
Every agent imports call_claude() from here — never calls the API directly.
"""

import os
import anthropic
from dotenv import load_dotenv

# Load .env from the FallonPrototype directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# Single shared client — initialized once at import time
_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# All agents use the same model. Change it here and it updates everywhere.
MODEL = "claude-sonnet-4-6"

# Session-level token usage tracker — accumulated across all calls in one run
_session_usage = {
    "input_tokens": 0,
    "output_tokens": 0,
}

# Approximate pricing for claude-sonnet-4-6 (per million tokens)
_PRICE_PER_M_INPUT = 3.00
_PRICE_PER_M_OUTPUT = 15.00


def call_claude(system_prompt: str, user_message: str, max_tokens: int = 2048) -> str:
    """
    Send a message to Claude and return the response text as a plain string.

    All sub-agents call this function. It handles:
    - API errors with a clean message (no stack traces in the UI)
    - Token usage tracking for the session cost display

    Args:
        system_prompt: The system-level instruction for Claude's role/behavior.
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
        response = _client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        # Accumulate token usage for the session cost tracker
        _session_usage["input_tokens"] += response.usage.input_tokens
        _session_usage["output_tokens"] += response.usage.output_tokens

        return response.content[0].text

    except anthropic.AuthenticationError:
        return "ERROR: Invalid API key. Check your ANTHROPIC_API_KEY in FallonPrototype/.env"

    except anthropic.RateLimitError:
        return "ERROR: Rate limit reached. Wait a moment and try again."

    except anthropic.APIStatusError as e:
        return f"ERROR: Claude API returned status {e.status_code}. Details: {e.message}"

    except Exception as e:
        return f"ERROR: Unexpected error calling Claude — {str(e)}"


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

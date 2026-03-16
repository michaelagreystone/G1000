"""
LLM client for Contract Reviewer.
Uses NVIDIA NIM API with Kimi K2 model (OpenAI-compatible endpoint).
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load .env from parent dirs (G1000/.env has the NVIDIA_API_KEY)
_this_dir = os.path.dirname(os.path.abspath(__file__))
for _up in [
    os.path.join(_this_dir, "..", "..", ".env"),   # G1000/.env
    os.path.join(_this_dir, "..", ".env"),          # ContractReviewer/.env
]:
    if os.path.exists(_up):
        load_dotenv(dotenv_path=_up)
        break

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL = "moonshotai/kimi-k2-instruct"

_client = OpenAI(
    base_url=NVIDIA_BASE_URL,
    api_key=os.environ.get("NVIDIA_API_KEY"),
)


def call_llm(system_prompt: str, user_message: str, max_tokens: int = 4096) -> str:
    """Send a message to the LLM and return the response text."""
    try:
        response = _client.chat.completions.create(
            model=MODEL,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content

    except Exception as e:
        error_str = str(e)
        if "401" in error_str or "authentication" in error_str.lower():
            return "ERROR: Invalid API key. Check your NVIDIA_API_KEY in .env"
        elif "429" in error_str or "rate" in error_str.lower():
            return "ERROR: Rate limit reached. Wait a moment and try again."
        else:
            return f"ERROR: Unexpected error calling NVIDIA NIM API — {error_str}"

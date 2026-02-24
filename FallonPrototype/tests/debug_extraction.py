"""Debug script to see what Claude returns."""

import sys
import os
_PROTO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(_PROTO_DIR))

from FallonPrototype.shared.claude_client import call_claude
from FallonPrototype.agents.financial_agent import EXTRACTION_SYSTEM_PROMPT

query = "200 units in Charlotte"
print(f"Query: {query}")
print(f"\nSystem prompt length: {len(EXTRACTION_SYSTEM_PROMPT)} chars")
print("\nCalling Claude...")

response = call_claude(EXTRACTION_SYSTEM_PROMPT, query, max_tokens=512)
print(f"\nRaw response:\n{response}")

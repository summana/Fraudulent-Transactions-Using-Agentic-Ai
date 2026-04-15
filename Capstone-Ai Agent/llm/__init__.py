"""LLM integration package.

Exposes the Ollama client functions for fraud analysis.
"""

from llm.ollama_client import call_ollama, build_llm_prompt

__all__ = [
    "call_ollama",
    "build_llm_prompt",
]

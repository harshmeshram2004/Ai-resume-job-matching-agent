"""Local LLM provider stub - falls back to rule-based when no cloud LLM available."""
from __future__ import annotations
from .base import LLMProvider


class LocalLLMProvider(LLMProvider):
    """No-op provider that always signals unavailable so the pipeline falls back
    to deterministic rule-based extraction. This exists so the LLM interface is
    swappable (e.g., wire up Ollama here later)."""

    @property
    def name(self) -> str:
        return "local:rule-based"

    @property
    def available(self) -> bool:
        return False

    def complete(self, system: str, user: str, temperature: float = 0.1) -> str:
        raise RuntimeError("LocalLLMProvider is not wired to a live model.")

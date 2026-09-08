"""LLM provider abstraction."""
from __future__ import annotations
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract LLM provider interface."""

    @abstractmethod
    def complete(self, system: str, user: str, temperature: float = 0.1) -> str:
        """Synchronously return a completion string."""
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    def available(self) -> bool:
        return True

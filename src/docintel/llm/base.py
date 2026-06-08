from __future__ import annotations

from abc import ABC, abstractmethod


class LocalLLM(ABC):
    name: str

    @abstractmethod
    def complete(self, prompt: str) -> str:
        """Return a model completion as plain text."""


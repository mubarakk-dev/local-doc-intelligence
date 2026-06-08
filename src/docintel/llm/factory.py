from __future__ import annotations

from docintel.llm.base import LocalLLM
from docintel.llm.heuristic import HeuristicLLM


def build_llm(name: str, model: str | None = None) -> LocalLLM:
    normalized = name.lower().strip()
    if normalized == "heuristic":
        return HeuristicLLM()
    if normalized == "ollama":
        from docintel.llm.ollama import OllamaLLM

        return OllamaLLM(model=model or "qwen2.5:1.5b")
    raise ValueError(f"Unknown LLM '{name}'. Choose from: heuristic, ollama.")

from __future__ import annotations

from docintel.llm.base import LocalLLM


class OllamaLLM(LocalLLM):
    name = "ollama"

    def __init__(
        self,
        model: str = "qwen2.5:1.5b",
        host: str = "http://localhost:11434",
        temperature: float = 0.0,
        top_k: int = 20,
        timeout: int = 120,
    ) -> None:
        self.model = model
        self.host = host.rstrip("/")
        self.temperature = temperature
        self.top_k = top_k
        self.timeout = timeout

    def complete(self, prompt: str) -> str:
        try:
            import requests
        except ImportError as exc:
            raise RuntimeError(
                "The Ollama backend requires requests. Install project dependencies with: "
                "python -m pip install -e ."
            ) from exc

        response = requests.post(
            f"{self.host}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": self.temperature,
                    "top_k": self.top_k,
                },
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        return str(payload["response"])

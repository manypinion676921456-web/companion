"""
Avcore — Companion's core model wrapper.

This module is intentionally the ONLY place that knows how inference
actually happens. Everything else (server, memory, tools) calls
`Avcore.generate()` and doesn't care whether that's Ollama today or
a fine-tuned custom checkpoint later. That's the "swappable plug-in"
principle: replace this file's internals, keep the interface.

Requires Ollama running locally: https://ollama.com
    ollama pull llama3.1:8b     (or qwen2.5:7b)
    ollama serve                (usually starts automatically on Windows)
"""

import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "llama3.1:8b"

AVCORE_SYSTEM_PROMPT = """You are Avcore, the core model powering Companion,
a personal AI assistant. Be direct, helpful, and clear. If you don't know
something current or factual, say so rather than guessing."""


class Avcore:
    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name

    def generate(self, user_message: str, history: list[dict] | None = None) -> str:
        """
        Generate a response from Avcore.

        history: list of {"role": "user"|"assistant", "content": str}
                 representing prior turns (pulled from memory by the caller).
        """
        messages = [{"role": "system", "content": AVCORE_SYSTEM_PROMPT}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "stream": False,
                },
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]

        except requests.exceptions.ConnectionError:
            return (
                "Avcore can't reach Ollama. Make sure it's installed and running "
                "(`ollama serve`), and that the model is pulled "
                f"(`ollama pull {self.model_name}`)."
            )
        except Exception as e:
            return f"Avcore hit an error: {e}"


# Quick manual test: `python core/model/avcore.py`
if __name__ == "__main__":
    avcore = Avcore()
    print(avcore.generate("Say hello in one short sentence."))

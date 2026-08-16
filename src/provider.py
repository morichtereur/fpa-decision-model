"""Model access behind one interface, so the provider is configuration.

The commentary layer needs exactly one capability: a system prompt, a user
prompt, and text back. That is the common denominator across the Anthropic
API, Bedrock, Vertex and OpenAI-compatible endpoints, so it is the whole
contract — a wider one would abstract over differences this project does not
use.

Deliberately duplicated rather than shared with the sibling repositories:
each is a standalone project a reader can clone and run, and a private
package dependency between portfolio repos would buy consistency at the cost
of that.

Swapping providers means adding a class here and setting `LLM_PROVIDER` —
not touching `src/commentary.py`. The forecast never calls a model at all,
so nothing about the numbers depends on this choice.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Completion:
    text: str
    usage: dict  # {"input_tokens": int, "output_tokens": int}


class Provider(Protocol):
    name: str

    def complete(self, *, system: str, user: str, model: str, max_tokens: int) -> Completion:
        ...


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str | None = None):
        # Imported here, not at module scope: verify_grounding() is the tested
        # half of the trust layer and must import without the SDK installed.
        import anthropic

        from src import config as C

        self._client = anthropic.Anthropic(api_key=api_key or C.ANTHROPIC_API_KEY)

    def complete(self, *, system: str, user: str, model: str, max_tokens: int) -> Completion:
        message = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return Completion(
            text="".join(block.text for block in message.content if block.type == "text"),
            usage={
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
            },
        )


PROVIDERS: dict[str, type] = {
    "anthropic": AnthropicProvider,
}


def get_provider(name: str | None = None) -> Provider:
    """Unknown names fail loudly rather than falling back to a default the
    caller did not ask for — a silent fallback would bill the wrong account."""
    resolved = (name or os.getenv("LLM_PROVIDER") or "anthropic").strip().lower()
    if resolved not in PROVIDERS:
        raise ValueError(
            f"Unknown LLM_PROVIDER {resolved!r}. Available: {sorted(PROVIDERS)}. "
            "Adding one means implementing Provider.complete() in src/provider.py."
        )
    return PROVIDERS[resolved]()

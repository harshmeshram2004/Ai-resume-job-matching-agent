"""Cloud LLM provider using emergentintegrations."""
from __future__ import annotations
import asyncio
import os
import uuid
from typing import Optional

from .base import LLMProvider


class CloudLLMProvider(LLMProvider):
    """Uses Emergent Universal LLM key with a configurable provider/model."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "openai",
        model: str = "gpt-5.4",
    ) -> None:
        self.api_key = api_key or os.environ.get("EMERGENT_LLM_KEY", "")
        self.provider = provider
        self.model = model

    @property
    def name(self) -> str:
        return f"{self.provider}:{self.model}"

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def complete(self, system: str, user: str, temperature: float = 0.1) -> str:
        if not self.available:
            raise RuntimeError(
                "No EMERGENT_LLM_KEY set. Configure it in backend/.env."
            )

        from emergentintegrations.llm.chat import LlmChat, UserMessage

        async def _run() -> str:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"resume-agent-{uuid.uuid4().hex[:8]}",
                system_message=system,
            ).with_model(self.provider, self.model)
            response = await chat.send_message(UserMessage(text=user))
            # Response may be a string or an object with .text/.content
            if isinstance(response, str):
                return response
            for attr in ("text", "content", "message"):
                if hasattr(response, attr):
                    val = getattr(response, attr)
                    if isinstance(val, str):
                        return val
            return str(response)

        try:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(_run())
            finally:
                loop.close()
        except RuntimeError:
            # If already in a loop (Streamlit), use run
            return asyncio.run(_run())

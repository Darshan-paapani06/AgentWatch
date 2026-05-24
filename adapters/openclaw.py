"""OpenClaw adapter."""

from __future__ import annotations

import uuid
from typing import Any

from agentwatch.core.event_bus import EventBus, get_event_bus
from agentwatch.core.schema import AgentEvent, AgentFramework, EventType


class OpenClawAdapter:
    def __init__(
        self,
        session_id: str | None = None,
        agent_id: str | None = None,
        event_bus: EventBus | None = None,
    ):
        self.session_id = session_id or str(uuid.uuid4())
        self.agent_id = agent_id or f"openclaw-{uuid.uuid4().hex[:8]}"
        self._bus = event_bus or get_event_bus()

    async def _publish(self, event: AgentEvent) -> AgentEvent:
        await self._bus.publish(event)
        return event

    def _build_event(self, metadata: dict[str, Any]) -> AgentEvent:
        return AgentEvent(
            session_id=self.session_id,
            agent_id=self.agent_id,
            framework=AgentFramework.OPENCLAW,
            event_type=EventType.CUSTOM,
            metadata=metadata,
        )

    async def emit_observation(self, payload: dict[str, Any]) -> AgentEvent:
        return await self._publish(self._build_event(payload))

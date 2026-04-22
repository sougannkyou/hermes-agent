"""
Orchestrator for AGP

Single-agent mode — runs one Hermes AIAgent per request.
The agent uses delegate_task internally if it needs sub-agents.
"""

import asyncio
import logging
from typing import Any, AsyncGenerator, Dict, Optional

from .adapter import HermesAdapter
from .session import get_session_manager
from .types import (
    AgentRequest,
    EventType,
    GatewayEvent,
)

logger = logging.getLogger(__name__)


class Orchestrator:
    """Runs a single Hermes AIAgent per request."""

    def __init__(self):
        self.session_manager = get_session_manager()
        self._active_adapters: Dict[str, HermesAdapter] = {}

    async def run_session(
        self,
        request: AgentRequest,
    ) -> AsyncGenerator[GatewayEvent, None]:
        session = self.session_manager.get_or_create_session(
            session_id=request.session_id,
            context=request.context,
        )

        yield GatewayEvent(event=EventType.SESSION_START, data={"sessionId": session.id})

        self.session_manager.add_message(
            session.id, role="user", content=request.message.content,
        )

        # Use the first agent definition (primary agent)
        agent_def = request.agents[0] if request.agents else None
        if not agent_def:
            yield GatewayEvent(event=EventType.ERROR, data={
                "code": "NO_AGENT", "message": "No agent definition provided",
            })
            return

        yield GatewayEvent(
            event=EventType.AGENT_START,
            data={"agentId": agent_def.id, "agentName": agent_def.name},
        )

        # Run the agent
        adapter = HermesAdapter()
        self._active_adapters[session.id] = adapter

        accumulated = ""
        try:
            history = self.session_manager.get_messages(session.id)
            if history and history[-1].get("role") == "user":
                history = history[:-1]

            adapter.run(
                agent_def=agent_def,
                message=request.message.content,
                context=session.context,
                model_config=request.model,
                history=history if history else None,
                session_id=session.id,
            )

            for event in adapter.get_events(timeout=0.1):
                if event.event == EventType.TEXT_DONE:
                    accumulated = event.data.get("fullContent", "")
                yield event
                await asyncio.sleep(0.01)

        finally:
            adapter.stop()
            self._active_adapters.pop(session.id, None)

        yield GatewayEvent(event=EventType.AGENT_END, data={"agentId": agent_def.id})

        if accumulated:
            self.session_manager.add_message(
                session.id, role="assistant", content=accumulated, agent_id=agent_def.id,
            )

        yield GatewayEvent(
            event=EventType.SESSION_END,
            data={"sessionId": session.id, "reason": "completed"},
        )

    def interrupt(self, session_id: str) -> bool:
        adapter = self._active_adapters.get(session_id)
        if adapter:
            adapter.stop()
            return True
        return False


_orchestrator = None

def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator

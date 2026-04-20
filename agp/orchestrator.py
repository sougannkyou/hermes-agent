"""
Orchestrator for AGP

Manages multi-agent coordination, handoffs, and event streaming.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

from .adapter import HermesAdapter
from .session import Session, get_session_manager
from .types import (
    AgentDefinition,
    AgentRequest,
    EventType,
    GatewayEvent,
    ModelConfig,
)

logger = logging.getLogger(__name__)


class Orchestrator:
    """Orchestrates multi-agent conversations."""
    
    def __init__(self):
        self.session_manager = get_session_manager()
        self._active_adapters: Dict[str, HermesAdapter] = {}
    
    async def run_session(
        self,
        request: AgentRequest,
    ) -> AsyncGenerator[GatewayEvent, None]:
        """
        Run a chat session and yield events.
        
        This is the main entry point for handling a chat request.
        """
        # Get or create session
        session = self.session_manager.get_or_create_session(
            session_id=request.session_id,
            context=request.context,
        )
        
        # Emit session start
        yield GatewayEvent(
            event=EventType.SESSION_START,
            data={"sessionId": session.id}
        )
        
        # Add user message to history
        self.session_manager.add_message(
            session.id,
            role="user",
            content=request.message.content,
        )
        
        # Determine initial agent
        agents_by_id = {a.id: a for a in request.agents}
        current_agent_id = request.initial_agent_id or request.agents[0].id
        
        if current_agent_id not in agents_by_id:
            yield GatewayEvent(
                event=EventType.ERROR,
                data={
                    "code": "INVALID_AGENT",
                    "message": f"Agent '{current_agent_id}' not found in request",
                }
            )
            return
        
        # Run agent loop (supports handoffs)
        max_handoffs = 5
        handoff_count = 0
        accumulated_content = ""
        
        while handoff_count < max_handoffs:
            agent_def = agents_by_id[current_agent_id]
            self.session_manager.set_current_agent(session.id, current_agent_id)
            
            # Emit agent start
            yield GatewayEvent(
                event=EventType.AGENT_START,
                data={
                    "agentId": agent_def.id,
                    "agentName": agent_def.name,
                }
            )
            
            # Run the agent
            handoff_target = None
            handoff_reason = None
            
            async for event in self._run_agent(
                session=session,
                agent_def=agent_def,
                message=request.message.content,
                model_config=request.model,
            ):
                # Check for handoff in the response
                if event.event == EventType.TEXT_DONE:
                    accumulated_content = event.data.get("fullContent", "")
                    # Check if content contains handoff instruction
                    handoff_info = self._detect_handoff(
                        accumulated_content, 
                        agent_def.can_handoff_to,
                        agents_by_id,
                    )
                    if handoff_info:
                        handoff_target, handoff_reason = handoff_info
                
                yield event
            
            # Emit agent end
            yield GatewayEvent(
                event=EventType.AGENT_END,
                data={"agentId": agent_def.id}
            )
            
            # Add assistant message to history
            if accumulated_content:
                self.session_manager.add_message(
                    session.id,
                    role="assistant",
                    content=accumulated_content,
                    agent_id=agent_def.id,
                )
            
            # Handle handoff
            if handoff_target and handoff_target in agents_by_id:
                yield GatewayEvent(
                    event=EventType.AGENT_HANDOFF,
                    data={
                        "from": current_agent_id,
                        "to": handoff_target,
                        "reason": handoff_reason or "Agent requested handoff",
                    }
                )
                current_agent_id = handoff_target
                handoff_count += 1
                accumulated_content = ""
                continue
            
            # No handoff, we're done
            break
        
        # Emit session end
        yield GatewayEvent(
            event=EventType.SESSION_END,
            data={
                "sessionId": session.id,
                "reason": "completed",
            }
        )
    
    async def _run_agent(
        self,
        session: Session,
        agent_def: AgentDefinition,
        message: str,
        model_config: Optional[ModelConfig],
    ) -> AsyncGenerator[GatewayEvent, None]:
        """Run a single agent and yield events."""
        adapter = HermesAdapter()
        self._active_adapters[session.id] = adapter
        
        try:
            # Get conversation history
            history = self.session_manager.get_messages(session.id)
            # Remove the last message (current user message) since we pass it separately
            if history and history[-1].get("role") == "user":
                history = history[:-1]
            
            # Start the agent in background
            adapter.run(
                agent_def=agent_def,
                message=message,
                context=session.context,
                model_config=model_config,
                history=history if history else None,
            )
            
            # Yield events from the adapter
            for event in adapter.get_events(timeout=0.1):
                yield event
                # Small delay to prevent tight loop
                await asyncio.sleep(0.01)
                
        finally:
            adapter.stop()
            self._active_adapters.pop(session.id, None)
    
    def _detect_handoff(
        self,
        content: str,
        allowed_targets: List[str],
        agents_by_id: Dict[str, AgentDefinition],
    ) -> Optional[tuple]:
        """
        Detect if the agent wants to handoff to another agent.
        
        Returns (target_agent_id, reason) or None.
        """
        if not allowed_targets:
            return None
        
        content_lower = content.lower()
        
        # Look for explicit handoff patterns
        handoff_patterns = [
            "让我请",
            "我需要请",
            "交给",
            "请求",
            "handoff to",
            "let me ask",
            "i need to consult",
        ]
        
        for target_id in allowed_targets:
            if target_id not in agents_by_id:
                continue
            
            target_name = agents_by_id[target_id].name.lower()
            
            # Check if target is mentioned with handoff intent
            for pattern in handoff_patterns:
                if pattern in content_lower and target_name in content_lower:
                    return (target_id, f"Handoff to {agents_by_id[target_id].name}")
        
        return None
    
    def interrupt(self, session_id: str) -> bool:
        """Interrupt an active session."""
        adapter = self._active_adapters.get(session_id)
        if adapter:
            adapter.stop()
            return True
        return False


# Global orchestrator instance
_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    """Get the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator

"""
Hermes Adapter for AGP

Maps Hermes AIAgent callbacks to AGP events.
"""

import json
import logging
import queue
import threading
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

from .types import (
    AgentDefinition,
    EventType,
    GatewayEvent,
    ModelConfig,
)

logger = logging.getLogger(__name__)


class HermesAdapter:
    """Adapter that runs Hermes AIAgent and emits AGP events."""
    
    def __init__(self):
        self.event_queue: queue.Queue[GatewayEvent] = queue.Queue()
        self._stop_event = threading.Event()
        self._current_agent_id: Optional[str] = None
        self._tool_start_times: Dict[str, float] = {}
        self._full_content: str = ""
    
    def run(
        self,
        agent_def: AgentDefinition,
        message: str,
        context: Dict[str, Any],
        model_config: Optional[ModelConfig] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Run the Hermes agent in a background thread.
        Events are pushed to self.event_queue.
        """
        self._current_agent_id = agent_def.id
        self._full_content = ""
        self._stop_event.clear()
        
        thread = threading.Thread(
            target=self._run_agent,
            args=(agent_def, message, context, model_config, history),
            daemon=True,
        )
        thread.start()
    
    def _run_agent(
        self,
        agent_def: AgentDefinition,
        message: str,
        context: Dict[str, Any],
        model_config: Optional[ModelConfig],
        history: Optional[List[Dict[str, Any]]],
    ) -> None:
        """Internal method that runs in a thread."""
        try:
            from run_agent import AIAgent
            from tools.skills_tool import skill_view
            
            # Build system prompt with skills
            system_prompt = agent_def.persona
            
            # Preload skills if specified
            if agent_def.skills:
                skill_contents = []
                for skill_name in agent_def.skills:
                    try:
                        result = json.loads(skill_view(skill_name))
                        if result.get("success"):
                            skill_contents.append(f"\n\n## Skill: {skill_name}\n\n{result.get('content', '')}")
                            logger.info(f"Loaded skill: {skill_name}")
                        else:
                            logger.warning(f"Failed to load skill {skill_name}: {result.get('error')}")
                    except Exception as e:
                        logger.warning(f"Error loading skill {skill_name}: {e}")
                
                if skill_contents:
                    system_prompt = system_prompt + "\n\n# Preloaded Skills\n" + "\n".join(skill_contents)
            
            # Add context to system prompt
            if context:
                context_str = json.dumps(context, ensure_ascii=False, indent=2)
                system_prompt = system_prompt + f"\n\n# Current Context\n```json\n{context_str}\n```"
            
            # Determine model and provider
            # Default to MiniMax provider with MiniMax-Text-01 model
            model = "MiniMax-M2.7"
            provider = "minimax"
            api_key = None
            if model_config:
                model = model_config.name or model
                provider = model_config.provider or provider
                api_key = model_config.api_key
            
            # Build prefill messages (history only, current message is passed to chat())
            messages = []
            if history:
                messages.extend(history)
            
            # Create agent with callbacks
            agent = AIAgent(
                model=model,
                provider=provider,
                api_key=api_key,
                ephemeral_system_prompt=system_prompt,
                prefill_messages=messages if messages else None,
                stream_delta_callback=self._on_stream_delta,
                tool_start_callback=self._on_tool_start,
                tool_complete_callback=self._on_tool_complete,
                tool_progress_callback=self._on_tool_progress,
                tool_gen_callback=self._on_tool_gen,
                thinking_callback=self._on_thinking,
                status_callback=self._on_status,
                # Enable skills tools
                enabled_toolsets=["skills", "web", "terminal"],
            )
            
            # Run the agent
            result = agent.chat(message)
            
            # Emit text.done
            self._emit(EventType.TEXT_DONE, {
                "agentId": self._current_agent_id,
                "fullContent": self._full_content or result or "",
            })
            
        except Exception as e:
            logger.exception("Agent execution failed")
            self._emit(EventType.ERROR, {
                "code": "AGENT_ERROR",
                "message": str(e),
            })
        finally:
            self._stop_event.set()
    
    def _emit(self, event_type: EventType, data: Dict[str, Any]) -> None:
        """Emit an event to the queue."""
        event = GatewayEvent(event=event_type, data=data)
        self.event_queue.put(event)
    
    def _on_stream_delta(self, text: str) -> None:
        """Called when text is streamed from the model."""
        self._full_content += text
        self._emit(EventType.TEXT_DELTA, {
            "agentId": self._current_agent_id,
            "content": text,
        })
    
    def _on_tool_start(self, tool_call_id: str, name: str, args: Dict[str, Any]) -> None:
        """Called when a tool starts executing."""
        self._tool_start_times[tool_call_id] = time.time()
        self._emit(EventType.TOOL_START, {
            "toolCallId": tool_call_id,
            "agentId": self._current_agent_id,
            "toolName": name,
            "args": args,
        })
    
    def _on_tool_complete(
        self, 
        tool_call_id: str, 
        name: str, 
        args: Dict[str, Any], 
        result: Any
    ) -> None:
        """Called when a tool completes."""
        start_time = self._tool_start_times.pop(tool_call_id, time.time())
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Truncate large results for the event
        result_preview = result
        if isinstance(result, str) and len(result) > 1000:
            result_preview = result[:1000] + "... [truncated]"
        
        self._emit(EventType.TOOL_DONE, {
            "toolCallId": tool_call_id,
            "result": result_preview,
            "duration": duration_ms,
        })
    
    def _on_tool_progress(
        self,
        event_type: str,
        name: str,
        preview: str,
        **kwargs
    ) -> None:
        """Called for tool progress updates."""
        tool_call_id = kwargs.get("tool_call_id", "")
        progress = kwargs.get("progress", 0)
        
        self._emit(EventType.TOOL_PROGRESS, {
            "toolCallId": tool_call_id,
            "progress": progress,
            "message": preview,
        })
    
    def _on_tool_gen(self, name: str) -> None:
        """Called when the model is generating a tool call."""
        self._emit(EventType.THINKING_DELTA, {
            "agentId": self._current_agent_id,
            "content": f"Preparing to use {name}...",
        })
    
    def _on_thinking(self, content: str) -> None:
        """Called for thinking/reasoning output."""
        self._emit(EventType.THINKING_DELTA, {
            "agentId": self._current_agent_id,
            "content": content,
        })
    
    def _on_status(self, kind: str, text: Optional[str]) -> None:
        """Called for status updates."""
        self._emit(EventType.THINKING_DELTA, {
            "agentId": self._current_agent_id,
            "content": text or kind,
        })
    
    def get_events(self, timeout: float = 0.1):
        """Generator that yields events from the queue."""
        while not self._stop_event.is_set() or not self.event_queue.empty():
            try:
                event = self.event_queue.get(timeout=timeout)
                yield event
            except queue.Empty:
                # Emit heartbeat
                yield GatewayEvent(
                    event=EventType.HEARTBEAT,
                    data={"timestamp": int(time.time() * 1000)}
                )
    
    def stop(self) -> None:
        """Stop the adapter."""
        self._stop_event.set()

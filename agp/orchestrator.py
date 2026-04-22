"""
Orchestrator for AGP

Manages multi-agent coordination with LLM-based Director routing.

Flow:
  User message → Director(LLM) decides next_agent → Agent executes
  → Director decides again (continue / switch / END) → ...
"""

import asyncio
import json
import logging
import os
import threading
import time
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

# ---------------------------------------------------------------------------
# Director — LLM-based routing
# ---------------------------------------------------------------------------

DIRECTOR_PROMPT = """你是一个调度员（Director），负责将用户消息路由给最合适的 Agent。

# 可用 Agent
{agent_list}

# 对话历史
{history}

# 路由规则
1. 分析用户消息和对话上下文，决定下一个应该响应的 Agent。
2. 用户询问数据、统计、趋势、实时信息 → 路由给有数据查询能力的 Agent（通常是数据工程师）。
3. 用户询问分析解读、观点、策略建议 → 路由给分析师 Agent（通常是舆情分析师）。
4. 上一个 Agent 请求了另一个 Agent 的协助 → 路由给被请求的 Agent。
5. 上一个 Agent 提供了数据，需要解读 → 路由给分析师。
6. 对话已完成，不需要更多 Agent 响应 → 输出 END。
7. 每次请求最多 {max_turns} 轮 Agent 响应，当前第 {current_turn} 轮。

# 输出格式
只输出一个 JSON 对象，不要有任何其他内容：
{{"next_agent": "<agent_id>"}}
或
{{"next_agent": "END"}}
"""


def _run_director_sync(
    agents: List[AgentDefinition],
    history_text: str,
    model_config: Optional[ModelConfig],
    current_turn: int,
    max_turns: int,
) -> str:
    """Run Director LLM call synchronously, return agent_id or 'END'."""
    try:
        from openai import OpenAI

        # Build agent list description
        agent_lines = []
        for a in agents:
            skills_str = f" [skills: {', '.join(a.skills)}]" if a.skills else ""
            agent_lines.append(f"- {a.id}: {a.name} — {a.persona[:120]}...{skills_str}")
        agent_list = "\n".join(agent_lines)

        prompt = DIRECTOR_PROMPT.format(
            agent_list=agent_list,
            history=history_text or "(empty — this is the first message)",
            max_turns=max_turns,
            current_turn=current_turn,
        )

        # Use same model as agents
        provider = model_config.provider if model_config else "minimax"
        model = model_config.name if model_config else "MiniMax-M2.7-highspeed"
        api_key = model_config.api_key if model_config else None

        if not api_key:
            api_key = os.environ.get("MINIMAX_API_KEY", "")

        # Resolve base URL by provider
        PROVIDER_URLS = {
            "minimax": "https://api.minimaxi.com/v1/",
            "anthropic": "https://api.anthropic.com/v1/",
            "openai": "https://api.openai.com/v1/",
            "deepseek": "https://api.deepseek.com/v1/",
        }
        base_url = PROVIDER_URLS.get(provider, "https://api.minimaxi.com/v1/")

        client = OpenAI(api_key=api_key, base_url=base_url)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个路由助手。你只输出 JSON，不要解释、不要思考过程、不要 markdown。只输出一个 JSON 对象。"},
                {"role": "user", "content": prompt + "\n\n只输出 JSON 对象，不要有任何其他内容："},
            ],
            max_tokens=256,
            temperature=0.1,
        )

        raw = response.choices[0].message.content or ""
        logger.info(f"Director raw response: {raw[:200]}")
        # Strip <think> blocks but keep the actual decision
        import re
        cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        
        # If cleaned is empty, try to find JSON inside think block
        if not cleaned:
            # MiniMax may put the answer inside think block
            think_match = re.search(r"<think>(.*?)</think>", raw, flags=re.DOTALL)
            if think_match:
                cleaned = think_match.group(1).strip()

        # Parse JSON
        json_match = re.search(r'\{[^}]+\}', cleaned or raw)
        if json_match:
            decision = json.loads(json_match.group())
            next_agent = decision.get("next_agent", "END")
            logger.info(f"Director decision: {next_agent} (raw: {raw[:80]})")
            return next_agent

        logger.warning(f"Director returned unparseable response: {raw[:200]}")
        return "END"

    except Exception as e:
        logger.exception(f"Director LLM call failed: {e}")
        # Fallback: turn 0 → first agent; turn 1 after data agent → try analyst; else END
        if current_turn == 0 and agents:
            return agents[0].id
        # If previous agent was data engineer, fallback to analyst
        if current_turn > 0 and len(agents) > 1:
            return agents[0].id  # Usually the analyst
        return "END"


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class Orchestrator:
    """Orchestrates multi-agent conversations with LLM Director."""

    def __init__(self):
        self.session_manager = get_session_manager()
        self._active_adapters: Dict[str, HermesAdapter] = {}

    async def run_session(
        self,
        request: AgentRequest,
    ) -> AsyncGenerator[GatewayEvent, None]:
        """Run a chat session with Director-based routing."""

        session = self.session_manager.get_or_create_session(
            session_id=request.session_id,
            context=request.context,
        )

        yield GatewayEvent(event=EventType.SESSION_START, data={"sessionId": session.id})

        # Add user message to history
        self.session_manager.add_message(
            session.id, role="user", content=request.message.content,
        )

        agents_by_id = {a.id: a for a in request.agents}
        max_turns = 4
        turn = 0

        while turn < max_turns:
            # --- Director decides ---
            history = self.session_manager.get_messages(session.id)
            history_text = self._format_history(history)

            # If initial_agent_id is set and this is turn 0, use it directly
            if turn == 0 and request.initial_agent_id and request.initial_agent_id in agents_by_id:
                next_agent_id = request.initial_agent_id
                logger.info(f"Director: using initial_agent_id={next_agent_id}")
            else:
                next_agent_id = await asyncio.to_thread(
                    _run_director_sync,
                    request.agents,
                    history_text,
                    request.model,
                    turn,
                    max_turns,
                )

            if next_agent_id == "END" or next_agent_id not in agents_by_id:
                logger.info(f"Director: END (turn {turn})")
                break

            agent_def = agents_by_id[next_agent_id]
            logger.info(f"Director: dispatch → {agent_def.name} ({agent_def.id}), turn {turn}")

            # --- Run agent ---
            yield GatewayEvent(
                event=EventType.AGENT_START,
                data={"agentId": agent_def.id, "agentName": agent_def.name},
            )

            accumulated = ""
            async for event in self._run_agent(
                session=session,
                agent_def=agent_def,
                message=request.message.content,
                model_config=request.model,
            ):
                if event.event == EventType.TEXT_DONE:
                    accumulated = event.data.get("fullContent", "")
                yield event

            yield GatewayEvent(
                event=EventType.AGENT_END, data={"agentId": agent_def.id},
            )

            # Save to history
            if accumulated:
                self.session_manager.add_message(
                    session.id,
                    role="assistant",
                    content=accumulated,
                    agent_id=agent_def.id,
                )

            turn += 1
            logger.info(f"Turn {turn} completed, looping back to Director...")

        # Session end
        yield GatewayEvent(
            event=EventType.SESSION_END,
            data={"sessionId": session.id, "reason": "completed"},
        )

    # ------------------------------------------------------------------

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
            history = self.session_manager.get_messages(session.id)
            if history and history[-1].get("role") == "user":
                history = history[:-1]

            adapter.run(
                agent_def=agent_def,
                message=message,
                context=session.context,
                model_config=model_config,
                history=history if history else None,
            )

            for event in adapter.get_events(timeout=0.1):
                yield event
                await asyncio.sleep(0.01)

        finally:
            adapter.stop()
            self._active_adapters.pop(session.id, None)

    def _format_history(self, messages: List[Dict[str, Any]]) -> str:
        """Format message history for Director prompt."""
        if not messages:
            return ""
        lines = []
        for m in messages[-10:]:  # Last 10 messages
            role = m.get("role", "?")
            agent = m.get("agent_id", "")
            content = m.get("content", "")[:200]
            prefix = f"[{agent}]" if agent else f"[{role}]"
            lines.append(f"{prefix}: {content}")
        return "\n".join(lines)

    def interrupt(self, session_id: str) -> bool:
        """Interrupt an active session."""
        adapter = self._active_adapters.get(session_id)
        if adapter:
            adapter.stop()
            return True
        return False


# Global instance
_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator

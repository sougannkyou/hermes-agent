"""
AGP Type Definitions

Defines the request/response types for Agent Gateway Protocol.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional
from enum import Enum


# ============================================================================
# Request Types
# ============================================================================

@dataclass
class Attachment:
    """File attachment in a message."""
    type: Literal["image", "file", "audio", "video"]
    url: Optional[str] = None
    base64: Optional[str] = None
    filename: Optional[str] = None
    mime_type: Optional[str] = None


@dataclass
class UserMessage:
    """User message in a chat request."""
    role: Literal["user"] = "user"
    content: str = ""
    attachments: List[Attachment] = field(default_factory=list)


@dataclass
class ToolDefinition:
    """Definition of a tool available to an agent."""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    execution: Dict[str, Any] = field(default_factory=lambda: {"type": "backend"})


@dataclass
class AgentDefinition:
    """Definition of an agent."""
    id: str
    name: str
    persona: str  # System prompt
    capabilities: List[str] = field(default_factory=list)
    can_handoff_to: List[str] = field(default_factory=list)
    tools: List[ToolDefinition] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)  # Skill names to preload


@dataclass
class ModelConfig:
    """LLM model configuration."""
    provider: str = "anthropic"
    name: str = "claude-sonnet-4-20250514"
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 8192


@dataclass
class AgentRequest:
    """Request to the AGP /chat endpoint."""
    message: UserMessage
    agents: List[AgentDefinition]
    session_id: Optional[str] = None
    initial_agent_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    model: Optional[ModelConfig] = None


# ============================================================================
# Response/Event Types
# ============================================================================

class EventType(str, Enum):
    """SSE event types."""
    # Session lifecycle
    SESSION_START = "session.start"
    SESSION_END = "session.end"
    
    # Agent lifecycle
    AGENT_START = "agent.start"
    AGENT_END = "agent.end"
    AGENT_HANDOFF = "agent.handoff"
    
    # Text streaming
    TEXT_DELTA = "text.delta"
    TEXT_DONE = "text.done"
    
    # Thinking/reasoning
    THINKING_START = "thinking.start"
    THINKING_DELTA = "thinking.delta"
    THINKING_DONE = "thinking.done"
    
    # Tool calls
    TOOL_START = "tool.start"
    TOOL_PROGRESS = "tool.progress"
    TOOL_DONE = "tool.done"
    TOOL_ERROR = "tool.error"
    
    # Frontend tools
    TOOL_FRONTEND = "tool.frontend"
    
    # User interaction
    USER_CUE = "user.cue"
    USER_CLARIFY = "user.clarify"
    
    # Error & heartbeat
    ERROR = "error"
    HEARTBEAT = "heartbeat"


@dataclass
class GatewayEvent:
    """Base class for all gateway events."""
    event: EventType
    data: Dict[str, Any]
    
    def to_sse(self) -> str:
        """Convert to SSE format."""
        import json
        return f"event: {self.event.value}\ndata: {json.dumps(self.data, ensure_ascii=False)}\n\n"


# ============================================================================
# Event Data Types (for type hints)
# ============================================================================

@dataclass
class SessionStartData:
    session_id: str


@dataclass
class SessionEndData:
    session_id: str
    reason: str


@dataclass
class AgentStartData:
    agent_id: str
    agent_name: str


@dataclass
class AgentEndData:
    agent_id: str


@dataclass
class AgentHandoffData:
    from_agent: str
    to_agent: str
    reason: str


@dataclass
class TextDeltaData:
    agent_id: str
    content: str


@dataclass
class TextDoneData:
    agent_id: str
    full_content: str


@dataclass
class ToolStartData:
    tool_call_id: str
    agent_id: str
    tool_name: str
    args: Dict[str, Any]
    estimated_duration: Optional[int] = None


@dataclass
class ToolProgressData:
    tool_call_id: str
    progress: int  # 0-100
    message: Optional[str] = None


@dataclass
class ToolDoneData:
    tool_call_id: str
    result: Any
    duration: int  # ms


@dataclass
class ToolErrorData:
    tool_call_id: str
    error: str


@dataclass
class ErrorData:
    code: str
    message: str

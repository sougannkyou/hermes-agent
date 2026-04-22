"""
AGP HTTP Server

FastAPI-based HTTP server with SSE streaming for Agent Gateway Protocol.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .orchestrator import get_orchestrator
from .session import get_session_manager
from .types import (
    AgentDefinition,
    AgentRequest,
    Attachment,
    ModelConfig,
    ToolDefinition,
    UserMessage,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models for API
# ============================================================================

class AttachmentModel(BaseModel):
    type: str = "file"
    url: Optional[str] = None
    base64: Optional[str] = None
    filename: Optional[str] = None
    mime_type: Optional[str] = None


class UserMessageModel(BaseModel):
    role: str = "user"
    content: str
    attachments: List[AttachmentModel] = Field(default_factory=list)


class ToolDefinitionModel(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    execution: Dict[str, Any] = Field(default_factory=lambda: {"type": "backend"})


class AgentDefinitionModel(BaseModel):
    id: str
    name: str
    persona: str
    capabilities: List[str] = Field(default_factory=list)
    can_handoff_to: List[str] = Field(default_factory=list, alias="canHandoffTo")
    tools: List[ToolDefinitionModel] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    
    class Config:
        populate_by_name = True


class ModelConfigModel(BaseModel):
    provider: str = ""
    name: str = ""
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 8192


class ChatRequestModel(BaseModel):
    message: UserMessageModel
    agents: List[AgentDefinitionModel]
    session_id: Optional[str] = Field(None, alias="sessionId")
    initial_agent_id: Optional[str] = Field(None, alias="initialAgentId")
    context: Dict[str, Any] = Field(default_factory=dict)
    model: Optional[ModelConfigModel] = None
    
    class Config:
        populate_by_name = True


class ToolResultModel(BaseModel):
    session_id: str = Field(alias="sessionId")
    tool_call_id: str = Field(alias="toolCallId")
    result: Any
    error: Optional[str] = None
    
    class Config:
        populate_by_name = True


class ClarifyModel(BaseModel):
    session_id: str = Field(alias="sessionId")
    request_id: str = Field(alias="requestId")
    answer: str
    
    class Config:
        populate_by_name = True


# ============================================================================
# FastAPI App
# ============================================================================

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Agent Gateway Protocol (AGP)",
        description="HTTP/SSE Gateway for Hermes Agent",
        version="1.0.0",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "agp"}
    
    @app.post("/api/agent/chat")
    async def chat(request: ChatRequestModel):
        """
        Main chat endpoint with SSE streaming.
        
        Accepts a chat request and returns an SSE stream of events.
        """
        # Convert Pydantic models to dataclasses
        agent_request = _convert_request(request)
        
        async def event_generator():
            orchestrator = get_orchestrator()
            
            try:
                async for event in orchestrator.run_session(agent_request):
                    yield event.to_sse()
            except Exception as e:
                logger.exception("Error in chat stream")
                error_event = f"event: error\ndata: {json.dumps({'code': 'STREAM_ERROR', 'message': str(e)})}\n\n"
                yield error_event
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            },
        )
    
    @app.post("/api/agent/tool-result")
    async def submit_tool_result(request: ToolResultModel):
        """
        Submit the result of a frontend tool execution.
        
        Called by the frontend after executing a tool.frontend event.
        """
        # TODO: Implement tool result handling
        # This requires maintaining a pending tool calls registry
        return {"success": True, "message": "Tool result received"}
    
    @app.post("/api/agent/clarify")
    async def submit_clarification(request: ClarifyModel):
        """
        Submit a user clarification response.
        
        Called when the agent requests clarification from the user.
        """
        # TODO: Implement clarification handling
        return {"success": True, "message": "Clarification received"}
    
    @app.post("/api/agent/interrupt")
    async def interrupt_session(session_id: str):
        """Interrupt an active session."""
        orchestrator = get_orchestrator()
        success = orchestrator.interrupt(session_id)
        
        if success:
            return {"success": True, "message": "Session interrupted"}
        else:
            raise HTTPException(status_code=404, detail="Session not found or not active")
    
    @app.get("/api/sessions/{session_id}")
    async def get_session(session_id: str):
        """Get session information."""
        session_manager = get_session_manager()
        session = session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "id": session.id,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "message_count": len(session.messages),
            "current_agent_id": session.current_agent_id,
            "context": session.context,
        }
    
    @app.get("/api/sessions/{session_id}/messages")
    async def get_session_messages(session_id: str):
        """Get all messages in a session."""
        session_manager = get_session_manager()
        messages = session_manager.get_messages(session_id)
        
        if not messages and not session_manager.get_session(session_id):
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"messages": messages}
    
    @app.delete("/api/sessions/{session_id}")
    async def delete_session(session_id: str):
        """Delete a session."""
        session_manager = get_session_manager()
        success = session_manager.delete_session(session_id)
        
        if success:
            return {"success": True, "message": "Session deleted"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    
    return app


def _convert_request(request: ChatRequestModel) -> AgentRequest:
    """Convert Pydantic model to dataclass."""
    agents = [
        AgentDefinition(
            id=a.id,
            name=a.name,
            persona=a.persona,
            capabilities=a.capabilities,
            can_handoff_to=a.can_handoff_to,
            tools=[
                ToolDefinition(
                    name=t.name,
                    description=t.description,
                    parameters=t.parameters,
                    execution=t.execution,
                )
                for t in a.tools
            ],
            skills=a.skills,
        )
        for a in request.agents
    ]
    
    model_config = None
    if request.model:
        model_config = ModelConfig(
            provider=request.model.provider,
            name=request.model.name,
            api_key=request.model.api_key,
            temperature=request.model.temperature,
            max_tokens=request.model.max_tokens,
        )
    
    return AgentRequest(
        message=UserMessage(
            role=request.message.role,
            content=request.message.content,
            attachments=[
                Attachment(
                    type=a.type,
                    url=a.url,
                    base64=a.base64,
                    filename=a.filename,
                    mime_type=a.mime_type,
                )
                for a in request.message.attachments
            ],
        ),
        agents=agents,
        session_id=request.session_id,
        initial_agent_id=request.initial_agent_id,
        context=request.context,
        model=model_config,
    )


def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
):
    """Run the AGP server."""
    import uvicorn
    
    app = create_app()
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run AGP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    run_server(host=args.host, port=args.port, reload=args.reload)

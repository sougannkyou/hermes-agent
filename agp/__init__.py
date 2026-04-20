"""
Agent Gateway Protocol (AGP) - HTTP/SSE Gateway for Hermes Agent

This module provides a standardized HTTP API with SSE streaming for
frontend applications to interact with Hermes Agent.

Architecture:
    Frontend App (OpenMAIC) 
        ↓ HTTP POST /chat + SSE response
    AGP Server (FastAPI)
        ↓ callbacks
    Hermes AIAgent
"""

from .server import create_app, run_server
from .types import AgentRequest, AgentDefinition, GatewayEvent

__all__ = [
    "create_app",
    "run_server", 
    "AgentRequest",
    "AgentDefinition",
    "GatewayEvent",
]

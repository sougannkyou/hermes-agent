#!/usr/bin/env python3
"""
AGP Server Entry Point

Run the Agent Gateway Protocol server.

Usage:
    python agp_serve.py [--host HOST] [--port PORT] [--reload]
    
Examples:
    python agp_serve.py
    python agp_serve.py --port 8080
    python agp_serve.py --reload  # Development mode
"""

import argparse
import logging
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(
        description="Run the Agent Gateway Protocol (AGP) server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python agp_serve.py                    # Run on default port 8000
    python agp_serve.py --port 8080        # Run on port 8080
    python agp_serve.py --reload           # Development mode with auto-reload
    
API Endpoints:
    POST /api/agent/chat     - Main chat endpoint (SSE streaming)
    POST /api/agent/interrupt - Interrupt an active session
    GET  /api/sessions/{id}  - Get session info
    GET  /health             - Health check
        """,
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting AGP server on {args.host}:{args.port}")
    
    # Import and run server
    from agp.server import run_server
    
    run_server(
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()

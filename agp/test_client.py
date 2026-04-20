#!/usr/bin/env python3
"""
AGP Test Client

Simple CLI client for testing the AGP server.

Usage:
    python -m agp.test_client "你好"
    python -m agp.test_client --skills istarshine-data "搜索比亚迪在抖音上的热度"
    python -m agp.test_client --url http://localhost:8080 "Hello"
"""

import argparse
import json
import sys
from typing import List, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def chat(
    message: str,
    base_url: str = "http://localhost:8000",
    agent_name: str = "助手",
    agent_persona: str = "你是一个有帮助的AI助手。用中文回答问题。",
    skills: Optional[List[str]] = None,
) -> None:
    """Send a chat message and print the streaming response."""
    
    url = f"{base_url}/api/agent/chat"
    
    request_body = {
        "message": {
            "role": "user",
            "content": message,
        },
        "agents": [{
            "id": "assistant",
            "name": agent_name,
            "persona": agent_persona,
            "capabilities": ["general"],
            "canHandoffTo": [],
            "skills": skills or [],
        }],
        "context": {},
    }
    
    req = Request(
        url,
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        method="POST",
    )
    
    print(f"\n🔗 Connecting to {base_url}...")
    print(f"📤 Sending: {message}\n")
    print("-" * 50)
    
    try:
        with urlopen(req, timeout=300) as response:
            current_event = None
            buffer = ""
            full_response = ""
            
            for line in response:
                line = line.decode("utf-8").strip()
                
                if line.startswith("event:"):
                    current_event = line[6:].strip()
                elif line.startswith("data:") and current_event:
                    data_str = line[5:].strip()
                    try:
                        data = json.loads(data_str)
                        
                        if current_event == "session.start":
                            print(f"📝 Session: {data.get('sessionId', 'unknown')}")
                        
                        elif current_event == "agent.start":
                            print(f"\n🤖 {data.get('agentName', 'Agent')}:")
                        
                        elif current_event == "text.delta":
                            content = data.get("content", "")
                            print(content, end="", flush=True)
                            full_response += content
                        
                        elif current_event == "text.done":
                            print()  # New line after response
                        
                        elif current_event == "tool.start":
                            print(f"\n⚙️  Tool: {data.get('toolName', 'unknown')}...")
                        
                        elif current_event == "tool.progress":
                            progress = data.get("progress", 0)
                            msg = data.get("message", "")
                            print(f"   [{progress}%] {msg}")
                        
                        elif current_event == "tool.done":
                            print(f"   ✅ Done ({data.get('duration', 0)}ms)")
                        
                        elif current_event == "tool.error":
                            print(f"   ❌ Error: {data.get('error', 'unknown')}")
                        
                        elif current_event == "agent.handoff":
                            print(f"\n🔄 Handoff: {data.get('from')} → {data.get('to')}")
                            print(f"   Reason: {data.get('reason', '')}")
                        
                        elif current_event == "session.end":
                            print(f"\n✅ Session ended: {data.get('reason', 'completed')}")
                        
                        elif current_event == "error":
                            print(f"\n❌ Error [{data.get('code')}]: {data.get('message')}")
                        
                        elif current_event == "heartbeat":
                            pass  # Ignore heartbeats
                        
                        else:
                            # Print other events for debugging
                            pass
                            
                    except json.JSONDecodeError:
                        pass
                    
                    current_event = None
            
            print("-" * 50)
            print(f"\n📊 Response length: {len(full_response)} chars")
            
    except HTTPError as e:
        print(f"\n❌ HTTP Error {e.code}: {e.reason}")
        try:
            error_body = e.read().decode("utf-8")
            print(f"   {error_body}")
        except:
            pass
        sys.exit(1)
        
    except URLError as e:
        print(f"\n❌ Connection Error: {e.reason}")
        print(f"   Is the AGP server running at {base_url}?")
        print(f"\n   Start it with: python agp_serve.py --port 8000")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="AGP Test Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m agp.test_client "你好"
    python -m agp.test_client --skills istarshine-data "搜索比亚迪"
    python -m agp.test_client --url http://localhost:8080 "Hello"
        """,
    )
    
    parser.add_argument(
        "message",
        help="Message to send to the agent",
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="AGP server URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--name",
        default="助手",
        help="Agent name (default: 助手)",
    )
    parser.add_argument(
        "--persona",
        default="你是一个有帮助的AI助手。用中文回答问题，回答简洁明了。",
        help="Agent persona/system prompt",
    )
    parser.add_argument(
        "--skills",
        help="Comma-separated list of skills to load (e.g., istarshine-data,arxiv)",
    )
    
    args = parser.parse_args()
    
    skills = args.skills.split(",") if args.skills else None
    
    chat(
        message=args.message,
        base_url=args.url,
        agent_name=args.name,
        agent_persona=args.persona,
        skills=skills,
    )


if __name__ == "__main__":
    main()

"""Chat route — connects the web UI to the Agno team with SSE streaming."""

import json
import logging
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agno.agent import RunEvent
from agno.team import TeamRunEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])

# Lazy-init the team so startup stays fast
_team = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[list[ChatMessage]] = None


def _get_team():
    """Create the Agno team on first use (avoids slow startup)."""
    global _team
    if _team is not None:
        return _team

    try:
        from jobby_bot.agent import create_agents, create_team

        agents = create_agents()
        _team = create_team(agents)
        logger.info("Agno team initialised for chat.")
        return _team
    except Exception as e:
        logger.error("Failed to initialise Agno team: %s", e)
        raise


def _sse_event(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event string."""
    payload = json.dumps({"type": event_type, **data})
    return f"data: {payload}\n\n"


def _friendly_tool_name(name: str, args: dict | None = None) -> str:
    """Build a human-readable label from tool name + args."""
    # Static mapping for known tools
    mapping = {
        "search_jobs": "Searching for jobs",
        "read_file": "Reading file",
        "write_file": "Writing file",
        "generate_pdf": "Generating PDF",
        "send_email": "Sending email",
        "create_notion_entry": "Tracking in Notion",
        "apply_to_job": "Submitting application",
        "get_member_information": "Reviewing team capabilities",
        "validate_job_url": "Validating job URL",
    }

    # Special handling for delegation — include the member name
    if name == "transfer_task_to_member" and args:
        member = args.get("member_name", "")
        if member:
            return f"Delegating to {member}"
        return "Delegating to team member"

    base = mapping.get(name, name.replace("_", " ").capitalize())

    # Append brief contextual hint from args
    if args and isinstance(args, dict):
        if "search_term" in args:
            base += f" — \"{args['search_term']}\""
        elif "task_description" in args:
            desc = str(args["task_description"])[:80]
            base += f" — {desc}"

    return base


def _stream_team_response(prompt: str):
    """Generator that yields SSE events from the Agno team run."""
    _seen_labels: set[str] = set()
    _step_counter = 0
    _active_tools = 0          # track in-flight tool calls
    _any_tool_started = False   # whether any tool was ever invoked

    def _emit_tool_start(tool_name: str, label: str, agent: str = "") -> str | None:
        nonlocal _step_counter
        if label in _seen_labels:
            return None
        _seen_labels.add(label)
        _step_counter += 1
        return _sse_event("tool_start", {
            "tool": f"{tool_name}_{_step_counter}",
            "label": label,
            "agent": agent,
        })

    try:
        team = _get_team()

        yield _sse_event("status", {"content": "Thinking..."})

        stream = team.run(
            prompt,
            stream=True,
            stream_events=True,
            stream_intermediate_steps=True,
        )

        for event in stream:
            # --- Intermediate content → always thinking ---
            if event.event == TeamRunEvent.run_intermediate_content:
                content = getattr(event, "content", "")
                if content:
                    yield _sse_event("thinking", {"content": content})
                continue

            # --- Team-level tool calls ---
            if event.event == TeamRunEvent.tool_call_started:
                _active_tools += 1
                _any_tool_started = True
                tool_name = getattr(event.tool, "tool_name", "unknown") if event.tool else "unknown"
                tool_args = getattr(event.tool, "tool_args", None) if event.tool else None
                label = _friendly_tool_name(tool_name, tool_args)
                evt = _emit_tool_start(tool_name, label)
                if evt:
                    yield evt

            elif event.event == TeamRunEvent.tool_call_completed:
                _active_tools = max(0, _active_tools - 1)
                tool_name = getattr(event.tool, "tool_name", "unknown") if event.tool else "unknown"
                yield _sse_event("tool_end", {"tool": tool_name})

            # --- Member agent tool calls ---
            elif event.event == RunEvent.tool_call_started:
                _active_tools += 1
                _any_tool_started = True
                tool_name = getattr(event.tool, "tool_name", "unknown") if event.tool else "unknown"
                tool_args = getattr(event.tool, "tool_args", None) if event.tool else None
                agent_id = getattr(event, "agent_id", None) or ""
                label = _friendly_tool_name(tool_name, tool_args)
                evt = _emit_tool_start(tool_name, label, agent_id)
                if evt:
                    yield evt

            elif event.event == RunEvent.tool_call_completed:
                _active_tools = max(0, _active_tools - 1)
                tool_name = getattr(event.tool, "tool_name", "unknown") if event.tool else "unknown"
                yield _sse_event("tool_end", {"tool": tool_name})

            # --- Content streaming ---
            elif event.event == TeamRunEvent.run_content:
                content = getattr(event, "content", "")
                if content:
                    # If tools were ever used, ALL content is thinking
                    # (final answer is assembled on the frontend from thinking)
                    if _any_tool_started:
                        yield _sse_event("thinking", {"content": content})
                    else:
                        yield _sse_event("content", {"content": content})

        yield _sse_event("done", {})

    except Exception as e:
        logger.exception("Streaming chat error")
        yield _sse_event("error", {"content": f"Error: {str(e)[:200]}"})
        yield _sse_event("done", {})


@router.post("/chat")
async def chat(req: ChatRequest):
    """Stream a response from the Jobby Bot team via SSE."""
    # Build context from history
    context = ""
    if req.history:
        for msg in req.history[-6:]:
            prefix = "User" if msg.role == "user" else "Assistant"
            context += f"{prefix}: {msg.content}\n"

    prompt = req.message
    if context:
        prompt = f"Previous conversation:\n{context}\nUser: {req.message}"

    return StreamingResponse(
        _stream_team_response(prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

import asyncio
import json
import logging

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import SessionLocal, get_db
from app.models.execution import Execution
from app.models.message import Message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/executions", tags=["Executions"])


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def _serialize(e: Execution) -> dict:
    """Serializes an Execution ORM object to a dict, including new HITL fields."""
    return {
        "id": e.id,
        "workflow_id": e.workflow_id,
        "status": e.status,
        "current_node": e.current_node,
        "input_task": e.input_task,
        "final_output": e.final_output,
        "tokens_used": e.tokens_used,
        "cost_usd": e.cost_usd,
        "thread_id": e.thread_id,
        "approval_data": e.approval_data,
        "started_at": e.started_at.isoformat() if e.started_at else None,
        "completed_at": e.completed_at.isoformat() if e.completed_at else None,
    }


# -------------------------------------------------------------------------
# Existing Endpoints
# -------------------------------------------------------------------------

@router.get("/")
def get_executions(db: Session = Depends(get_db)):
    executions = (
        db.query(Execution)
        .order_by(Execution.started_at.desc())
        .limit(50)
        .all()
    )
    return [_serialize(e) for e in executions]


@router.get("/{execution_id}")
def get_execution(execution_id: int, db: Session = Depends(get_db)):
    e = db.query(Execution).filter(Execution.id == execution_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Execution not found")
    return _serialize(e)


# -------------------------------------------------------------------------
# NEW: HITL Resume Endpoint
# -------------------------------------------------------------------------

@router.post("/{execution_id}/resume")
def resume_execution(
    execution_id: int,
    body: dict = Body(default={}),
    db: Session = Depends(get_db),
):
    """
    Resume a HITL-paused execution with a human decision.

    **How this works end-to-end:**

    1. The LangGraph graph called `interrupt({...})` inside a node.
    2. LangGraph saved a checkpoint (thread_id = str(execution.id)) and returned.
    3. RuntimeEngine detected `state_snap.next` was non-empty → set status to
       `"waiting_for_approval"` and stored the interrupt payload in `approval_data`.
    4. This endpoint calls `graph.invoke(Command(resume=decision), config)`:
       - LangGraph loads the checkpoint for thread_id from the MemorySaver.
       - The `decision` value becomes the return value of `interrupt()` in the node.
       - Execution continues from exactly where it paused.
    5. If another `interrupt()` fires, status returns to `"waiting_for_approval"`.
       Otherwise, execution completes normally.

    **Request body:** `{ "decision": "APPROVED" | "REJECTED" }`

    **Requirements:** execution must have `status == "waiting_for_approval"`
    """
    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution #{execution_id} not found")

    if execution.status != "waiting_for_approval":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Execution #{execution_id} cannot be resumed "
                f"(current status: '{execution.status}'). "
                f"Only executions with status 'waiting_for_approval' can be resumed."
            ),
        )

    decision = body.get("decision", "APPROVED").strip().upper()
    if decision not in ("APPROVED", "REJECTED"):
        raise HTTPException(
            status_code=400,
            detail="'decision' must be exactly 'APPROVED' or 'REJECTED'"
        )

    # Check if this is a Failure Policy approval item
    if execution.approval_data:
        try:
            app_data = json.loads(execution.approval_data) if isinstance(execution.approval_data, str) else execution.approval_data
            if isinstance(app_data, dict) and app_data.get("action_type") == "CREATE_GITHUB_ISSUE":
                if decision == "APPROVED":
                    from app.mcp.manager import MCPManager
                    try:
                        res = MCPManager.call_tool(
                            db=db,
                            agent_id=None,
                            server_name="github-mcp",
                            tool_name="create_issue",
                            arguments={
                                "repo": app_data.get("repo", "hariom2509/Yuno-Agentic-AI"),
                                "title": app_data.get("issue_title", f"Failure Alert #{execution.id}"),
                                "body": app_data.get("issue_body", f"Workflow execution #{execution.id} failed."),
                            }
                        )
                        result_text = res.get("result", "Issue created")
                    except Exception as mcp_err:
                        result_text = f"Notice: GitHub MCP call returned ({mcp_err})"

                    execution.status = "failed"
                    execution.final_output = f"[Platform Policy Executed] GitHub Issue Action: {result_text}"
                else:
                    execution.status = "failed"
                    execution.final_output = "[Platform Policy Action Rejected] GitHub issue creation rejected by human operator."
                
                execution.approval_data = None
                db.commit()
                return _serialize(execution)
        except Exception as e:
            logger.warning(f"Failure policy approval resolution notice: {e}")

    from app.runtime.runtime_engine import RuntimeEngine
    updated = RuntimeEngine.resume_workflow(db, execution, decision)

    return {
        "execution_id": updated.id,
        "status": updated.status,
        "decision_applied": decision,
        "current_node": updated.current_node,
        "final_output": updated.final_output,
        "approval_data": updated.approval_data,
        "tokens_used": updated.tokens_used,
        "cost_usd": updated.cost_usd,
        "completed_at": updated.completed_at.isoformat() if updated.completed_at else None,
    }


# -------------------------------------------------------------------------
# NEW: SSE Execution Streaming
# -------------------------------------------------------------------------

@router.get("/{execution_id}/stream")
async def stream_execution_events(execution_id: int):
    """
    Server-Sent Events (SSE) stream for a running execution.

    **What this demonstrates:**
    The production equivalent of `graph.stream()` — instead of streaming
    LangGraph node events in-process, we tail the `messages` table and push
    each new row as an SSE event. This works across processes (Celery workers),
    across restarts, and is compatible with the existing WebSocket broadcast.

    **How to use from the browser / client:**
    ```javascript
    const es = new EventSource(`/executions/${id}/stream`);
    es.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        if (msg.type === 'message') { ... }   // inter-agent message
        if (msg.type === 'done')    { es.close(); }  // terminal
    };
    ```

    **Event types:**
    - `{"type": "message", "sender": ..., "receiver": ..., "content": ..., "message_type": ...}`
    - `{"type": "done", "status": "completed"|"failed"|"waiting_for_approval", "output": ...}`

    Polls every second for up to 5 minutes, then closes.
    """
    poll_state = {"last_id": 0}

    async def event_generator():
        for _ in range(300):  # 300 polls × 1s = 5-minute max window
            # Run blocking DB queries off the async event loop
            def fetch():
                db_local = SessionLocal()
                try:
                    new_msgs = (
                        db_local.query(Message)
                        .filter(
                            Message.execution_id == execution_id,
                            Message.id > poll_state["last_id"],
                        )
                        .order_by(Message.id.asc())
                        .limit(20)
                        .all()
                    )
                    exec_row = (
                        db_local.query(Execution)
                        .filter(Execution.id == execution_id)
                        .first()
                    )
                    return new_msgs, exec_row
                finally:
                    db_local.close()

            new_msgs, exec_row = await asyncio.to_thread(fetch)

            for msg in new_msgs:
                poll_state["last_id"] = msg.id
                yield f"data: {json.dumps({'type': 'message', 'id': msg.id, 'sender': msg.sender, 'receiver': msg.receiver, 'content': msg.content[:500], 'message_type': msg.message_type, 'timestamp': msg.timestamp.isoformat() if msg.timestamp else None})}\n\n"

            if exec_row and exec_row.status in ("completed", "failed", "waiting_for_approval"):
                yield f"data: {json.dumps({'type': 'done', 'execution_id': execution_id, 'status': exec_row.status, 'output': (exec_row.final_output or '')[:400], 'approval_data': exec_row.approval_data})}\n\n"
                break

            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",   # Disables nginx proxy buffering
        },
    )
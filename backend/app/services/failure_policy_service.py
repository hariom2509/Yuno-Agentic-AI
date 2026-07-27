import json
import logging
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.models.execution import Execution
from app.models.workflow_failure_policy import WorkflowFailurePolicy
from app.mcp.manager import MCPManager

logger = logging.getLogger(__name__)


class FailurePolicyService:
    @staticmethod
    def handle_workflow_failure(db: Session, execution: Execution) -> Optional[Dict[str, Any]]:
        """
        Triggered when a workflow execution reaches a terminal FAILED state.
        Checks for configured WorkflowFailurePolicy and invokes platform automation (e.g. GitHub MCP create_issue).
        If requires_approval is True, sets approval_data for Human-in-the-Loop approval banner in Monitoring UI.
        """
        try:
            policy = (
                db.query(WorkflowFailurePolicy)
                .filter(WorkflowFailurePolicy.workflow_id == execution.workflow_id, WorkflowFailurePolicy.enabled == True)
                .first()
            )
            
            # If no explicit policy found, create default policy for demo/production safety
            if not policy:
                policy = WorkflowFailurePolicy(
                    workflow_id=execution.workflow_id,
                    enabled=True,
                    action_type="CREATE_GITHUB_ISSUE",
                    mcp_server_name="github-mcp",
                    repository_config={"repo": "hariom2509/Yuno-Agentic-AI"},
                    requires_approval=True,
                )
                db.add(policy)
                db.commit()

            repo_full = (policy.repository_config or {}).get("repo", "hariom2509/Yuno-Agentic-AI")
            issue_title = f"[Workflow Failure Alert] Execution #{execution.id} Failed"
            issue_body = (
                f"### Workflow Execution Failure Diagnostic Report\n\n"
                f"- **Execution ID**: #{execution.id}\n"
                f"- **Workflow ID**: {execution.workflow_id}\n"
                f"- **Failed Node**: `{execution.current_node or 'Unknown'}`\n"
                f"- **Input Task**: {execution.input_task}\n"
                f"- **Error Summary**: {str(execution.final_output)[:300]}\n"
            )

            if policy.requires_approval:
                logger.info(f"Failure policy triggered HITL approval requirement for Execution #{execution.id}")
                approval_info = {
                    "action_type": policy.action_type,
                    "target_server": policy.mcp_server_name,
                    "target_tool": "create_issue",
                    "repo": repo_full,
                    "issue_title": issue_title,
                    "issue_body": issue_body,
                    "prompt": f"Workflow Execution #{execution.id} failed. Post diagnostic issue to GitHub repo '{repo_full}'?",
                }
                execution.status = "waiting_for_approval"
                execution.approval_data = json.dumps(approval_info)
                db.commit()
                return approval_info

            # If no approval required, execute tool directly
            return MCPManager.call_tool(
                db=db,
                agent_id=None,
                server_name=policy.mcp_server_name,
                tool_name="create_issue",
                arguments={
                    "repo": repo_full,
                    "title": issue_title,
                    "body": issue_body,
                }
            )

        except Exception as e:
            logger.warning(f"FailurePolicyService encountered error for Execution #{execution.id}: {e}")
            return None

import os
import subprocess
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.skill import Skill
from app.services.capability_registry import CapabilityRegistry

router = APIRouter(prefix="/api/capabilities", tags=["Capabilities"])


@router.get("/builder-tools")
def get_builder_tools(db: Session = Depends(get_db)):
    """
    Returns only BUILDER_VISIBLE capabilities grouped for the Visual Builder dropdown.
    Excludes platform integration tools (GitHub, Postgres admin).
    Includes custom user skills.
    """
    data = CapabilityRegistry.get_builder_tools(db)
    
    # Append custom skills group
    skills = db.query(Skill).filter(Skill.active == True).all()
    if skills:
        skill_tools = [
            {
                "id": f"skill::{sk.name}",
                "canonical_name": sk.name,
                "short_name": sk.name,
                "label": f"Skill: {sk.name}",
                "description": sk.description,
                "risk_level": "LOW",
                "requires_approval": False,
            }
            for sk in skills
        ]
        data["groups"].append({
            "id": "custom_skills",
            "name": "Custom Skills",
            "tools": skill_tools,
        })
        
    return data


@router.get("/agent-tools")
def get_agent_assignable_tools(db: Session = Depends(get_db)):
    """
    Returns AGENT_ASSIGNABLE tools eligible for Agent configuration.
    """
    return CapabilityRegistry.get_agent_assignable_tools(db)


@router.get("/integrations/github/status")
def get_github_integration_status():
    """
    Reports runtime status for GitHub MCP platform integration without blocking Yuno.
    """
    token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN")
    docker_ok = False
    try:
        res = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=3)
        docker_ok = (res.returncode == 0)
    except Exception:
        docker_ok = False

    if token and not token.startswith("secret_reference"):
        status = "CONFIGURED"
        reason = "Personal access token detected and active"
    else:
        status = "NOT_CONFIGURED"
        reason = "GITHUB_PERSONAL_ACCESS_TOKEN env variable not set"

    return {
        "status": status,
        "reason": reason,
        "docker_available": docker_ok,
        "enabled": True,
    }

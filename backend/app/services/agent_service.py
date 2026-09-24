from sqlalchemy.orm import Session

from app.models.agent import Agent


class AgentService:

    @staticmethod
    def create_agent(db: Session, payload) -> Agent:
        agent = Agent(
            name=payload.name,
            role=payload.role,
            description=payload.description,
            system_prompt=payload.system_prompt,
            model=payload.model,
            tools=payload.tools,
            memory_enabled=payload.memory_enabled,
            max_iterations=payload.max_iterations,
            max_tokens=payload.max_tokens,
            temperature=payload.temperature,
            channel=payload.channel,
            guardrails=payload.guardrails,
            schedule_config=payload.schedule_config,
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)

        # Auto-assign all AGENT_ASSIGNABLE tools to the new agent.
        # This seeds the agent_mcp_tools ACL junction table so that
        # MCPAuthorizationService.verify_agent_tool_access() has records
        # to check against at execution time.
        try:
            from app.models.mcp_server import MCPTool, AgentMCPTool
            assignable_tools = (
                db.query(MCPTool)
                .filter(MCPTool.exposure == "AGENT_ASSIGNABLE", MCPTool.enabled == True)
                .all()
            )
            for tool in assignable_tools:
                assignment = AgentMCPTool(agent_id=agent.id, mcp_tool_id=tool.id, enabled=True)
                db.add(assignment)
            db.commit()
        except Exception:
            pass  # Non-fatal: ACL assignment failure should not block agent creation

        return agent

    @staticmethod
    def get_agents(db: Session) -> list[Agent]:
        return db.query(Agent).filter(Agent.active == True).all()

    @staticmethod
    def get_agent_by_id(db: Session, agent_id: int) -> Agent | None:
        return db.query(Agent).filter(Agent.id == agent_id).first()

    @staticmethod
    def update_agent(db: Session, agent_id: int, payload) -> Agent | None:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return None

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(agent, field, value)

        db.commit()
        db.refresh(agent)
        return agent

    @staticmethod
    def delete_agent(db: Session, agent_id: int) -> bool:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return False
        agent.active = False  # Soft delete
        db.commit()
        return True
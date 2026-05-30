from typing import List, Optional
from pydantic import BaseModel


class AgentCreate(BaseModel):
    name: str
    role: str
    description: str = ""
    system_prompt: str
    model: str = "llama-3.3-70b-versatile"
    tools: Optional[List[str]] = []
    memory_enabled: bool = True
    max_iterations: int = 5
    max_tokens: int = 2000
    temperature: float = 0.7
    channel: str = "none"
    guardrails: Optional[dict] = {}
    schedule_config: Optional[dict] = {}


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    tools: Optional[List[str]] = None
    memory_enabled: Optional[bool] = None
    max_iterations: Optional[int] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    channel: Optional[str] = None
    guardrails: Optional[dict] = None
    schedule_config: Optional[dict] = None


class AgentResponse(BaseModel):
    id: int
    name: str
    role: str
    description: str
    system_prompt: str
    model: str
    tools: list
    memory_enabled: bool
    max_iterations: int
    max_tokens: int
    temperature: float
    channel: str
    guardrails: dict
    active: bool

    class Config:
        from_attributes = True
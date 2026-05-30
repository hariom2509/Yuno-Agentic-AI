from typing import Optional
from pydantic import BaseModel


class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    graph: Optional[dict] = {"nodes": [], "edges": []}
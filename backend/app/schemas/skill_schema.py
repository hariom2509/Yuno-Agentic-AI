from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class SkillBase(BaseModel):
    name: str
    description: Optional[str] = ""
    code: str


class SkillCreate(SkillBase):
    pass


class SkillResponse(SkillBase):
    id: int
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True

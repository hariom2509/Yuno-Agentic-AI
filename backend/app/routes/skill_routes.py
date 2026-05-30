from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.skill_schema import SkillCreate, SkillResponse
from app.services.skill_service import SkillService

router = APIRouter(prefix="/skills", tags=["Skills"])


@router.get("/", response_model=list[SkillResponse])
def get_skills(db: Session = Depends(get_db)):
    return SkillService.get_skills(db)


@router.post("/", response_model=SkillResponse, status_code=201)
def create_skill(payload: SkillCreate, db: Session = Depends(get_db)):
    # Check if name already exists
    existing = SkillService.get_skill_by_name(db, payload.name)
    if existing:
        raise HTTPException(status_code=400, detail="Skill with this name already exists")
    return SkillService.create_skill(db, payload)


@router.put("/{skill_id}", response_model=SkillResponse)
def update_skill(skill_id: int, payload: SkillCreate, db: Session = Depends(get_db)):
    # Check if name is taken by another skill
    existing = SkillService.get_skill_by_name(db, payload.name)
    if existing and existing.id != skill_id:
        raise HTTPException(status_code=400, detail="Skill with this name already exists")
    
    skill = SkillService.update_skill(db, skill_id, payload)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.delete("/{skill_id}", status_code=204)
def delete_skill(skill_id: int, db: Session = Depends(get_db)):
    deleted = SkillService.delete_skill(db, skill_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Skill not found")

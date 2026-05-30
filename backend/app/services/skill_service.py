from sqlalchemy.orm import Session
from app.models.skill import Skill
from app.schemas.skill_schema import SkillCreate


class SkillService:

    @staticmethod
    def get_skills(db: Session):
        return db.query(Skill).filter(Skill.active == True).all()

    @staticmethod
    def get_skill(db: Session, skill_id: int):
        return db.query(Skill).filter(Skill.id == skill_id).first()

    @staticmethod
    def get_skill_by_name(db: Session, name: str):
        return db.query(Skill).filter(Skill.name == name, Skill.active == True).first()

    @staticmethod
    def create_skill(db: Session, payload: SkillCreate):
        skill = Skill(
            name=payload.name,
            description=payload.description,
            code=payload.code,
        )
        db.add(skill)
        db.commit()
        db.refresh(skill)
        return skill

    @staticmethod
    def update_skill(db: Session, skill_id: int, payload: SkillCreate):
        skill = db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            return None
        skill.name = payload.name
        skill.description = payload.description
        skill.code = payload.code
        db.commit()
        db.refresh(skill)
        return skill

    @staticmethod
    def delete_skill(db: Session, skill_id: int):
        skill = db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            return False
        skill.active = False
        db.commit()
        return True

# repos/docentes_repo.py
from typing import List, Dict
from config.firebase_config import db

def get_teacher_by_id(teacher_id: str):
    doc_ref = db.collection("docentes").document(teacher_id).get()
    return doc_ref.to_dict() if doc_ref.exists else None

def get_subjects_by_teacher(teacher_id: str):
    docs = db.collection("materias").where("teacher_id", "==", teacher_id).stream()
    return [doc.to_dict() for doc in docs]

def get_groups_by_subject(subject_code: str):
    docs = db.collection("grupos").where("subject_code", "==", subject_code).stream()
    return [doc.to_dict() for doc in docs]

def get_projects_by_teacher(teacher_id: str):
    docs = db.collection("proyectos").where("teacher_id", "==", teacher_id).stream()
    return [doc.to_dict() for doc in docs]

def get_project_detail(project_id: str):
    doc_ref = db.collection("proyectos").document(project_id).get()
    return doc_ref.to_dict() if doc_ref.exists else None


###################################################
def get_all_projects():
    docs = db.collection("proyectos").stream()
    project_list = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        project_list.append(data)
    return project_list
from typing import Optional, List, Dict, Any
import logging

from .base_repository import BaseRepository
from app.core.firebase import Collections

logger = logging.getLogger(__name__)

class TeacherRepository(BaseRepository):
    
    def __init__(self):
        super().__init__(Collections.DOCENTES, "id_docente")

    async def get_teachers_by_program(self, program_code: str) -> List[Dict[str, Any]]:
        return await self.get_all(filters={"codigo_programa": program_code})

    async def get_active_teachers(self) -> List[Dict[str, Any]]:
        return await self.get_all(filters={"activo": True})

    async def get_teacher_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.get_by_field("id_usuario", user_id)

# services/docentes_service.py
from typing import List
from app.repositories import teacher_repository
from app.schemas.proyect import Proyecto    

def get_teacher_info(teacher_id: str):
    teacher = teacher_repository.get_teacher_by_id(teacher_id)
    if not teacher:
        raise ValueError("Teacher not found")
    return teacher

def list_teacher_subjects(teacher_id: str):
    return teacher_repository.get_subjects_by_teacher(teacher_id)

def list_subject_groups(subject_code: str):
    return teacher_repository.get_groups_by_subject(subject_code)

def list_teacher_projects(teacher_id: str):
    return teacher_repository.get_projects_by_teacher(teacher_id)

def get_project_info(project_id: str):
    project = teacher_repository.get_project_detail(project_id)
    if not project:
        raise ValueError("Project not found")
    return project

######################################################################

def list_all_projects() -> List[Proyecto]:
    projects = teacher_repository.get_all_projects()
    return projects

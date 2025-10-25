from fastapi import APIRouter, HTTPException
from typing import List
from app.services import teacher_service
from app.schemas.proyect import Proyecto
from app.schemas.teacher import TeacherBase

router = APIRouter(prefix="/teachers", tags=["Teachers"])

@router.get("/projects")
def get_all_projects():
    projects = teacher_service.list_all_projects()
    return projects

@router.get("/{teacher_id}/profile", response_model=TeacherBase)
def get_teacher_info(teacher_id: str):
    try:
        teacher = teacher_service.get_teacher_info(teacher_id)
        return teacher
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{teacher_id}/subjects")
def get_teacher_subjects(teacher_id: str):
    return teacher_service.list_teacher_subjects(teacher_id)

@router.get("/{teacher_id}/subjects/{subject_code}/groups")
def get_subject_groups(teacher_id: str, subject_code: str):
    return teacher_service.list_subject_groups(subject_code)

@router.get("/{teacher_id}/projects", response_model=List[Proyecto])
def get_teacher_projects(teacher_id: str):
    return teacher_service.list_teacher_projects(teacher_id)

@router.get("/{teacher_id}/projects/{project_id}", response_model=Proyecto)
def get_project_detail(teacher_id: str, project_id: str):
    try:
        project = teacher_service.get_project_info(project_id)
        return project
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


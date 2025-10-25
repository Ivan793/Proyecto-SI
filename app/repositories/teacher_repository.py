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
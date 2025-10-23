# repos/docentes_repo.py
from typing import List, Dict
from config.firebase_config import db

def get_teacher_by_id(teacher_id: str):
    doc_ref = db.collection("teachers").document(teacher_id).get()
    return doc_ref.to_dict() if doc_ref.exists else None

def get_subjects_by_teacher(teacher_id: str):
    docs = db.collection("subjects").where("teacher_id", "==", teacher_id).stream()
    return [doc.to_dict() for doc in docs]

def get_groups_by_subject(subject_code: str):
    docs = db.collection("groups").where("subject_code", "==", subject_code).stream()
    return [doc.to_dict() for doc in docs]

def get_projects_by_teacher(teacher_id: str):
    docs = db.collection("projects").where("teacher_id", "==", teacher_id).stream()
    return [doc.to_dict() for doc in docs]

def get_project_detail(project_id: str):
    doc_ref = db.collection("projects").document(project_id).get()
    return doc_ref.to_dict() if doc_ref.exists else None
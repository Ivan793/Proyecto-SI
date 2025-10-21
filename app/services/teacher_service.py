# services/docentes_service.py
from typing import List
<<<<<<< HEAD
from app.repositories import teacher_repository
from app.schemas.subject import SubjectBase
from app.schemas.group import Grupo
from app.schemas.proyect import Proyecto    
=======
from repositories import teacher_repository
from schemas.subject import subject
from schemas.group import group
from schemas.proyect import Proyecto    
>>>>>>> parent of 29e0cce (Version preliminar, aun en prueba)

def listar_asignaturas_docente(id_docente: str) -> List[subject]:
    raw = teacher_repository.get_asignaturas_by_docente(id_docente)
    asignaturas = [subject(**{
        "codigo": r.get("codigo"),
        "nombre": r.get("nombre"),
        "docente_id": r.get("docente_id"),
        "descripcion": r.get("descripcion")
    }) for r in raw]
    return asignaturas

def listar_grupos_asignatura(asignatura_codigo: str) -> List[Grupo]:
    raw = teacher_repository.get_grupos_por_asignatura(asignatura_codigo)
    grupos = [Grupo(**{
        "id_grupo": r.get("id_grupo"),
        "nombre": r.get("nombre"),
        "semestre": r.get("semestre"),
        "capacidad": r.get("capacidad"),
    }) for r in raw]
    return grupos

def listar_proyectos_docente(id_docente: str) -> List[Proyecto]:
    # 1) obtener asignaturas del docente
    asigns = teacher_repository.get_asignaturas_by_docente(id_docente)
    codigos = [a.id if hasattr(a, "id") else a.get("codigo") for a in asigns]
    # 2) obtener proyectos asociados a esas asignaturas
    raw_proy = teacher_repository.get_proyectos_por_asignaturas(codigos)
    proyectos = [Proyecto(**{
        "id_proyecto": p.get("id_proyecto"),
        "titulo": p.get("titulo"),
        "descripcion": p.get("descripcion"),
        "autor": p.get("autor"),
        "asignatura_codigo": p.get("asignatura_codigo"),
        "fecha_registro": p.get("fecha_registro"),
    }) for p in raw_proy]
    return proyectos

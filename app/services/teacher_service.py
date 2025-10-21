# services/docentes_service.py
from typing import List
from app.repositories import teacher_repository
from app.schemas.subject import SubjectBase
from app.schemas.group import Grupo
from app.schemas.proyect import Proyecto    

def listar_asignaturas_docente(id_docente: str) -> List[SubjectBase]:
    raw = teacher_repository.get_asignaturas_by_docente(id_docente)
    asignaturas = [SubjectBase(**{
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

def get_materias():
    materias_ref = teacher_repository.get_all_materias()
    return materias_ref
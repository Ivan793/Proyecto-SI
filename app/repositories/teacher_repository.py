# repos/docentes_repo.py
from typing import List, Dict
from config.firebase_config import db

# NOTA: estos métodos asumen la estructura de colecciones comentada arriba.
# Ajusta nombres de colección/atributos según tu Firestore.

def get_docente_by_id(id_docente: str) -> Dict:
    doc_ref = db.collection("docentes").document(id_docente)
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        data["id_docente"] = doc.id
        return data
    return None

def get_asignaturas_by_docente(id_docente: str) -> List[Dict]:
    # Asignaturas donde 'docente_id' == id_docente
    asignaturas_ref = db.collection("asignaturas").where("docente_id", "==", id_docente)
    docs = asignaturas_ref.stream()
    result = []
    for d in docs:
        obj = d.to_dict()
        obj["codigo"] = d.id
        result.append(obj)
    return result

def get_grupos_por_asignatura(asignatura_codigo: str) -> List[Dict]:
    # Subcolección 'grupos' dentro de cada asignatura
    grupos_ref = db.collection("asignaturas").document(asignatura_codigo).collection("grupos")
    docs = grupos_ref.stream()
    result = []
    for g in docs:
        obj = g.to_dict()
        obj["id_grupo"] = g.id
        result.append(obj)
    return result

def get_proyectos_por_asignaturas(codigos_asignaturas: List[str]) -> List[Dict]:
    # Suponiendo una colección 'proyectos' con campo 'asignatura_codigo'
    proyectos_ref = db.collection("proyectos")
    # Firestore no permite 'where in' con una lista vacía; manejarlo
    if not codigos_asignaturas:
        return []
    # Firestore permite up to 10 elementos en 'in' queries; si hay más, dividir en chunks
    def chunk_list(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i+n]
    result = []
    for chunk in chunk_list(codigos_asignaturas, 10):
        docs = proyectos_ref.where("asignatura_codigo", "in", chunk).stream()
        for p in docs:
            obj = p.to_dict()
            obj["id_proyecto"] = p.id
            result.append(obj)
    return result

def get_all_materias():
    materias_ref = db.collection("materias").stream()
    materias = [m.to_dict() for m in materias_ref]
    return materias
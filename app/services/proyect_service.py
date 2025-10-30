from typing import List, Optional
from datetime import datetime
import json
from fastapi import HTTPException
from app.repositories.event_repository import EventRepository
from app.schemas.proyect import ProyectoCreate, ProyectoResponse, ProyectoUpdate
from app.services.cloudinary_service import upload_pdf_to_cloudinary
from app.core.firebase import firebase_client, Collections
from google.cloud.firestore_v1.base_query import FieldFilter

db = firebase_client.get_db()
proyectos_ref = db.collection(Collections.PROYECTOS)
evento_repo = EventRepository()


# --------------    -------------------------------------------------
# FUNCIONES AUXILIARES
# ---------------------------------------------------------------
def _generar_id_proyecto() -> str:
    """Genera un nuevo ID autoincremental ('001', '002', ...)."""
    proyectos = list(proyectos_ref.stream())
    if not proyectos:
        return "001"

    ids = []
    for doc in proyectos:
        data = doc.to_dict()
        id_p = data.get("id_proyecto")
        if id_p and id_p.isdigit():
            ids.append(int(id_p))

    nuevo_id = max(ids, default=0) + 1
    return f"{nuevo_id:03d}"


def _existe_en_coleccion(coleccion: str, campo_id: str, valor_id: str, valor_area=0) -> bool:
    """Verifica si un documento existe en una colección dada con un ID específico."""
    print("entro a la validacion")
    print(coleccion, campo_id, valor_id)
    collection_ref = db.collection(coleccion)

    query = (collection_ref.where(filter=FieldFilter(campo_id, "==", valor_id)).stream())

    for _ in query:

        if "sublineas" in coleccion and valor_area != 0:
            coleccion_areas = _.to_dict()
            print("este es coleccion area", coleccion_areas)
            for area in coleccion_areas["areas_tematicas"]:
                print("esta es el area", area)
                if area["codigo_area"] == valor_area:
                    return True
            return False
        return True
    return False


def _validar_existencia_ids(proyecto: any):
    """
    Verifica que todos los IDs y códigos referenciados existan en Firestore.
    Si alguno no existe, lanza ValueError.
    """

    #  Validar docente
    if not _existe_en_coleccion(Collections.DOCENTES, "id_usuario", proyecto["id_docente"]):
        raise ValueError(f"No existe ningún docente con ID '{proyecto['id_docente']}'.")

    #  Validar estudiantes
    for eid in proyecto["id_estudiantes"]:
        print("este es el eid", eid)
        if not _existe_en_coleccion(Collections.ESTUDIANTES, "id_usuario", eid["id_estudiante"]):
            raise ValueError(f"No existe ningún estudiante con ID '{eid['id_estudiante']}'.")

    #  Validar grupo
    if not _existe_en_coleccion(Collections.GRUPOS, "codigo_grupo", proyecto["id_grupo"]):
        raise ValueError(f"No existe ningún grupo con ID '{proyecto['id_grupo']}'.")

    # Validar Linea de Investigacion
    if proyecto["codigo_linea"] and not _existe_en_coleccion(Collections.LINEAS_INVESTIGACION, "codigo_linea",
                                                             proyecto["codigo_linea"]):
        raise ValueError(f"No existe ninguna línea de investigación con código '{proyecto['codigo_linea']}'.")

    # Validar Sub_linea de investigacion
    if proyecto["codigo_sublinea"] and not _existe_en_coleccion(
            Collections.LINEAS_INVESTIGACION + "/" + str(proyecto["codigo_linea"]) + "/sublineas", "codigo_sublinea",
            proyecto["codigo_sublinea"]):
        raise ValueError(f"No existe ninguna sublínea de investigación con código '{proyecto['codigo_sublinea']}'.")

    # Validar Area Tematica
    if proyecto["codigo_sublinea"] and not _existe_en_coleccion(
            Collections.LINEAS_INVESTIGACION + "/" + str(proyecto["codigo_linea"]) + "/sublineas", "codigo_sublinea",
            proyecto["codigo_sublinea"], proyecto["codigo_area"]):
        raise ValueError(f"No existe ninguna area tematica con código '{proyecto['codigo_area']}'.")

    #  Validar materia
    if not _existe_en_coleccion(Collections.MATERIAS, "codigo_materia", proyecto["codigo_materia"]):
        raise ValueError(f"No existe ninguna materia con ID '{proyecto['codigo_materia']}'.")

    evento_ref = db.collection(Collections.EVENTOS).document(proyecto["id_evento"])
    evento_doc = evento_ref.get()

    print("UID recibido para evento:", proyecto["id_evento"])  # <-- Verificación en consola
    if not evento_doc.exists:
        raise ValueError(f"No existe ningún evento con UID '{proyecto['id_evento']}' en la base de datos.")
    else:
        print("Evento encontrado:", evento_doc.to_dict())

    return True, ("objeto existente")


# ---------------------------------------------------------------
# CREAR PROYECTO
# ---------------------------------------------------------------
async def create_proyecto(proyecto: ProyectoCreate, archivo) -> ProyectoResponse:
    """Crea un nuevo proyecto validando datos y referencias."""
    if not archivo:
        raise ValueError("Es obligatorio subir un archivo PDF para crear el proyecto.")
    if not archivo.filename.lower().endswith(".pdf"):
        raise ValueError("El archivo debe tener formato PDF (.pdf).")

    #  Convertir cadena JSON de estudiantes si es necesario
    if isinstance(proyecto.id_estudiantes, str):
        try:
            proyecto.id_estudiantes = json.loads(proyecto.id_estudiantes)
        except json.JSONDecodeError:
            raise ValueError("El campo 'id_estudiantes' debe ser un JSON válido (por ejemplo: ['EST001','EST002']).")

    if not isinstance(proyecto.id_estudiantes, list) or not proyecto.id_estudiantes:
        raise ValueError("Debe incluirse al menos un estudiante en la lista 'id_estudiantes'.")

    #  Validaciones básicas de formato
    for eid in proyecto.id_estudiantes:
        if not isinstance(eid, str) or len(eid.strip()) < 5:
            raise ValueError(f"El ID del estudiante '{eid}' no es válido (mínimo 5 caracteres).")
    if len(proyecto.id_docente.strip()) < 3:
        raise ValueError("El ID del docente no cumple el tamaño mínimo de 3 caracteres.")
    if not proyecto.titulo_proyecto or len(proyecto.titulo_proyecto.strip()) < 3:
        raise ValueError("El título del proyecto debe tener al menos 3 caracteres.")
    for field in ["id_grupo", "codigo_area", "id_evento", "id_materia"]:
        valor = getattr(proyecto, field, None)
        if not valor or len(valor.strip()) < 3:
            raise ValueError(f"El campo '{field}' es obligatorio y debe tener al menos 3 caracteres.")
    if not proyecto.tipo_actividad or len(proyecto.tipo_actividad.strip()) < 3:
        raise ValueError("El tipo de actividad debe tener al menos 3 caracteres.")

    # Validar las demás referencias (como diccionario)
    _validar_existencia_ids(proyecto.dict())

    #  Generar ID y subir PDF
    id_proyecto = _generar_id_proyecto()
    pdf_url = await upload_pdf_to_cloudinary(archivo)

    #  Crear documento en Firebase
    nuevo_doc = proyectos_ref.document()
    data = {
        "id_proyecto": id_proyecto,
        "id_docente": proyecto.id_docente,
        "id_estudiantes": proyecto.id_estudiantes,
        "id_grupo": proyecto.id_grupo,
        "codigo_area": proyecto.codigo_area,
        "id_evento": proyecto.id_evento,
        "id_materia": proyecto.codigo_materia,
        "codigo_linea": proyecto.codigo_linea,
        "codigo_sublinea": proyecto.codigo_sublinea,
        "titulo_proyecto": proyecto.titulo_proyecto.strip(),
        "tipo_actividad": proyecto.tipo_actividad.strip(),
        "archivo_pdf": pdf_url,
        "fecha_subida": datetime.utcnow().isoformat(),
        "calificacion": proyecto.calificacion,
        "activo": True,
    }

    nuevo_doc.set(data)
    return ProyectoResponse(**data)


# LISTAR PROYECTOS

def list_proyectos(include_inactivos: bool = False) -> List[ProyectoResponse]:
    docs = proyectos_ref.stream()
    proyectos = []
    for doc in docs:
        data = doc.to_dict()
        if include_inactivos or data.get("activo", True):
            proyectos.append(ProyectoResponse(**data))
    proyectos.sort(key=lambda x: int(x.id_proyecto))
    return proyectos


# OBTENER POR ID DE DOCUMENTO O ID_PROYECTO

def get_proyecto(document_id: str) -> Optional[ProyectoResponse]:
    if not document_id or len(document_id.strip()) < 3:
        raise ValueError("El ID del documento no es válido.")
    doc = proyectos_ref.document(document_id).get()
    if not doc.exists:
        return None
    return ProyectoResponse(**doc.to_dict())


def get_proyecto_by_id_proyecto(id_proyecto: str) -> Optional[ProyectoResponse]:
    if not id_proyecto or not id_proyecto.isdigit():
        raise ValueError("El 'id_proyecto' debe ser un número en formato texto, por ejemplo: '001'.")
    query = proyectos_ref.where("id_proyecto", "==", id_proyecto).limit(1).stream()
    for doc in query:
        return ProyectoResponse(**doc.to_dict())
    return None


# ACTUALIZAR PROYECTO

async def update_proyecto(proyecto_id: str, proyecto: ProyectoUpdate, archivo=None) -> Optional[ProyectoResponse]:
    query = proyectos_ref.where("id_proyecto", "==", proyecto_id).limit(1).stream()
    doc_ref = None
    for doc in query:
        doc_ref = proyectos_ref.document(doc.id)
        break
    if not doc_ref:
        return None

    update_data = proyecto.dict(exclude_unset=True)
    campos_no_editables = {"id_docente", "id_materia", "id_grupo"}
    update_data = {k: v for k, v in update_data.items() if k not in campos_no_editables}

    if "id_estudiantes" in update_data:
        if isinstance(update_data["id_estudiantes"], str):
            try:
                update_data["id_estudiantes"] = json.loads(update_data["id_estudiantes"])
            except json.JSONDecodeError:
                raise ValueError(
                    "El campo 'id_estudiantes' debe ser un JSON válido (por ejemplo: ['EST001','EST002']).")

        if not isinstance(update_data["id_estudiantes"], list) or not update_data["id_estudiantes"]:
            raise ValueError("Debe haber al menos un estudiante asociado al proyecto.")

    if archivo:
        if not archivo.filename.lower().endswith(".pdf"):
            raise ValueError("El archivo debe tener formato PDF (.pdf).")
        pdf_url = await upload_pdf_to_cloudinary(archivo)
        update_data["archivo_pdf"] = pdf_url

    update_data["updated_at"] = datetime.utcnow().isoformat()
    doc_ref.update(update_data)

    updated_doc = doc_ref.get()
    return ProyectoResponse(**updated_doc.to_dict())


# ELIMINAR (DESACTIVAR) PROYECTO

def delete_proyecto(id_proyecto: str) -> bool:
    query = proyectos_ref.where("id_proyecto", "==", id_proyecto).limit(1).stream()
    doc_ref = None
    for doc in query:
        doc_ref = proyectos_ref.document(doc.id)
        break
    if not doc_ref:
        return False

    doc_ref.update({
        "activo": False,
        "updated_at": datetime.utcnow().isoformat()
    })
    return True
from typing import List, Optional
from datetime import datetime
import json
from app.schemas.proyect import ProyectoCreate, ProyectoResponse, ProyectoUpdate
from app.services.cloudinary_service import upload_pdf_to_cloudinary
from app.core.firebase import firebase_client, Collections

db = firebase_client.get_db()
proyectos_ref = db.collection(Collections.PROYECTOS)


# ---------------------------------------------------------------
# FUNCIONES AUXILIARES
# ---------------------------------------------------------------
def _generar_id_proyecto() -> str:
    """
    Genera un nuevo ID de proyecto autoincremental con formato '001', '002', ...
    Busca el último ID en Firebase y le suma 1.
    """
    proyectos = list(proyectos_ref.stream())
    if not proyectos:
        return "001"

    # Obtener todos los IDs existentes y convertirlos a int
    ids = []
    for doc in proyectos:
        data = doc.to_dict()
        id_p = data.get("id_proyecto")
        if id_p and id_p.isdigit():
            ids.append(int(id_p))

    nuevo_id = max(ids, default=0) + 1
    return f"{nuevo_id:03d}"  # Ejemplo: 1 -> '001', 12 -> '012'


# ---------------------------------------------------------------
# CREAR PROYECTO (archivo obligatorio)
# ---------------------------------------------------------------
async def create_proyecto(proyecto: ProyectoCreate, archivo) -> ProyectoResponse:
    """
    Crea un nuevo proyecto y lo almacena en Firestore.
    El archivo PDF es obligatorio.
    """

    # -------------------------
    # VALIDACIONES
    # -------------------------
    if not archivo:
        raise ValueError("Es obligatorio subir un archivo PDF para crear el proyecto.")

    if not archivo.filename.lower().endswith(".pdf"):
        raise ValueError("El archivo debe tener formato PDF (.pdf).")

    # Validar id_estudiantes
    if isinstance(proyecto.id_estudiantes, str):
        try:
            proyecto.id_estudiantes = json.loads(proyecto.id_estudiantes)
        except json.JSONDecodeError:
            raise ValueError("El campo 'id_estudiantes' debe ser un JSON válido (por ejemplo: ['EST001','EST002']).")

    if not isinstance(proyecto.id_estudiantes, list) or not proyecto.id_estudiantes:
        raise ValueError("Debe incluirse al menos un estudiante en la lista 'id_estudiantes'.")

    for eid in proyecto.id_estudiantes:
        if not isinstance(eid, str) or len(eid.strip()) < 5:
            raise ValueError(f"El ID del estudiante '{eid}' no es válido (mínimo 5 caracteres).")

    if len(proyecto.id_docente.strip()) < 5:
        raise ValueError("El ID del docente no cumple el tamaño mínimo de 5 caracteres.")

    if not proyecto.titulo_proyecto or len(proyecto.titulo_proyecto.strip()) < 3:
        raise ValueError("El título del proyecto debe tener al menos 3 caracteres.")

    # Validar campos obligatorios
    for field in ["id_grupo", "id_area_tematica", "id_evento", "id_materia"]:
        valor = getattr(proyecto, field, None)
        if not valor or len(valor.strip()) < 3:
            raise ValueError(f"El campo '{field}' es obligatorio y debe tener al menos 3 caracteres.")

    if not proyecto.tipo_actividad or len(proyecto.tipo_actividad.strip()) < 3:
        raise ValueError("El tipo de actividad debe tener al menos 3 caracteres.")

    # -------------------------
    # GENERAR ID Y SUBIR ARCHIVO
    # -------------------------
    id_proyecto = _generar_id_proyecto()
    pdf_url = await upload_pdf_to_cloudinary(archivo)

    # -------------------------
    # GUARDAR EN FIREBASE
    # -------------------------
    nuevo_doc = proyectos_ref.document()

    data = {
        "id_proyecto": id_proyecto,
        "id_docente": proyecto.id_docente,
        "id_estudiantes": proyecto.id_estudiantes,
        "id_grupo": proyecto.id_grupo,
        "id_area_tematica": proyecto.id_area_tematica,
        "id_evento": proyecto.id_evento,
        "id_materia": proyecto.id_materia,
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


# ---------------------------------------------------------------
# LISTAR PROYECTOS
# ---------------------------------------------------------------
def list_proyectos(include_inactivos: bool = False) -> List[ProyectoResponse]:
    """
    Retorna todos los proyectos activos.
    Si include_inactivos=True, retorna también los inactivos.
    """
    docs = proyectos_ref.stream()
    proyectos = []

    for doc in docs:
        data = doc.to_dict()
        if include_inactivos or data.get("activo", True):
            proyectos.append(ProyectoResponse(**data))

    # Ordenamos por id_proyecto (numérico)
    proyectos.sort(key=lambda x: int(x.id_proyecto))
    return proyectos


# ---------------------------------------------------------------
# OBTENER UN PROYECTO POR DOCUMENT ID (interno de Firebase)
# ---------------------------------------------------------------
def get_proyecto(document_id: str) -> Optional[ProyectoResponse]:
    """
    Obtiene un proyecto por su ID de documento (interno de Firebase).
    """
    if not document_id or len(document_id.strip()) < 3:
        raise ValueError("El ID del documento no es válido.")

    doc = proyectos_ref.document(document_id).get()
    if not doc.exists:
        return None
    return ProyectoResponse(**doc.to_dict())


# ---------------------------------------------------------------
# OBTENER UN PROYECTO POR SU ID_PROYECTO AUTOGENERADO
# ---------------------------------------------------------------
def get_proyecto_by_id_proyecto(id_proyecto: str) -> Optional[ProyectoResponse]:
    """
    Busca un proyecto por su campo 'id_proyecto' (por ejemplo: '001', '002', etc.).
    """
    if not id_proyecto or not id_proyecto.isdigit():
        raise ValueError("El 'id_proyecto' debe ser un número en formato de texto, por ejemplo: '001'.")

    query = proyectos_ref.where("id_proyecto", "==", id_proyecto).limit(1).stream()
    for doc in query:
        return ProyectoResponse(**doc.to_dict())
    return None


# ---------------------------------------------------------------
# ACTUALIZAR PROYECTO
# ---------------------------------------------------------------
async def update_proyecto(proyecto_id: str, proyecto: ProyectoUpdate, archivo=None) -> Optional[ProyectoResponse]:
    """
    Actualiza un proyecto existente por su 'id_proyecto' (no el ID interno de Firebase).
    Si se envía un nuevo PDF, se sube a Cloudinary.
    """

    # Buscar el documento correspondiente al id_proyecto
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

    # Validar id_estudiantes si se manda
    if "id_estudiantes" in update_data:
        if isinstance(update_data["id_estudiantes"], str):
            try:
                update_data["id_estudiantes"] = json.loads(update_data["id_estudiantes"])
            except json.JSONDecodeError:
                raise ValueError("El campo 'id_estudiantes' debe ser un JSON válido (por ejemplo: ['EST001','EST002']).")

        if not isinstance(update_data["id_estudiantes"], list) or not update_data["id_estudiantes"]:
            raise ValueError("Debe haber al menos un estudiante asociado al proyecto.")

    # Subir nuevo archivo si se envía
    if archivo:
        if not archivo.filename.lower().endswith(".pdf"):
            raise ValueError("El archivo debe tener formato PDF (.pdf).")
        pdf_url = await upload_pdf_to_cloudinary(archivo)
        update_data["archivo_pdf"] = pdf_url

    update_data["updated_at"] = datetime.utcnow().isoformat()
    doc_ref.update(update_data)

    updated_doc = doc_ref.get()
    return ProyectoResponse(**updated_doc.to_dict())


# ---------------------------------------------------------------
# ELIMINAR (DESACTIVAR) PROYECTO
# ---------------------------------------------------------------
def delete_proyecto(id_proyecto: str) -> bool:
    """
    Marca un proyecto como inactivo (no lo borra físicamente).
    """
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

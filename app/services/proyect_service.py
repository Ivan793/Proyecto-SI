from typing import List, Optional
from datetime import datetime
import json
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


def _existe_en_coleccion(coleccion: str, campo_id: str, valor_id: str, valor_area = 0) -> bool:
    """Verifica si un documento existe en una colección dada con un ID específico."""
    print("entro a la validacion")
    print(coleccion, campo_id, valor_id)
    collection_ref = db.collection(coleccion)    
    
    query = (collection_ref.where(filter = FieldFilter(campo_id, "==", valor_id)).stream())

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

def _obtener_documento(coleccion, campo, valor):
    docs = db.collection(coleccion).where(campo, "==", valor).limit(1).get()
    return docs[0] if docs else None


def _validar_existencia_ids(proyecto: any):
    """
    Verifica que todos los IDs y códigos referenciados existan en Firestore.
    Si alguno no existe, lanza ValueError.
    """
    # Validar docente en colección DOCENTES

    docente_uid = proyecto["id_docente"]["uid_docente"]

    # Traer el docente
    docente_ref = db.collection(Collections.DOCENTES).document(docente_uid)
    docente_doc = docente_ref.get()

    if not docente_doc.exists:
        raise ValueError(f"No existe ningún docente con UID '{docente_uid}' en la base de datos.")

    docente_data = docente_doc.to_dict()

    # Aquí está el usuario real del docente
    usuario_uid = docente_data.get("id_usuario")

    if not usuario_uid:
        raise ValueError(f"El docente '{docente_uid}' no tiene un id_usuario asociado.")

    # Buscar al usuario en la colección usuarios
    usuario_ref = db.collection(Collections.USUARIOS).document(usuario_uid)
    usuario_doc = usuario_ref.get()

    if not usuario_doc.exists:
        raise ValueError(f"No existe usuario asociado al docente con UID '{docente_uid}'.")

    usuario_data = usuario_doc.to_dict()

    primer_nombre = usuario_data.get("primer_nombre", "")
    segundo_nombre = usuario_data.get("segundo_nombre", "")
    primer_apellido = usuario_data.get("primer_apellido", "")
    segundo_apellido = usuario_data.get("segundo_apellido", "")

    nombre_completo = f"{primer_nombre} {segundo_nombre} {primer_apellido} {segundo_apellido}".strip()

    # Guardar el nombre dentro del proyecto
    proyecto["id_docente"]["nombre"] = nombre_completo




   # Validar estudiantes
    for estudiante in proyecto["id_estudiantes"]:
        
        id_estudiante = estudiante["id_estudiante"]

        # 1️ Validar que el estudiante exista
        estudiante_ref = db.collection(Collections.ESTUDIANTES).document(id_estudiante)
        estudiante_doc = estudiante_ref.get()

        if not estudiante_doc.exists:
            raise ValueError(f"No existe ningún estudiante con UID '{id_estudiante}' en la base de datos.")

        estudiante_data = estudiante_doc.to_dict()

        # 2️ Obtener el id_usuario del estudiante
        id_usuario = estudiante_data.get("id_usuario")
        if not id_usuario:
            raise ValueError(f"El estudiante '{id_estudiante}' no tiene asociado un id_usuario.")

        # 3️ Buscar el usuario para obtener el nombre completo
        usuario_ref = db.collection(Collections.USUARIOS).document(id_usuario)
        usuario_doc = usuario_ref.get()

        if not usuario_doc.exists:
            raise ValueError(f"No existe el usuario '{id_usuario}' asociado al estudiante '{id_estudiante}'.")

        usuario_data = usuario_doc.to_dict()

        primer_nombre = usuario_data.get("primer_nombre", "")
        segundo_nombre = usuario_data.get("segundo_nombre", "")
        primer_apellido = usuario_data.get("primer_apellido", "")
        segundo_apellido = usuario_data.get("segundo_apellido", "")

        nombre_completo = " ".join([
            primer_nombre, segundo_nombre, primer_apellido, segundo_apellido
        ]).strip()

        # Guardar el nombre en el objeto proyecto
        estudiante["nombre"] = nombre_completo

        print(f" Estudiante validado: {id_estudiante} - {nombre_completo}")




    #  Validar grupo
    if not _existe_en_coleccion(Collections.GRUPOS, "codigo_grupo", proyecto["id_grupo"]):
        raise ValueError(f"No existe ningún grupo con ID '{proyecto["id_grupo"]}'.")

# ----- Validar Línea de Investigación -----
    linea_doc = _obtener_documento(Collections.LINEAS_INVESTIGACION, "codigo_linea", proyecto["codigo_linea"])
    if not linea_doc:
        raise ValueError(f"No existe ninguna línea de investigación con código '{proyecto['codigo_linea']}'.")

    linea_data = linea_doc.to_dict()
    proyecto["nombre_linea"] = linea_data.get("nombre_linea")


    # ----- Validar Sublinea -----
    sublinea_path = f"{Collections.LINEAS_INVESTIGACION}/{proyecto['codigo_linea']}/sublineas"
    sublinea_doc = _obtener_documento(sublinea_path, "codigo_sublinea", proyecto.get("codigo_sublinea"))

    if not sublinea_doc:
        raise ValueError(f"No existe ninguna sublínea con código '{proyecto.get('codigo_sublinea')}'.")

    sublinea_data = sublinea_doc.to_dict()
    proyecto["nombre_sublinea"] = sublinea_data.get("nombre_sublinea")
    


    # ----- Validar Área Temática -----
    areas = sublinea_data.get("areas_tematicas", [])

    area_match = next((a for a in areas if a.get("codigo_area") == proyecto["codigo_area"]), None)
    if not area_match:
        raise ValueError(f"No existe ninguna área temática con código '{proyecto['codigo_area']}'.")

    proyecto["nombre_area"] = area_match.get("nombre_area")

    
    
    #  Validar materia
    if not _existe_en_coleccion(Collections.MATERIAS, "codigo_materia", proyecto["codigo_materia"]):
        raise ValueError(f"No existe ninguna materia con ID '{proyecto["codigo_materia"]}'.")

    evento_ref = db.collection(Collections.EVENTOS).document(proyecto["id_evento"])
    evento_doc = evento_ref.get()

    print("UID recibido para evento:", proyecto["id_evento"])  # <-- Verificación en consola
    if not evento_doc.exists:
        raise ValueError(f"No existe ningún evento con UID '{proyecto["id_evento"]}' en la base de datos.")
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

    #  Convertir cadena JSON de estudiantes si viene como string
    if isinstance(proyecto.id_estudiantes, str):
        try:
            proyecto.id_estudiantes = json.loads(proyecto.id_estudiantes)
        except json.JSONDecodeError:
            raise ValueError("El campo 'id_estudiantes' debe ser un JSON válido.")

    if not isinstance(proyecto.id_estudiantes, list) or not proyecto.id_estudiantes:
        raise ValueError("Debe incluirse al menos un estudiante en la lista 'id_estudiantes'.")

    #  Validar estructura de cada estudiante
    for estudiante in proyecto.id_estudiantes:
        if not isinstance(estudiante, dict) or "id_estudiante" not in estudiante:
            raise ValueError("Cada estudiante debe tener la clave 'id_estudiante'.")

    #  Validar y obtener nombre de cada estudiante
    estudiantes_validados = []
    for estudiante in proyecto.id_estudiantes:
        id_estudiante = estudiante["id_estudiante"]

        estudiante_ref = db.collection(Collections.ESTUDIANTES).document(id_estudiante)
        estudiante_doc = estudiante_ref.get()
        if not estudiante_doc.exists:
            raise ValueError(f"No existe ningún estudiante con UID '{id_estudiante}'.")

        estudiante_data = estudiante_doc.to_dict()
        id_usuario = estudiante_data.get("id_usuario")
        if not id_usuario:
            raise ValueError(f"El estudiante '{id_estudiante}' no tiene asociado un id_usuario.")

        usuario_ref = db.collection(Collections.USUARIOS).document(id_usuario)
        usuario_doc = usuario_ref.get()
        if not usuario_doc.exists:
            raise ValueError(f"No existe el usuario con UID '{id_usuario}' asociado al estudiante '{id_estudiante}'.")

        usuario_data = usuario_doc.to_dict()
        nombre_completo = " ".join(
            filter(None, [
                usuario_data.get("primer_nombre"),
                usuario_data.get("segundo_nombre"),
                usuario_data.get("primer_apellido"),
                usuario_data.get("segundo_apellido"),
            ])
        )

        estudiantes_validados.append({
            "id_estudiante": id_estudiante,
            "nombre": nombre_completo.strip()
        })

    #  Validar docente (análogo)
    docente_id = proyecto.id_docente.uid_docente
    docente_ref = db.collection(Collections.DOCENTES).document(docente_id)
    docente_doc = docente_ref.get()
    if not docente_doc.exists:
        raise ValueError(f"No existe ningún docente con UID '{docente_id}'.")

    docente_data = docente_doc.to_dict()
    id_usuario_docente = docente_data.get("id_usuario")
    usuario_docente = db.collection(Collections.USUARIOS).document(id_usuario_docente).get().to_dict()
    nombre_docente = " ".join(
        filter(None, [
            usuario_docente.get("primer_nombre"),
            usuario_docente.get("segundo_nombre"),
            usuario_docente.get("primer_apellido"),
            usuario_docente.get("segundo_apellido"),
        ])
    )

    docente_info = {
        "uid_docente": docente_id,
        "nombre": nombre_docente.strip()
    }

    #  Subir archivo PDF
    id_proyecto = _generar_id_proyecto()
    pdf_url = await upload_pdf_to_cloudinary(archivo)

    #  Datos del proyecto
    data = {
        "id_proyecto": id_proyecto,
        "id_docente": docente_info,
        "id_estudiantes": estudiantes_validados,
        "id_grupo": proyecto.id_grupo,
        "codigo_area": proyecto.codigo_area,
        "id_evento": proyecto.id_evento,
        "codigo_materia": proyecto.codigo_materia,
        "codigo_linea": proyecto.codigo_linea,
        "codigo_sublinea": proyecto.codigo_sublinea,
        "titulo_proyecto": proyecto.titulo_proyecto.strip(),
        "tipo_actividad": proyecto.tipo_actividad,
        "archivo_pdf": pdf_url,
        "fecha_subida": datetime.utcnow().isoformat(),
        "activo": True,

        #  Aquí establecemos los valores por defecto
        "calificacion": None,
        "estado_calificacion": "pendiente",
    }

    proyectos_ref.document(id_proyecto).set(data)
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
                raise ValueError("El campo 'id_estudiantes' debe ser un JSON válido (por ejemplo: ['EST001','EST002']).")

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
    """
    Desactiva un proyecto cambiando el campo 'activo' a False.
    """
    # Buscar el documento cuyo campo 'id_proyecto' coincide
    query = proyectos_ref.where("id_proyecto", "==", id_proyecto).limit(1).stream()
    doc_ref = None

    for doc in query:
        doc_ref = proyectos_ref.document(doc.id)
        break

    # Si no se encuentra, retorna False
    if not doc_ref:
        return False

    # Actualizar el campo 'activo' a False
    doc_ref.update({
        "activo": False,
        "updated_at": datetime.utcnow().isoformat()
    })

    return True

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

# ---------------------------------------------------------------
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
    
    query = collection_ref.where(filter=FieldFilter(campo_id, "==", valor_id)).stream()

    for doc in query:
        if "sublineas" in coleccion and valor_area != 0:
            coleccion_areas = doc.to_dict()
            print("este es coleccion area", coleccion_areas)
            for area in coleccion_areas["areas_tematicas"]:
                print("esta es el area", area)
                if area["codigo_area"] == valor_area:
                    return True
            return False
        return True
    return False


def _obtener_documento(coleccion, campo, valor):
    """Obtiene un documento de una colección según un campo y valor específicos."""
    docs = db.collection(coleccion).where(campo, "==", valor).limit(1).get()
    return docs[0] if docs else None


def _detectar_tipo_usuario_y_obtener_datos(id_usuario: str) -> dict:
    """
    Detecta si un ID corresponde a un estudiante o egresado y retorna sus datos.
    
    Returns:
        dict con keys: {
            'tipo': 'estudiante' | 'egresado',
            'existe': bool,
            'id_usuario': str,
            'nombre_completo': str,
            'datos': dict (datos completos del documento)
        }
    """
    # Primero intentar buscar en estudiantes
    estudiante_ref = db.collection(Collections.ESTUDIANTES).document(id_usuario)
    estudiante_doc = estudiante_ref.get()
    
    if estudiante_doc.exists:
        estudiante_data = estudiante_doc.to_dict()
        id_usuario_ref = estudiante_data.get("id_usuario")
        
        if not id_usuario_ref:
            raise ValueError(f"El estudiante '{id_usuario}' no tiene asociado un id_usuario.")
        
        # Obtener datos del usuario
        usuario_ref = db.collection(Collections.USUARIOS).document(id_usuario_ref)
        usuario_doc = usuario_ref.get()
        
        if not usuario_doc.exists:
            raise ValueError(f"No existe el usuario con UID '{id_usuario_ref}' asociado al estudiante '{id_usuario}'.")
        
        usuario_data = usuario_doc.to_dict()
        nombre_completo = " ".join(
            filter(None, [
                usuario_data.get("primer_nombre"),
                usuario_data.get("segundo_nombre"),
                usuario_data.get("primer_apellido"),
                usuario_data.get("segundo_apellido"),
            ])
        )
        
        return {
            'tipo': 'estudiante',
            'existe': True,
            'id_usuario': id_usuario_ref,
            'nombre_completo': nombre_completo.strip(),
            'datos': estudiante_data,
            'usuario_data': usuario_data
        }
    
    # Si no es estudiante, buscar en egresados
    egresado_ref = db.collection(Collections.EGRESADOS).document(id_usuario)
    egresado_doc = egresado_ref.get()
    
    if egresado_doc.exists:
        egresado_data = egresado_doc.to_dict()
        id_usuario_ref = egresado_data.get("id_usuario")
        
        if not id_usuario_ref:
            raise ValueError(f"El egresado '{id_usuario}' no tiene asociado un id_usuario.")
        
        # Obtener datos del usuario
        usuario_ref = db.collection(Collections.USUARIOS).document(id_usuario_ref)
        usuario_doc = usuario_ref.get()
        
        if not usuario_doc.exists:
            raise ValueError(f"No existe el usuario con UID '{id_usuario_ref}' asociado al egresado '{id_usuario}'.")
        
        usuario_data = usuario_doc.to_dict()
        nombre_completo = " ".join(
            filter(None, [
                usuario_data.get("primer_nombre"),
                usuario_data.get("segundo_nombre"),
                usuario_data.get("primer_apellido"),
                usuario_data.get("segundo_apellido"),
            ])
        )
        
        return {
            'tipo': 'egresado',
            'existe': True,
            'id_usuario': id_usuario_ref,
            'nombre_completo': nombre_completo.strip(),
            'datos': egresado_data,
            'usuario_data': usuario_data
        }
    
    # Si no existe en ninguna colección
    return {
        'tipo': None,
        'existe': False,
        'id_usuario': None,
        'nombre_completo': None,
        'datos': None,
        'usuario_data': None
    }


# ---------------------------------------------------------------
# CREAR PROYECTO
# ---------------------------------------------------------------
async def create_proyecto_from_dict(proyecto_dict: dict, archivo) -> ProyectoResponse:
    """
    Crea un nuevo proyecto desde un diccionario, validando datos y referencias.
    Esta función maneja la conversión y validación antes de llamar a create_proyecto.
    """
    
    # Validar archivo PDF
    if not archivo:
        raise ValueError("Es obligatorio subir un archivo PDF para crear el proyecto.")
    if not archivo.filename.lower().endswith(".pdf"):
        raise ValueError("El archivo debe tener formato PDF (.pdf).")

    # Normalizar id_docente
    id_docente = proyecto_dict.get("id_docente")
    if id_docente:
        if isinstance(id_docente, dict):
            uid = id_docente.get("uid_docente", "")
            if not uid or uid.strip() == "":
                proyecto_dict["id_docente"] = None
        elif isinstance(id_docente, str) and id_docente.strip() == "":
            proyecto_dict["id_docente"] = None
    
    # Normalizar id_grupo
    if "id_grupo" in proyecto_dict:
        if proyecto_dict["id_grupo"] == "" or proyecto_dict["id_grupo"] is None:
            proyecto_dict["id_grupo"] = None
    
    # Normalizar codigo_materia
    if "codigo_materia" in proyecto_dict:
        if proyecto_dict["codigo_materia"] == "" or proyecto_dict["codigo_materia"] is None:
            proyecto_dict["codigo_materia"] = None

    # Manejar id_estudiantes
    id_estudiantes = proyecto_dict.get("id_estudiantes")
    
    if isinstance(id_estudiantes, str):
        try:
            id_estudiantes = json.loads(id_estudiantes)
        except json.JSONDecodeError:
            raise ValueError("El campo 'id_estudiantes' debe ser un JSON válido.")
    
    if not isinstance(id_estudiantes, list) or not id_estudiantes:
        raise ValueError("Debe incluirse al menos un estudiante en la lista 'id_estudiantes'.")

    # Normalizar cada estudiante
    estudiantes_normalizados = []
    for est in id_estudiantes:
        if isinstance(est, dict) and "id_estudiante" in est:
            estudiantes_normalizados.append(est)
        elif isinstance(est, str):
            estudiantes_normalizados.append({"id_estudiante": est})
        else:
            raise ValueError(f"Formato de estudiante no válido: {est}")
    
    proyecto_dict["id_estudiantes"] = estudiantes_normalizados

    # Validar y obtener nombre de cada estudiante/egresado
    estudiantes_validados = []
    primer_usuario_info = None
    
    for idx, estudiante in enumerate(estudiantes_normalizados):
        id_estudiante = estudiante.get("id_estudiante")
        
        if not id_estudiante or id_estudiante.strip() == "":
            raise ValueError("El campo 'id_estudiante' no puede estar vacío.")

        # Detectar si es estudiante o egresado
        usuario_info = _detectar_tipo_usuario_y_obtener_datos(id_estudiante)
        
        if not usuario_info['existe']:
            raise ValueError(f"No existe ningún estudiante ni egresado con UID '{id_estudiante}'.")
        
        # Guardar info del primer usuario para determinar tipo de proyecto
        if idx == 0:
            primer_usuario_info = usuario_info
        
        estudiantes_validados.append({
            "id_estudiante": id_estudiante,
            "nombre": usuario_info['nombre_completo']
        })

    # Determinar si es proyecto de egresado basado en el primer usuario
    es_egresado = (primer_usuario_info['tipo'] == 'egresado')

    print(f"DEBUG - Proyecto detectado como: {'EGRESADO' if es_egresado else 'ESTUDIANTE'}")
    print(f"DEBUG - Tipo de usuario: {primer_usuario_info['tipo']}")

    # Validar que si es egresado no venga docente, materia, grupo o calificación
    if es_egresado:
        if proyecto_dict.get("id_docente") is not None:
            raise ValueError("Los proyectos de egresados no pueden tener docente asignado.")
        if proyecto_dict.get("codigo_materia") is not None:
            raise ValueError("Los proyectos de egresados no pueden tener materia asignada.")
        if proyecto_dict.get("id_grupo") is not None:
            raise ValueError("Los proyectos de egresados no pueden tener grupo asignado.")
        if proyecto_dict.get("calificacion") is not None:
            raise ValueError("Los proyectos de egresados no pueden tener calificación.")

    docente_info = None

    # SI NO ES EGRESADO → VALIDACIONES NORMALES
    if not es_egresado:
        # Validar que vengan los campos obligatorios
        if not proyecto_dict.get("id_docente"):
            raise ValueError("El campo 'id_docente' es obligatorio para estudiantes activos.")
        if not proyecto_dict.get("id_grupo"):
            raise ValueError("El campo 'id_grupo' es obligatorio para estudiantes activos.")
        if not proyecto_dict.get("codigo_materia"):
            raise ValueError("El campo 'codigo_materia' es obligatorio para estudiantes activos.")

        # Validar docente
        docente_data = proyecto_dict["id_docente"]
        docente_id = docente_data.get("uid_docente") if isinstance(docente_data, dict) else docente_data
        
        docente_ref = db.collection(Collections.DOCENTES).document(docente_id)
        docente_doc = docente_ref.get()
        if not docente_doc.exists:
            raise ValueError(f"No existe ningún docente con UID '{docente_id}'.")

        docente_data_db = docente_doc.to_dict()
        id_usuario_docente = docente_data_db.get("id_usuario")
        if not id_usuario_docente:
            raise ValueError(f"El docente '{docente_id}' no tiene un id_usuario asociado.")

        usuario_docente_ref = db.collection(Collections.USUARIOS).document(id_usuario_docente)
        usuario_docente_doc = usuario_docente_ref.get()
        if not usuario_docente_doc.exists:
            raise ValueError(f"No se encontró el usuario asociado al docente '{docente_id}'.")
        
        usuario_docente = usuario_docente_doc.to_dict()
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

        # VALIDAR GRUPO
        if not _existe_en_coleccion(Collections.GRUPOS, "codigo_grupo", proyecto_dict["id_grupo"]):
            raise ValueError(f"No existe ningún grupo con código '{proyecto_dict['id_grupo']}'.")

        # VALIDAR MATERIA
        if not _existe_en_coleccion(Collections.MATERIAS, "codigo_materia", proyecto_dict["codigo_materia"]):
            raise ValueError(f"No existe ninguna materia con código '{proyecto_dict['codigo_materia']}'.")

    # VALIDAR LÍNEA DE INVESTIGACIÓN (obligatorio para todos)
    linea_doc = _obtener_documento(Collections.LINEAS_INVESTIGACION, "codigo_linea", proyecto_dict["codigo_linea"])
    if not linea_doc:
        raise ValueError(f"No existe ninguna línea de investigación con código '{proyecto_dict['codigo_linea']}'.")

    linea_data = linea_doc.to_dict()
    nombre_linea = linea_data.get("nombre_linea")

    # VALIDAR SUBLÍNEA (obligatorio para todos)
    sublinea_path = f"{Collections.LINEAS_INVESTIGACION}/{proyecto_dict['codigo_linea']}/sublineas"
    sublinea_doc = _obtener_documento(sublinea_path, "codigo_sublinea", proyecto_dict.get("codigo_sublinea"))

    if not sublinea_doc:
        raise ValueError(f"No existe ninguna sublínea con código '{proyecto_dict.get('codigo_sublinea')}'.")

    sublinea_data = sublinea_doc.to_dict()
    nombre_sublinea = sublinea_data.get("nombre_sublinea")

    # VALIDAR ÁREA TEMÁTICA (obligatorio para todos)
    areas = sublinea_data.get("areas_tematicas", [])
    area_match = next((a for a in areas if a.get("codigo_area") == proyecto_dict["codigo_area"]), None)
    if not area_match:
        raise ValueError(f"No existe ninguna área temática con código '{proyecto_dict['codigo_area']}'.")

    nombre_area = area_match.get("nombre_area")

    # VALIDAR EVENTO (obligatorio para todos)
    evento_ref = db.collection(Collections.EVENTOS).document(proyecto_dict["id_evento"])
    evento_doc = evento_ref.get()

    print("UID recibido para evento:", proyecto_dict["id_evento"])
    if not evento_doc.exists:
        raise ValueError(f"No existe ningún evento con UID '{proyecto_dict['id_evento']}' en la base de datos.")
    else:
        print("Evento encontrado:", evento_doc.to_dict())

    # SUBIR ARCHIVO PDF
    id_proyecto = _generar_id_proyecto()
    pdf_url = await upload_pdf_to_cloudinary(archivo)

    # DATOS DEL PROYECTO (EGRESADO O NO EGRESADO)
    data = {
        "id_proyecto": id_proyecto,
        "id_docente": docente_info if not es_egresado else None,
        "id_estudiantes": estudiantes_validados,
        "id_grupo": proyecto_dict.get("id_grupo") if not es_egresado else None,
        "codigo_area": proyecto_dict["codigo_area"],
        "nombre_area": nombre_area,
        "id_evento": proyecto_dict["id_evento"],
        "codigo_materia": proyecto_dict.get("codigo_materia") if not es_egresado else None,
        "codigo_linea": proyecto_dict["codigo_linea"],
        "nombre_linea": nombre_linea,
        "codigo_sublinea": proyecto_dict.get("codigo_sublinea"),
        "nombre_sublinea": nombre_sublinea,
        "titulo_proyecto": proyecto_dict["titulo_proyecto"].strip(),
        "tipo_actividad": proyecto_dict["tipo_actividad"],
        "archivo_pdf": pdf_url,
        "fecha_subida": datetime.utcnow().isoformat(),
        "activo": True,
        "es_egresado": es_egresado,
        
        # Valores por defecto - para egresados NO puede haber calificación
        "calificacion": None,
        "estado_calificacion": "no_aplica" if es_egresado else "pendiente",
    }

    proyectos_ref.document(id_proyecto).set(data)
    return ProyectoResponse(**data)


# ---------------------------------------------------------------
# LISTAR PROYECTOS
# ---------------------------------------------------------------
def list_proyectos(include_inactivos: bool = False) -> List[ProyectoResponse]:
    """Lista todos los proyectos, opcionalmente incluyendo los inactivos."""
    docs = proyectos_ref.stream()
    proyectos = []
    for doc in docs:
        data = doc.to_dict()
        if include_inactivos or data.get("activo", True):
            proyectos.append(ProyectoResponse(**data))
    proyectos.sort(key=lambda x: int(x.id_proyecto))
    return proyectos


# ---------------------------------------------------------------
# OBTENER POR ID DE DOCUMENTO O ID_PROYECTO
# ---------------------------------------------------------------
def get_proyecto(document_id: str) -> Optional[ProyectoResponse]:
    """Obtiene un proyecto por su ID de documento de Firestore."""
    if not document_id or len(document_id.strip()) < 3:
        raise ValueError("El ID del documento no es válido.")
    
    doc = proyectos_ref.document(document_id).get()
    if not doc.exists:
        return None
    return ProyectoResponse(**doc.to_dict())


def get_proyecto_by_id_proyecto(id_proyecto: str) -> Optional[ProyectoResponse]:
    """Obtiene un proyecto por su id_proyecto (formato '001', '002', etc.)."""
    if not id_proyecto or not id_proyecto.isdigit():
        raise ValueError("El 'id_proyecto' debe ser un número en formato texto, por ejemplo: '001'.")
    
    query = proyectos_ref.where("id_proyecto", "==", id_proyecto).limit(1).stream()
    for doc in query:
        return ProyectoResponse(**doc.to_dict())
    return None


# ---------------------------------------------------------------
# ACTUALIZAR PROYECTO
# ---------------------------------------------------------------
async def update_proyecto(proyecto_id: str, proyecto: ProyectoUpdate, archivo=None) -> Optional[ProyectoResponse]:
    """Actualiza un proyecto existente."""
    
    # Buscar el proyecto por id_proyecto
    query = proyectos_ref.where("id_proyecto", "==", proyecto_id).limit(1).stream()
    doc_ref = None
    proyecto_actual = None
    
    for doc in query:
        doc_ref = proyectos_ref.document(doc.id)
        proyecto_actual = doc.to_dict()
        break
    
    if not doc_ref:
        return None

    # Verificar si es un proyecto de egresado
    es_egresado = proyecto_actual.get("es_egresado", False)

    # Preparar datos de actualización
    update_data = proyecto.dict(exclude_unset=True)
    
    # Campos no editables
    campos_no_editables = {"id_docente", "id_materia", "id_grupo", "id_estudiantes"}
    update_data = {k: v for k, v in update_data.items() if k not in campos_no_editables}

    # Si es egresado, NO permitir actualizar calificación
    if es_egresado and "calificacion" in update_data:
        raise ValueError("No se puede asignar calificación a proyectos de egresados.")

    # Validar calificación si viene en la actualización (solo para NO egresados)
    if not es_egresado and "calificacion" in update_data:
        calificacion = update_data["calificacion"]
        if calificacion is not None:
            if calificacion < 0 or calificacion > 5:
                raise ValueError("La calificación debe estar entre 0 y 5.")
            
            # Actualizar estado de calificación según la nota
            if calificacion >= 3:
                update_data["estado_calificacion"] = "aprobado"
            else:
                update_data["estado_calificacion"] = "reprobado"
        else:
            update_data["estado_calificacion"] = "pendiente"

    # Si se sube un nuevo archivo PDF
    if archivo:
        if not archivo.filename.lower().endswith(".pdf"):
            raise ValueError("El archivo debe tener formato PDF (.pdf).")
        pdf_url = await upload_pdf_to_cloudinary(archivo)
        update_data["archivo_pdf"] = pdf_url

    # Agregar timestamp de actualización
    update_data["updated_at"] = datetime.utcnow().isoformat()

    # Actualizar el documento
    doc_ref.update(update_data)

    # Obtener y devolver el documento actualizado
    updated_doc = doc_ref.get()
    return ProyectoResponse(**updated_doc.to_dict())


# ---------------------------------------------------------------
# ELIMINAR (DESACTIVAR) PROYECTO
# ---------------------------------------------------------------
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
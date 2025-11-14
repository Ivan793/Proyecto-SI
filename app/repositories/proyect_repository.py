from app.repositories.base_repository import BaseRepository
from app.exceptions.base_exceptions import DatabaseException, NotFoundException
from app.services.cloudinary_service import upload_pdf_to_cloudinary
from datetime import datetime, timezone
from app.core.firebase import firebase_client, Collections
import logging

logger = logging.getLogger(__name__)

db = firebase_client.get_db()

class ProyectoRepository(BaseRepository):
    def __init__(self):
        super().__init__(collection_name="proyectos", id_field="id_proyecto")
        # Usa un nombre diferente al del property en BaseRepository
        self._collection_ref = db.collection(Collections.PROYECTOS)

    async def create_with_pdf(self, data: dict, archivo) -> str:
        """
        Crea un nuevo proyecto subiendo obligatoriamente un archivo PDF a Cloudinary.
        """
        if not archivo:
            raise ValueError("Debe subir un archivo PDF para crear el proyecto.")

        try:
            pdf_url = await upload_pdf_to_cloudinary(archivo)
            data["archivo_pdf"] = pdf_url
            data["fecha_subida"] = datetime.now(timezone.utc).isoformat()
            data["activo"] = True

            return await super().create(data)
        except Exception as e:
            logger.error(f"Error al crear proyecto: {e}")
            raise DatabaseException(f"No se pudo crear el proyecto: {str(e)}")

    async def update_with_pdf(self, proyecto_id: str, data: dict, archivo=None) -> bool:
        """
        Actualiza los datos de un proyecto. Si se envía un nuevo PDF, se reemplaza.
        """
        try:
            if archivo:
                pdf_url = await upload_pdf_to_cloudinary(archivo)
                data["archivo_pdf"] = pdf_url

            return await super().update(proyecto_id, data)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error al actualizar proyecto {proyecto_id}: {e}")
            raise DatabaseException("No se pudo actualizar el proyecto")

    async def soft_delete_proyect(self, document_id: str) -> bool:
        """
        Desactiva un proyecto cambiando el campo 'activo' a False.
        """
        try:
            doc_ref = self._collection_ref.document(document_id)
            doc = doc_ref.get()

            if not doc.exists:
                return False

            doc_ref.update({
                "activo": False,
                "updated_at": datetime.now(timezone.utc)
            })
            return True
        except Exception as e:
            logger.error(f"Error al desactivar proyecto {document_id}: {e}")
            return False

    async def get_students_by_project(self, project_id: str) -> list:
        """
        Obtiene los UIDs de los estudiantes asociados a un proyecto.
        
        Args:
            project_id: ID del proyecto
        
        Returns:
            Lista de UIDs de estudiantes
        """
        try:
            # Obtener el documento del proyecto
            doc_ref = self._collection_ref.document(project_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                logger.error(f"Proyecto {project_id} no encontrado")
                raise NotFoundException(f"Proyecto con ID {project_id} no encontrado")
            
            proyecto = doc.to_dict()
            
            # Obtener el campo id_estudiantes (puede tener diferentes estructuras)
            id_estudiantes = proyecto.get('id_estudiantes', [])
            
            if not id_estudiantes:
                logger.warning(f"Proyecto {project_id} no tiene estudiantes asociados")
                return []
            
            # Normalizar los datos - puede venir como lista de strings o lista de dicts
            uids_estudiantes = []
            
            for estudiante in id_estudiantes:
                if isinstance(estudiante, str):
                    # Si es un string directo, es el UID
                    uids_estudiantes.append(estudiante)
                elif isinstance(estudiante, dict):
                    # Si es un diccionario, buscar el campo id_estudiante o id_usuario
                    uid = estudiante.get('id_estudiante') or estudiante.get('id_usuario')
                    if uid:
                        uids_estudiantes.append(uid)
                else:
                    logger.warning(f"Formato de estudiante no reconocido: {type(estudiante)}")
            
            logger.info(f"Proyecto {project_id}: {len(uids_estudiantes)} estudiante(s) encontrado(s)")
            
            return uids_estudiantes
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo estudiantes del proyecto {project_id}: {e}")
            raise DatabaseException(f"Error al obtener estudiantes del proyecto: {str(e)}")
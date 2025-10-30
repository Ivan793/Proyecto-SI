from app.repositories.base_repository import BaseRepository
from app.exceptions.base_exceptions import DatabaseException, NotFoundException
from app.services.cloudinary_service import upload_pdf_to_cloudinary
from datetime import datetime, timezone
from typing import List, Dict, Any

import logging

logger = logging.getLogger(__name__)


class ProyectoRepository(BaseRepository):
    def __init__(self):
        super().__init__(collection_name="proyectos", id_field="id_proyecto")

    async def create_with_pdf(self, data: dict, archivo) -> str:
        """
        Crea un nuevo proyecto subiendo obligatoriamente un archivo PDF a Cloudinary.
        """
        if not archivo:
            raise ValueError("Debe subir un archivo PDF para crear el proyecto.")

        try:
            # Subir el PDF
            pdf_url = await upload_pdf_to_cloudinary(archivo)

            # Agregar metadata
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

    # ==================== MÉTODOS PARA CERTIFICADOS ====================

    async def get_students_by_project(self, id_proyecto: str) -> List[str]:
        """
        Obtiene los UIDs (IDs de usuario de Firebase Auth) de estudiantes asociados a un proyecto.

        IMPORTANTE: El proyecto guarda UIDs en el campo id_estudiantes.
        Este método los extrae y valida que existan en la colección estudiantes.

        Args:
            id_proyecto: ID del proyecto (ID de documento de Firebase)

        Returns:
            Lista de UIDs de Firebase Auth de los estudiantes

        Raises:
            ValueError: Si el proyecto no existe o no tiene estudiantes asignados
        """
        try:
            # Obtener el proyecto
            proyecto = await self.get_by_id(id_proyecto)

            if not proyecto:
                logger.warning(f"⚠️ Proyecto {id_proyecto} no encontrado")
                raise ValueError(f"Proyecto con ID {id_proyecto} no encontrado")

            uids_estudiantes = []

            #  Extraer UIDs del campo id_estudiantes
            if 'id_estudiantes' in proyecto and isinstance(proyecto['id_estudiantes'], list):
                for estudiante_info in proyecto['id_estudiantes']:
                    # Puede ser un dict (EstudianteInfo) o un string (UID directo)
                    if isinstance(estudiante_info, dict):
                        # Extraer el UID del campo id_estudiante
                        uid = estudiante_info.get('id_estudiante')
                        if uid:
                            uids_estudiantes.append(uid)
                    elif isinstance(estudiante_info, str):
                        # Formato antiguo: UID directo como string
                        uids_estudiantes.append(estudiante_info)

                logger.info(f" {len(uids_estudiantes)} UID(s) extraído(s): {uids_estudiantes}")

            # Caso alternativo: campo id_estudiante único
            elif 'id_estudiante' in proyecto and proyecto['id_estudiante']:
                uid = proyecto['id_estudiante']
                if isinstance(uid, dict):
                    uids_estudiantes = [uid.get('id_estudiante')]
                else:
                    uids_estudiantes = [uid]
                logger.info(f" UID único encontrado: {uids_estudiantes}")

            if not uids_estudiantes:
                logger.error(f" Proyecto {id_proyecto} no tiene estudiantes asignados")
                raise ValueError(f"El proyecto no tiene estudiantes asignados")

            #  VALIDACIÓN: Verificar que los UIDs existan en la colección estudiantes
            from app.core.firebase import get_firestore_client
            db = get_firestore_client()
            estudiantes_collection = db.collection('estudiantes')

            uids_validos = []
            for uid in uids_estudiantes:
                try:
                    # Buscar por el campo id_usuario (que contiene el UID)
                    query = estudiantes_collection.where('id_usuario', '==', uid).limit(1)
                    docs = query.stream()
                    docs_list = list(docs)

                    if docs_list:
                        # El UID existe en estudiantes
                        uids_validos.append(uid)
                        doc = docs_list[0]
                        logger.info(f" Estudiante validado: UID '{uid}' -> Doc ID: '{doc.id}'")
                    else:
                        logger.warning(f" No se encontró estudiante con id_usuario='{uid}'")

                except Exception as e:
                    logger.error(f" Error validando estudiante '{uid}': {str(e)}")
                    continue

            if not uids_validos:
                logger.error(f" No se encontraron estudiantes válidos en la BD")
                raise ValueError(
                    f"No se encontraron estudiantes válidos. "
                    f"UIDs buscados: {uids_estudiantes}"
                )

            logger.info(f" {len(uids_validos)} estudiante(s) validado(s) para proyecto {id_proyecto}")
            return uids_validos

        except ValueError:
            raise
        except Exception as e:
            logger.error(f" Error obteniendo estudiantes del proyecto {id_proyecto}: {str(e)}")
            raise DatabaseException(f"Error al obtener estudiantes del proyecto: {str(e)}")

    async def get_by_student(self, uid_estudiante: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los proyectos de un estudiante específico.

        Args:
            uid_estudiante: UID de Firebase Auth del estudiante

        Returns:
            Lista de proyectos del estudiante
        """
        try:
            proyectos = []
            todos_proyectos = await self.get_all()

            for proyecto in todos_proyectos:
                # Verificar si el estudiante está en el array de id_estudiantes
                if 'id_estudiantes' in proyecto and isinstance(proyecto['id_estudiantes'], list):
                    for est_info in proyecto['id_estudiantes']:
                        # Puede ser dict (EstudianteInfo) o string (UID)
                        if isinstance(est_info, dict):
                            if est_info.get('id_estudiante') == uid_estudiante:
                                proyectos.append(proyecto)
                                break
                        elif isinstance(est_info, str) and est_info == uid_estudiante:
                            proyectos.append(proyecto)
                            break

                # También verificar campo único por retrocompatibilidad
                elif 'id_estudiante' in proyecto:
                    est = proyecto['id_estudiante']
                    if isinstance(est, dict):
                        if est.get('id_estudiante') == uid_estudiante:
                            proyectos.append(proyecto)
                    elif est == uid_estudiante:
                        proyectos.append(proyecto)

            logger.info(f" {len(proyectos)} proyecto(s) encontrado(s) para estudiante {uid_estudiante}")
            return proyectos

        except Exception as e:
            logger.error(f" Error obteniendo proyectos del estudiante {uid_estudiante}: {str(e)}")
            raise DatabaseException(f"Error al obtener proyectos del estudiante: {str(e)}")

    async def get_by_event(self, id_evento: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los proyectos asociados a un evento específico.

        Args:
            id_evento: ID del evento

        Returns:
            Lista de proyectos del evento
        """
        try:
            proyectos = await self.get_all(filters={'id_evento': id_evento})

            logger.info(f" {len(proyectos)} proyecto(s) encontrado(s) para evento {id_evento}")
            return proyectos

        except Exception as e:
            logger.error(f" Error obteniendo proyectos del evento {id_evento}: {str(e)}")
            raise DatabaseException(f"Error al obtener proyectos del evento: {str(e)}")


# Alias retrocompatible
ProyectRepository = ProyectoRepository
__all__ = ["ProyectoRepository", "ProyectRepository"]
<<<<<<< HEAD
# app/repositories/proyect_repository.py

from typing import List, Optional, Dict, Any
import logging
from app.repositories.base_repository import BaseRepository
from app.core.firebase import Collections
=======
from app.repositories.base_repository import BaseRepository
from app.exceptions.base_exceptions import DatabaseException, NotFoundException
from app.services.cloudinary_service import upload_pdf_to_cloudinary
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
>>>>>>> origin/Miguel

logger = logging.getLogger(__name__)

<<<<<<< HEAD
class ProyectRepository(BaseRepository):
    """Repositorio para gestión de proyectos en Firestore"""
    
    def __init__(self):
        super().__init__(Collections.PROYECTOS, "id_proyecto")
    
    async def get_students_by_project(self, project_id: str) -> List[str]:
        """
        Obtiene IDs de estudiantes de un proyecto.
        Por ahora retorna datos mock para pruebas.
        """
        try:
            # En producción, esto consultaría la relación proyectos-estudiantes
            # Por ahora retornamos mock data para que funcione el certificado
            return ["estudiante1", "estudiante2", "estudiante3"]
        except Exception as e:
            logger.error(f"Error obteniendo estudiantes del proyecto {project_id}: {str(e)}")
            return []
    
    async def get_by_student(self, student_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene proyectos de un estudiante.
        Por ahora retorna datos mock para pruebas.
        """
        try:
            # Mock data - en producción esto consultaría Firestore
            return [
                {
                    "id_proyecto": "proyecto1",
                    "titulo_proyecto": "Sistema de Gestión Académica",
                    "tipo_actividad": "Exposición",
                    "id_evento": "evento1",
                    "calificacion": "4.5",
                    "fecha_exposicion": "2024-01-15",
                    "id_estudiante": student_id
                },
                {
                    "id_proyecto": "proyecto2", 
                    "titulo_proyecto": "Aplicación Móvil para Eventos",
                    "tipo_actividad": "Poster",
                    "id_evento": "evento1",
                    "calificacion": "4.8",
                    "fecha_exposicion": "2024-01-15",
                    "id_estudiante": student_id
                }
            ]
        except Exception as e:
            logger.error(f"Error obteniendo proyectos del estudiante {student_id}: {str(e)}")
            return []
=======
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

>>>>>>> origin/Miguel

# app/repositories/proyect_repository.py

from typing import List, Optional, Dict, Any
import logging
from app.repositories.base_repository import BaseRepository
from app.core.firebase import Collections

logger = logging.getLogger(__name__)

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
from typing import Optional, List, Dict, Any
import logging
from google.cloud.firestore import FieldFilter

from .base_repository import BaseRepository
from app.core.firebase import Collections

logger = logging.getLogger(__name__)


class GroupRepository(BaseRepository):
    
    def __init__(self):
        super().__init__(Collections.GRUPOS, "codigo_grupo")

    async def get_all(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        try:
            collection_ref = self.db.collection(self.collection_name)
            
            # Aplicar filtros si existen
            if filters:
                query = collection_ref
                for field, value in filters.items():
                    query = query.where(filter=FieldFilter(field, "==", value))
                docs = query.stream()
            else:
                docs = collection_ref.stream()
            
            result = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                # Asegurar que codigo_grupo sea int
                if "codigo_grupo" in data and isinstance(data["codigo_grupo"], str):
                    try:
                        data["codigo_grupo"] = int(data["codigo_grupo"])
                    except ValueError:
                        pass
                result.append(data)
            
            logger.info(f"Grupos recuperados: {len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"Error en get_all: {str(e)}")
            return []

    async def get_groups_by_subject(self, subject_code: str) -> List[Dict[str, Any]]:
        return await self.get_all(filters={"codigo_materia": subject_code})

    async def get_group_with_details(self, group_code: int) -> Optional[Dict[str, Any]]:
        try:
            group = await self.get_by_id(str(group_code))
            if not group:
                return None

            # Asegurar que codigo_grupo sea int
            if "codigo_grupo" in group and isinstance(group["codigo_grupo"], str):
                group["codigo_grupo"] = int(group["codigo_grupo"])

            # Obtener información de la materia
            from app.repositories.subject_repository import SubjectRepository
            subject_repo = SubjectRepository()
            subject_info = await subject_repo.get_by_id(group.get("codigo_materia", ""))

            # Obtener docentes asignados desde TeacherSubject
            from app.repositories.teacher_subject_repository import TeacherSubjectRepository
            ts_repo = TeacherSubjectRepository()
            assignments = await ts_repo.get_assignments_by_group(group_code)
            
            group["materia_info"] = subject_info
            group["nombre_materia"] = subject_info.get("nombre_materia") if subject_info else None
            group["docentes_asignados"] = assignments
            
            logger.info(f"Grupo {group_code} tiene {len(assignments)} asignaciones")
            return group
            
        except Exception as e:
            logger.error(f"Error en get_group_with_details: {str(e)}")
            return None
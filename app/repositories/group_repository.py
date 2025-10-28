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
        """Obtener todos los grupos con filtros opcionales"""
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
                # Mantener codigo_grupo como string (cambio aplicado)
                if "codigo_grupo" not in data:
                    data["codigo_grupo"] = doc.id
                result.append(data)
            
            logger.info(f"Grupos recuperados: {len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"Error en get_all: {str(e)}")
            return []

    async def get_groups_by_subject(self, subject_code: str) -> List[Dict[str, Any]]:
        """Obtener grupos por materia"""
        return await self.get_all(filters={"codigo_materia": subject_code})

    async def get_groups_by_teacher(self, teacher_id: str) -> List[Dict[str, Any]]:
        """Obtener grupos por docente asignado"""
        return await self.get_all(filters={"id_docente": teacher_id})

    async def get_group_with_details(self, group_code: str) -> Optional[Dict[str, Any]]:
        """
        Obtener grupo con información detallada de materia y docente.
        """
        try:
            group = await self.get_by_id(group_code)
            if not group:
                return None

            # Asegurar que codigo_grupo esté presente
            if "codigo_grupo" not in group:
                group["codigo_grupo"] = group_code

            # Obtener información de la materia (si está asignada)
            subject_code = group.get("codigo_materia")
            if subject_code:
                from app.repositories.subject_repository import SubjectRepository
                subject_repo = SubjectRepository()
                subject_info = await subject_repo.get_by_id(subject_code)
                
                group["materia_info"] = subject_info
                group["nombre_materia"] = subject_info.get("nombre_materia") if subject_info else None
            else:
                group["materia_info"] = None
                group["nombre_materia"] = None

            # Obtener información del docente asignado
            teacher_id = group.get("id_docente")
            if teacher_id:
                from app.repositories.teacher_repository import TeacherRepository
                from app.repositories.user_repository import UserRepository
                
                teacher_repo = TeacherRepository()
                user_repo = UserRepository()
                
                teacher_info = await teacher_repo.get_by_id(teacher_id)
                
                if teacher_info:
                    user_id = teacher_info.get("id_usuario")
                    if user_id:
                        user_info = await user_repo.get_by_id(user_id)
                        if user_info:
                            group["docente_info"] = {
                                "id_docente": teacher_id,
                                "nombre_completo": f"{user_info.get('nombres', '')} {user_info.get('apellidos', '')}",
                                "correo": user_info.get("correo"),
                                "categoria": teacher_info.get("categoria_docente")
                            }
                        else:
                            group["docente_info"] = None
                    else:
                        group["docente_info"] = None
                else:
                    group["docente_info"] = None
            else:
                group["docente_info"] = None
            
            logger.info(f"Grupo {group_code} obtenido con detalles completos")
            return group
            
        except Exception as e:
            logger.error(f"Error en get_group_with_details: {str(e)}")
            return None

    async def get_groups_without_subject(self) -> List[Dict[str, Any]]:
        """Obtener grupos que no tienen materia asignada"""
        try:
            collection_ref = self.db.collection(self.collection_name)
            
            # Buscar grupos donde codigo_materia no existe o es None
            query = collection_ref.where(
                filter=FieldFilter("codigo_materia", "==", None)
            )
            docs = query.stream()
            
            result = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                if "codigo_grupo" not in data:
                    data["codigo_grupo"] = doc.id
                result.append(data)
            
            logger.info(f"Grupos sin materia encontrados: {len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"Error obteniendo grupos sin materia: {str(e)}")
            return []

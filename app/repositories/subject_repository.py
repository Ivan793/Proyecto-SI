from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import logging
from google.cloud.firestore import FieldFilter

from .base_repository import BaseRepository
from app.core.firebase import Collections

logger = logging.getLogger(__name__)


class SubjectRepository(BaseRepository):
    
    def __init__(self):
        super().__init__(Collections.MATERIAS, "codigo_materia")

    async def get_subjects_by_cycle(self, cycle: str) -> List[Dict[str, Any]]:
        """Obtener materias por ciclo"""
        return await self.get_all(filters={"ciclo_semestral": cycle})

    async def get_active_subjects(self) -> List[Dict[str, Any]]:
        """Obtener solo materias activas"""
        return await self.get_all(filters={"activo": True})

    async def subject_has_groups(self, subject_code: str) -> bool:
        """Verificar si una materia tiene grupos asignados"""
        from app.repositories.group_repository import GroupRepository
        group_repo = GroupRepository()
        groups = await group_repo.get_groups_by_subject(subject_code)
        return len(groups) > 0

    async def get_subject_with_groups(self, subject_code: str) -> Optional[Dict[str, Any]]:
        """
        Obtener materia con sus grupos y docentes asignados.
        """
        subject = await self.get_by_id(subject_code)
        if not subject:
            return None

        from app.repositories.group_repository import GroupRepository
        group_repo = GroupRepository()
        
        # Obtener grupos de esta materia
        groups = await group_repo.get_groups_by_subject(subject_code)
        
        # Enriquecer cada grupo con información de docente
        enriched_groups = []
        for group in groups:
            group_code = group.get("codigo_grupo")
            if group_code:
                group_details = await group_repo.get_group_with_details(group_code)
                if group_details:
                    enriched_groups.append(group_details)

        subject["total_grupos"] = len(enriched_groups)
        
        # Obtener lista única de docentes asignados
        unique_teachers = set()
        for group in enriched_groups:
            teacher_id = group.get("id_docente")
            if teacher_id:
                unique_teachers.add(teacher_id)
        
        subject["total_docentes_asignados"] = len(unique_teachers)
        
        return subject

    async def count_groups_for_subject(self, subject_code: str) -> int:
        """Contar grupos asignados a una materia"""
        from app.repositories.group_repository import GroupRepository
        group_repo = GroupRepository()
        groups = await group_repo.get_groups_by_subject(subject_code)
        return len(groups)

    async def get_teachers_for_subject(self, subject_code: str) -> List[Dict[str, Any]]:
        """
        Obtener todos los docentes asignados a una materia.
        Consulta directamente desde los grupos.
        """
        try:
            from app.repositories.group_repository import GroupRepository
            from app.repositories.teacher_repository import TeacherRepository
            
            group_repo = GroupRepository()
            teacher_repo = TeacherRepository()
            
            # Obtener grupos de la materia
            groups = await group_repo.get_groups_by_subject(subject_code)
            
            # Extraer IDs únicos de docentes
            teacher_ids = set()
            for group in groups:
                teacher_id = group.get("id_docente")
                if teacher_id:
                    teacher_ids.add(teacher_id)
            
            # Obtener información completa de cada docente
            teachers = []
            for teacher_id in teacher_ids:
                teacher = await teacher_repo.get_by_id(teacher_id)
                if teacher:
                    # Agregar información de qué grupos tiene
                    teacher_groups = [
                        g.get("codigo_grupo") 
                        for g in groups 
                        if g.get("id_docente") == teacher_id
                    ]
                    teacher["grupos_asignados"] = teacher_groups
                    teachers.append(teacher)
            
            return teachers
            
        except Exception as e:
            logger.error(f"Error obteniendo docentes de materia {subject_code}: {str(e)}")
            return []

    # NUEVO MÉTODO: Actualizar la lista de grupos en la materia
    async def update_subject_groups(self, subject_code: str, group_codes: List[str]) -> bool:
        """Actualizar la lista de grupos asignados a una materia"""
        try:
            subject = await self.get_by_id(subject_code)
            if not subject:
                return False
            
            await self.update(subject_code, {
                "grupos_asignados": group_codes,
                "updated_at": datetime.now(timezone.utc)
            })
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando grupos de materia {subject_code}: {str(e)}")
            return False

    # NUEVO MÉTODO: Agregar un grupo a la lista de grupos de la materia
    async def add_group_to_subject_list(self, subject_code: str, group_code: str) -> bool:
        """Agregar un grupo a la lista de grupos de la materia"""
        try:
            subject = await self.get_by_id(subject_code)
            if not subject:
                return False
            
            grupos_actuales = subject.get("grupos_asignados", [])
            if group_code not in grupos_actuales:
                grupos_actuales.append(group_code)
                await self.update(subject_code, {
                    "grupos_asignados": grupos_actuales,
                    "updated_at": datetime.now(timezone.utc)
                })
            
            return True
            
        except Exception as e:
            logger.error(f"Error agregando grupo {group_code} a materia {subject_code}: {str(e)}")
            return False

    # NUEVO MÉTODO: Remover un grupo de la lista de grupos de la materia
    async def remove_group_from_subject_list(self, subject_code: str, group_code: str) -> bool:
        """Remover un grupo de la lista de grupos de la materia"""
        try:
            subject = await self.get_by_id(subject_code)
            if not subject:
                return False
            
            grupos_actuales = subject.get("grupos_asignados", [])
            if group_code in grupos_actuales:
                grupos_actuales.remove(group_code)
                await self.update(subject_code, {
                    "grupos_asignados": grupos_actuales,
                    "updated_at": datetime.now(timezone.utc)
                })
            
            return True
            
        except Exception as e:
            logger.error(f"Error removiendo grupo {group_code} de materia {subject_code}: {str(e)}")
            return False
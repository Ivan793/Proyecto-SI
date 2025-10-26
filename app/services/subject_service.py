import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

from app.repositories.subject_repository import SubjectRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.teacher_subject_repository import TeacherSubjectRepository
from app.repositories.teacher_repository import TeacherRepository
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse, SubjectSummary
from app.schemas.group import GroupCreate
from app.schemas.teacherSubject import TeacherSubjectCreate
from app.exceptions.subject_exceptions import (
    SubjectNotFoundException,
    SubjectAlreadyExistsException,
    SubjectHasDependenciesException,
    MinimumGroupsRequiredException
)
from app.exceptions.group_exceptions import GroupAlreadyExistsException
from app.exceptions.teacher_exceptions import TeacherNotFoundException
from app.exceptions.base_exceptions import DatabaseException, ValidationException

logger = logging.getLogger(__name__)


class SubjectService:
    
    def __init__(self):
        self.subject_repo = SubjectRepository()
        self.group_repo = GroupRepository()
        self.teacher_subject_repo = TeacherSubjectRepository()
        self.teacher_repo = TeacherRepository()

    async def _validate_teacher_exists_and_active(self, teacher_id: str) -> None:
        """Valida que un docente exista y esté activo"""
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise TeacherNotFoundException(teacher_id)
        
        if not teacher.get("activo", True):
            raise ValidationException(
                message=f"El docente {teacher_id} no está activo",
                field="id_docente",
                details={
                    "teacher_id": teacher_id,
                    "teacher_status": "inactive"
                }
            )
        
    

    async def create_subject_with_groups_and_teachers(
        self,
        subject_data: SubjectCreate,
        groups_with_teachers: List[Dict],
        created_by: str
    ) -> SubjectResponse:
        """
        Crea una materia con sus grupos y asignaciones de docentes.
        """
        
        # Fase 1: Validar todos los requisitos antes de escribir
        await self._validate_all_prerequisites(
            subject_data=subject_data,
            groups_with_teachers=groups_with_teachers
        )

        # Fase 2: Crear entidades con tracking para rollback
        completed_operations = []
        
        try:
            # Crear la materia
            subject_dict = subject_data.model_dump()
            subject_dict.update({
                "created_at": datetime.utcnow(),
                "created_by": created_by,
                "activo": True
            })
            
            await self.subject_repo.create(
                subject_dict,
                subject_data.codigo_materia
            )
            completed_operations.append(
                ("subject", subject_data.codigo_materia)
            )

            # Crear grupos y asignaciones
            for group_data in groups_with_teachers:
                # Crear grupo
                group_dict = {
                    "codigo_grupo": group_data["codigo_grupo"],
                    "codigo_materia": subject_data.codigo_materia,
                    "id_docente": group_data["id_docente"],
                    "created_at": datetime.utcnow(),
                    "created_by": created_by,
                    "activo": True
                }
                
                await self.group_repo.create(group_dict,
                    str(group_data["codigo_grupo"]),
                    
                )
                completed_operations.append(
                    ("group", str(group_data["codigo_grupo"]))
                )

                # Crear asignación TeacherSubject
                assignment_id = (
                    f"{subject_data.codigo_materia}_"
                    f"{group_data['codigo_grupo']}"
                )
                assignment_dict = {
                    "id_docente_materia": assignment_id,
                    "id_docente": group_data["id_docente"],
                    "codigo_materia": subject_data.codigo_materia,
                    "codigo_grupo": group_data["codigo_grupo"],
                    "created_at": datetime.utcnow(),
                    "created_by": created_by,
                    "activo": True
                }
                
                await self.teacher_subject_repo.create(
                    assignment_dict,
                    assignment_id  
                )
                completed_operations.append(
                    ("assignment", assignment_id)
                )

            # Operación exitosa: retornar materia creada
            created_subject = await self.subject_repo.get_by_id(
                subject_data.codigo_materia
            )
            return SubjectResponse(**created_subject)

        except Exception as e:
            # Hacer rollback de todas las operaciones completadas
            await self._rollback_creation(completed_operations)
            
            # Re-lanzar excepción original o convertir a DatabaseException
            if isinstance(e, (
                SubjectAlreadyExistsException,
                GroupAlreadyExistsException,
                TeacherNotFoundException,
                ValidationException
            )):
                raise
            
            raise DatabaseException(
                message=f"Error al crear materia: {str(e)}",
                details={"subject_code": subject_data.codigo_materia}
            )
        
    async def _validate_all_prerequisites(
        self,
        subject_data: SubjectCreate,
        groups_with_teachers: List[Dict]
    ):
        """
        Valida todos los requisitos antes de escribir en Firestore.
        """
        
        # Validar que la materia NO exista
        existing_subject = await self.subject_repo.get_by_id(
            subject_data.codigo_materia
        )
        if existing_subject:
            raise SubjectAlreadyExistsException(subject_data.codigo_materia)

        # Validar mínimo de grupos
        if not groups_with_teachers or len(groups_with_teachers) == 0:
            raise MinimumGroupsRequiredException()

        # Extraer IDs únicos
        group_codes = [g["codigo_grupo"] for g in groups_with_teachers]
        teacher_ids = list(set(g["id_docente"] for g in groups_with_teachers))

        # Validar grupos únicos en la solicitud
        if len(group_codes) != len(set(group_codes)):
            duplicates = [
                code for code in group_codes 
                if group_codes.count(code) > 1
            ]
            raise ValidationException(
                message=f"Grupos duplicados en la solicitud: {duplicates[0]}",
                field="grupos_con_docentes"
            )

        # Validar grupos y docentes en paralelo (optimización)
        await asyncio.gather(
            self._validate_groups_availability(group_codes),
            self._validate_teachers_exist_and_active(teacher_ids)
        )
        
    async def _validate_groups_availability(
        self,
        group_codes: List[int]
    ):
        """
        Valida que ningún grupo exista ya en Firestore.
        """
        
        # Buscar todos los grupos en paralelo
        check_tasks = [
            self.group_repo.get_by_id(str(code)) 
            for code in group_codes
        ]
        existing_groups = await asyncio.gather(*check_tasks)

        # Identificar grupos que ya existen
        conflicts = [
            group_codes[i] 
            for i, group in enumerate(existing_groups) 
            if group is not None
        ]

        if conflicts:
            raise GroupAlreadyExistsException(conflicts[0])
    
    async def _validate_teachers_exist_and_active(
        self,
        teacher_ids: List[str]
    ):
        """
        Valida que todos los docentes existan y estén activos.
        """
        
        # Buscar todos los docentes en paralelo
        check_tasks = [
            self.teacher_repo.get_by_id(teacher_id)
            for teacher_id in teacher_ids
        ]
        teachers = await asyncio.gather(*check_tasks)

        # Validar existencia y estado
        for i, teacher in enumerate(teachers):
            teacher_id = teacher_ids[i]
            
            if teacher is None or not teacher.get("activo", False):
                raise TeacherNotFoundException(teacher_id)

    async def _rollback_creation(
        self,
        completed_operations: List[tuple]
    ):
        """
        Elimina documentos creados durante operación fallida.
        """
        
        for entity_type, entity_id in reversed(completed_operations):
            try:
                if entity_type == "subject":
                    await self.subject_repo.delete(entity_id)
                elif entity_type == "group":
                    await self.group_repo.delete(entity_id)
                elif entity_type == "assignment":
                    await self.teacher_subject_repo.delete(entity_id)
            except Exception:
                # Ignorar errores durante rollback
                # El documento puede no existir o ya haber sido eliminado
                pass
    
    async def get_subject(self, subject_code: str) -> SubjectResponse:
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)
        return SubjectResponse(**subject)

    async def get_subject_with_groups(self, subject_code: str) -> Dict[str, Any]:
        subject_with_groups = await self.subject_repo.get_subject_with_groups(subject_code)
        if not subject_with_groups:
            raise SubjectNotFoundException(subject_code)
        
        # Obtener información de docentes asignados desde TeacherSubject
        assignments = await self.teacher_subject_repo.get_assignments_by_subject(subject_code)
        subject_with_groups["asignaciones_docentes"] = assignments
        
        return subject_with_groups

    async def get_all_subjects(
        self, 
        active_only: bool = True,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[SubjectSummary], int]:
        filters = {"activo": True} if active_only else {}
        subjects = await self.subject_repo.get_all(filters=filters)
        
        total = len(subjects)
        start = (page - 1) * limit
        end = start + limit
        paginated_subjects = subjects[start:end]
        
        return [SubjectSummary(**subject) for subject in paginated_subjects], total

    async def update_subject(
        self, 
        subject_code: str, 
        subject_data: SubjectUpdate
    ) -> SubjectResponse:
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)

        # Si se cambia el código de la materia, actualizar todas las referencias
        if hasattr(subject_data, 'codigo_materia') and subject_data.codigo_materia:
            new_subject_code = subject_data.codigo_materia
            
            # Actualizar grupos que referencian esta materia
            groups = await self.group_repo.get_groups_by_subject(subject_code)
            for group in groups:
                await self.group_repo.update(
                    str(group["codigo_grupo"]),
                    {"codigo_materia": new_subject_code}
                )
            
            # Actualizar asignaciones TeacherSubject
            assignments = await self.teacher_subject_repo.get_assignments_by_subject(subject_code)
            active_assignments = [a for a in assignments if a.get("activo", True)]
            
            if active_assignments:
                logger.warning(
                    f"Materia {subject_code} tiene {len(active_assignments)} asignaciones activas "
                    f"que se actualizarán al nuevo código {new_subject_code}"
                )
                
                for assignment in active_assignments:
                    await self.teacher_subject_repo.update(
                        assignment["id_docente_materia"],
                        {"codigo_materia": new_subject_code}
                    )

        update_dict = subject_data.model_dump(exclude_none=True)
        if update_dict:
            await self.subject_repo.update(subject_code, update_dict)

        updated_subject = await self.subject_repo.get_by_id(subject_code)
        return SubjectResponse(**updated_subject)

    async def deactivate_subject(self, subject_code: str, reason: str) -> bool:
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)

        # Verificar si la materia tiene grupos activos
        if await self.subject_repo.subject_has_groups(subject_code):
            raise SubjectHasDependenciesException(
                subject_code,
                dependencies={"grupos_activos": True}
            )

        return await self.subject_repo.update(subject_code, {
            "activo": False,
            "razon_desactivacion": reason
        })
    
    async def activate_subject(self, subject_code: str) -> bool:
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)

        return await self.subject_repo.update(subject_code, {"activo": True})

    async def add_group_to_subject(
        self, 
        subject_code: str, 
        group_data: GroupCreate,
        teacher_id: str,
        created_by: str
    ) -> bool:
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)

        # Validar que el docente existe y está activo
        await self._validate_teacher_exists_and_active(teacher_id)

        # Verificar si el grupo ya existe
        existing_group = await self.group_repo.get_by_id(str(group_data.codigo_grupo))
        if existing_group:
            raise GroupAlreadyExistsException(group_data.codigo_grupo)

        # Crear el grupo (sin docente)
        group_dict = group_data.model_dump()
        group_dict.update({
            "codigo_materia": subject_code,
            "activo": True,
            "created_by": created_by
        })
        
        await self.group_repo.create(group_dict, str(group_data.codigo_grupo))
        
        # Crear asignación en TeacherSubject
        teacher_subject_data = TeacherSubjectCreate(
            id_docente=teacher_id,
            codigo_materia=subject_code,
            codigo_grupo=group_data.codigo_grupo
        )
        
        teacher_subject_dict = teacher_subject_data.model_dump()
        teacher_subject_dict.update({
            "activo": True,
            "created_by": created_by
        })
        
        await self.teacher_subject_repo.create(teacher_subject_dict)
        
        return True

    async def get_subject_assignments(self, subject_code: str) -> List[Dict[str, Any]]:
        """Obtiene todas las asignaciones de docentes para una materia"""
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)
            
        assignments = await self.teacher_subject_repo.get_assignments_by_subject(subject_code)
        return assignments
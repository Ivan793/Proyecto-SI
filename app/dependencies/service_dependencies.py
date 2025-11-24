from app.repositories.group_repository import GroupRepository
from app.repositories.proyect_repository import ProyectoRepository
from app.repositories.teacher_repository import TeacherRepository
from app.services.teacher_service import TeacherService
from functools import lru_cache
from fastapi import Depends


from app.repositories.student_repository import StudentRepository
from app.repositories.user_repository import UserRepository
from app.repositories.academic_repository import ProgramRepository
from app.services.auth_service import AuthService
from app.validators.student_validators import StudentValidators
from app.validators.teacher_validators import TeacherValidators
from app.validators.user_validators import UserValidators
from app.services.student_service import StudentService

# ==================== REPOSITORIOS (SINGLETONS) ====================
@lru_cache()
def get_group_repository() -> GroupRepository:
    """Singleton del repositorio de grupos"""
    return GroupRepository()

@lru_cache()
def get_proyecto_repository() -> ProyectoRepository:
    """Singleton del repositorio de proyectos"""
    return ProyectoRepository()
from app.services.teacher_service import TeacherService
from functools import lru_cache
from fastapi import Depends

@lru_cache()
def get_student_repository() -> StudentRepository:
    """Singleton del repositorio de estudiantes"""
    return StudentRepository()


@lru_cache()
def get_user_repository() -> UserRepository:
    """Singleton del repositorio de usuarios"""
    return UserRepository()


@lru_cache()
def get_program_repository() -> ProgramRepository:
    """Singleton del repositorio de programas"""
    return ProgramRepository()


@lru_cache()
def get_auth_service() -> AuthService:
    """Singleton del servicio de autenticación"""
    return AuthService()


# ==================== VALIDADORES (CON REPOS INYECTADOS) ====================

def get_student_validators(
    program_repo: ProgramRepository = Depends(get_program_repository)
) -> StudentValidators:
    """Crea validadores de estudiante con repositorio inyectado"""
    return StudentValidators(program_repo)


def get_user_validators(
    user_repo: UserRepository = Depends(get_user_repository)
) -> UserValidators:
    """Crea validadores de usuario con repositorio inyectado"""
    return UserValidators(user_repo)


# ==================== SERVICIO DE ESTUDIANTES ====================

def get_student_service(
    student_repo: StudentRepository = Depends(get_student_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    program_repo: ProgramRepository = Depends(get_program_repository),
    auth_service: AuthService = Depends(get_auth_service),
    student_validators: StudentValidators = Depends(get_student_validators),
    user_validators: UserValidators = Depends(get_user_validators)
) -> StudentService:
    """
    Factory del servicio de estudiantes con todas las dependencias inyectadas.
    
    Returns:
        StudentService completamente configurado y listo para usar
    """
    return StudentService(
        student_repo=student_repo,
        user_repo=user_repo,
        program_repo=program_repo,
        auth_service=auth_service,
        student_validators=student_validators,
        user_validators=user_validators
    )


@lru_cache()
def get_teacher_repository() -> TeacherRepository:
    """Singleton del repositorio de docentes"""
    return TeacherRepository()

def get_teacher_validators(
    program_repo: ProgramRepository = Depends(get_program_repository)
) -> TeacherValidators:
    """Crea validadores de docente con repositorio inyectado"""
    return TeacherValidators(program_repo)

def get_teacher_service(
    teacher_repo: TeacherRepository = Depends(get_teacher_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    program_repo: ProgramRepository = Depends(get_program_repository),
    auth_service: AuthService = Depends(get_auth_service),
    teacher_validators: TeacherValidators = Depends(get_teacher_validators),
    user_validators: UserValidators = Depends(get_user_validators),
    group_repo: GroupRepository = Depends(get_group_repository),
    project_repo: ProyectoRepository = Depends(get_proyecto_repository)
    
) -> TeacherService:
    """
    Factory del servicio de docentes con todas las dependencias inyectadas.
    """
    return TeacherService(
        teacher_repo=teacher_repo,
        user_repo=user_repo,
        program_repo=program_repo,
        auth_service=auth_service,
        teacher_validators=teacher_validators,
        user_validators=user_validators,
        group_repo=group_repo,
        project_repo=project_repo
    )

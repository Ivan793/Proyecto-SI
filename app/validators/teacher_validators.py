import logging
from app.exceptions.base_exceptions import ValidationException
from app.repositories.academic_repository import ProgramRepository

logger = logging.getLogger(__name__)

class TeacherValidators:
    """Validadores específicos del dominio de docentes."""

    def __init__(self, program_repo: ProgramRepository = None):
        self.program_repo = program_repo or ProgramRepository()

    async def validate_program_existence(self, codigo_programa: str) -> None:
        """
        Valida que el programa académico exista en cualquier facultad.
        Los programas están guardados en subcolecciones bajo cada facultad.
        """
        try:
            faculties = self.program_repo.db.collection("facultades").stream()

            for faculty in faculties:
                faculty_id = faculty.id
                program = await self.program_repo.get_by_id(faculty_id, codigo_programa)
                if program:
                    logger.info(
                        f"Programa validado para docente: {codigo_programa} en facultad {faculty_id}"
                    )
                    return

            raise ValidationException(
                message=f"El programa con código '{codigo_programa}' no existe en ninguna facultad.",
                field="codigo_programa"
            )

        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Error validando programa {codigo_programa}: {str(e)}")
            raise ValidationException(
                message="Error al verificar el programa académico del docente",
                field="codigo_programa"
            )

    async def validate_all_teacher_fields(self, teacher_data) -> None:
        """
        Ejecuta las validaciones específicas del rol docente.
        Actualmente valida que el programa exista.
        """
        await self.validate_program_existence(teacher_data.codigo_programa)
        logger.info("Validaciones específicas del docente completadas correctamente.")
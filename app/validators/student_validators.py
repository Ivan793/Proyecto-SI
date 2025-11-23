import logging
from datetime import datetime

from app.exceptions.base_exceptions import ValidationException
from app.repositories.academic_repository import ProgramRepository

logger = logging.getLogger(__name__)


class StudentValidators:
    """Validadores específicos del dominio de estudiantes"""
    
    def __init__(self, program_repo: ProgramRepository = None):
        self.program_repo = program_repo or ProgramRepository()
    
    async def validate_program_existence(self, codigo_programa: str) -> None:
        """
        Valida que el programa académico exista en cualquier facultad.
        IMPORTANTE: Los programas están en subcolecciones de facultades,
        por lo que debemos buscar en todas las facultades.
        """
        try:
            # Obtener todas las facultades
            faculties = self.program_repo.db.collection("facultades").stream()
            
            # Buscar el programa en cada facultad
            for faculty in faculties:
                faculty_id = faculty.id
                program = await self.program_repo.get_by_id(faculty_id, codigo_programa)
                
                if program:
                    logger.info(f"Programa académico validado: {codigo_programa} en facultad {faculty_id}")
                    return  # Programa encontrado
            
            # Si llegamos aquí, el programa no existe
            raise ValidationException(
                message=f"El programa académico con código '{codigo_programa}' no existe",
                field="codigo_programa"
            )
            
        except ValidationException:
            # Re-lanzar ValidationException sin modificar
            raise
        except Exception as e:
            logger.error(f"Error validando existencia del programa {codigo_programa}: {str(e)}")
            raise ValidationException(
                message="No se pudo verificar la existencia del programa académico",
                field="codigo_programa"
            )
    
    async def validate_semester_range(self, semestre: int) -> None:
        """
        Valida que el semestre esté en un rango válido (1-20)
        """
        if semestre < 1 or semestre > 20:
            raise ValidationException(
                message="El semestre debe estar entre 1 y 20",
                field="semestre"
            )
        logger.debug(f"Semestre validado: {semestre}")
    
    async def validate_admission_year(self, anio_ingreso: int) -> None:
        """
        Valida que el año de ingreso sea razonable
        """
        current_year = datetime.now().year
        
        if anio_ingreso < 2000:
            raise ValidationException(
                message="El año de ingreso no puede ser anterior a 2000",
                field="anio_ingreso"
            )
        
        if anio_ingreso > current_year + 1:
            raise ValidationException(
                message=f"El año de ingreso no puede ser posterior a {current_year + 1}",
                field="anio_ingreso"
            )
        
        logger.debug(f"Año de ingreso validado: {anio_ingreso}")
    
    async def validate_periodo(self, periodo: int) -> None:
        """
        Valida que el periodo sea válido (1 o 2)
        """
        if periodo not in [1, 2]:
            raise ValidationException(
                message="El periodo debe ser 1 o 2",
                field="periodo"
            )
        logger.debug(f"Periodo validado: {periodo}")

    async def validate_all_student_fields(self, student_data) -> None:
        """
        Ejecuta todas las validaciones de estudiante en orden lógico.
        """
        await self.validate_program_existence(student_data.codigo_programa)
        await self.validate_semester_range(student_data.semestre)
        await self.validate_admission_year(student_data.anio_ingreso)
        await self.validate_periodo(student_data.periodo)
        logger.info("Todas las validaciones específicas del estudiante completadas correctamente.")
import logging
from datetime import datetime
from typing import Optional

from app.exceptions.base_exceptions import ValidationException
from app.repositories.academic_repository import ProgramRepository

logger = logging.getLogger(__name__)


class StudentValidators:
    """
    Validadores específicos del dominio de estudiantes.
    
    Args:
        program_repo: Repositorio de programas académicos (inyectado)
    """
    
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
        Valida que el semestre esté en un rango válido (1-20).
        
        Args:
            semestre: Semestre a validar
        
        Raises:
            ValidationException: Si el semestre está fuera de rango
        """
        if semestre < 1 or semestre > 20:
            raise ValidationException(
                message="El semestre debe estar entre 1 y 20",
                field="semestre"
            )
        logger.debug(f"Semestre validado: {semestre}")
    
    async def validate_admission_year(self, anio_ingreso: int) -> None:
        """
        Valida que el año de ingreso sea razonable.
        
        Args:
            anio_ingreso: Año de ingreso a validar
        
        Raises:
            ValidationException: Si el año de ingreso no es válido
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
        Valida que el periodo sea válido (1 o 2).
        
        Args:
            periodo: Periodo a validar
        
        Raises:
            ValidationException: Si el periodo no es 1 o 2
        """
        if periodo not in [1, 2]:
            raise ValidationException(
                message="El periodo debe ser 1 o 2",
                field="periodo"
            )
        logger.debug(f"Periodo validado: {periodo}")

    async def validate_semester_year_coherence(
    self, 
    semestre: int, 
    anio_ingreso: int, 
    periodo: int,
    codigo_programa: Optional[str] = None
    ) -> None:
        """
        Valida coherencia entre semestre, año de ingreso y periodo.
        
        Lógica: 
        - Máximo semestre razonable basado en años transcurridos
        - Considerar programas de 4-5 años (8-10 semestres)
        - Validar contra duración real del programa si está disponible
        
        Args:
            semestre: Semestre actual
            anio_ingreso: Año de ingreso
            periodo: Periodo de ingreso (1, 2)
            codigo_programa: Código del programa para validación específica
        
        Raises:
            ValidationException: Si hay incoherencia temporal
        """
        current_year = datetime.now().year
        current_period = 1 if datetime.now().month <= 6 else 2
        
        # Calcular períodos académicos transcurridos
        years_diff = current_year - anio_ingreso
        periods_diff = (years_diff * 2) + (current_period - periodo)
        
        # El semestre no puede ser mayor a los períodos + margen (repeticiones)
        max_reasonable_semester = periods_diff + 2  # Margen para repeticiones
        
        if semestre > max_reasonable_semester:
            raise ValidationException(
                message=(
                    f"El semestre {semestre} no es coherente con el año de ingreso "
                    f"{anio_ingreso}-{periodo}. Máximo razonable: {max_reasonable_semester}"
                ),
                field="semestre",
                details={
                    "semestre_actual": semestre,
                    "anio_ingreso": anio_ingreso,
                    "periodo_ingreso": periodo,
                    "maximo_razonable": max_reasonable_semester
                }
            )

    async def validate_all_student_fields(self, student_data) -> None:
        """
        Ejecuta todas las validaciones de estudiante en orden lógico.
        
        Args:
            student_data: Datos del estudiante a validar
        
        Raises:
            ValidationException: Si alguna validación falla
        """
        await self.validate_program_existence(student_data.codigo_programa)
        # Validaciones individuales
        await self.validate_semester_range(student_data.semestre)
        await self.validate_admission_year(student_data.anio_ingreso)
        await self.validate_periodo(student_data.periodo)
        # Validación cruzada
        await self.validate_semester_year_coherence(
            student_data.semestre,
            student_data.anio_ingreso,
            student_data.periodo,
            student_data.codigo_programa
        )
        
        logger.info("Todas las validaciones específicas del estudiante completadas correctamente.")
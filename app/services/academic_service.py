from typing import List
import logging

from app.repositories.academic_repository import FacultyRepository, ProgramRepository
from app.repositories.subject_repository import SubjectRepository
from app.exceptions.academic_exceptions import (
    FacultyNotFoundException, FacultyAlreadyExistsException,
    ProgramNotFoundException, ProgramAlreadyExistsException,
    InvalidFacultyException
)
from app.exceptions.subject_exceptions import SubjectAlreadyExistsException, SubjectNotFoundException
from app.schemas.faculty import (
    FacultyCreate, FacultyResponse, FacultyUpdate, FacultyWithPrograms
)
from app.schemas.program import (
    ProgramCreate, ProgramResponse, ProgramUpdate, ProgramWithSubjects
)
from app.schemas.subject import SubjectSummary

logger = logging.getLogger(__name__)

# ==================== SERVICIO DE FACULTADES ====================

class FacultyService:
    
    def __init__(self):
        self.faculty_repo = FacultyRepository()
    
    async def create_faculty(self, faculty_data: FacultyCreate) -> FacultyResponse:
        """Crea una facultad"""
        if await self.faculty_repo.faculty_exists(faculty_data.id_facultad):
            raise FacultyAlreadyExistsException(faculty_data.id_facultad)
        
        data = faculty_data.model_dump()
        await self.faculty_repo.create_faculty(faculty_data.id_facultad, data)
        
        created_faculty = await self.faculty_repo.get_by_code(faculty_data.id_facultad)
        return FacultyResponse(**created_faculty)
    
    async def get_faculty(self, faculty_id: str) -> FacultyResponse:
        """Obtiene una facultad por código"""
        faculty = await self.faculty_repo.get_by_code(faculty_id)
        if not faculty:
            raise FacultyNotFoundException(faculty_id)
        return FacultyResponse(**faculty)
    
    async def get_all_faculties(self) -> List[FacultyResponse]:
        """Obtiene todas las facultades"""
        faculties = await self.faculty_repo.get_all()
        return [FacultyResponse(**faculty) for faculty in faculties]
    
    async def update_faculty(self, faculty_id: str, 
                            faculty_data: FacultyUpdate) -> FacultyResponse:
        """Actualiza una facultad"""
        if not await self.faculty_repo.faculty_exists(faculty_id):
            raise FacultyNotFoundException(faculty_id)
        
        update_dict = faculty_data.model_dump(exclude_none=True)
        if update_dict:
            await self.faculty_repo.update(faculty_id, update_dict)
        
        updated_faculty = await self.faculty_repo.get_by_code(faculty_id)
        return FacultyResponse(**updated_faculty)

# ==================== SERVICIO DE PROGRAMAS ====================

class ProgramService:
    
    def __init__(self):
        self.program_repo = ProgramRepository()
        self.faculty_repo = FacultyRepository()
        self.subject_repo = SubjectRepository()
    
    async def create_program(self, program_data: ProgramCreate) -> ProgramResponse:
        """Crea un programa dentro de una facultad (subcollection)"""
        faculty_id = program_data.id_facultad
        
        # Validar que la facultad existe
        if not await self.faculty_repo.faculty_exists(faculty_id):
            raise InvalidFacultyException(faculty_id)
        
        # Verificar que no exista el programa en esta facultad
        existing_program = await self.program_repo.get_by_id(
            faculty_id, 
            program_data.codigo_programa
        )
        if existing_program:
            raise ProgramAlreadyExistsException(program_data.codigo_programa)
        
        # Verificar nombre duplicado
        if await self.program_repo.program_name_exists(
            faculty_id,
            program_data.nombre_programa
        ):
            raise ProgramAlreadyExistsException(
                f"Ya existe un programa con el nombre '{program_data.nombre_programa}'"
            )
        
        data = program_data.model_dump()
        
        # Crear programa en subcollection
        await self.program_repo.create_program(
            faculty_id, 
            program_data.codigo_programa, 
            data
        )
        
        # Obtener programa creado
        created_program = await self.program_repo.get_by_id(
            faculty_id, 
            program_data.codigo_programa
        )
        return ProgramResponse(**created_program)
    
    async def add_subject_to_program(self, faculty_id: str, program_code: str, 
        subject_code: str) -> ProgramResponse:
        """Agrega una materia existente a un programa"""
        # Validar que la facultad y programa existen
        program = await self.program_repo.get_by_id(faculty_id, program_code)
        if not program:
            raise ProgramNotFoundException(program_code)
        
        # Validar que la materia existe
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)
        
        # Verificar que la materia no esté ya en el programa
        materias = program.get('materias', [])
        if subject_code in materias:
            raise SubjectAlreadyExistsException(
                f"La materia '{subject_code}' ya está en el programa"
            )
        
        # Agregar materia al programa
        await self.program_repo.add_subject_to_program(faculty_id, program_code, subject_code)
        
        # Obtener programa actualizado
        updated_program = await self.program_repo.get_by_id(faculty_id, program_code)
        return ProgramResponse(**updated_program)
    
    async def remove_subject_from_program(self, faculty_id: str, program_code: str, 
        subject_code: str) -> ProgramResponse:
        """Remueve una materia de un programa"""
        # Validar que la facultad y programa existen
        program = await self.program_repo.get_by_id(faculty_id, program_code)
        if not program:
            raise ProgramNotFoundException(program_code)
        
        # Verificar que la materia esté en el programa
        materias = program.get('materias', [])
        if subject_code not in materias:
            raise SubjectNotFoundException(subject_code)
        
        # Remover materia del programa
        await self.program_repo.remove_subject_from_program(faculty_id, program_code, subject_code)
        
        # Obtener programa actualizado
        updated_program = await self.program_repo.get_by_id(faculty_id, program_code)
        return ProgramResponse(**updated_program)
    
    async def get_program(self, faculty_id: str, program_code: str) -> ProgramResponse:
        """Obtiene un programa específico"""
        program = await self.program_repo.get_by_id(faculty_id, program_code)
        if not program:
            raise ProgramNotFoundException(program_code)
        return ProgramResponse(**program)
    
    async def get_program_subjects(self, faculty_id: str, program_code: str) -> List[SubjectSummary]:
        """Obtiene todas las materias de un programa con detalles completos"""
        # Validar que el programa existe
        program = await self.program_repo.get_by_id(faculty_id, program_code)
        if not program:
            raise ProgramNotFoundException(program_code)
        
        # Obtener códigos de materias del programa
        subject_codes = program.get('materias', [])
        
        # Obtener detalles de cada materia
        subjects = []
        for subject_code in subject_codes:
            try:
                subject = await self.subject_repo.get_by_id(subject_code)
                if subject and subject.get('activo', True):
                    subjects.append(SubjectSummary(**subject))
            except Exception as e:
                logger.warning(f"Materia {subject_code} no encontrada: {str(e)}")
                continue
        
        return subjects
    
    async def get_programs_by_faculty(self, faculty_id: str) -> List[ProgramResponse]:
        """Obtiene todos los programas de una facultad"""
        programs = await self.program_repo.get_by_faculty(faculty_id)
        return [ProgramResponse(**program) for program in programs]
    
    async def update_program(self, faculty_id: str, program_code: str, 
                            program_data: ProgramUpdate) -> ProgramResponse:
        """Actualiza un programa"""
        program = await self.program_repo.get_by_id(faculty_id, program_code)
        if not program:
            raise ProgramNotFoundException(program_code)
        
        update_dict = program_data.model_dump(exclude_none=True)
        
        # Verificar nombre duplicado si se cambia
        if "nombre_programa" in update_dict:
            if await self.program_repo.program_name_exists(
                faculty_id,
                update_dict["nombre_programa"],
                exclude_code=program_code
            ):
                raise ProgramAlreadyExistsException(update_dict["nombre_programa"])
        
        if update_dict:
            await self.program_repo.update_program(faculty_id, program_code, update_dict)
        
        updated_program = await self.program_repo.get_by_id(faculty_id, program_code)
        return ProgramResponse(**updated_program)

# ==================== SERVICIO COMBINADO ====================

class AcademicService:
    """Servicio que combina facultades y programas para consultas jerárquicas"""
    
    def __init__(self):
        self.faculty_repo = FacultyRepository()
        self.program_repo = ProgramRepository()
        self.subject_repo = SubjectRepository()
    
    async def get_complete_academic_tree(self) -> List[FacultyWithPrograms]:
        """
        Obtiene el árbol completo académico:
        Facultades -> Programas -> Materias
        """
        try:
            faculties_data = await self.faculty_repo.get_all_faculties_with_programs()
            
            result = []
            for faculty_data in faculties_data:
                # Enriquecer cada programa con sus materias completas
                programs = faculty_data.get('programas', [])
                enriched_programs = []
                
                for program in programs:
                    subject_codes = program.get('materias', [])
                    
                    # Obtener detalles de cada materia
                    subjects = []
                    for subject_code in subject_codes:
                        try:
                            subject = await self.subject_repo.get_by_id(subject_code)
                            if subject:
                                subjects.append(SubjectSummary(**subject))
                        except Exception as e:
                            logger.warning(f"Materia {subject_code} no encontrada: {str(e)}")
                            continue
                    
                    program['materias'] = [s.model_dump() for s in subjects]
                    enriched_programs.append(ProgramWithSubjects(**program))
                
                faculty_data['programas'] = [p.model_dump() for p in enriched_programs]
                result.append(FacultyWithPrograms(**faculty_data))
            
            return result
            
        except Exception as e:
            logger.error(f"Error obteniendo árbol académico: {str(e)}")
            raise
    
    async def get_faculty_with_details(self, faculty_id: str) -> FacultyWithPrograms:
        """Obtiene una facultad con sus programas y materias"""
        faculty_data = await self.faculty_repo.get_faculty_with_programs(faculty_id)
        
        if not faculty_data:
            raise FacultyNotFoundException(faculty_id)
        
        # Enriquecer programas con materias
        programs = faculty_data.get('programas', [])
        enriched_programs = []
        
        for program in programs:
            program_code = program.get('codigo_programa')
            subject_codes = program.get('materias', [])
            
            subjects = []
            for subject_code in subject_codes:
                try:
                    subject = await self.subject_repo.get_by_id(subject_code)
                    if subject and subject.get('activo', True):
                        subjects.append(SubjectSummary(**subject))
                except Exception:
                    continue
            
            program['materias'] = [s.model_dump() for s in subjects]
            enriched_programs.append(ProgramWithSubjects(**program))
        
        faculty_data['programas'] = [p.model_dump() for p in enriched_programs]
        return FacultyWithPrograms(**faculty_data)
    
    async def get_program_with_subjects(self, faculty_id: str, program_code: str) -> ProgramWithSubjects:
        """Obtiene un programa con todas sus materias pobladas"""
        program_data = await self.program_repo.get_by_id(faculty_id, program_code)
        
        if not program_data:
            raise ProgramNotFoundException(program_code)
        
        # Obtener materias pobladas
        subject_codes = program_data.get('materias', [])
        subjects = []
        
        for subject_code in subject_codes:
            try:
                subject = await self.subject_repo.get_by_id(subject_code)
                if subject and subject.get('activo', True):
                    subjects.append(SubjectSummary(**subject))
            except Exception as e:
                logger.warning(f"Materia {subject_code} no encontrada: {str(e)}")
                continue
        
        # Convertir a ProgramWithSubjects
        program_data['materias'] = [s.model_dump() for s in subjects]
        return ProgramWithSubjects(**program_data)
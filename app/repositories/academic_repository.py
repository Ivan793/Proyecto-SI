from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, timezone

from .base_repository import BaseRepository
from app.core.firebase import Collections

logger = logging.getLogger(__name__)

# ==================== FACULTAD ====================

class FacultyRepository(BaseRepository):
    
    def __init__(self):
        super().__init__(Collections.FACULTADES, "id_facultad")
    
    async def get_by_code(self, faculty_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene facultad por código"""
        return await self.get_by_id(faculty_id)
    
    async def faculty_exists(self, faculty_id: str) -> bool:
        """Verifica si existe una facultad"""
        faculty = await self.get_by_code(faculty_id)
        return faculty is not None
    
    async def create_faculty(self, faculty_id: str, data: Dict[str, Any]) -> str:
        """Crea una facultad con código específico"""
        return await self.create(data, document_id=faculty_id)
    
    async def get_faculty_with_programs(self, faculty_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene facultad con todos sus programas y materias.
        Usa subcollections para organización jerárquica.
        """
        try:
            # Consulta 1: Obtener la facultad
            faculty_ref = self.collection.document(faculty_id)
            faculty_doc = faculty_ref.get()
            
            if not faculty_doc.exists:
                return None
            
            faculty_data = faculty_doc.to_dict()
            faculty_data['id_facultad'] = faculty_doc.id
            
            # Consulta 2: Obtener todos los programas de la facultad
            programs_ref = faculty_ref.collection('programas')
            programs_docs = programs_ref.stream()
            
            programs = []
            for doc in programs_docs:
                program_data = doc.to_dict()
                program_data['codigo_programa'] = doc.id
                
                # Las materias vienen embebidas en el programa
                if 'materias' not in program_data:
                    program_data['materias'] = []
                
                programs.append(program_data)
            
            faculty_data['programas'] = programs
            
            return self._convert_firestore_data(faculty_data)
            
        except Exception as e:
            logger.error(f"Error obteniendo facultad con programas {faculty_id}: {str(e)}")
            raise
    
    async def get_all_faculties_with_programs(self) -> List[Dict[str, Any]]:
        """Obtiene todas las facultades con su estructura completa"""
        try:
            faculties = await self.get_all()
            
            result = []
            for faculty in faculties:
                faculty_id = faculty.get('id_facultad')
                faculty_with_programs = await self.get_faculty_with_programs(faculty_id)
                if faculty_with_programs:
                    result.append(faculty_with_programs)
            
            return result
            
        except Exception as e:
            logger.error(f"Error obteniendo todas las facultades: {str(e)}")
            raise

# ==================== PROGRAMA ====================

class ProgramRepository(BaseRepository):
    
    def __init__(self):
        super().__init__(Collections.FACULTADES, "codigo_programa")
    
    async def create_program(self, faculty_id: str, program_code: str, 
                            data: Dict[str, Any]) -> str:
        """
        Crea un programa dentro de una facultad como subcollection.
        Las materias se guardan embebidas en el documento del programa.
        """
        try:
            now = datetime.now(timezone.utc)
            data['created_at'] = now
            data['updated_at'] = now
            data['codigo_programa'] = program_code
            
            # Inicializar array vacío de materias
            if 'materias' not in data:
                data['materias'] = []
            
            # Crear programa en subcollection
            faculty_ref = self.db.collection(Collections.FACULTADES).document(faculty_id)
            program_ref = faculty_ref.collection('programas').document(program_code)
            
            program_ref.set(data)
            
            logger.info(f"Programa {program_code} creado en facultad {faculty_id}")
            return program_code
            
        except Exception as e:
            logger.error(f"Error creando programa: {str(e)}")
            raise
    
    async def get_by_id(self, faculty_id: str, program_code: str) -> Optional[Dict[str, Any]]:
        """Obtiene un programa específico"""
        try:
            faculty_ref = self.db.collection(Collections.FACULTADES).document(faculty_id)
            program_ref = faculty_ref.collection('programas').document(program_code)
            
            doc = program_ref.get()
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            data['codigo_programa'] = doc.id
            
            if 'materias' not in data:
                data['materias'] = []
            
            return self._convert_firestore_data(data)
            
        except Exception as e:
            logger.error(f"Error obteniendo programa {program_code}: {str(e)}")
            raise
    
    async def get_by_faculty(self, faculty_id: str) -> List[Dict[str, Any]]:
        """Obtiene todos los programas de una facultad"""
        try:
            faculty_ref = self.db.collection(Collections.FACULTADES).document(faculty_id)
            programs_ref = faculty_ref.collection('programas')
            
            docs = programs_ref.stream()
            
            programs = []
            for doc in docs:
                data = doc.to_dict()
                data['codigo_programa'] = doc.id
                
                if 'materias' not in data:
                    data['materias'] = []
                
                programs.append(self._convert_firestore_data(data))
            
            return programs
            
        except Exception as e:
            logger.error(f"Error obteniendo programas de facultad {faculty_id}: {str(e)}")
            raise
    
    async def update_program(self, faculty_id: str, program_code: str, 
                            data: Dict[str, Any]) -> bool:
        """Actualiza un programa"""
        try:
            faculty_ref = self.db.collection(Collections.FACULTADES).document(faculty_id)
            program_ref = faculty_ref.collection('programas').document(program_code)
            
            doc = program_ref.get()
            if not doc.exists:
                return False
            
            data['updated_at'] = datetime.now(timezone.utc)
            program_ref.update(data)
            
            logger.info(f"Programa {program_code} actualizado")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando programa: {str(e)}")
            raise
    
    async def program_name_exists(self, faculty_id: str, program_name: str, 
                                exclude_code: Optional[str] = None) -> bool:
        """Verifica si existe un programa con el mismo nombre en la facultad"""
        try:
            programs = await self.get_by_faculty(faculty_id)
            
            for program in programs:
                if (program.get("nombre_programa") == program_name and 
                    (exclude_code is None or program.get("codigo_programa") != exclude_code)):
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Error verificando nombre de programa: {str(e)}")
            raise
    
    async def add_subject_to_program(self, faculty_id: str, program_code: str, 
                                    subject_code: str) -> bool:
        """Agrega una materia al array de materias del programa"""
        try:
            faculty_ref = self.db.collection(Collections.FACULTADES).document(faculty_id)
            program_ref = faculty_ref.collection('programas').document(program_code)
            
            program_doc = program_ref.get()
            if not program_doc.exists:
                return False
            
            program_data = program_doc.to_dict()
            materias = program_data.get('materias', [])
            
            # Evitar duplicados
            if subject_code not in materias:
                materias.append(subject_code)
                
                program_ref.update({
                    'materias': materias,
                    'updated_at': datetime.now(timezone.utc)
                })
                
                logger.info(f"Materia {subject_code} agregada al programa {program_code}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error agregando materia a programa: {str(e)}")
            raise
    
    async def remove_subject_from_program(self, faculty_id: str, program_code: str, 
                                        subject_code: str) -> bool:
        """Remueve una materia del programa"""
        try:
            faculty_ref = self.db.collection(Collections.FACULTADES).document(faculty_id)
            program_ref = faculty_ref.collection('programas').document(program_code)
            
            program_doc = program_ref.get()
            if not program_doc.exists:
                return False
            
            program_data = program_doc.to_dict()
            materias = program_data.get('materias', [])
            
            if subject_code in materias:
                materias.remove(subject_code)
                
                program_ref.update({
                    'materias': materias,
                    'updated_at': datetime.now(timezone.utc)
                })
                
                logger.info(f"Materia {subject_code} removida del programa {program_code}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error removiendo materia de programa: {str(e)}")
            raise
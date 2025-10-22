from typing import Optional, List, Dict, Any
import logging

from .base_repository import BaseRepository
from app.core.firebase import Collections

logger = logging.getLogger(__name__)

# ==================== LÍNEA DE INVESTIGACIÓN ====================

class ResearchLineRepository(BaseRepository):
    
    def __init__(self):
        super().__init__(Collections.LINEAS_INVESTIGACION, "codigo_linea")
    
    async def get_by_code(self, code: int) -> Optional[Dict[str, Any]]:
        """Obtiene línea por código"""
        return await self.get_by_id(str(code))
    
    async def line_exists(self, code: int) -> bool:
        """Verifica si existe una línea con el código dado"""
        line = await self.get_by_code(code)
        return line is not None
    
    async def create_line(self, code: int, data: Dict[str, Any]) -> str:
        """Crea una línea con código específico"""
        return await self.create(data, document_id=str(code))
    
    async def get_line_with_hierarchy(self, code: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene línea con toda su jerarquía (sublíneas + áreas) en 2 consultas.
        Usa subcollections para organización jerárquica.
        """
        try:
            # Consulta 1: Obtener la línea principal
            line_ref = self.collection.document(str(code))
            line_doc = line_ref.get()
            
            if not line_doc.exists:
                return None
            
            line_data = line_doc.to_dict()
            line_data['codigo_linea'] = int(line_doc.id)
            
            # Consulta 2: Obtener todas las sublíneas con áreas embebidas
            sublines_ref = line_ref.collection('sublineas')
            sublines_docs = sublines_ref.stream()
            
            sublines = []
            for doc in sublines_docs:
                subline_data = doc.to_dict()
                subline_data['codigo_sublinea'] = int(doc.id)
                # Las áreas ya vienen embebidas en la sublínea
                if 'areas_tematicas' in subline_data:
                    for area in subline_data['areas_tematicas']:
                        # Agregar el código de la sublínea a cada área
                        area['codigo_sublinea'] = int(doc.id)
            
                sublines.append(subline_data)
            
            line_data['sublineas'] = sublines
            
            return self._convert_firestore_data(line_data)
            
        except Exception as e:
            logger.error(f"Error obteniendo línea con jerarquía {code}: {str(e)}")
            raise
    
    async def get_all_lines_with_hierarchy(self) -> List[Dict[str, Any]]:
        """
        Obtiene todas las líneas con su jerarquía completa.
        Para N líneas: N + N consultas (mucho mejor que el método anterior)
        """
        try:
            # Obtener todas las líneas
            lines = await self.get_all()
            
            result = []
            for line in lines:
                line_code = line.get('codigo_linea')
                line_with_hierarchy = await self.get_line_with_hierarchy(line_code)
                if line_with_hierarchy:
                    result.append(line_with_hierarchy)
            
            return result
            
        except Exception as e:
            logger.error(f"Error obteniendo todas las líneas con jerarquía: {str(e)}")
            raise

# ==================== SUBLÍNEA DE INVESTIGACIÓN ====================

class SubResearchLineRepository(BaseRepository):
    
    def __init__(self):
        # usamos subcollections
        super().__init__(Collections.LINEAS_INVESTIGACION, "codigo_sublinea")
    
    async def create_subline(self, line_code: int, subline_code: int, 
                        data: Dict[str, Any]) -> str:
        """
        Crea una sublínea dentro de una línea como subcollection.
        Las áreas se guardan embebidas en el documento de la sublínea.
        """
        try:
            from datetime import datetime, timezone
            
            # Agregar timestamps
            now = datetime.now(timezone.utc)
            data['created_at'] = now
            data['updated_at'] = now
            data['codigo_sublinea'] = subline_code
            
            # Inicializar array vacío de áreas temáticas
            if 'areas_tematicas' not in data:
                data['areas_tematicas'] = []
            
            # Crear sublínea en subcollection
            line_ref = self.db.collection(Collections.LINEAS_INVESTIGACION).document(str(line_code))
            subline_ref = line_ref.collection('sublineas').document(str(subline_code))
            
            subline_ref.set(data)
            
            logger.info(f"Sublínea {subline_code} creada en línea {line_code}")
            return str(subline_code)
            
        except Exception as e:
            logger.error(f"Error creando sublínea: {str(e)}")
            raise

    async def get_by_id(self, line_code: int, subline_code: int) -> Optional[Dict[str, Any]]:
        """Obtiene una sublínea específica"""
        try:
            line_ref = self.db.collection(Collections.LINEAS_INVESTIGACION).document(str(line_code))
            subline_ref = line_ref.collection('sublineas').document(str(subline_code))
            
            doc = subline_ref.get()
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            data['codigo_sublinea'] = int(doc.id)
            
            if 'areas_tematicas' in data:
                for area in data['areas_tematicas']:
                    area['codigo_sublinea'] = int(doc.id)
            
            return self._convert_firestore_data(data)
            
        except Exception as e:
            logger.error(f"Error obteniendo sublínea {subline_code}: {str(e)}")
            raise
    
    async def get_by_research_line(self, line_code: int) -> List[Dict[str, Any]]:
        """Obtiene todas las sublíneas de una línea"""
        try:
            line_ref = self.db.collection(Collections.LINEAS_INVESTIGACION).document(str(line_code))
            sublines_ref = line_ref.collection('sublineas')
            
            docs = sublines_ref.stream()
            
            sublines = []
            for doc in docs:
                data = doc.to_dict()
                subline_code = int(doc.id)
                data['codigo_sublinea'] = int(doc.id)
                if 'areas_tematicas' in data:
                    for area in data['areas_tematicas']:
                        area['codigo_sublinea'] = subline_code
                sublines.append(self._convert_firestore_data(data))
            
            return sublines
            
        except Exception as e:
            logger.error(f"Error obteniendo sublíneas de línea {line_code}: {str(e)}")
            raise
    
    async def get_next_code(self, line_code: int) -> int:
        """Obtiene el siguiente código disponible para sublíneas de una línea"""
        try:
            sublines = await self.get_by_research_line(line_code)
            if not sublines:
                return 1
            
            codes = [int(sub.get("codigo_sublinea", 0)) for sub in sublines]
            return max(codes) + 1
            
        except Exception as e:
            logger.error(f"Error obteniendo siguiente código: {str(e)}")
            raise
    
    async def update_subline(self, line_code: int, subline_code: int, 
                            data: Dict[str, Any]) -> bool:
        """Actualiza una sublínea"""
        try:
            from datetime import datetime, timezone
            
            line_ref = self.db.collection(Collections.LINEAS_INVESTIGACION).document(str(line_code))
            subline_ref = line_ref.collection('sublineas').document(str(subline_code))
            
            doc = subline_ref.get()
            if not doc.exists:
                return False
            
            data['updated_at'] = datetime.now(timezone.utc)
            subline_ref.update(data)
            
            logger.info(f"Sublínea {subline_code} actualizada")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando sublínea: {str(e)}")
            raise
    
    async def subline_name_exists(self, line_code: int, name: str, 
                                exclude_code: Optional[int] = None) -> bool:
        """Verifica si existe una sublínea con el mismo nombre en la línea"""
        try:
            sublines = await self.get_by_research_line(line_code)
            
            for subline in sublines:
                if (subline.get("nombre_sublinea") == name and 
                    (exclude_code is None or subline.get("codigo_sublinea") != exclude_code)):
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Error verificando nombre de sublínea: {str(e)}")
            raise

# ==================== ÁREA TEMÁTICA ====================

class ThematicAreaRepository(BaseRepository):
    
    def __init__(self):
        super().__init__(Collections.LINEAS_INVESTIGACION, "codigo_area")
    
    async def create_area(self, line_code: int, subline_code: int, 
                        area_code: int, data: Dict[str, Any]) -> str:
        """
        Crea un área temática embebida en una sublínea.
        Las áreas se guardan como elementos en el array 'areas_tematicas'.
        """
        try:
            from datetime import datetime, timezone
            
            line_ref = self.db.collection(Collections.LINEAS_INVESTIGACION).document(str(line_code))
            subline_ref = line_ref.collection('sublineas').document(str(subline_code))
            
            # Obtener sublínea actual
            subline_doc = subline_ref.get()
            if not subline_doc.exists:
                raise Exception(f"Sublínea {subline_code} no encontrada")
            
            subline_data = subline_doc.to_dict()
            areas = subline_data.get('areas_tematicas', [])
            
            # Agregar nueva área
            new_area = {
                'codigo_area': area_code,
                'nombre_area': data.get('nombre_area'),
                'codigo_sublinea': subline_code,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }
            
            areas.append(new_area)
            
            # Actualizar sublínea con nueva área
            subline_ref.update({
                'areas_tematicas': areas,
                'updated_at': datetime.now(timezone.utc)
            })
            
            logger.info(f"Área {area_code} creada en sublínea {subline_code}")
            return str(area_code)
            
        except Exception as e:
            logger.error(f"Error creando área temática: {str(e)}")
            raise
    
    async def get_by_id(self, line_code: int, subline_code: int, 
                        area_code: int) -> Optional[Dict[str, Any]]:
        """Obtiene un área específica"""
        try:
            line_ref = self.db.collection(Collections.LINEAS_INVESTIGACION).document(str(line_code))
            subline_ref = line_ref.collection('sublineas').document(str(subline_code))
            
            subline_doc = subline_ref.get()
            if not subline_doc.exists:
                return None
            
            subline_data = subline_doc.to_dict()
            areas = subline_data.get('areas_tematicas', [])
            
            # Buscar el área específica
            for area in areas:
                if area.get('codigo_area') == area_code:
                    return self._convert_firestore_data(area)
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo área {area_code}: {str(e)}")
            raise
    
    async def get_by_subline(self, line_code: int, subline_code: int) -> List[Dict[str, Any]]:
        """Obtiene todas las áreas de una sublínea"""
        try:
            line_ref = self.db.collection(Collections.LINEAS_INVESTIGACION).document(str(line_code))
            subline_ref = line_ref.collection('sublineas').document(str(subline_code))
            
            subline_doc = subline_ref.get()
            if not subline_doc.exists:
                return []
            
            subline_data = subline_doc.to_dict()
            areas = subline_data.get('areas_tematicas', [])
            
            return [self._convert_firestore_data(area) for area in areas]
            
        except Exception as e:
            logger.error(f"Error obteniendo áreas de sublínea {subline_code}: {str(e)}")
            raise
    
    async def get_next_code(self, line_code: int, subline_code: int) -> int:
        """Obtiene el siguiente código disponible para áreas"""
        try:
            areas = await self.get_by_subline(line_code, subline_code)
            if not areas:
                return 1
            
            codes = [int(area.get("codigo_area", 0)) for area in areas]
            return max(codes) + 1
            
        except Exception as e:
            logger.error(f"Error obteniendo siguiente código de área: {str(e)}")
            raise
    
    async def update_area(self, line_code: int, subline_code: int, 
                        area_code: int, data: Dict[str, Any]) -> bool:
        """Actualiza un área temática"""
        try:
            from datetime import datetime, timezone
            
            line_ref = self.db.collection(Collections.LINEAS_INVESTIGACION).document(str(line_code))
            subline_ref = line_ref.collection('sublineas').document(str(subline_code))
            
            subline_doc = subline_ref.get()
            if not subline_doc.exists:
                return False
            
            subline_data = subline_doc.to_dict()
            areas = subline_data.get('areas_tematicas', [])
            
            # Actualizar el área específica
            area_found = False
            for i, area in enumerate(areas):
                if area.get('codigo_area') == area_code:
                    areas[i].update(data)
                    areas[i]['updated_at'] = datetime.now(timezone.utc)
                    area_found = True
                    break
            
            if not area_found:
                return False
            
            # Actualizar sublínea
            subline_ref.update({
                'areas_tematicas': areas,
                'updated_at': datetime.now(timezone.utc)
            })
            
            logger.info(f"Área {area_code} actualizada")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando área: {str(e)}")
            raise
    
    async def area_name_exists(self, line_code: int, subline_code: int, 
                            name: str, exclude_code: Optional[int] = None) -> bool:
        """Verifica si existe un área con el mismo nombre en la sublínea"""
        try:
            areas = await self.get_by_subline(line_code, subline_code)
            
            for area in areas:
                if (area.get("nombre_area") == name and 
                    (exclude_code is None or area.get("codigo_area") != exclude_code)):
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Error verificando nombre de área: {str(e)}")
            raise
from typing import List, Optional
import logging

from app.repositories.research_repository import (
    ResearchLineRepository,
    SubResearchLineRepository,
    ThematicAreaRepository
)

from app.exceptions.research_exceptions import (
    ResearchLineNotFoundException, ResearchLineAlreadyExistsException,
    SubResearchLineNotFoundException, SubResearchLineAlreadyExistsException,
    ThematicAreaNotFoundException, ThematicAreaAlreadyExistsException,
    InvalidResearchLineException, InvalidSubResearchLineException
)
from app.schemas.SubResearchLine import (
    SubResearchLineCreate, 
    SubResearchLineResponseAdmin,
    SubResearchLineResponsePublic, 
    SubResearchLineUpdate, 
    SubResearchLineWithAreasAdmin,
    SubResearchLineWithAreasPublic
)
from app.schemas.ThematicArea import (
    ThematicAreaCreate, 
    ThematicAreaResponseAdmin,
    ThematicAreaResponsePublic, 
    ThematicAreaUpdate
)
from app.schemas.researchLine import (
    ResearchLineAdminResponse,
    ResearchLineCreate,
    ResearchLinePublicResponse, 
    ResearchLineUpdate, 
    ResearchLineWithSublinesAdmin,
    ResearchLineWithSublinesPublic
)

logger = logging.getLogger(__name__)

# ==================== SERVICIO DE LÍNEAS ====================
class ResearchLineService:
    
    def __init__(self):
        self.line_repo = ResearchLineRepository()
    
    async def create_line(self, line_data: ResearchLineCreate) -> ResearchLineAdminResponse:
        """Crea una línea de investigación (solo código 1 o 2)"""
        if await self.line_repo.line_exists(line_data.codigo_linea):
            raise ResearchLineAlreadyExistsException(line_data.codigo_linea)
        
        data = line_data.model_dump()
        await self.line_repo.create_line(line_data.codigo_linea, data)
        
        created_line = await self.line_repo.get_by_code(line_data.codigo_linea)
        return ResearchLineAdminResponse(**created_line)
    
    async def get_line(self, line_code: int, is_admin: bool = False) -> ResearchLinePublicResponse | ResearchLineAdminResponse:
        """Obtiene una línea por código"""
        line = await self.line_repo.get_by_code(line_code)
        if not line:
            raise ResearchLineNotFoundException(line_code)
        
        if is_admin:
            return ResearchLineAdminResponse(**line)
        else:
            # Para usuarios no admin, crear respuesta sin timestamps
            public_data = {
                "codigo_linea": line["codigo_linea"],
                "nombre_linea": line["nombre_linea"]
            }
            return ResearchLinePublicResponse(**public_data)
    
    async def get_all_lines(self, is_admin: bool = False) -> List[ResearchLinePublicResponse | ResearchLineAdminResponse]:
        """Obtiene todas las líneas"""
        lines = await self.line_repo.get_all()
        
        result = []
        for line in lines:
            if is_admin:
                result.append(ResearchLineAdminResponse(**line))
            else:
                # Para usuarios no admin, filtrar campos
                public_data = {
                    "codigo_linea": line["codigo_linea"],
                    "nombre_linea": line["nombre_linea"]
                }
                result.append(ResearchLinePublicResponse(**public_data))
        
        return result
    
    async def update_line(self, line_code: int, 
                        line_data: ResearchLineUpdate) -> ResearchLineAdminResponse:
        """Actualiza una línea"""
        if not await self.line_repo.line_exists(line_code):
            raise ResearchLineNotFoundException(line_code)
        
        update_dict = line_data.model_dump(exclude_none=True)
        if update_dict:
            await self.line_repo.update(str(line_code), update_dict)
        
        updated_line = await self.line_repo.get_by_code(line_code)
        return ResearchLineAdminResponse(**updated_line)

# ==================== SERVICIO DE SUBLÍNEAS ====================

class SubResearchLineService:
    
    def __init__(self):
        self.subline_repo = SubResearchLineRepository()
        self.line_repo = ResearchLineRepository()
    
    async def create_subline(self, 
        subline_data: SubResearchLineCreate) -> SubResearchLineResponseAdmin:
        """Crea una sublínea dentro de una línea (subcollection)"""
        line_code = subline_data.codigo_linea
        
        # Validar que la línea existe
        if not await self.line_repo.line_exists(line_code):
            raise InvalidResearchLineException(line_code)
        
        # Verificar nombre duplicado dentro de la línea
        if await self.subline_repo.subline_name_exists(
            line_code,
            subline_data.nombre_sublinea
        ):
            raise SubResearchLineAlreadyExistsException(subline_data.nombre_sublinea)
        
        # Generar código automático para esta línea
        next_code = await self.subline_repo.get_next_code(line_code)
        
        data = subline_data.model_dump()
        
        # Crear sublínea en subcollection
        await self.subline_repo.create_subline(line_code, next_code, data)
        
        # Obtener sublínea creada
        created_subline = await self.subline_repo.get_by_id(line_code, next_code)
        return SubResearchLineResponseAdmin(**created_subline)
    
    async def get_subline(self, line_code: int, subline_code: int, is_admin: bool = False) -> SubResearchLineResponsePublic | SubResearchLineResponseAdmin:
        """Obtiene una sublínea específica"""
        subline = await self.subline_repo.get_by_id(line_code, subline_code)
        if not subline:
            raise SubResearchLineNotFoundException(subline_code)
        
        if is_admin:
            return SubResearchLineResponseAdmin(**subline)
        else:
            # Para usuarios no admin, filtrar campos
            public_data = {
                "codigo_sublinea": subline["codigo_sublinea"],
                "nombre_sublinea": subline["nombre_sublinea"],
                "codigo_linea": subline["codigo_linea"]
            }
            return SubResearchLineResponsePublic(**public_data)
    
    async def get_sublines_by_line(self, line_code: int, is_admin: bool = False) -> List[SubResearchLineResponsePublic | SubResearchLineResponseAdmin]:
        """Obtiene todas las sublíneas de una línea"""
        sublines = await self.subline_repo.get_by_research_line(line_code)
        
        result = []
        for subline in sublines:
            if is_admin:
                result.append(SubResearchLineResponseAdmin(**subline))
            else:
                # Para usuarios no admin, filtrar campos
                public_data = {
                    "codigo_sublinea": subline["codigo_sublinea"],
                    "nombre_sublinea": subline["nombre_sublinea"],
                    "codigo_linea": subline["codigo_linea"]
                }
                result.append(SubResearchLineResponsePublic(**public_data))
        
        return result
    
    async def update_subline(self, line_code: int, subline_code: int, 
                            subline_data: SubResearchLineUpdate) -> SubResearchLineResponseAdmin:
        """Actualiza una sublínea"""
        subline = await self.subline_repo.get_by_id(line_code, subline_code)
        if not subline:
            raise SubResearchLineNotFoundException(subline_code)
        
        update_dict = subline_data.model_dump(exclude_none=True)
        
        # Verificar nombre duplicado si se cambia
        if "nombre_sublinea" in update_dict:
            if await self.subline_repo.subline_name_exists(
                line_code,
                update_dict["nombre_sublinea"],
                exclude_code=subline_code
            ):
                raise SubResearchLineAlreadyExistsException(update_dict["nombre_sublinea"])
        
        if update_dict:
            await self.subline_repo.update_subline(line_code, subline_code, update_dict)
        
        updated_subline = await self.subline_repo.get_by_id(line_code, subline_code)
        return SubResearchLineResponseAdmin(**updated_subline)
    
# ==================== SERVICIO DE ÁREAS TEMÁTICAS ====================

class ThematicAreaService:
    
    def __init__(self):
        self.area_repo = ThematicAreaRepository()
        self.subline_repo = SubResearchLineRepository()
    
    async def create_area(self, line_code: int, 
                        area_data: ThematicAreaCreate) -> ThematicAreaResponseAdmin:
        """Crea un área temática embebida en una sublínea"""
        subline_code = area_data.codigo_sublinea
        
        # Validar que la sublínea existe
        subline = await self.subline_repo.get_by_id(line_code, subline_code)
        if not subline:
            raise InvalidSubResearchLineException(subline_code)
        
        # Verificar nombre duplicado
        if await self.area_repo.area_name_exists(
            line_code,
            subline_code,
            area_data.nombre_area
        ):
            raise ThematicAreaAlreadyExistsException(area_data.nombre_area)
        
        # Generar código automático
        next_code = await self.area_repo.get_next_code(line_code, subline_code)
        
        data = area_data.model_dump()
        
        # Crear área embebida
        await self.area_repo.create_area(line_code, subline_code, next_code, data)
        
        # Obtener área creada
        created_area = await self.area_repo.get_by_id(line_code, subline_code, next_code)
        created_area['codigo_sublinea'] = subline_code
        return ThematicAreaResponseAdmin(**created_area)
    
    async def get_area(self, line_code: int, subline_code: int, 
                        area_code: int, is_admin: bool = False) -> ThematicAreaResponsePublic | ThematicAreaResponseAdmin:
        """Obtiene un área específica"""
        area = await self.area_repo.get_by_id(line_code, subline_code, area_code)
        if not area:
            raise ThematicAreaNotFoundException(area_code)
        area['codigo_sublinea'] = subline_code
        
        if is_admin:
            return ThematicAreaResponseAdmin(**area)
        return ThematicAreaResponsePublic(**area)
    
    async def get_areas_by_subline(self, line_code: int, 
                                    subline_code: int, is_admin: bool = False) -> List[ThematicAreaResponsePublic | ThematicAreaResponseAdmin]:
        """Obtiene todas las áreas de una sublínea"""
        areas = await self.area_repo.get_by_subline(line_code, subline_code)
        result = []
        for area in areas:
            area['codigo_sublinea'] = subline_code
            if is_admin:
                result.append(ThematicAreaResponseAdmin(**area))
            else:
                result.append(ThematicAreaResponsePublic(**area))
        return result
    
    async def update_area(self, line_code: int, subline_code: int, 
                        area_code: int, 
                        area_data: ThematicAreaUpdate) -> ThematicAreaResponseAdmin:
        """Actualiza un área temática"""
        area = await self.area_repo.get_by_id(line_code, subline_code, area_code)
        if not area:
            raise ThematicAreaNotFoundException(area_code)
        
        update_dict = area_data.model_dump(exclude_none=True)
        
        # Verificar nombre duplicado si se cambia
        if "nombre_area" in update_dict:
            if await self.area_repo.area_name_exists(
                line_code,
                subline_code,
                update_dict["nombre_area"],
                exclude_code=area_code
            ):
                raise ThematicAreaAlreadyExistsException(update_dict["nombre_area"])
        
        if update_dict:
            await self.area_repo.update_area(line_code, subline_code, area_code, update_dict)
        
        updated_area = await self.area_repo.get_by_id(line_code, subline_code, area_code)
        updated_area['codigo_sublinea'] = subline_code
        return ThematicAreaResponseAdmin(**updated_area)
    
# ==================== SERVICIO COMBINADO ====================
class ResearchService:
    """Servicio que combina las tres entidades para consultas jerárquicas"""
    
    def __init__(self):
        self.line_repo = ResearchLineRepository()
        self.subline_service = SubResearchLineService()
        self.area_service = ThematicAreaService()
    
    async def get_line_with_hierarchy(self, line_code: int, is_admin: bool = False) -> ResearchLineWithSublinesPublic | ResearchLineWithSublinesAdmin:
        """
        Obtiene línea con sublíneas y áreas en SOLO 2 CONSULTAS.
        """
        # Usar el método optimizado del repositorio
        line_data = await self.line_repo.get_line_with_hierarchy(line_code)
        
        if not line_data:
            raise ResearchLineNotFoundException(line_code)
        
        if is_admin:
            return ResearchLineWithSublinesAdmin(**line_data)
        return ResearchLineWithSublinesPublic(**line_data)
    
    async def get_subline_with_areas(self, line_code: int, 
                                    subline_code: int, is_admin: bool = False) -> SubResearchLineWithAreasPublic | SubResearchLineWithAreasAdmin:
        """Obtiene una sublínea con sus áreas temáticas"""
        subline = await self.subline_service.get_subline(line_code, subline_code, is_admin)
        areas = await self.area_service.get_areas_by_subline(line_code, subline_code, is_admin)
        
        subline_dict = subline.model_dump()
        subline_dict["areas_tematicas"] = [area.model_dump() for area in areas]
        
        if is_admin:
            return SubResearchLineWithAreasAdmin(**subline_dict)
        return SubResearchLineWithAreasPublic(**subline_dict)
    
    async def get_all_lines_with_hierarchy(self, is_admin: bool = False) -> List[ResearchLineWithSublinesPublic | ResearchLineWithSublinesAdmin]:
        """
        Obtiene todas las líneas con su jerarquía completa.
        """
        lines_data = await self.line_repo.get_all_lines_with_hierarchy()
        
        if is_admin:
            return [ResearchLineWithSublinesAdmin(**line) for line in lines_data]
        return [ResearchLineWithSublinesPublic(**line) for line in lines_data]
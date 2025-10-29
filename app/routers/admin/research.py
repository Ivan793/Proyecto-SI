from fastapi import APIRouter, Depends, Request, status, Path
from typing import Dict, Any
import logging

from app.services.research_service import (
    ResearchLineService,
    SubResearchLineService, 
    ThematicAreaService
)
from app.schemas.researchLine import ResearchLineCreate, ResearchLineUpdate, ResearchLineAdminResponse
from app.schemas.SubResearchLine import SubResearchLineCreate, SubResearchLineUpdate, SubResearchLineResponseAdmin
from app.schemas.ThematicArea import ThematicAreaCreate, ThematicAreaUpdate, ThematicAreaResponseAdmin

from app.dependencies.auth_dependencies import get_current_admin_user
from app.core.rate_limiter import admin_rate_limit
from app.utils.responses import (
    created_response, updated_response, success_response,
    not_found_response, conflict_response, internal_server_error_response
)
from app.utils.swagger_docs import ResponseDocumentation
from app.exceptions.research_exceptions import (
    ResearchLineNotFoundException, ResearchLineAlreadyExistsException,
    SubResearchLineNotFoundException, SubResearchLineAlreadyExistsException,
    ThematicAreaNotFoundException, ThematicAreaAlreadyExistsException,
    InvalidResearchLineException, InvalidSubResearchLineException
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Investigación - Admin"])

# ==================== LÍNEAS DE INVESTIGACIÓN ====================

@router.post(
    "/lineas",
    status_code=status.HTTP_201_CREATED,
    summary="Crear línea de investigación",
    description="**Solo Administradores**",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def create_research_line(
    request: Request,
    line_data: ResearchLineCreate,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = ResearchLineService()
        line = await service.create_line(line_data)        
        return created_response(
            data=line.model_dump(),
            message="Línea de investigación creada exitosamente"
        )
        
    except ResearchLineAlreadyExistsException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error creando línea: {str(e)}")
        return internal_server_error_response()

@router.put(
    "/lineas/{line_code}",
    summary="Actualizar línea de investigación", 
    description="**Solo Administradores**",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def update_research_line(
    request: Request,
    line_code: int = Path(..., description="Código de la línea de investigación"),
    line_data: ResearchLineUpdate = ...,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = ResearchLineService()
        line = await service.update_line(line_code, line_data)        
        return updated_response(
            data=line.model_dump(),
            message="Línea de investigación actualizada exitosamente"
        )
        
    except ResearchLineNotFoundException:
        return not_found_response("Línea de investigación", str(line_code))
    except ResearchLineAlreadyExistsException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error actualizando línea {line_code}: {str(e)}")
        return internal_server_error_response()

# ==================== SUBLÍNEAS DE INVESTIGACIÓN ====================

@router.post(
    "/lineas/{line_code}/sublineas",
    status_code=status.HTTP_201_CREATED,
    summary="Crear sublínea de investigación",
    description="**Solo Administradores**. Crea una sublínea dentro de una línea específica",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def create_subresearch_line(
    request: Request,
    line_code: int = Path(..., description="Código de la línea de investigación"),
    subline_data: SubResearchLineCreate = ...,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        if subline_data.codigo_linea != line_code:
            return conflict_response(
                message="El código de línea en el path no coincide con el del cuerpo de la solicitud"
            )
        
        service = SubResearchLineService()
        subline = await service.create_subline(subline_data)        
        return created_response(
            data=subline.model_dump(),
            message="Sublínea de investigación creada exitosamente"
        )
        
    except InvalidResearchLineException as e:
        return not_found_response("Línea de investigación", str(line_code))
    except SubResearchLineAlreadyExistsException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error creando sublínea: {str(e)}")
        return internal_server_error_response()

@router.put(
    "/lineas/{line_code}/sublineas/{subline_code}",
    summary="Actualizar sublínea de investigación",
    description="**Solo Administradores**",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def update_subresearch_line(
    request: Request,
    line_code: int = Path(..., description="Código de la línea de investigación"),
    subline_code: int = Path(..., description="Código de la sublínea"),
    subline_data: SubResearchLineUpdate = ...,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = SubResearchLineService()
        subline = await service.update_subline(line_code, subline_code, subline_data)        
        return updated_response(
            data=subline.model_dump(),
            message="Sublínea de investigación actualizada exitosamente"
        )
        
    except SubResearchLineNotFoundException:
        return not_found_response("Sublínea de investigación", str(subline_code))
    except SubResearchLineAlreadyExistsException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error actualizando sublínea {subline_code}: {str(e)}")
        return internal_server_error_response()

# ==================== ÁREAS TEMÁTICAS ====================

@router.post(
    "/lineas/{line_code}/sublineas/{subline_code}/areas-tematicas",
    status_code=status.HTTP_201_CREATED,
    summary="Crear área temática",
    description="**Solo Administradores**. Crea un área temática dentro de una sublínea",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def create_thematic_area(
    request: Request,
    line_code: int = Path(..., description="Código de la línea de investigación"),
    subline_code: int = Path(..., description="Código de la sublínea"),
    area_data: ThematicAreaCreate = ...,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        if area_data.codigo_sublinea != subline_code:
            return conflict_response(
                message="El código de sublínea en el path no coincide con el del cuerpo de la solicitud"
            )
        
        service = ThematicAreaService()
        area = await service.create_area(line_code, area_data)        
        return created_response(
            data=area.model_dump(),
            message="Área temática creada exitosamente"
        )
        
    except InvalidSubResearchLineException as e:
        return not_found_response("Sublínea de investigación", str(subline_code))
    except ThematicAreaAlreadyExistsException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error creando área temática: {str(e)}")
        return internal_server_error_response()

@router.put(
    "/lineas/{line_code}/sublineas/{subline_code}/areas-tematicas/{area_code}",
    summary="Actualizar área temática",
    description="**Solo Administradores**",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def update_thematic_area(
    request: Request,
    line_code: int = Path(..., description="Código de la línea de investigación"),
    subline_code: int = Path(..., description="Código de la sublínea"),
    area_code: int = Path(..., description="Código del área temática"),
    area_data: ThematicAreaUpdate = ...,
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = ThematicAreaService()
        area = await service.update_area(line_code, subline_code, area_code, area_data)        
        return updated_response(
            data=area.model_dump(),
            message="Área temática actualizada exitosamente"
        )
        
    except ThematicAreaNotFoundException:
        return not_found_response("Área temática", str(area_code))
    except ThematicAreaAlreadyExistsException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error actualizando área temática {area_code}: {str(e)}")
        return internal_server_error_response()
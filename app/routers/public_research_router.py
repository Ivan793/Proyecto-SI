from fastapi import APIRouter, Depends, Request, Path
from typing import Dict, Any
import logging

from app.services.research_service import (
    ResearchLineService,
    SubResearchLineService, 
    ThematicAreaService,
    ResearchService
)

from app.dependencies.auth_dependencies import (
    get_authenticated_user,
    require_admin_or_teacher
)

from app.core.rate_limiter import auth_rate_limit
from app.utils.responses import (
    success_response, not_found_response, internal_server_error_response
)
from app.utils.swagger_docs import ResponseDocumentation
from app.exceptions.research_exceptions import (
    ResearchLineNotFoundException,
    SubResearchLineNotFoundException,
    ThematicAreaNotFoundException
)
from app.dependencies.auth_dependencies import get_role_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public-investigacion", tags=["Investigación"])

role_ctx = Depends(get_role_context)

# ==================== LÍNEAS DE INVESTIGACIÓN (PÚBLICAS) ====================

@router.get(
    "/lineas",
    summary="Listar todas las líneas de investigación",
    description="**Todos los roles autenticados** - Respuesta pública sin timestamps",
    responses=ResponseDocumentation.get_standard_responses()
)
@auth_rate_limit()
async def get_all_research_lines(
    request: Request,
    role_ctx = Depends(get_role_context),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    try:
        service = ResearchLineService()
        is_admin = role_ctx["is_admin"] or role_ctx["is_teacher"]
        lines = await service.get_all_lines(is_admin=is_admin)
        
        return success_response(
            data=[line.model_dump() for line in lines],
            message="Líneas de investigación obtenidas correctamente"
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo líneas: {str(e)}")
        return internal_server_error_response()

@router.get(
    "/lineas/{line_code}",
    summary="Obtener línea específica con sublíneas y áreas",
    description="**Todos los roles autenticados**. Retorna la línea con todas sus sublíneas y áreas. Los administradores ven información adicional.",
    responses=ResponseDocumentation.get_standard_responses()
)
@auth_rate_limit()
async def get_research_line_with_hierarchy(
    request: Request,
    role_ctx = Depends(get_role_context),
    line_code: int = Path(..., description="Código de la línea de investigación"),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    try:
        service = ResearchService()
        is_admin = role_ctx["is_admin"] or role_ctx["is_teacher"]
        line_with_hierarchy = await service.get_line_with_hierarchy(line_code, is_admin=is_admin)
        
        return success_response(
            data=line_with_hierarchy.model_dump(),
            message="Línea con jerarquía completa obtenida correctamente"
        )
        
    except ResearchLineNotFoundException:
        return not_found_response("Línea de investigación", str(line_code))
    except Exception as e:
        logger.error(f"Error obteniendo línea {line_code}: {str(e)}")
        return internal_server_error_response()

# ==================== SUBLÍNEAS DE INVESTIGACIÓN (PÚBLICAS) ====================

@router.get(
    "/lineas/{line_code}/sublineas",
    summary="Obtener sublíneas de una línea específica",
    description="**Todos los roles autenticados** - Los administradores ven información adicional",
    responses=ResponseDocumentation.get_standard_responses()
)
@auth_rate_limit()
async def get_sublines_by_research_line(
    request: Request,
    role_ctx = Depends(get_role_context),
    line_code: int = Path(..., description="Código de la línea de investigación"),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    try:
        service = SubResearchLineService()
        is_admin = role_ctx["is_admin"] or role_ctx["is_teacher"]
        sublines = await service.get_sublines_by_line(line_code, is_admin=is_admin)
        
        return success_response(
            data=[subline.model_dump() for subline in sublines],
            message="Sublíneas obtenidas correctamente"
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo sublíneas para línea {line_code}: {str(e)}")
        return internal_server_error_response()

@router.get(
    "/lineas/{line_code}/sublineas/{subline_code}",
    summary="Obtener sublínea específica con áreas temáticas", 
    description="**Todos los roles autenticados** - Los administradores ven información adicional",
    responses=ResponseDocumentation.get_standard_responses()
)
@auth_rate_limit()
async def get_subresearch_line_with_areas(
    request: Request,
    role_ctx = Depends(get_role_context),
    line_code: int = Path(..., description="Código de la línea de investigación"),
    subline_code: int = Path(..., description="Código de la sublínea"),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    try:
        service = ResearchService()
        is_admin = role_ctx["is_admin"] or role_ctx["is_teacher"]
        subline_with_areas = await service.get_subline_with_areas(line_code, subline_code, is_admin=is_admin)
        
        return success_response(
            data=subline_with_areas.model_dump(),
            message="Sublínea con áreas obtenida correctamente"
        )
        
    except SubResearchLineNotFoundException:
        return not_found_response("Sublínea de investigación", str(subline_code))
    except Exception as e:
        logger.error(f"Error obteniendo sublínea {subline_code}: {str(e)}")
        return internal_server_error_response()

# ==================== ÁREAS TEMÁTICAS (PÚBLICAS) ====================

@router.get(
    "/lineas/{line_code}/sublineas/{subline_code}/areas-tematicas",
    summary="Obtener áreas temáticas de una sublínea",
    description="**Todos los roles autenticados** - Los administradores ven información adicional",
    responses=ResponseDocumentation.get_standard_responses()
)
@auth_rate_limit()
async def get_areas_by_subresearch_line(
    request: Request,
    role_ctx = Depends(get_role_context),
    line_code: int = Path(..., description="Código de la línea de investigación"),
    subline_code: int = Path(..., description="Código de la sublínea"),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    try:
        service = ThematicAreaService()
        is_admin = role_ctx["is_admin"] or role_ctx["is_teacher"]
        areas = await service.get_areas_by_subline(line_code, subline_code, is_admin=is_admin)
        
        return success_response(
            data=[area.model_dump() for area in areas],
            message="Áreas temáticas obtenidas correctamente"
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo áreas para sublínea {subline_code}: {str(e)}")
        return internal_server_error_response()

@router.get(
    "/lineas/{line_code}/sublineas/{subline_code}/areas-tematicas/{area_code}",
    summary="Obtener área temática específica",
    description="**Todos los roles autenticados** - Los administradores ven información adicional",
    responses=ResponseDocumentation.get_standard_responses()
)
@auth_rate_limit()
async def get_thematic_area(
    request: Request,
    role_ctx = Depends(get_role_context),
    line_code: int = Path(..., description="Código de la línea de investigación"),
    subline_code: int = Path(..., description="Código de la sublínea"),
    area_code: int = Path(..., description="Código del área temática"),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    try:
        service = ThematicAreaService()
        is_admin = role_ctx["is_admin"] or role_ctx["is_teacher"]
        area = await service.get_area(line_code, subline_code, area_code, is_admin=is_admin)
        
        return success_response(
            data=area.model_dump(),
            message="Área temática obtenida correctamente"
        )
        
    except ThematicAreaNotFoundException:
        return not_found_response("Área temática", str(area_code))
    except Exception as e:
        logger.error(f"Error obteniendo área {area_code}: {str(e)}")
        return internal_server_error_response()

# ==================== CONSULTAS AVANZADAS (RESTRINGIDAS) ====================

@router.get(
    "/arbol-completo",
    summary="Obtener árbol completo de investigación",
    description="**Administradores y Profesores**. Retorna todas las líneas con su jerarquía completa con información administrativa",
    responses=ResponseDocumentation.get_standard_responses()
)
@auth_rate_limit()
async def get_complete_research_tree(
    request: Request,
    role_ctx = Depends(get_role_context),
    current_user: Dict[str, Any] = Depends(require_admin_or_teacher)
):
    try:
        service = ResearchService()
        # Siempre información completa para admin/teachers
        complete_tree = await service.get_all_lines_with_hierarchy(is_admin=True)
        
        return success_response(
            data=[line.model_dump() for line in complete_tree],
            message="Árbol completo de investigación obtenido"
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo árbol completo: {str(e)}")
        return internal_server_error_response()
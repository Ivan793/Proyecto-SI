from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from app.dependencies.auth_dependencies import get_current_admin_user
from app.services.assistence_service import AssistenceService
from app.schemas.assistence import AsistenciaBase

router = APIRouter(prefix="/asistencia", tags=["Asistencia"])
service = AssistenceService()

@router.post("/generar-qr/{id_evento}")
async def generar_qr_evento(
    id_evento: str,
    url_front: str = Query(
        default="https://exposoftware.unicesar.edu.co",
        description="URL base del frontend"
    )
):
    """
    Genera un código QR para registro de asistencia del evento.
    Público - No requiere autenticación.
    """
    service = AssistenceService()
    resultado = await service.generar_qr_evento(id_evento, url_front)
    
    if "error" in resultado:
        raise HTTPException(
            status_code=resultado.get("status", 500),
            detail=resultado["error"]
        )
    
    return {
        "status": "success",
        "message": "Código QR generado correctamente",
        "data": resultado
    }

@router.post("/registrar/{id_evento}")
async def registrar_asistencia(id_evento: str, datos: AsistenciaBase):
    """
    Registra la asistencia de un usuario en el evento.
    """
    correo = datos.correo_usuario
    print(correo)
    if not correo:
        raise HTTPException(status_code=400, detail="Faltan datos obligatorios")

    service = AssistenceService()
    resultado = await service.registrar_asistencia(id_evento, correo)
    if not resultado:
        raise HTTPException(status_code=500, detail="Error al registrar asistencia")
    if "error" in resultado:
        raise HTTPException(
            status_code=resultado.get("status", 500),
            detail=resultado["error"]
        )
    return {
        "status": "success",
        "message": resultado.get("mensaje", "Asistencia registrada correctamente"),
        "data": resultado.get("data", {})
    }


@router.get("/evento/{id_evento}")
async def obtener_asistencias_evento(
    id_evento: str,
    limit: int = Query(default=100, ge=1, le=500),
    _: Dict[str, Any] = Depends(get_current_admin_user)
):
    """
    Obtiene todas las asistencias de un evento.
    **Requiere autenticación ADMIN**.
    """
    service = AssistenceService()
    resultado = await service.obtener_asistencias_evento(id_evento, limit)
    
    if "error" in resultado:
        raise HTTPException(
            status_code=resultado.get("status", 500),
            detail=resultado["error"]
        )
    
    return {
        "status": "success",
        "message": "Asistencias obtenidas correctamente",
        "data": resultado
    }
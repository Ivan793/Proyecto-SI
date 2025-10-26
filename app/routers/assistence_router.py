from fastapi import APIRouter, HTTPException
from app.services.assistence_service import AssistenceService

router = APIRouter(prefix="/asistencia", tags=["Asistencia"])
service = AssistenceService()

@router.post("/generar_qr/{id_evento}")
async def generar_qr_evento(id_evento: str):
    """
    Genera un QR que lleva al registro de asistencia del evento.
    """
    url_front = "https://exposoftware.com"
    qr_data = await service.generar_qr_evento(id_evento, url_front)
    if not qr_data:
        raise HTTPException(status_code=500, detail="Error al generar el código QR")
    return qr_data

@router.post("/registrar/{id_evento}")
async def registrar_asistencia(id_evento: str, datos: dict):
    """
    Registra la asistencia de un usuario en el evento.
    """
    correo = datos.get("correo")

    if not correo:
        raise HTTPException(status_code=400, detail="Faltan datos obligatorios")

    resultado = await service.registrar_asistencia(id_evento, correo)
    if not resultado:
        raise HTTPException(status_code=500, detail="Error al registrar asistencia")
    return {"mensaje": "Asistencia registrada correctamente"}

from fastapi import APIRouter
from app.schemas.graduate import GraduateCreate, GraduateUpdate

router = APIRouter(prefix="/egresados", tags=["Egresados"])

@router.post("/", response_description="Egresado y usuario creados exitosamente")
def crear_egresado(data: GraduateCreate):
    return crear_egresado_controlador(data)

@router.get("/", response_description="Lista de egresados obtenida exitosamente")
def obtener_egresados():
    return obtener_todos_egresados_controlador()

@router.put("/{id_egresado}", response_description="Egresado actualizado exitosamente")
def actualizar_egresado(id_egresado: str, data: GraduateUpdate):
    return actualizar_egresado_controlador(id_egresado, data)

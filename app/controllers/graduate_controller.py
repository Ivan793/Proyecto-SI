from app.services.graduate_service import GraduateService
from app.schemas.graduate import GraduateCreate, GraduateUpdate

graduate_service = GraduateService()

def crear_egresado_controlador(data: GraduateCreate):
    return graduate_service.create_graduate(data)

def obtener_egresado_controlador(id_egresado: str):
    return graduate_service.get_graduate(id_egresado)

def obtener_todos_egresados_controlador():
    return graduate_service.get_all_graduates()

def actualizar_egresado_controlador(id_egresado: str, data: GraduateUpdate):
    return graduate_service.update_graduate(id_egresado, data)

def eliminar_egresado_controlador(id_egresado: str):
    return graduate_service.delete_graduate(id_egresado)

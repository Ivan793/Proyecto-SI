from fastapi import HTTPException, status
from app.repositories import graduate_repository, user_repository
from app.schemas.graduate import GraduateCreate, GraduateUpdate
from app.schemas.user import UserCreate


class GraduateService:
    def create_graduate(self, data: GraduateCreate):
        try:
            # ✅ Convertimos correctamente el modelo del usuario
            usuario_dict = data.usuario.model_dump() if hasattr(data.usuario, "model_dump") else dict(data.usuario)
            usuario_data = UserCreate(**usuario_dict)

            # 1️⃣ Crear el usuario primero
            nuevo_usuario = user_repository.create_user(usuario_data.model_dump())

            # ✅ Si el repo devuelve dentro de "data", tomamos el id de ahí
            id_usuario = (
                nuevo_usuario.get("id_usuario") or
                (nuevo_usuario.get("data", {}).get("id_usuario"))
            )

            if not id_usuario:
                raise ValueError("No se pudo obtener el id_usuario del nuevo usuario")

            # 2️⃣ Crear el egresado asociado a ese usuario
            egresado_data = {
                "id_usuario": id_usuario,
                "anio_finalizacion": data.anio_finalizacion,
                "titulado": data.titulado,
                "codigo_programa": data.codigo_programa
            }

            nuevo_egresado = graduate_repository.create(egresado_data)

            return {
                "mensaje": "✅ Egresado y usuario creados exitosamente",
                "usuario": nuevo_usuario,
                "egresado": nuevo_egresado
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al crear egresado: {str(e)}")

    def get_all_graduates(self):
        return graduate_repository.get_all()

    def get_graduate(self, id_egresado: str):
        egresado = graduate_repository.get_by_id(id_egresado)
        if not egresado:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Egresado no encontrado")
        return egresado

    def update_graduate(self, id_egresado: str, data: GraduateUpdate):
        return graduate_repository.update(id_egresado, data.model_dump(exclude_unset=True))

    def delete_graduate(self, id_egresado: str):
        return graduate_repository.delete(id_egresado)

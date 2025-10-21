# app/services/guest_service.py
from app.repositories import user_repository
from typing import Dict, List

# Simulación de base de datos de invitados
fake_guests_db: List[Dict] = []


class GuestService:
    def crear_invitado(self, data: Dict):
        """
        Crea un invitado junto con su usuario asociado (en cascada).
        """
        # 1️⃣ Crear usuario primero
        user_data = data.get("usuario")
        if not user_data:
            return {"error": "❌ Falta la información del usuario"}

        usuario_creado = user_repository.create_user(user_data)

        # 2️⃣ Crear invitado asociado al usuario
        nuevo_invitado = {
            "id_invitado": f"guest_{len(fake_guests_db) + 1}",
            "id_usuario": usuario_creado["data"]["id_usuario"],
            "empresa": data.get("empresa"),
            "cargo": data.get("cargo"),
            "motivo_visita": data.get("motivo_visita"),
        }
        fake_guests_db.append(nuevo_invitado)

        return {
            "mensaje": "✅ Invitado y usuario creados correctamente (simulado)",
            "usuario": usuario_creado["data"],
            "invitado": nuevo_invitado
        }

    def obtener_invitados(self):
        return fake_guests_db

    def actualizar_invitado(self, id_invitado: str, data: Dict):
        for invitado in fake_guests_db:
            if invitado["id_invitado"] == id_invitado:
                invitado.update(data)
                return {
                    "mensaje": "✅ Invitado actualizado correctamente",
                    "data": invitado
                }
        return {"error": "❌ Invitado no encontrado"}

    def eliminar_invitado(self, id_invitado: str):
        global fake_guests_db
        fake_guests_db = [
            i for i in fake_guests_db if i["id_invitado"] != id_invitado
        ]
        return {"mensaje": "🗑️ Invitado eliminado correctamente"}


# Instancia global
guest_service = GuestService()

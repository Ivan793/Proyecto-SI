# app/repositories/guest_repository.py
from typing import Dict, List

class GuestRepository:
    def __init__(self):
        # Simulación de base de datos en memoria
        self.fake_guests_db: List[Dict] = []

    # Crear invitado (creación en cascada simulada)
    def create_guest(self, data: Dict):
        new_guest = {
            "id_invitado": f"inv_{len(self.fake_guests_db) + 1}",
            "persona": data.get("persona"),
            "id_sector": data.get("id_sector"),
            "nombre_empresa": data.get("nombre_empresa")
        }
        self.fake_guests_db.append(new_guest)
        return {
            "mensaje": "✅ Invitado y persona creados exitosamente (simulado)",
            "data": new_guest
        }

    # Obtener todos los invitados
    def get_all_guests(self):
        return {
            "total": len(self.fake_guests_db),
            "invitados": self.fake_guests_db
        }

    # Actualizar invitado (en cascada simulada)
    def update_guest(self, id_invitado: str, data: Dict):
        for guest in self.fake_guests_db:
            if guest["id_invitado"] == id_invitado:
                if "persona" in data:
                    guest["persona"].update(data["persona"])
                if "id_sector" in data:
                    guest["id_sector"] = data["id_sector"]
                if "nombre_empresa" in data:
                    guest["nombre_empresa"] = data["nombre_empresa"]

                return {
                    "mensaje": "✅ Invitado y persona actualizados exitosamente (simulado)",
                    "data": guest
                }
        return {"mensaje": f"⚠️ No se encontró invitado con id {id_invitado}"}

    # Eliminar invitado
    def delete_guest(self, id_invitado: str):
        for guest in self.fake_guests_db:
            if guest["id_invitado"] == id_invitado:
                self.fake_guests_db = [
                    g for g in self.fake_guests_db if g["id_invitado"] != id_invitado
                ]
                return {"mensaje": f"✅ Invitado con id {id_invitado} eliminado correctamente"}
        return {"mensaje": f"⚠️ No se encontró invitado con id {id_invitado}"}

# ✅ Instancia global que otros módulos pueden importar
guest_repository = GuestRepository()

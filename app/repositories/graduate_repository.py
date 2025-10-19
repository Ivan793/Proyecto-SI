from typing import Dict, List

# Simulación de base de datos en memoria
fake_graduates_db: List[Dict] = []


def create(data: Dict):
    # Validamos que venga el id_usuario antes de crear
    if "id_usuario" not in data or not data["id_usuario"]:
        raise ValueError("Falta el campo id_usuario al crear egresado")

    new_graduate = {
        "id_egresado": f"grad_{len(fake_graduates_db) + 1}",
        "id_usuario": data["id_usuario"],  # ✅ aseguramos que se guarde correctamente
        "anio_finalizacion": data.get("anio_finalizacion"),
        "titulado": data.get("titulado"),
        "codigo_programa": data.get("codigo_programa")
    }

    fake_graduates_db.append(new_graduate)
    return new_graduate


def get_all():
    return {"total": len(fake_graduates_db), "egresados": fake_graduates_db}


def get_by_id(id_egresado: str):
    return next((g for g in fake_graduates_db if g["id_egresado"] == id_egresado), None)


def update(id_egresado: str, data: Dict):
    for graduate in fake_graduates_db:
        if graduate["id_egresado"] == id_egresado:
            graduate.update(data)
            return {
                "mensaje": "✅ Egresado actualizado exitosamente (simulado)",
                "data": graduate
            }
    return {"mensaje": f"⚠️ No se encontró egresado con id {id_egresado}"}


def delete(id_egresado: str):
    global fake_graduates_db
    fake_graduates_db = [g for g in fake_graduates_db if g["id_egresado"] != id_egresado]
    return {"mensaje": "🗑️ Egresado eliminado correctamente"}

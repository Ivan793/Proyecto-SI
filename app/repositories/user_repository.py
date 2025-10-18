# app/repositories/user_repository.py
from typing import Dict, List

# Simulación de base de datos en memoria
fake_users_db: List[Dict] = []

def create_user(data: Dict):
    new_user = {
        "id_usuario": f"user_{len(fake_users_db) + 1}",
        **data
    }
    fake_users_db.append(new_user)
    return {
        "mensaje": "✅ Usuario creado exitosamente (simulado)",
        "data": new_user
    }

def get_all_users():
    return fake_users_db

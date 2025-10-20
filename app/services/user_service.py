from typing import List, Optional
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.repositories import user_repository
import re
from datetime import date


def validate_email(email: str, rol: str):
    if rol in ("Docente", "Estudiante"):
        if not email.endswith("@unicesar.edu.co"):
            raise ValueError("El correo debe ser institucional (@unicesar.edu.co) para docentes y estudiantes.")
    elif not re.match(r"^[\w\.-]+@(gmail|hotmail|outlook|yahoo)\.com$", email):
        raise ValueError("Correo personal inválido. Solo se permiten Gmail, Hotmail, Outlook o Yahoo.")
    return email


def validate_password(password: str):
    if len(password) < 8 or len(password) > 12:
        raise ValueError("La contraseña debe tener entre 8 y 12 caracteres.")
    if "@" in password:
        raise ValueError("El carácter '@' no está permitido en la contraseña.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Debe contener al menos una letra mayúscula.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Debe contener al menos una letra minúscula.")
    if not re.search(r"\d", password):
        raise ValueError("Debe contener al menos un número.")
    if not re.search(r"[!#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        raise ValueError("Debe contener al menos un carácter especial.")
    return password


def validate_identification(identificacion: str):
    if not re.match(r"^[A-Za-z0-9]+$", identificacion):
        raise ValueError("La identificación solo puede contener letras y números, sin espacios ni símbolos.")
    return identificacion


def validate_phone(phone: str):
    if not re.match(r"^\+\d{10,15}$", phone):
        raise ValueError("Formato de teléfono inválido. Debe incluir el prefijo internacional, ejemplo: +57301343343.")
    return phone


def validate_birthdate(fecha_nacimiento: date):
    if fecha_nacimiento > date.today():
        raise ValueError("La fecha de nacimiento no puede ser posterior a la fecha actual.")
    return fecha_nacimiento


def create_user(user: UserCreate) -> UserResponse:
    # Validaciones de negocio
    user.identificacion = validate_identification(user.identificacion)
    user.telefono = validate_phone(user.telefono)
    user.correo = validate_email(user.correo, user.rol)
    user.contraseña = validate_password(user.contraseña)
    user.fecha_nacimiento = validate_birthdate(user.fecha_nacimiento)

    # Evitar duplicados (identificación o correo)
    users = user_repository.list_users()
    if any(u.identificacion == user.identificacion for u in users):
        raise ValueError("Ya existe un usuario con esta identificación.")
    if any(u.correo == user.correo for u in users):
        raise ValueError("Ya existe un usuario con este correo electrónico.")

    return user_repository.create_user(user)


def list_users() -> List[UserResponse]:
    return user_repository.list_users()


def get_user(user_id: str) -> Optional[UserResponse]:
    user = user_repository.get_user(user_id)
    if not user:
        raise ValueError(f"No se encontró un usuario con ID {user_id}.")
    return user


def update_user(user_id: str, user_data: UserUpdate) -> Optional[UserResponse]:
    # Validar existencia
    existing = user_repository.get_user(user_id)
    if not existing:
        raise ValueError(f"No se encontró un usuario con ID {user_id}.")

    # Validaciones si se envían nuevos datos
    if user_data.correo:
        user_data.correo = validate_email(user_data.correo, user_data.rol or existing.rol)
    if user_data.telefono:
        user_data.telefono = validate_phone(user_data.telefono)
    if user_data.identificacion:
        user_data.identificacion = validate_identification(user_data.identificacion)
    if user_data.contraseña:
        user_data.contraseña = validate_password(user_data.contraseña)
    if user_data.fecha_nacimiento:
        user_data.fecha_nacimiento = validate_birthdate(user_data.fecha_nacimiento)

    # Los nuevos campos que agregaste
    if user_data.departamento is None and hasattr(existing, "departamento"):
        user_data.departamento = existing.departamento
    if user_data.municipio is None and hasattr(existing, "municipio"):
        user_data.municipio = existing.municipio
    if user_data.direccion_residencia is None and hasattr(existing, "direccion_residencia"):
        user_data.direccion_residencia = existing.direccion_residencia
    if user_data.pais_residencia is None and hasattr(existing, "pais_residencia"):
        user_data.pais_residencia = existing.pais_residencia
    if user_data.nacionalidad is None and hasattr(existing, "nacionalidad"):
        user_data.nacionalidad = existing.nacionalidad

    return user_repository.update_user(user_id, user_data)


def delete_user(user_id: str) -> bool:
    if not user_repository.get_user(user_id):
        raise ValueError(f"No existe un usuario con ID {user_id}.")
    return user_repository.delete_user(user_id)

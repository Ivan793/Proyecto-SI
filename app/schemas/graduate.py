from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Dict
from datetime import datetime
import re

from app.schemas.types import *
from app.schemas.user import UserCreate
from app.core.constants import Defaults, ValidationMessages, Limits
from app.core.patterns import Patterns


class GraduateBase(BaseModel):
    codigo_programa: Optional[str] = None  
    programa_academico: Optional[AcademicProgram] = None  
    año_graduacion: Optional[GraduationYear] = None
    titulo_obtenido: Optional[DegreeTitle] = None
    titulado: Optional[bool] = None  

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "codigo_programa": "ING-SIS-001",
                "programa_academico": "Ingeniería de Sistemas",
                "año_graduacion": 2023,
                "titulo_obtenido": "Ingeniero de Sistemas",
                "titulado": True
            }
        }
    )


class GraduateCreate(UserCreate, GraduateBase):  # ✅ hereda de UserCreate
    @field_validator("correo")
    def validate_graduate_email(cls, v):
        """Valida formato de correo del egresado"""
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", v):
            raise ValueError(ValidationMessages.INVALID_EMAIL)
        return v

    @field_validator("contraseña")
    def validate_password_strength(cls, v):
        """Valida la fortaleza de la contraseña"""
        base_pattern = Patterns.PASSWORD.rstrip('$')
        full_pattern = f"{base_pattern}.{{{Limits.PASSWORD_MIN},{Limits.PASSWORD_MAX}}}$"
        if not re.match(full_pattern, v):
            raise ValueError(ValidationMessages.INVALID_PASSWORD)
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tipo_documento": DocumentType.CC,
                "identificacion": "1002431808",
                "primer_nombre": "David",
                "segundo_nombre": "José",
                "primer_apellido": "Rodríguez",
                "segundo_apellido": "González",
                "sexo": Sex.HOMBRE,
                "identidad_sexual": "Heterosexual",
                "fecha_nacimiento": "2000-06-03",
                "nacionalidad": "Colombiana",
                "pais_residencia": "Colombia",
                "departamento": "Cesar",
                "municipio": "Valledupar",
                "ciudad_residencia": "Valledupar",
                "direccion_residencia": "Calle 45 #22-10",
                "telefono": "+57301343343",
                "correo": "egresado@unicesar.edu.co",
                "contraseña": "Egresado123#",
                "rol": Role.EGRESADO,
                "codigo_programa": "ING-SIS-001",
                "programa_academico": "Ingeniería de Sistemas",
                "año_graduacion": 2023,
                "titulo_obtenido": "Ingeniero de Sistemas",
                "titulado": True
            }
        }
    )


class GraduateCreateExistingUser(GraduateBase):
    id_usuario: UserId

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_usuario": "abc12345",
                "codigo_programa": "ADM-EMP-002",
                "programa_academico": "Administración de Empresas",
                "año_graduacion": 2022,
                "titulo_obtenido": "Administrador de Empresas",
                "titulado": False
            }
        }
    )


# ✅ Aquí añadimos los campos del usuario para actualizar
class GraduateUpdate(BaseModel):
    # --- Campos de egresado ---
    codigo_programa: Optional[str] = None
    programa_academico: Optional[AcademicProgram] = None
    año_graduacion: Optional[GraduationYear] = None
    titulo_obtenido: Optional[DegreeTitle] = None
    titulado: Optional[bool] = None

    # --- Campos del usuario (solo los que se pueden editar) ---
    primer_nombre: Optional[UserName] = None
    segundo_nombre: Optional[UserName] = None
    primer_apellido: Optional[UserName] = None
    segundo_apellido: Optional[UserName] = None
    sexo: Optional[UserSex] = None
    identidad_sexual: Optional[UserSexualIdentity] = None
    fecha_nacimiento: Optional[datetime] = None
    nacionalidad: Optional[UserNationality] = None
    pais_residencia: Optional[UserCountry] = None
    departamento: Optional[UserDepartment] = None
    municipio: Optional[UserMunicipality] = None
    ciudad_residencia: Optional[UserCity] = None
    direccion_residencia: Optional[UserAddress] = None
    telefono: Optional[UserPhone] = None
    contraseña: Optional[UserPassword] = None
    activo: Optional[StatusActive] = None
    razon_desactivacion: Optional[ReasonText] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "codigo_programa": "ING-SIS-001",
                "programa_academico": "Ingeniería de Sistemas",
                "año_graduacion": 2023,
                "titulo_obtenido": "Ingeniero de Sistemas",
                "titulado": False,
                "primer_nombre": "juancho",
                "segundo_nombre": "juan",
                "primer_apellido": "quintero",
                "segundo_apellido": "quintero",
                "telefono": "+573128492382",
                "activo": True
            }
        }
    )


class GraduateResponse(BaseModel):
    id_egresado: GraduateId
    id_usuario: UserId
    codigo_programa: Optional[str] = None
    programa_academico: Optional[AcademicProgram] = None
    año_graduacion: Optional[GraduationYear] = None
    titulo_obtenido: Optional[DegreeTitle] = None
    titulado: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class GraduateWithUserResponse(BaseModel):
    egresado: GraduateResponse
    usuario: Dict

    model_config = ConfigDict(from_attributes=True)

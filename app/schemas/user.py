from pydantic import BaseModel, field_validator, ConfigDict, model_validator
from typing import Any, Dict, Optional, ClassVar
from datetime import datetime

# Importar tipos Annotated
from app.schemas.types import *
from app.core.patterns import Patterns
from app.core.constants import ValidationMessages, Limits, Defaults
from app.core.validators import UserValidatorMixin, BaseValidators

class UserBase(BaseModel, UserValidatorMixin):
    tipo_documento: UserDocumentType
    identificacion: UserIdentification
    primer_nombre: UserName
    segundo_nombre: Optional[UserName] = None
    primer_apellido: UserName
    segundo_apellido: Optional[UserName] = None
    sexo: UserSex
    identidad_sexual: UserSexualIdentity
    fecha_nacimiento: datetime
    nacionalidad: UserNationality
    pais_residencia: UserCountry
    departamento: UserDepartment
    municipio: UserMunicipality
    ciudad_residencia: UserCity
    direccion_residencia: UserAddress
    telefono: UserPhone
    correo: UserEmail
    rol: UserRole
    activo: StatusActive = Field(default=Defaults.ACTIVE_STATUS)
    razon_desactivacion: Optional[ReasonText] = None

    @model_validator(mode='after')
    def validate_deactivation_logic(self) -> 'UserBase':
        """Valida lógica de negocio para desactivación"""
        if not self.activo and not self.razon_desactivacion:
            raise ValueError(
                "Debe proporcionar una razón al desactivar el usuario"
            )
        
        # Limpiar razón si está activo
        if self.activo and self.razon_desactivacion:
            self.razon_desactivacion = None
            
        return self


    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tipo_documento": DocumentType.CC,
                "identificacion": "1023456789",
                "primer_nombre": "David",
                "segundo_nombre": "Jose",
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
                "direccion_residencia": "Calle 45 #22-10, Barrio San Jose",
                "telefono": "+57301343343",
                "correo": "david.rodriguez@unicesar.edu.co",
                "contraseña" : "Prueba123#",
                "rol": Role.ESTUDIANTE,
                "activo": True,
                "razon_desactivacion": None
            }
        }
    )

class UserCreate(UserBase):
    contraseña: UserPassword

    @field_validator('contraseña')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Valida fortaleza de la contraseña."""
        return BaseValidators.validate_password_complexity(v)


class UserUpdate(BaseModel):    
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

    @model_validator(mode='after')
    def validate_update_rules(self) -> 'UserUpdate':
        """Valida reglas de negocio para actualización."""
        update_fields = self.model_dump(exclude_unset=True, exclude_none=True)
        
        # Validar que se envíe al menos un campo
        if not update_fields:
            raise ValueError("Debe proporcionar al menos un campo para actualizar")
        
        # Validar lógica de desactivación
        if self.activo is False and not self.razon_desactivacion:
            raise ValueError("Debe proporcionar una razón al desactivar")
            
        return self

    # Validadores opcionales para actualización
    @field_validator('primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido')
    @classmethod
    def transform_names_optional(cls, v: Optional[str]) -> Optional[str]:
        """Transforma nombres si se proporcionan."""
        if v is None:
            return None
        return BaseValidators.transform_text_fields(v)
    
    @field_validator('contraseña')
    @classmethod
    def validate_password_complexity_optional(cls, v: Optional[str]) -> Optional[str]:
        """Valida complejidad de contraseña si se proporciona."""
        if v is None:
            return None
        return BaseValidators.validate_password_complexity(v)
    


class UserResponse(UserBase):    
    id_usuario: UserId
    activo: bool = Field(default=Defaults.ACTIVE_STATUS)
    razon_desactivacion: Optional[ReasonText] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class UserBasicInfo(BaseModel):
    """Información básica del usuario reutilizable para todos los roles"""
    id_usuario: Optional[UserId] = None
    nombre_completo: str = Field(description="Nombre completo del usuario")
    identificacion: UserIdentification
    correo: UserEmail
    telefono: Optional[UserPhone] = None
    activo: Optional[StatusActive] = True
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_usuario": "user_456def",
                "nombre_completo": "Juan Carlos Pérez González",
                "identificacion": "1023456789",
                "correo": "juan.perez@unicesar.edu.co",
                "telefono": "+57301343343",
                "activo": True
            }
        }
    )

    @classmethod
    def from_user_data(cls, user_data: Dict[str, Any]) -> 'UserBasicInfo':
        """Crea UserBasicInfo a partir de datos de usuario de Firestore"""
        return cls(
            id_usuario=user_data.get("id_usuario") or user_data.get("id"),
            nombre_completo=f"{user_data.get('primer_nombre', '')} {user_data.get('segundo_nombre', '')} {user_data.get('primer_apellido', '')} {user_data.get('segundo_apellido', '')}".strip(),
            identificacion=user_data.get('identificacion', ''),
            correo=user_data.get('correo', ''),
            telefono=user_data.get('telefono'),
            activo=user_data.get('activo', True)
        )
import logging
from firebase_admin import auth as firebase_auth

from app.exceptions.base_exceptions import ValidationException
from app.exceptions.user_exceptions import (
    InvalidEmailDomainException,
    UserAlreadyExistsException
)
from app.repositories.user_repository import UserRepository
from app.core.validators import validate_user_role_email_match
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)


class UserValidators:
    """
    Validadores comunes para usuarios de cualquier rol.
    
    Args:
        user_repo: Repositorio de usuarios (inyectado)
    """
    
    def __init__(self, user_repo: UserRepository = None):
        self.user_repo = user_repo or UserRepository()
    
    async def validate_role(self, usuario_data: UserCreate, expected_role: str) -> None:
        """
        Valida que el rol coincida con el esperado.
        
        Args:
            usuario_data: Datos del usuario
            expected_role: Rol esperado
        
        Raises:
            ValidationException: Si el rol no coincide
        """
        if usuario_data.rol != expected_role:
            raise ValidationException(
                message=f"El rol debe ser '{expected_role}' para este endpoint",
                field="rol"
            )
        logger.debug(f"Rol validado: {expected_role}")
    
    async def validate_unique_identification(self, identificacion: str) -> None:
        """
        Valida que la identificación sea única en el sistema.
        
        Args:
            identificacion: Número de identificación
        
        Raises:
            UserAlreadyExistsException: Si ya existe
        """
        existing_by_id = await self.user_repo.get_by_field(
            "identificacion", 
            identificacion
        )
        if existing_by_id:
            raise UserAlreadyExistsException(
                field="identificacion", 
                value=identificacion
            )
        logger.debug(f"Identificación única validada: {identificacion}")
    
    async def validate_unique_email(self, correo: str) -> None:
        """
        Valida que el correo sea único en Firestore y Firebase Auth.
        
        Args:
            correo: Correo electrónico
        
        Raises:
            UserAlreadyExistsException: Si ya existe
        """
        # Validar correo único en Firestore
        existing_user = await self.user_repo.get_user_by_email(correo)
        if existing_user:
            raise UserAlreadyExistsException(
                field="correo", 
                value=correo
            )
        
        # Validar correo único en Firebase Auth
        if await self._email_exists_in_firebase_auth(correo):
            raise UserAlreadyExistsException(
                field="correo", 
                value=correo
            )
        
        logger.debug(f"Correo único validado: {correo}")
    
    async def validate_email_domain(self, correo: str, rol: str) -> None:
        """
        Valida que el dominio del correo coincida con el rol.
        
        Args:
            correo: Correo electrónico
            rol: Rol del usuario
        
        Raises:
            InvalidEmailDomainException: Si el dominio no corresponde
        """
        try:
            validate_user_role_email_match(correo, rol)
            logger.debug(f"Dominio de correo validado para rol {rol}: {correo}")
        except ValueError as e:
            raise InvalidEmailDomainException(
                role=rol, 
                custom_message=str(e)
            )
    
    async def validate_user_uniqueness(self, usuario_data: UserCreate) -> None:
        """
        Valida que identificación y correo sean únicos.
        Agrupa las validaciones de unicidad para optimizar.
        
        Args:
            usuario_data: Datos del usuario
        
        Raises:
            UserAlreadyExistsException: Si ya existe
        """
        await self.validate_unique_identification(usuario_data.identificacion)
        await self.validate_unique_email(usuario_data.correo)
    
    async def validate_all_user_fields(self, usuario_data: UserCreate, expected_role: str) -> None:
        """
        Ejecuta todas las validaciones de usuario en orden lógico.
        
        Args:
            usuario_data: Datos del usuario a validar
            expected_role: Rol esperado del usuario
        
        Raises:
            ValidationException: Si alguna validación falla
            UserAlreadyExistsException: Si el usuario ya existe
            InvalidEmailDomainException: Si el dominio no corresponde
        """
        await self.validate_role(usuario_data, expected_role)
        await self.validate_user_uniqueness(usuario_data)
        await self.validate_email_domain(usuario_data.correo, usuario_data.rol)
        logger.info(f"Todas las validaciones de usuario completadas: {usuario_data.correo}")
    
    async def _email_exists_in_firebase_auth(self, email: str) -> bool:
        """
        Verifica si el email existe en Firebase Authentication.
        
        Args:
            email: Correo electrónico
        
        Returns:
            True si existe, False en caso contrario
        """
        try:
            firebase_auth.get_user_by_email(email)
            return True
        except firebase_auth.UserNotFoundError:
            return False
        except Exception as e:
            logger.warning(f"Error verificando email en Firebase Auth: {str(e)}")
            return False
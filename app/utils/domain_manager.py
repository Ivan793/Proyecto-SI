from typing import List, Dict
import logging

from app.core.constants import EmailDomains

logger = logging.getLogger(__name__)


class DomainManager:
    """
    Gestor de dominios de correo institucionales.
    Permite modificar dominios permitidos en tiempo de ejecución.
    """
    
    @classmethod
    def get_allowed_domains(cls, role: str) -> List[str]:
        """Obtiene dominios permitidos para un rol."""
        return EmailDomains.get_allowed_domains(role)
    
    @classmethod
    def add_domain_for_role(cls, role: str, domain: str) -> bool:
        """Agrega un nuevo dominio para un rol específico."""
        try:
            EmailDomains.add_domain_for_role(role, domain)
            logger.info(f"Dominio '{domain}' agregado para rol '{role}'")
            return True
        except Exception as e:
            logger.error(f"Error agregando dominio: {str(e)}")
            return False
    
    @classmethod
    def remove_domain_for_role(cls, role: str, domain: str) -> bool:
        """Elimina un dominio para un rol específico."""
        try:
            if role.upper() in EmailDomains.ALLOWED_DOMAINS:
                if domain in EmailDomains.ALLOWED_DOMAINS[role.upper()]:
                    EmailDomains.ALLOWED_DOMAINS[role.upper()].remove(domain)
                    logger.info(f"Dominio '{domain}' eliminado para rol '{role}'")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error eliminando dominio: {str(e)}")
            return False
    
    @classmethod
    def get_all_domains_config(cls) -> Dict[str, List[str]]:
        """Obtiene toda la configuración de dominios."""
        return EmailDomains.ALLOWED_DOMAINS.copy()
    
    @classmethod
    def validate_email_for_role(cls, email: str, role: str) -> bool:
        """Valida si un email es válido para un rol."""
        return EmailDomains.is_domain_allowed(email, role)
    
    @classmethod
    def update_domains_for_role(cls, role: str, domains: List[str]) -> bool:
        """Actualiza todos los dominios para un rol."""
        try:
            EmailDomains.ALLOWED_DOMAINS[role.upper()] = domains
            logger.info(f"Dominios actualizados para rol '{role}': {domains}")
            return True
        except Exception as e:
            logger.error(f"Error actualizando dominios: {str(e)}")
            return False


# Ejemplos de uso:
"""
# Agregar nuevo dominio para docentes
DomainManager.add_domain_for_role("DOCENTE", "@nuevodominio.edu.co")

# Ver dominios permitidos para estudiantes
domains = DomainManager.get_allowed_domains("ESTUDIANTE")

# Validar email específico
is_valid = DomainManager.validate_email_for_role("usuario@nuevodominio.edu.co", "DOCENTE")
"""
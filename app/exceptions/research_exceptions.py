from .base_exceptions import NotFoundException, ConflictException, ValidationException

# ==================== LÍNEA DE INVESTIGACIÓN ====================

class ResearchLineNotFoundException(NotFoundException):
    """Línea de investigación no encontrada"""
    
    def __init__(self, line_code: int):
        super().__init__(
            resource="Línea de investigación",
            identifier=str(line_code)
        )

class ResearchLineAlreadyExistsException(ConflictException):
    """Línea de investigación ya existe"""
    
    def __init__(self, line_code: int):
        super().__init__(
            message=f"Ya existe una línea de investigación con código {line_code}",
            conflict_field="codigo_linea"
        )

# ==================== SUBLÍNEA DE INVESTIGACIÓN ====================

class SubResearchLineNotFoundException(NotFoundException):
    """Sublínea de investigación no encontrada"""
    
    def __init__(self, subline_code: int):
        super().__init__(
            resource="Sublínea de investigación",
            identifier=str(subline_code)
        )

class SubResearchLineAlreadyExistsException(ConflictException):
    """Sublínea de investigación ya existe"""
    
    def __init__(self, subline_name: str):
        super().__init__(
            message=f"Ya existe una sublínea con el nombre '{subline_name}'",
            conflict_field="nombre_sublinea"
        )

class InvalidResearchLineException(ValidationException):
    """Línea de investigación inválida"""
    
    def __init__(self, line_code: int):
        super().__init__(
            message=f"La línea de investigación {line_code} no existe",
            field="codigo_linea"
        )

# ==================== ÁREA TEMÁTICA ====================

class ThematicAreaNotFoundException(NotFoundException):
    """Área temática no encontrada"""
    
    def __init__(self, area_code: int):
        super().__init__(
            resource="Área temática",
            identifier=str(area_code)
        )

class ThematicAreaAlreadyExistsException(ConflictException):
    """Área temática ya existe"""
    
    def __init__(self, area_name: str):
        super().__init__(
            message=f"Ya existe un área temática con el nombre '{area_name}'",
            conflict_field="nombre_area"
        )

class InvalidSubResearchLineException(ValidationException):
    """Sublínea de investigación inválida"""
    
    def __init__(self, subline_code: int):
        super().__init__(
            message=f"La sublínea de investigación {subline_code} no existe",
            field="codigo_sublinea"
        )

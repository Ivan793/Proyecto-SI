class Patterns:
    """Expresiones regulares reutilizables para validaciones."""
    IDENTIFICATION = r"^[A-Za-z0-9]+$"
    ADDRESS = r"^[A-Za-z0-9#\-\s,]+$"
    PHONE = r"^\+?\d+$"
    PASSWORD = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@#$%^&+=!*()_\-{}\[\]:;<>,.?/~`|\\]).*$"
    NAME = r"^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$"
    PROGRAM_CODE = r"^[A-Z0-9_]+$"
    # Email básico
    EMAIL = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    EMAIL_INSTITUTIONAL = r"^[a-zA-Z0-9_.+-]+@unicesar\.edu\.co$"
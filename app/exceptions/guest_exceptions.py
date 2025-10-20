# app/exceptions/guest_exceptions.py

class GuestNotFoundException(Exception):
    def __init__(self, guest_id: str):
        self.guest_id = guest_id
        super().__init__(f"Invitado con id {guest_id} no encontrado")


class GuestAlreadyExistsException(Exception):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Invitado con email {email} ya existe")

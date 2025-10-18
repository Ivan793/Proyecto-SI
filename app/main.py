from fastapi import FastAPI
from app.routers import student_router, guest_router, graduate_router

app = FastAPI(
    title="API de Gestión de Usuarios - Universidad Popular del Cesar",
    description="API para la gestión de estudiantes, invitados y egresados. Versión de prueba sin base de datos.",
    version="2.1.0"
)

app.include_router(student_router.router)
app.include_router(guest_router.router)
app.include_router(graduate_router.router)

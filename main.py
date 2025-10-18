from fastapi import FastAPI
from app.routers import proyect_router
app = FastAPI(title="Gestión de proyectos - FastAPI en Capas")

app.include_router(proyect_router.router)

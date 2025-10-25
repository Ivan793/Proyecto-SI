from fastapi import FastAPI
import logging
from app.routers.teacher_router import router as teacher_router

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Proyecto-SI")

# ✅ Registrar el router correctamente
app.include_router(teacher_router)

@app.on_event("startup")
def _print_routes():
    logging.info("Rutas registradas: %s", [r.path for r in app.routes])

@app.get("/")
def root():
    return {"message": "API conectada"}

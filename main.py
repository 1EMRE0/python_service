# python_service/main.py
import os
import sys
import sys
import shutil

print("Python:", sys.executable)
print("PATH:", shutil.which("piper"))

# Windows üzerinde sanal ortamdaki NVIDIA CUDA DLL'lerini sisteme tanıtır
if sys.platform == "win32":
    venv_base = os.path.dirname(sys.executable)
    nvidia_bin_dirs = [
        os.path.join(venv_base, "Lib", "site-packages", "nvidia", "cublas", "bin"),
        os.path.join(venv_base, "Lib", "site-packages", "nvidia", "cudnn", "bin"),
    ]
    for d in nvidia_bin_dirs:
        if os.path.exists(d):
            os.add_dll_directory(d)
from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

from api.v1.websocket import process_executor, router as ws_router
from config.settings import settings
from core.logging import logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Uygulama yaşam döngüsü yöneticisi.
    Başlangıçta loglama kurulur, kapanışta ProcessPool temizlenir.
    """
    setup_logging()
    logger.info("IoT Voice Order Sunucusu Başlatılıyor...")
    yield
    logger.info("Sunucu Kapatılıyor, Kaynaklar Temizleniyor...")
    process_executor.shutdown(wait=True)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# WebSocket Router'ı Entegre Et
app.include_router(ws_router)


@app.get("/health")
async def health_check():
    """Sistem durum kontrol endpoint'i."""
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.WS_HOST,
        port=settings.WS_PORT,
        reload=settings.DEBUG
    )
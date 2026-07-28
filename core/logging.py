# python_service/core/logging.py
import sys
from loguru import logger
from python_service.config.settings import settings


def setup_logging():
    """
    Loguru konfigürasyonu.
    Uygulama genelinde standart ve biçimlendirilmiş loglama sağlar.
    """
    # Standart log handler'ını temizle
    logger.remove()

    # Konsol Çıktısı (Formatlı ve Renkli)
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # Konsola yazma handler'ı
    logger.add(
        sys.stdout,
        level="DEBUG" if settings.DEBUG else "INFO",
        format=log_format,
        colorize=True,
    )

    # İleride logları dosyaya kaydetmek istersen:
    logger.add(
        "logs/system.log",
        rotation="10 MB",  # 10 MB olunca yeni dosyaya geç
        retention="7 days", # 7 günden eski logları sil
        level="INFO",
        enqueue=True,     # Asenkron/Thread-safe yazma için kritik
    )

    logger.info(f"{settings.PROJECT_NAME} v{settings.VERSION} loglama sistemi başlatıldı.")


# Kolay erişim için logger'ı dışa aktar
__all__ = ["logger", "setup_logging"]
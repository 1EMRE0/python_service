# python_service/tts/piper_engine.py
import asyncio
from pathlib import Path
from config.settings import settings
from core.logging import logger


class PiperTTSEngine:
    def __init__(self):
        # python_service/tts/piper_engine.py -> parent.parent bizi python_service kök dizinine götürür
        base_dir = Path(__file__).resolve().parent.parent
        model_file = Path(settings.PIPER_VOICE_MODEL)

        if not model_file.is_absolute():
            self.model_path = str(base_dir / model_file)
        else:
            self.model_path = str(model_file)

        logger.info(f"Piper TTS Model Yolu: {self.model_path}")

    async def synthesize(self, text: str) -> bytes:
        """
        Gelen metni Piper C++ / ONNX CLI aracılığıyla sentezleyip
        ham PCM baytları olarak döndürür.
        """
        if not text:
            logger.warning("TTS'e boş metin gönderildi, sentezleme atlandı.")
            return b""

        try:
            cmd = [
                "piper",
                "--model", self.model_path,
                "--output_raw"  # WAV başlığı olmadan ham 16kHz PCM üretir
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await proc.communicate(input=text.encode("utf-8"))

            if proc.returncode != 0:
                logger.error(f"Piper TTS Alt Süreç Hatası: {stderr.decode('utf-8', errors='ignore')}")
                return b""

            logger.info(f"TTS Sentezleme Başarılı ({len(stdout)} bayt PCM üretildi)")
            return stdout

        except FileNotFoundError:
            logger.error("Piper çalıştırılabilir dosyası bulunamadı.")
            return b""
        except Exception as e:
            logger.error(f"TTS Asenkron İşlem Hatası: {e}")
            return b""
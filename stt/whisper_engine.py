# python_service/stt/whisper_engine.py
import io
import wave
import os
import sys
import asyncio
from concurrent.futures import ProcessPoolExecutor
from faster_whisper import WhisperModel
from config.settings import settings
from core.logging import logger

# Windows üzerinde alt süreçlerde CUDA DLL yollarını ekler (GPU kullanımı için)
if sys.platform == "win32":
    venv_base = os.path.dirname(sys.executable)
    cublas_path = os.path.join(venv_base, "Lib", "site-packages", "nvidia", "cublas", "bin")
    cudnn_path = os.path.join(venv_base, "Lib", "site-packages", "nvidia", "cudnn", "bin")
    
    if os.path.exists(cublas_path):
        try:
            os.add_dll_directory(cublas_path)
        except AttributeError:
            pass
        os.environ["PATH"] = cublas_path + os.pathsep + os.environ.get("PATH", "")
    if os.path.exists(cudnn_path):
        try:
            os.add_dll_directory(cudnn_path)
        except AttributeError:
            pass
        os.environ["PATH"] = cudnn_path + os.pathsep + os.environ.get("PATH", "")


def _pcm_to_wav(pcm_bytes: bytes, sample_rate: int = 16000, channels: int = 1, sample_width: int = 2) -> bytes:
    """Ham PCM baytlarına bellekte WAV başlığı (header) ekler."""
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return wav_io.getvalue()


def _run_transcribe(audio_bytes: bytes, model_size: str, device: str, compute_type: str) -> str:
    """
    Ayrı proseste çalışacak senkron STT fonksiyonu.
    """
    try:
        wav_bytes = _pcm_to_wav(
            audio_bytes, 
            sample_rate=settings.SAMPLE_RATE, 
            channels=settings.CHANNELS
        )
        audio_stream = io.BytesIO(wav_bytes)

        model = WhisperModel(model_size, device=device, compute_type=compute_type)

        # Whisper'a duyacağı muhtemel kelimeleri ipucu veriyoruz
        menu_prompt = "Restoran menü siparişi: hamburger, pizza, kola, zero kola, fanta, sprite, patates kızartması, su, ayran."

        segments, _ = model.transcribe(
            audio_stream, 
            language="tr", 
            beam_size=5,
            vad_filter=True,
            initial_prompt=menu_prompt  # <-- MENÜ İPUCU
        )

        text = " ".join([segment.text for segment in segments]).strip()
        return text
    except Exception as e:
        logger.error(f"STT Senkron Çıkarım Hatası: {e}")
        return ""


class WhisperSTTEngine:
    def __init__(self, executor: ProcessPoolExecutor = None):
        self.executor = executor

    async def transcribe(self, audio_bytes: bytes) -> str:
        if not audio_bytes:
            logger.warning("STT'ye boş ses verisi gönderildi, işlem atlanıyor.")
            return ""

        try:
            loop = asyncio.get_running_loop()
            text = await loop.run_in_executor(
                self.executor,
                _run_transcribe,
                audio_bytes,
                settings.STT_MODEL_SIZE,
                settings.STT_DEVICE,
                settings.STT_COMPUTE_TYPE
            )
            return text
        except asyncio.CancelledError:
            logger.warning("STT işlemi iptal edildi (Sunucu durduruldu veya istemci ayrıldı).")
            raise
        except Exception as e:
            logger.error(f"STT Asenkron İşlem Hatası: {e}")
            return ""
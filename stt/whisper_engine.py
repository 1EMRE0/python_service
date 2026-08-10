import io
import wave
import os
import sys
import asyncio
from concurrent.futures import ProcessPoolExecutor
from faster_whisper import WhisperModel
from config.settings import settings
from core.logging import logger

# Windows CUDA DLL yolları
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


def _pcm_to_wav(pcm_bytes: bytes, sample_rate: int, channels: int = 1, sample_width: int = 2) -> bytes:
    """Ham PCM baytlarına bellekte WAV başlığı (header) ekler."""
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return wav_io.getvalue()


# Modül yüklendiğinde modeli Global/Cache seviyesinde BİR KERE yüklüyoruz (Her istekte yüklenmesini önler)
_whisper_model_instance = None

def _get_whisper_model(model_size: str, device: str, compute_type: str) -> WhisperModel:
    global _whisper_model_instance
    if _whisper_model_instance is None:
        logger.info(f"Whisper Modeli Yükleniyor: {model_size} ({device} - {compute_type})...")
        _whisper_model_instance = WhisperModel(model_size, device=device, compute_type=compute_type)
        logger.info("Whisper Modeli Başarıyla Yüklendi.")
    return _whisper_model_instance


def _run_transcribe(audio_bytes: bytes, model_size: str, device: str, compute_type: str, sample_rate: int) -> str:
    """Ayrı proseste çalışacak senkron STT fonksiyonu."""
    try:
        # 1. PCM -> WAV Dönüştürme
        wav_bytes = _pcm_to_wav(
            audio_bytes, 
            sample_rate=sample_rate, 
            channels=settings.CHANNELS
        )
        with open("gelen_ses_test.wav", "wb") as f:
            f.write(wav_bytes)
        logger.info("Test sesi 'gelen_ses_test.wav' olarak kaydedildi.")

        # --- DEBUG: Gelen sesi bilgisayara kaydet (Dinleyip kontrol etmek için) ---
        # with open("debug_last_recording.wav", "wb") as f:
        #     f.write(wav_bytes)

        audio_stream = io.BytesIO(wav_bytes)

        # 2. Modeli önbellekten al
        model = _get_whisper_model(model_size, device, compute_type)

        menu_prompt = "Restoran menü siparişi: hamburger, pizza, kola, zero kola, fanta, sprite, patates kızartması, su, ayran."

        # 3. Transkripsiyon (vad_filter=False yapıldı, hassasiyet artırıldı)
        segments, _ = model.transcribe(
            audio_stream, 
            language="tr", 
            beam_size=5,
            vad_filter=False,  # <-- VAD kapalı (sesin silinmesini engeller)
            initial_prompt=menu_prompt
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
                settings.STT_COMPUTE_TYPE,
                settings.SAMPLE_RATE  # ESP32 ile birebir aynı olmalı (Örn: 22050 veya 16000)
            )
            return text
        except asyncio.CancelledError:
            logger.warning("STT işlemi iptal edildi.")
            raise
        except Exception as e:
            logger.error(f"STT Asenkron İşlem Hatası: {e}")
            return ""
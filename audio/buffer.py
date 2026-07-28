# python_service/audio/buffer.py
from config.settings import settings
from core.logging import logger


class AudioBuffer:
    """
    ESP32'den gelen ham PCM (16kHz, 16-bit Mono) ses verisini güvenli
    şekilde bellekte tutan arabellekleme sınıfı.
    Bellek taşmasını engellemek için maksimum süre/boyut sınırı uygular.
    """
    def __init__(self, max_duration_seconds: int = 30):
        # 16kHz, 16-bit (2 bytes/sample), 1 kanal (mono)
        # 1 saniye = 16000 * 2 * 1 = 32,000 bytes
        self.bytes_per_second = settings.SAMPLE_RATE * 2 * settings.CHANNELS
        self.max_bytes = max_duration_seconds * self.bytes_per_second
        self._buffer = bytearray()

    def append(self, chunk: bytes) -> bool:
        """
        Gelen ses paketini arabelleğe ekler.
        Maksimum boyuta ulaşıldıysa eklemeyi durdurur ve False döner.
        """
        if len(self._buffer) + len(chunk) > self.max_bytes:
            logger.warning("Ses arabelleği maksimum boyuta ulaştı. Yeni paket reddedildi.")
            return False
            
        self._buffer.extend(chunk)
        return True

    def get_bytes(self) -> bytes:
        """Arabellekteki ses verisini değişmez (bytes) kopyası olarak döndürür."""
        return bytes(self._buffer)

    def clear(self):
        """Arabelleği temizler."""
        self._buffer.clear()

    @property
    def duration_seconds(self) -> float:
        """Arabellekte biriken sesin saniye cinsinden süresi."""
        return len(self._buffer) / self.bytes_per_second

    def is_empty(self) -> bool:
        """Arabellek boş mu kontrolü."""
        return len(self._buffer) == 0
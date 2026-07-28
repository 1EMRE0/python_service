# python_service/core/fsm.py
from python_service.schemas.state import SessionState
from python_service.core.logging import logger


class SessionFSM:
    """
    ESP32 cihazı ile sunucu arasındaki canlı oturumun durumunu yönetir.
    Geçersiz durum geçişlerini engeller.
    """
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.current_state = SessionState.IDLE
        self.cached_order_text: str = ""  # İlk verilen sipariş metni burada tutulur

    def transition_to(self, new_state: SessionState):
        """Durum geçişini kontrol eder ve loglar."""
        logger.info(f"[{self.device_id}] Durum Değişimi: {self.current_state.value} -> {new_state.value}")
        self.current_state = new_state

    def is_state(self, state: SessionState) -> bool:
        """Mevcut durum kontrolü."""
        return self.current_state == state

    def reset(self):
        """Oturumu başlangıç durumuna döndürür."""
        logger.debug(f"[{self.device_id}] Oturum sıfırlandı.")
        self.current_state = SessionState.IDLE
        self.cached_order_text = ""
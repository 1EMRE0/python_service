# python_service/schemas/state.py
from enum import Enum


class SessionState(str, Enum):
    IDLE = "IDLE"                                   # Boşta, ses beklemiyor
    LISTENING_ORDER = "LISTENING_ORDER"             # Kullanıcı ilk siparişi veriyor
    PROCESSING_STT = "PROCESSING_STT"               # Ses metne dönüştürülüyor
    CONFIRMING = "CONFIRMING"                       # TTS doğrulama sesi üretiliyor
    LISTENING_CONFIRMATION = "LISTENING_CONFIRMATION" # Kullanıcıdan "Evet/Hayır" bekleniyor
    PROCESSING_JSON = "PROCESSING_JSON"             # LLM siparişi JSON yapıyor
    COMPLETED = "COMPLETED"                         # İşlem başarıyla bitti
    ERROR = "ERROR"                                 # Hata oluştu
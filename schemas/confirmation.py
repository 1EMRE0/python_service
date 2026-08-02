from enum import Enum


class ConfirmationIntent(Enum):
    """
    Kullanıcının doğrulama cevabının sonucunu temsil eder.
    """

    CONFIRMED = "confirmed"   # Kullanıcı siparişi onayladı.
    REJECTED = "rejected"     # Kullanıcı siparişi reddetti / iptal etti.
    UNKNOWN = "unknown"       # Kullanıcının cevabı anlaşılamadı.
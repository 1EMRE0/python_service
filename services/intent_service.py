import re

from core.logging import logger
from schemas.confirmation import ConfirmationIntent


class IntentService:
    """
    Kullanıcının doğrulama aşamasındaki cevabını analiz eder.

    Bu servis LLM kullanmaz.
    Amaç mümkün olan en düşük gecikmeyle
    kullanıcının siparişi onaylayıp onaylamadığını belirlemektir.
    """

    # Regex'i her çağrıda yeniden oluşturmamak için
    CLEAN_PATTERN = re.compile(r"[^\w\s]", re.UNICODE)

    def __init__(self):

        self.positive_keywords = {
            "evet",
            "onaylıyorum",
            "doğru",
            "tamam",
            "olur",
            "aynen",
            "evet gönder",
            "siparişi ver",
            "onay",
            "tamamdır",
            "evet lütfen",
            "gönder",
            "olur gönder"
        }

        self.negative_keywords = {
            "hayır",
            "iptal",
            "vazgeçtim",
            "yanlış",
            "istemiyorum",
            "dur",
            "değiştir",
            "baştan"
        }

    def analyze_confirmation(self, text: str) -> ConfirmationIntent:
        """
        Kullanıcının cevabını analiz eder.

        Returns
        -------
        ConfirmationIntent.CONFIRMED
            Sipariş onaylandı.

        ConfirmationIntent.REJECTED
            Sipariş reddedildi veya iptal edildi.

        ConfirmationIntent.UNKNOWN
            Kullanıcının cevabı anlaşılamadı.
        """

        if not text:
            logger.debug("Boş doğrulama metni alındı.")
            return ConfirmationIntent.UNKNOWN

        normalized = text.lower().strip()
        normalized = self.CLEAN_PATTERN.sub("", normalized)

        words = set(normalized.split())

        # -----------------------------
        # 1) Negatif kontrol (öncelikli)
        # -----------------------------
        if words.intersection(self.negative_keywords):
            logger.info(f"Doğrulama Sonucu: REDDEDİLDİ ({normalized})")
            return ConfirmationIntent.REJECTED

        for keyword in self.negative_keywords:
            if keyword in normalized:
                logger.info(f"Doğrulama Sonucu: REDDEDİLDİ ({normalized})")
                return ConfirmationIntent.REJECTED

        # -----------------------------
        # 2) Pozitif kontrol
        # -----------------------------
        if words.intersection(self.positive_keywords):
            logger.info(f"Doğrulama Sonucu: ONAYLANDI ({normalized})")
            return ConfirmationIntent.CONFIRMED

        for keyword in self.positive_keywords:
            if keyword in normalized:
                logger.info(f"Doğrulama Sonucu: ONAYLANDI ({normalized})")
                return ConfirmationIntent.CONFIRMED

        logger.warning(f"Doğrulama anlaşılamadı: '{normalized}'")

        return ConfirmationIntent.UNKNOWN
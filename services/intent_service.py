# python_service/services/intent_service.py
import re
from logging import logger


class IntentService:
    """
    Kullanıcının doğrulama adımındaki ("evet", "onaylıyorum", "hayır", "iptal" vb.)
    cevaplarını LLM kullanmadan, alt-milisaniye seviyesinde analiz eden motor.
    """
    def __init__(self):
        # Olumlu onay anahtar kelime kümesi
        self.positive_keywords = {
            "evet", "onaylıyorum", "doğru", "tamam", "olur", 
            "aynen", "evet gönder", "siparişi ver", "onay", 
            "tamamdır", "evet lütfen", "gönder", "olur gönder"
        }
        # Olumsuz / İptal anahtar kelime kümesi
        self.negative_keywords = {
            "hayır", "iptal", "vazgeçtim", "yanlış", "istemiyorum", 
            "dur", "değiştir", "baştan"
        }

    def analyze_confirmation(self, text: str) -> bool:
        """
        Metni temizler ve onay içerip içermediğini kontrol eder.
        Returns:
            True  -> Olumlu Onay
            False -> Olumsuz / Anlaşılamadı / İptal
        """
        if not text:
            return False

        # Metin temizleme: Küçük harfe çevir ve noktalama işaretlerini kaldır
        normalized = text.lower().strip()
        normalized = re.sub(r'[^\w\s]', '', normalized)

        words = set(normalized.split())

        # 1. Doğrudan kelime kesişim kontrolü O(1)
        if words.intersection(self.positive_keywords):
            logger.info(f"Niyet Analizi: OLUMLU (Eşleşen metin: '{normalized}')")
            return True

        # 2. Cümle içinde alt dize (substring) kontrolü
        for pos in self.positive_keywords:
            if pos in normalized:
                logger.info(f"Niyet Analizi: OLUMLU (Alt dize eşleşti: '{pos}')")
                return True

        logger.info(f"Niyet Analizi: OLUMSUZ / ANLAŞILAMADI (Metin: '{normalized}')")
        return False
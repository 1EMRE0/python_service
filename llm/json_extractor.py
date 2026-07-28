# python_service/llm/json_extractor.py
import httpx
from config.settings import settings
from schemas.order import OrderSchema
from core.logging import logger


class LLMJsonExtractor:
    """
    Ollama altyapısındaki Qwen2.5 modelini kullanarak metinsel siparişi
    Pydantic şemasına %100 sadık JSON verisine dönüştüren servis.
    """
    def __init__(self):
        self.ollama_url = f"{settings.OLLAMA_BASE_URL}/api/generate"

    async def extract_order(self, text: str) -> OrderSchema:
        if not text:
            logger.warning("LLM'e boş metin gönderildi, boş sipariş döndürülüyor.")
            return OrderSchema(items=[])

        prompt = f"""Sen bir restoran sipariş ayrıştırıcısısın.
Aşağıdaki ses tanıma (STT) çıktısından sipariş edilen ürünleri ve adetlerini çıkar.

ÖNEMLİ KURAL: Ses tanıma sistemi kelimeleri yanlış algılamış olabilir. 
(Örneğin "dezir okul", "dekir", "dezir" gibi anlamsız ifadeler "zero kola" anlamına gelir. "pitsa" -> "pizza" vb.)
Ürün isimlerini standart restoran menüsü ürün adlarına (hamburger, zero kola, pizza vb.) dönüştür.

Sipariş Cümlesi: "{text}"
"""

        payload = {
            "model": settings.LLM_MODEL_NAME,
            "prompt": prompt,
            "format": OrderSchema.model_json_schema(),
            "stream": False
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(self.ollama_url, json=payload)
                response.raise_for_status()
                
                result_data = response.json()
                raw_json_str = result_data.get("response", "{}")
                
                validated_order = OrderSchema.model_validate_json(raw_json_str)
                logger.info(f"LLM Yapılandırılmış Çıktı Oluşturuldu: {validated_order.model_dump()}")
                return validated_order

            except httpx.HTTPError as http_err:
                logger.error(f"Ollama Bağlantı Hatası: {http_err}.")
                return OrderSchema(items=[])
            except Exception as e:
                logger.error(f"LLM JSON Çıkarma/Doğrulama Hatası: {e}")
                return OrderSchema(items=[])
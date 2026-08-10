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
        self.menu_items = [
            "Hamburger", "Pizza", "Kola", "Margarita Pizza", 
            "Cheeseburger", "Zero Kola", "Ayran", "Su", 
            "Çay", "Türk Kahvesi", "Filtre Kahve", "San Sebastian", 
            "Sufle", "Americano", "Bitki Çayı", "Sıcak Çikolata", "Latte"
        ]

    def _generate_prompt(self, text: str) -> str:
        menu_str = ", ".join([f'"{item}"' for item in self.menu_items])    

        prompt = f"""### ROL VEYA GÖREV
Sen profesyonel bir restoran sipariş ayrıştırıcısısın.
Görevin, Türkçe ses tanıma (STT) metnini analiz ederek müşterinin sipariş ettiği ürünleri ve adetlerini çıkarmaktır.

### MEVCUT RESTORAN MENÜSÜ
[{menu_str}]

### KESİN KURALLAR
1. **İSİM KİLİTLEME:** Yanıtındaki `name` alanı KESİNLİKLE yukarıda verilen MEVCUT RESTORAN MENÜSÜ listesindeki isimlerle HARFİ HARFİNE AYNI olmalıdır.

2. **TÜRKÇE OKUNUŞ & STT DÜZELTME REHBERİ:** 
   Ses tanıma sistemi yabancı isimli ürünleri Türkçe okunuşlarıyla ("çiz burger" gibi) metne dökebilir. Bunları menüdeki orijinal isimlerine dönüştür:
   - "çiz burger", "çizburger", "cizburger", "peynirli burger" -> "Cheeseburger"
   - "hamburger", "hanburger", "hemburger" -> "Hamburger"
   - "sen sebastyan", "sen sebatyan", "san sebatyan" -> "San Sebastian"
   - "filtre kehve", "filtre kave" -> "Filtre Kahve"
   - "pitsa", "piza" -> "Pizza"
   - "dezir okul", "dekir", "zero kola" -> "Zero Kola"
   - "amerikanı", "amerikano" -> "Americano"
   - "suflör", "sufle" -> "Sufle"

3. **ADET MANTIĞI:** Metinde geçen adetleri sayıya çevir ("iki" -> 2). Eğer adet belirtilmemişse varsayılan olarak 1 al.
4. **ÇIKTI BİÇİMİ:** Sadece istenen JSON yapısını döndür. Açıklama veya ekstra metin yazma.

### SİPARİŞ METNİ
"{text}"
"""
        return prompt

    async def extract_order(self, text: str) -> OrderSchema:
        if not text:
            logger.warning("LLM'e boş metin gönderildi, boş sipariş döndürülüyor.")
            return OrderSchema(items=[])

        prompt_text = self._generate_prompt(text)

        payload = {
            "model": settings.LLM_MODEL_NAME,
            "prompt": prompt_text,
            "format": OrderSchema.model_json_schema(),
            "stream": False
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
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
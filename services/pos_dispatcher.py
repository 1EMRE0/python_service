# python_service/services/pos_dispatcher.py
import httpx
from schemas.order import OrderSchema
from core.logging import logger
from config.settings import POS_API_URL  # settings.py dosyasından URL'i çekiyoruz


class POSDispatcher:
    """
    Onaylanmış sipariş JSON verisini yerel ASP.NET Core POS sunucusuna
    HTTP REST Webhook üzerinden ileten servis.
    """
    def __init__(self, target_url: str = None):
        # Dışarıdan URL verilmezse config/settings.py içindeki POS_API_URL kullanılır
        self.target_url = target_url or POS_API_URL

    def _format_table_number(self, device_id: str) -> str:
        """
        Cihaz ID'sini (örneğin 'esp32_5' veya '5') 'Masa 5' formatına getirir.
        """
        if not device_id:
            return "Masa 1"
        if "masa" in device_id.lower():
            return device_id.capitalize()
        
        # İçindeki sayıları ayıkla
        numbers = ''.join(filter(str.isdigit, device_id))
        return f"Masa {numbers}" if numbers else device_id

    async def dispatch_order(self, order: OrderSchema, device_id: str = str) -> bool:
        """
        Siparişi ASP.NET Core POS sisteminin beklediği DTO formatına çevirip POST eder.
        """
        if not order or not getattr(order, "items", None):
            logger.warning("Siparişte ürün bulunmadığından POS sistemine iletilmedi.")
            return False

        table_name = self._format_table_number(device_id)

        # C# DTO Formatını Hazırlama
        items_payload = []
        
        # OrderSchema içindeki items dictionary mi yoksa liste mi kontrol edip dönüştürelim
        if isinstance(order.items, dict):
            for product_name, quantity in order.items.items():
                items_payload.append({
                    "productName": str(product_name).capitalize(),
                    "quantity": int(quantity),
                    "price": 0
                })
        elif isinstance(order.items, list):
            for item in order.items:
                item_dict = item.model_dump() if hasattr(item, "model_dump") else item
                items_payload.append({
                    "productName": str(item_dict.get("productName") or item_dict.get("name") or "").capitalize(),
                    "quantity": int(item_dict.get("quantity", 1)),
                    "price": float(item_dict.get("price", 0))
                })

        payload = {
            "tableNumber": table_name,
            "items": items_payload
        }

        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                logger.info(f"Sipariş POS'a gönderiliyor ({table_name}) -> {self.target_url}")
                response = await client.post(self.target_url, json=payload)
                response.raise_for_status()
                
                logger.info(f"Sipariş Web/POS sistemine başarıyla iletildi ({table_name}).")
                return True
            except httpx.HTTPError as err:
                logger.error(f"POS Sistemine Erişilemedi ({self.target_url}): {err}")
                return False
            except Exception as e:
                logger.error(f"POS İletim Hatası: {e}")
                return False
# python_service/services/pos_dispatcher.py
import httpx
from python_service.schemas.order import OrderSchema
from python_service.core.logging import logger


class POSDispatcher:
    """
    Onaylanmış sipariş JSON verisini yerel Web/POS sunucusuna
    HTTP REST Webhook üzerinden ileten servis.
    """
    def __init__(self, target_url: str = "http://localhost:3000/api/orders"):
        self.target_url = target_url

    async def dispatch_order(self, order: OrderSchema) -> bool:
        """
        Siparişi Web/POS sistemine POST eder.
        """
        if not order.items:
            logger.warning("Siparişte ürün bulunmadığından POS sistemine iletilmedi.")
            return False

        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.post(self.target_url, json=order.model_dump())
                response.raise_for_status()
                logger.info(f"Sipariş Web/POS sistemine iletildi: {order.model_dump()}")
                return True
            except httpx.HTTPError as err:
                logger.error(f"POS Sistemine Erişilemedi ({self.target_url}): {err}")
                return False
            except Exception as e:
                logger.error(f"POS İletim Hatası: {e}")
                return False
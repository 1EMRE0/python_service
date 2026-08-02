import requests

TARGET_IP = "127.0.0.1"
PORT = 5095
ENDPOINT = "/api/orders/create"
URL = f"http://{TARGET_IP}:{PORT}{ENDPOINT}"

# ASP.NET Core tarafının beklediği birebir JSON formatı
sample_order = {
    "tableNumber": "Masa 4",
    "items": [
        {
            "productName": "Hamburger",
            "quantity": 2,
            
        },
        {
            "productName": "pizza",
            "quantity": 3,
            
        },
        {
                    "productName": "türk kahvesi",
                    "quantity": 3,
                    
                },
                {
                                    "productName": "zero kola",
                                    "quantity": 3,
                                    
                                },
                                {
                                                                    "productName": "kola",
                                                                    "quantity": 3,
                                                                    
                                                                },
        

    ]
}

headers = {
    "Content-Type": "application/json"
}

try:
    print(f"[+] Sipariş POS'a gönderiliyor -> {URL}")
    response = requests.post(URL, json=sample_order, headers=headers, timeout=5)
    
    print(f"Durum Kodu: {response.status_code}")
    print(f"Sunucu Yanıtı: {response.text}")

    if response.status_code in [200, 201]:
        print("\n[✓] TEBRİKLER! Sipariş POS sistemine başarıyla ulaştı.")

except Exception as e:
    print(f"[X] Bağlantı Hatası: {e}")
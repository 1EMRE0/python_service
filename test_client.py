# test_client.py
import asyncio
import json
import wave
import os
from pathlib import Path
import websockets

# WebSocket Sunucu Adresi
SERVER_URL = "ws://localhost:8000/ws/v1/audio/test_esp32_01"


def create_dummy_wav(filename: str, duration_sec: int = 2):
    """
    Test için 16kHz, 16-bit Mono sessiz/örnek bir WAV dosyası oluşturur.
    (Eğer elinizde gerçek ses kaydı yoksa çökmeden test etmeyi sağlar)
    """
    sample_rate = 16000
    num_samples = sample_rate * duration_sec
    
    # 2 saniyelik boş (0 değerli) PCM verisi
    raw_pcm = b'\x00\x00' * num_samples
    
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)        # Mono
        wf.setsampwidth(2)        # 16-bit (2 bytes)
        wf.setframerate(sample_rate) # 16kHz
        wf.writeframes(raw_pcm)


async def stream_audio_file(websocket, wav_file_path: str, chunk_size: int = 1024):
    """
    WAV dosyasını okur ve ESP32'nin I2S akışını simüle ederek 
    parça parça WebSocket üzerinden sunucuya gönderir.
    """
    print(f"\n[+] '{wav_file_path}' ses dosyası okunuyor ve gönderiliyor...")
    
    if not os.path.exists(wav_file_path):
        print(f"[!] '{wav_file_path}' bulunamadı, geçici dosya oluşturuluyor...")
        create_dummy_wav(wav_file_path)

    with wave.open(wav_file_path, "rb") as wf:
        sample_rate = wf.getframerate()
        channels = wf.getnchannels()
        
        print(f"    Sinyal Detayı: {sample_rate}Hz | {channels} Kanal")
        
        data = wf.readframes(chunk_size)
        total_sent = 0
        
        while len(data) > 0:
            # Ham PCM baytlarını sunucuya at
            await websocket.send(data)
            total_sent += len(data)
            # ESP32 canlı akışını simüle etmek için minik bir bekleme (10ms)
            await asyncio.sleep(0.01)
            data = wf.readframes(chunk_size)

        print(f"[✓] Toplam {total_sent} bayt PCM verisi akıtıldı.")

    # Akışın bittiğini bildiren JSON paketi
    end_payload = json.dumps({"event": "STREAM_END"})
    await websocket.send(end_payload)
    print("[->] 'STREAM_END' bildirimi gönderildi.")


async def run_test():
    siparis_wav = "siparis_test.wav"
    onay_wav = "onay_test.wav"

    # Test dosyaları yoksa otomatik oluştur
    if not os.path.exists(siparis_wav):
        create_dummy_wav(siparis_wav, duration_sec=3)
    if not os.path.exists(onay_wav):
        create_dummy_wav(onay_wav, duration_sec=2)

    print(f"[*] Sunucuya bağlanılıyor: {SERVER_URL}")
    
    try:
        async with websockets.connect(SERVER_URL) as ws:
            print("[✓] WebSocket Bağlantısı Başarılı!\n")

            # -------------------------------------------------------------
            # AŞAMA 1: İlk Sipariş Sesini Gönder ("1 Pizza 1 Kola İstiyorum")
            # -------------------------------------------------------------
            print("=================== 1. AŞAMA: SİPARİŞ AKIŞI ===================")
            await stream_audio_file(ws, siparis_wav)

            # Sunucudan Yanıt Bekle (JSON ve TTS Audio)
            print("\n[<--] Sunucudan onay sorusu bekleniyor...")
            while True:
                response = await ws.recv()
                
                # Metin / JSON Yanıtı
                if isinstance(response, str):
                    data = json.loads(response)
                    print(f"  [EVENT]: {data.get('event')} | Metin: '{data.get('text', '')}'")
                # İkili (Binary) Yanıt -> TTS PCM Ses Baytları
                else:
                    print(f"  [SES ALINDI]: Piper TTS'den {len(response)} bayt PCM sesi geldi.")
                    break

            # -------------------------------------------------------------
            # AŞAMA 2: Onay Sesini Gönder ("Evet / Onaylıyorum")
            # -------------------------------------------------------------
            print("\n=================== 2. AŞAMA: ONAY AKIŞI ===================")
            await asyncio.sleep(1.5)  # İki konuşma arası doğal es
            await stream_audio_file(ws, onay_wav)

            print("\n[<--] Nihai işlem yanıtı bekleniyor...")
            while True:
                response = await ws.recv()
                
                if isinstance(response, str):
                    data = json.loads(response)
                    print(f"\n[ÇIKTI EVENT]: {data.get('event')}")
                    if "payload" in data:
                        print(f"  [URETILEN JSON]:\n{json.dumps(data['payload'], indent=2, ensure_ascii=False)}")
                else:
                    print(f"  [SON SES ALINDI]: {len(response)} bayt onay/tamamlama TTS sesi alındı.")
                    break

            print("\n[✓] Test Başarıyla Tamamlandı!")

    except Exception as e:
        print(f"\n[X] Test Hatası: {e}")


if __name__ == "__main__":
    asyncio.run(run_test())
# python_service/api/v1/websocket.py
import json
from concurrent.futures import ProcessPoolExecutor
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from audio.buffer import AudioBuffer
from core.fsm import SessionFSM
from core.logging import logger
from llm.json_extractor import LLMJsonExtractor
from schemas.state import SessionState
from schemas.confirmation import ConfirmationIntent
from services.intent_service import IntentService
from services.pos_dispatcher import POSDispatcher
from stt.whisper_engine import WhisperSTTEngine
from tts.piper_engine import PiperTTSEngine

router = APIRouter()

# Global ProcessPool (İstek başına yeniden başlatıp CPU yormamak için)
process_executor = ProcessPoolExecutor(max_workers=2)

stt_engine = WhisperSTTEngine(executor=process_executor)
tts_engine = PiperTTSEngine()
intent_service = IntentService()
llm_extractor = LLMJsonExtractor()
pos_dispatcher = POSDispatcher()


@router.websocket("/ws/v1/audio/{device_id}")
async def websocket_audio_endpoint(websocket: WebSocket, device_id: str):
    await websocket.accept()
    fsm = SessionFSM(device_id)
    audio_buffer = AudioBuffer(max_duration_seconds=30)

    logger.info(f"ESP32 Cihazı Bağlandı: {device_id}")

    try:
        while True:
            
            message = await websocket.receive()

            logger.info(f"Gelen ham veri anahtarları: {list(message.keys())}")

            
            # 1. Metin/Kontrol Paketi Geldiyse (JSON)
            if "text" in message:
                control_data = json.loads(message["text"])
                event = control_data.get("event")

                if event == "STREAM_END":
                    if audio_buffer.is_empty():
                        logger.warning("STREAM_END geldi fakat ses arabelleği boş.")
                        continue

                    # ----- AŞAMA A: İlk Siparişin Alınması -----
                    if fsm.is_state(SessionState.IDLE):
                        fsm.transition_to(SessionState.PROCESSING_STT)
                        transcribed_text = await stt_engine.transcribe(audio_buffer.get_bytes())
                        audio_buffer.clear()
                        logger.info(f"Whisper Ham Çıktısı: [{repr(transcribed_text)}]")
                        if not transcribed_text:
                            # STT boş metin dönerse
                            fsm.reset()
                            error_audio = await tts_engine.synthesize("Sizi tam anlayamadım, lütfen tekrar söyler misiniz?")
                            await websocket.send_bytes(error_audio)
                            continue

                        logger.info(f"Sipariş Metni: '{transcribed_text}'")
                        fsm.cached_order_text = transcribed_text

                        # Onay Sorusu Oluştur ve Seste Gönder
                        fsm.transition_to(SessionState.CONFIRMING)
                        confirm_prompt = f"{transcribed_text} siparişinizi onaylıyor musunuz?"
                        audio_response = await tts_engine.synthesize(confirm_prompt)

                        await websocket.send_text(json.dumps({
    "type": "tts_start",
    "text": confirm_prompt
}))
                        await websocket.send_bytes(audio_response)
                        fsm.transition_to(SessionState.LISTENING_CONFIRMATION)

                    # ----- AŞAMA B: Onay/İptal Cevabının Alınması -----
                    elif fsm.is_state(SessionState.LISTENING_CONFIRMATION):
                        confirmation_text = await stt_engine.transcribe(audio_buffer.get_bytes())
                        audio_buffer.clear()

                        logger.info(f"Onay Yanıtı Metni: '{confirmation_text}'")
                        confirmation_result = intent_service.analyze_confirmation(
    confirmation_text
)

                        if confirmation_result == ConfirmationIntent.CONFIRMED:

                            fsm.transition_to(SessionState.PROCESSING_JSON)

                            # Siparişi JSON'a dönüştür
                            order_json = await llm_extractor.extract_order(
                                fsm.cached_order_text
                            )

                            # POS sistemine gönder
                            await pos_dispatcher.dispatch_order(
                             order_json,
                             device_id
                            )

                            # ESP32'ye bilgi ver
                            success_audio = await tts_engine.synthesize(
                                "Teşekkür ederiz.Siparişiniz alındı, hazırlanıyor."
                            )

                            await websocket.send_text(json.dumps({
                                "type": "command",
                                "payload": "SIPARIS_ONAYLANDI"
                            }))

                            await websocket.send_bytes(success_audio)

                            fsm.reset()

                        elif confirmation_result == ConfirmationIntent.REJECTED:

                            cancel_audio = await tts_engine.synthesize(
                                "Sipariş iptal edildi. Yeni siparişinizi verebilirsiniz."
                            )

                            await websocket.send_bytes(cancel_audio)

                            fsm.reset()

                        else:

                            unknown_audio = await tts_engine.synthesize(
                                "Cevabınızı anlayamadım. Lütfen sadece evet veya hayır diyiniz."
                            )

                            await websocket.send_bytes(unknown_audio)

                            fsm.transition_to(SessionState.LISTENING_CONFIRMATION)

            # 2. Ham Ses Paketi (Binary Chunk) Geldiyse
            elif "bytes" in message:
                success = audio_buffer.append(message["bytes"])
                if not success:
                    logger.warning("Arabellek doldu, gelen pakete yer kalmadı.")

    except WebSocketDisconnect:
        logger.warning(f"ESP32 Bağlantısı Koptu: {device_id}")
    except Exception as e:
        logger.error(f"Soket İşlem Hatası [{device_id}]: {e}")
    finally:
        audio_buffer.clear()
        fsm.reset()
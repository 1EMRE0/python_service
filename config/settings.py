# app/config/settings.py
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "IoT Voice Order Backend"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # WebSocket Configuration
    WS_HOST: str = "0.0.0.0"
    WS_PORT: int = 8000
    
    # Audio Settings
    SAMPLE_RATE: int = 16000
    CHANNELS: int = 1
    CHUNK_SIZE: int = 1024
    
    # STT Settings
    STT_MODEL_SIZE: str = Field(default="small", description="Faster-whisper model size")
    STT_DEVICE: str = Field(default="cpu", description="cuda or cpu")
    STT_COMPUTE_TYPE: str = Field(default="int8", description="float16, int8, or int8_float16")
    
    # TTS Settings
    PIPER_VOICE_MODEL: str = Field(default="tr_TR-dfki-medium.onnx", description="Piper ONNX model path")
    
    # LLM Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL_NAME: str = "qwen2.5:1.5b"

    class Config:
        env_file = ".env"

    # POS / Webhook Ayarları
# POS / Webhook Ayarları
POS_TARGET_IP = "127.0.0.1"
POS_PORT = 5095
POS_ENDPOINT = "/api/orders/create"
POS_API_URL = f"http://{POS_TARGET_IP}:{POS_PORT}{POS_ENDPOINT}"   

settings = Settings()
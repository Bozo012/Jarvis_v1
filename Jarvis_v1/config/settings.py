import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base project directory
BASE_DIR = Path(__file__).parent.parent


class GeneralSettings(BaseModel):
    debug: bool = Field(default=os.getenv("DEBUG", "false").lower() == "true")
    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))
    host: str = Field(default=os.getenv("HOST", "0.0.0.0"))
    port: int = Field(default=int(os.getenv("PORT", "8000")))
    audio_device_index: int = Field(default=int(os.getenv("AUDIO_DEVICE_INDEX", "0")))


class LLMSettings(BaseModel):
    ollama_host: str = Field(default=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    model: str = Field(default=os.getenv("LLM_MODEL", "llama3"))


class WakeWordSettings(BaseModel):
    access_key: str = Field(default=os.getenv("PORCUPINE_ACCESS_KEY", ""))
    wake_word_path: Optional[str] = Field(default=os.getenv("WAKE_WORD_PATH"))
    sensitivity: float = Field(default=float(os.getenv("WAKE_WORD_SENSITIVITY", "0.5")))


class STTSettings(BaseModel):
    model: str = Field(default=os.getenv("WHISPER_MODEL", "base"))
    language: str = Field(default=os.getenv("WHISPER_LANGUAGE", "en"))


class TTSSettings(BaseModel):
    model: str = Field(default=os.getenv("TTS_MODEL", "tts_models/en/vctk/vits"))
    speaker: str = Field(default=os.getenv("TTS_SPEAKER", "p326"))
    language: str = Field(default=os.getenv("TTS_LANGUAGE", "en"))


class HomeAssistantSettings(BaseModel):
    url: str = Field(default=os.getenv("HASS_URL", ""))
    token: str = Field(default=os.getenv("HASS_TOKEN", ""))


class MediaSettings(BaseModel):
    mpd_host: str = Field(default=os.getenv("MPD_HOST", "localhost"))
    mpd_port: int = Field(default=int(os.getenv("MPD_PORT", "6600")))
    spotify_client_id: str = Field(default=os.getenv("SPOTIFY_CLIENT_ID", ""))
    spotify_client_secret: str = Field(default=os.getenv("SPOTIFY_CLIENT_SECRET", ""))
    spotify_redirect_uri: str = Field(default=os.getenv("SPOTIFY_REDIRECT_URI", ""))


class SMSSettings(BaseModel):
    account_sid: str = Field(default=os.getenv("TWILIO_ACCOUNT_SID", ""))
    auth_token: str = Field(default=os.getenv("TWILIO_AUTH_TOKEN", ""))
    phone_number: str = Field(default=os.getenv("TWILIO_PHONE_NUMBER", ""))


class EmailSettings(BaseModel):
    smtp_server: str = Field(default=os.getenv("SMTP_SERVER", ""))
    smtp_port: int = Field(default=int(os.getenv("SMTP_PORT", "587")))
    username: str = Field(default=os.getenv("SMTP_USERNAME", ""))
    password: str = Field(default=os.getenv("SMTP_PASSWORD", ""))
    email_from: str = Field(default=os.getenv("EMAIL_FROM", ""))


class TVSettings(BaseModel):
    tv_type: str = Field(default=os.getenv("TV_TYPE", "webos"))
    tv_ip: str = Field(default=os.getenv("TV_IP", ""))
    tv_mac: str = Field(default=os.getenv("TV_MAC", ""))
    ir_blaster_gpio_pin: int = Field(default=int(os.getenv("IR_BLASTER_GPIO_PIN", "17")))


class Settings(BaseModel):
    general: GeneralSettings = Field(default_factory=GeneralSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    wake_word: WakeWordSettings = Field(default_factory=WakeWordSettings)
    stt: STTSettings = Field(default_factory=STTSettings)
    tts: TTSSettings = Field(default_factory=TTSSettings)
    home_assistant: HomeAssistantSettings = Field(default_factory=HomeAssistantSettings)
    media: MediaSettings = Field(default_factory=MediaSettings)
    sms: SMSSettings = Field(default_factory=SMSSettings)
    email: EmailSettings = Field(default_factory=EmailSettings)
    tv: TVSettings = Field(default_factory=TVSettings)


# Create settings instance
settings = Settings()


# Helper function to get all audio devices for setup
def list_audio_devices():
    import pyaudio
    p = pyaudio.PyAudio()
    info = []
    
    for i in range(p.get_device_count()):
        dev_info = p.get_device_info_by_index(i)
        info.append({
            'index': i,
            'name': dev_info['name'],
            'input_channels': dev_info['maxInputChannels'],
            'output_channels': dev_info['maxOutputChannels'],
            'default_sample_rate': dev_info['defaultSampleRate'],
        })
    
    p.terminate()
    return info

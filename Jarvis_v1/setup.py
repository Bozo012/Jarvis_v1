from setuptools import setup, find_packages

setup(
    name="local-ai-assistant",
    version="1.0.0",
    description="Local AI Assistant with voice control and home automation",
    author="AI Assistant Developer",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn>=0.24.0",
        "typer>=0.9.0",
        "pydantic>=2.4.2",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "loguru>=0.7.2",
        "apscheduler>=3.10.4",
        "websockets>=12.0",
        "ollama>=0.1.5",
        "langchain>=0.0.335",
        "pyaudio>=0.2.13",
        "numpy>=1.26.1",
        "openai-whisper>=20231117",
        "pydub>=0.25.1",
        "pvporcupine>=3.0.0",
        "TTS>=0.18.0",
        "piper-tts>=1.2.0",
        "homeassistant-api>=4.0.0",
        "playwright>=1.40.0",
        "python-mpd2>=3.1.0",
        "spotipy>=2.23.0",
        "twilio>=8.10.0",
        "pywebostv>=0.8.9",
        "roku>=4.0.0",
        "pycec>=0.5.1",
        "docker>=6.1.3"
    ],
    entry_points={
        "console_scripts": [
            "local-ai-assistant=cli:app",
        ],
    },
    python_requires=">=3.8",
)

import os
import sys
import time
import typer
from typing import Optional
from loguru import logger

from mcp.controller import MicroservicesControlPlane
from core.audio_listener import AudioListener
from core.command_processor import CommandProcessor
from config.settings import settings, list_audio_devices

# Create Typer app
app = typer.Typer(help="Local AI Assistant CLI")
mcp = None


@app.command()
def start():
    """Start the local AI assistant."""
    global mcp
    
    logger.info("Starting Local AI Assistant...")
    
    # Initialize and start MCP
    mcp = MicroservicesControlPlane()
    if not mcp.initialize():
        logger.error("Failed to initialize MCP")
        return
        
    if not mcp.start():
        logger.error("Failed to start MCP")
        return
        
    logger.info("Local AI Assistant started successfully")
    
    # Keep running until interrupted
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        mcp.stop()
        logger.info("Local AI Assistant stopped")


@app.command()
def stop():
    """Stop the local AI assistant."""
    global mcp
    
    if mcp and mcp.running:
        logger.info("Stopping Local AI Assistant...")
        mcp.stop()
        logger.info("Local AI Assistant stopped")
    else:
        logger.warning("Local AI Assistant is not running")


@app.command()
def restart():
    """Restart the local AI assistant."""
    stop()
    time.sleep(1.0)
    start()


@app.command()
def command(text: str = typer.Argument(..., help="Command text to process")):
    """Send a command to the assistant."""
    global mcp
    
    if not mcp or not mcp.running:
        # Initialize MCP if not already running
        mcp = MicroservicesControlPlane()
        if not mcp.initialize():
            logger.error("Failed to initialize MCP")
            return
            
    # Process command
    response = mcp.process_command(text)
    typer.echo(f"Response: {response}")


@app.command()
def listen():
    """Listen for a single voice command."""
    # Initialize audio listener
    audio_listener = AudioListener()
    if not audio_listener.initialize():
        logger.error("Failed to initialize audio listener")
        return
        
    # Initialize command processor
    command_processor = CommandProcessor()
    if not command_processor.initialize(audio_listener):
        logger.error("Failed to initialize command processor")
        return
        
    # Listen for command
    logger.info("Listening for command...")
    command = audio_listener.listen_once()
    
    if command:
        logger.info(f"Command: {command}")
        response = command_processor.process_command(command)
        logger.info(f"Response: {response}")
        audio_listener.say(response)
    else:
        logger.warning("No command detected")
        
    # Cleanup
    audio_listener.cleanup()


@app.command()
def devices():
    """List available audio devices."""
    audio_devices = list_audio_devices()
    
    if not audio_devices:
        logger.warning("No audio devices found")
        return
        
    typer.echo("Available audio devices:")
    for device in audio_devices:
        typer.echo(f"Index: {device['index']}")
        typer.echo(f"Name: {device['name']}")
        typer.echo(f"Input channels: {device['input_channels']}")
        typer.echo(f"Output channels: {device['output_channels']}")
        typer.echo(f"Default sample rate: {device['default_sample_rate']}")
        typer.echo("")
        
    typer.echo(f"Current audio device index: {settings.general.audio_device_index}")


@app.command()
def test_tts(text: str = typer.Argument(..., help="Text to speak")):
    """Test text-to-speech functionality."""
    from core.tts import TextToSpeech
    
    tts = TextToSpeech()
    if not tts.initialize():
        logger.error("Failed to initialize TTS")
        return
        
    tts.speak(text)
    tts.cleanup()


@app.command()
def test_stt():
    """Test speech-to-text functionality."""
    from core.stt import SpeechToText
    
    stt = SpeechToText()
    if not stt.initialize():
        logger.error("Failed to initialize STT")
        return
        
    logger.info("Recording audio for transcription...")
    transcription = stt.listen_and_transcribe(max_duration=5)
    
    if transcription:
        logger.info(f"Transcription: {transcription}")
    else:
        logger.warning("No transcription available")
        
    stt.cleanup()


@app.command()
def test_wake_word():
    """Test wake word detection."""
    from core.wake_word import WakeWordDetector
    
    def wake_word_callback():
        logger.info("Wake word detected!")
        
    detector = WakeWordDetector()
    if not detector.initialize():
        logger.error("Failed to initialize wake word detector")
        return
        
    logger.info("Listening for wake word... (Press Ctrl+C to stop)")
    
    try:
        detector.start(wake_word_callback)
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        logger.info("Stopping wake word detection...")
    finally:
        detector.cleanup()


if __name__ == "__main__":
    # Configure logger
    logger.remove()
    logger.add(sys.stderr, level=settings.general.log_level)
    
    # Run Typer app
    app()

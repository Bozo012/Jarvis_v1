import os
import struct
import pyaudio
import pvporcupine
from typing import Callable, Optional
from loguru import logger

from config.settings import settings


class WakeWordDetector:
    """
    Wake word detection using PicoVoice's Porcupine.
    Listens for a specified wake word and triggers a callback when detected.
    """
    
    def __init__(self):
        self.access_key = settings.wake_word.access_key
        self.wake_word_path = settings.wake_word.wake_word_path
        self.sensitivity = settings.wake_word.sensitivity
        self.audio_device_index = settings.general.audio_device_index
        
        self.porcupine = None
        self.audio = None
        self.audio_stream = None
        self.is_running = False
        self.callback = None
        
    def initialize(self):
        """Initialize the wake word detector with the specified settings."""
        try:
            # Initialize Porcupine with either a built-in keyword or custom keyword file
            if self.wake_word_path and os.path.exists(self.wake_word_path):
                self.porcupine = pvporcupine.create(
                    access_key=self.access_key,
                    keyword_paths=[self.wake_word_path],
                    sensitivities=[self.sensitivity]
                )
            else:
                # Default to "Hey Computer" if no custom wake word provided
                self.porcupine = pvporcupine.create(
                    access_key=self.access_key,
                    keywords=["computer"],
                    sensitivities=[self.sensitivity]
                )
                
            logger.info(f"Wake word detector initialized with {'custom' if self.wake_word_path else 'default'} wake word")
            
            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()
            
        except Exception as e:
            logger.error(f"Failed to initialize wake word detector: {e}")
            self.cleanup()
            raise
    
    def start(self, callback: Callable[[], None]):
        """
        Start listening for the wake word.
        
        Args:
            callback: Function to call when wake word is detected
        """
        if self.is_running:
            logger.warning("Wake word detector is already running")
            return
            
        if not self.porcupine:
            self.initialize()
            
        self.callback = callback
        self.is_running = True
        
        try:
            self.audio_stream = self.audio.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length,
                input_device_index=self.audio_device_index
            )
            
            logger.info("Started listening for wake word")
            
            # Start processing audio input
            while self.is_running:
                pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                
                # Process with Porcupine
                keyword_index = self.porcupine.process(pcm)
                
                # If wake word detected (keyword_index >= 0)
                if keyword_index >= 0:
                    logger.info("Wake word detected!")
                    if self.callback:
                        self.callback()
                        
        except Exception as e:
            logger.error(f"Error in wake word detection: {e}")
            self.stop()
            
    def stop(self):
        """Stop listening for the wake word."""
        self.is_running = False
        
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
            
        logger.info("Stopped listening for wake word")
        
    def cleanup(self):
        """Release all resources."""
        self.stop()
        
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None
            
        if self.audio:
            self.audio.terminate()
            self.audio = None
            
        logger.info("Wake word detector resources released")

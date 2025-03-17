import threading
from typing import Callable, Optional
from loguru import logger

from core.wake_word import WakeWordDetector
from core.stt import SpeechToText
from core.tts import TextToSpeech


class AudioListener:
    """
    Audio listener service that combines wake word detection and speech-to-text.
    Listens for wake word, then captures and transcribes voice commands.
    """
    
    def __init__(self):
        self.wake_word_detector = WakeWordDetector()
        self.stt = SpeechToText()
        self.tts = TextToSpeech()
        
        self.is_running = False
        self.listen_thread = None
        self.command_callback = None
        
    def initialize(self) -> bool:
        """Initialize all audio components."""
        try:
            # Initialize wake word detector
            self.wake_word_detector.initialize()
            
            # Initialize STT
            self.stt.initialize()
            
            # Initialize TTS
            self.tts.initialize()
            
            logger.info("Audio listener initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize audio listener: {e}")
            return False
            
    def _wake_word_callback(self):
        """
        Callback function triggered when wake word is detected.
        Records audio, transcribes it, and passes to command processor.
        """
        try:
            # Play acknowledgment sound or speak confirmation
            self.tts.speak("Yes?")
            
            # Listen for command
            logger.info("Listening for command...")
            command = self.stt.listen_and_transcribe(max_duration=10)
            
            # Process command if not empty
            if command and self.command_callback:
                logger.info(f"Command received: {command}")
                self.command_callback(command)
            elif not command:
                logger.info("No command detected")
                self.tts.speak("I didn't hear anything")
                
        except Exception as e:
            logger.error(f"Error processing audio after wake word: {e}")
            
    def _listen_worker(self):
        """Worker thread function for continuous listening."""
        try:
            # Start wake word detection
            self.wake_word_detector.start(self._wake_word_callback)
            
        except Exception as e:
            logger.error(f"Error in listen worker thread: {e}")
            self.stop()
            
    def start(self, command_callback: Callable[[str], None]):
        """
        Start listening for wake word and commands.
        
        Args:
            command_callback: Function to call with transcribed command
        """
        if self.is_running:
            logger.warning("Audio listener is already running")
            return
            
        self.command_callback = command_callback
        self.is_running = True
        
        # Start listening in a separate thread
        self.listen_thread = threading.Thread(target=self._listen_worker)
        self.listen_thread.daemon = True
        self.listen_thread.start()
        
        logger.info("Audio listener started")
        
    def stop(self):
        """Stop listening for wake word and commands."""
        self.is_running = False
        
        # Stop wake word detector
        if self.wake_word_detector:
            self.wake_word_detector.stop()
            
        # Stop STT recording if active
        if self.stt:
            self.stt.stop_recording()
            
        # Wait for listen thread to finish
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=1.0)
            
        logger.info("Audio listener stopped")
        
    def say(self, text: str) -> Optional[str]:
        """
        Speak text using the TTS engine.
        
        Args:
            text: Text to speak
            
        Returns:
            Path to generated audio file or None
        """
        return self.tts.speak(text)
        
    def listen_once(self) -> str:
        """
        Listen for a single voice command and transcribe it.
        
        Returns:
            Transcribed command
        """
        # Play acknowledgment
        self.tts.speak("Listening")
        
        # Listen and transcribe
        return self.stt.listen_and_transcribe(max_duration=10)
        
    def cleanup(self):
        """Release all resources."""
        self.stop()
        
        if self.wake_word_detector:
            self.wake_word_detector.cleanup()
            
        if self.stt:
            self.stt.cleanup()
            
        if self.tts:
            self.tts.cleanup()
            
        logger.info("Audio listener resources released")

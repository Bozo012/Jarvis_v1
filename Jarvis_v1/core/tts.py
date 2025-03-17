import os
import tempfile
import subprocess
import numpy as np
import pyaudio
from pathlib import Path
from typing import Optional, Union
from loguru import logger
from TTS.api import TTS as CoquiTTS
from pydub import AudioSegment
from pydub.playback import play

from config.settings import settings


class TextToSpeech:
    """
    Text-to-Speech service that supports both Coqui TTS and Piper TTS.
    Converts text to speech and plays it through the audio output.
    """
    
    def __init__(self):
        self.model = settings.tts.model
        self.speaker = settings.tts.speaker
        self.language = settings.tts.language
        
        self.tts_engine = None
        self.audio = None
        self.use_piper = 'piper' in self.model.lower()
        
    def initialize(self):
        """Initialize the TTS model."""
        try:
            if not self.use_piper:
                # Initialize Coqui TTS
                logger.info(f"Loading Coqui TTS model: {self.model}")
                self.tts_engine = CoquiTTS(model_name=self.model, progress_bar=False)
            else:
                # For Piper, we'll verify the binary is installed
                piper_command = ["piper", "--help"]
                try:
                    subprocess.run(piper_command, capture_output=True, check=True)
                    logger.info("Piper TTS is available")
                except (subprocess.SubprocessError, FileNotFoundError):
                    logger.error("Piper TTS is not installed or not in PATH")
                    return False
            
            # Initialize PyAudio for playback
            self.audio = pyaudio.PyAudio()
            
            logger.info("Text-to-Speech initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Text-to-Speech: {e}")
            return False
    
    def synthesize_coqui(self, text: str, output_file: Optional[str] = None) -> Union[str, bytes]:
        """
        Synthesize speech using Coqui TTS.
        
        Args:
            text: Text to synthesize
            output_file: Optional path to save the audio file
            
        Returns:
            Path to the output file or raw audio data
        """
        if not self.tts_engine:
            self.initialize()
            
        try:
            # Create a temporary file if no output file specified
            if not output_file:
                temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                output_file = temp_file.name
                temp_file.close()
            
            # Synthesize speech
            logger.info(f"Synthesizing speech with Coqui TTS: {text[:50]}...")
            self.tts_engine.tts_to_file(
                text=text,
                file_path=output_file,
                speaker=self.speaker if self.speaker else None,
                language=self.language if self.language else None
            )
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error during Coqui TTS synthesis: {e}")
            return ""
            
    def synthesize_piper(self, text: str, output_file: Optional[str] = None) -> str:
        """
        Synthesize speech using Piper TTS.
        
        Args:
            text: Text to synthesize
            output_file: Optional path to save the audio file
            
        Returns:
            Path to the output file
        """
        try:
            # Create a temporary file if no output file specified
            if not output_file:
                temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                output_file = temp_file.name
                temp_file.close()
            
            # Prepare model path - extract from settings
            model_parts = self.model.split('/')
            model_name = model_parts[-1] if len(model_parts) > 0 else "en_US-lessac-medium"
            
            # Run Piper TTS command
            logger.info(f"Synthesizing speech with Piper TTS: {text[:50]}...")
            
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as text_file:
                text_file.write(text)
                text_file_path = text_file.name
            
            piper_command = [
                "piper",
                "--model", f"/app/models/piper/{model_name}.onnx",
                "--output_file", output_file,
                "--text_file", text_file_path
            ]
            
            subprocess.run(piper_command, check=True)
            
            # Clean up text file
            os.unlink(text_file_path)
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error during Piper TTS synthesis: {e}")
            return ""
            
    def synthesize(self, text: str, output_file: Optional[str] = None) -> str:
        """
        Synthesize speech using the configured TTS engine.
        
        Args:
            text: Text to synthesize
            output_file: Optional path to save the audio file
            
        Returns:
            Path to the output file
        """
        if self.use_piper:
            return self.synthesize_piper(text, output_file)
        else:
            return self.synthesize_coqui(text, output_file)
            
    def play_audio_file(self, file_path: str):
        """
        Play an audio file through the system's audio output.
        
        Args:
            file_path: Path to the audio file to play
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"Audio file does not exist: {file_path}")
                return
                
            # Load and play audio
            logger.info(f"Playing audio file: {file_path}")
            audio = AudioSegment.from_file(file_path)
            play(audio)
            
        except Exception as e:
            logger.error(f"Error playing audio file: {e}")
            
    def speak(self, text: str, save_to_file: Optional[str] = None) -> Optional[str]:
        """
        Convert text to speech and play it.
        
        Args:
            text: Text to speak
            save_to_file: Optional path to save the audio file
            
        Returns:
            Path to the generated audio file if save_to_file is provided
        """
        if not text:
            logger.warning("Empty text provided for speech synthesis")
            return None
            
        try:
            # Synthesize speech
            output_file = self.synthesize(text, save_to_file)
            
            if not output_file or not os.path.exists(output_file):
                logger.error("Failed to synthesize speech")
                return None
                
            # Play the audio
            self.play_audio_file(output_file)
            
            # Clean up temporary file if not saving
            if not save_to_file and output_file:
                try:
                    os.unlink(output_file)
                except Exception:
                    pass
                    
            return output_file if save_to_file else None
            
        except Exception as e:
            logger.error(f"Error during speech synthesis and playback: {e}")
            return None
            
    def cleanup(self):
        """Release all resources."""
        if self.audio:
            self.audio.terminate()
            self.audio = None
            
        self.tts_engine = None
        logger.info("Text-to-Speech resources released")

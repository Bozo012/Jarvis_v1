import os
import tempfile
import numpy as np
import whisper
import pyaudio
import wave
from pathlib import Path
from typing import Optional, Tuple
from loguru import logger

from config.settings import settings


class SpeechToText:
    """
    Speech-to-Text service using OpenAI's Whisper.
    Transcribes audio input to text.
    """
    
    def __init__(self):
        self.model_name = settings.stt.model
        self.language = settings.stt.language
        self.audio_device_index = settings.general.audio_device_index
        
        self.model = None
        self.audio = None
        self.sample_rate = 16000  # Whisper works with 16kHz audio
        self.is_recording = False
        self.audio_stream = None
        
    def initialize(self):
        """Initialize the STT model and audio interface."""
        try:
            # Initialize Whisper model
            logger.info(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
            
            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()
            
            logger.info("Speech-to-Text initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Speech-to-Text: {e}")
            return False
    
    def record_audio(self, duration: int = 5, silence_threshold: float = 0.03, 
                    silence_duration: float = 1.0) -> Tuple[np.ndarray, bool]:
        """
        Record audio from the microphone with dynamic stopping based on silence.
        
        Args:
            duration: Maximum recording duration in seconds
            silence_threshold: Threshold for silence detection
            silence_duration: How long silence must persist to stop recording
            
        Returns:
            Tuple containing audio data as numpy array and a boolean indicating if 
            recording stopped due to silence
        """
        if not self.audio:
            self.initialize()
            
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = self.sample_rate
        
        self.is_recording = True
        frames = []
        silent_chunks = 0
        required_silent_chunks = int(silence_duration * RATE / CHUNK)
        max_chunks = int(duration * RATE / CHUNK)
        
        # Start recording
        stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            input_device_index=self.audio_device_index
        )
        
        logger.info("Started recording audio")
        
        try:
            # Record audio until silence or max duration
            for i in range(max_chunks):
                if not self.is_recording:
                    break
                
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
                
                # Check for silence to auto-stop recording
                audio_data = np.frombuffer(data, dtype=np.int16)
                volume_norm = np.abs(audio_data).mean() / 32768.0
                
                if volume_norm < silence_threshold:
                    silent_chunks += 1
                    if silent_chunks >= required_silent_chunks:
                        logger.info("Silence detected, stopping recording")
                        break
                else:
                    silent_chunks = 0
        
        except Exception as e:
            logger.error(f"Error during recording: {e}")
        
        finally:
            # Stop and close the stream
            stream.stop_stream()
            stream.close()
            self.is_recording = False
            
            logger.info("Recording stopped")
            
            # Convert frames to numpy array
            audio_data = np.frombuffer(b''.join(frames), dtype=np.int16).astype(np.float32) / 32768.0
            return audio_data, silent_chunks >= required_silent_chunks
    
    def save_audio_to_file(self, audio_data: np.ndarray, filename: str = "recording.wav"):
        """Save recorded audio to a WAV file."""
        # Convert float array back to int16
        audio_int16 = (audio_data * 32768).astype(np.int16)
        
        # Create a temporary WAV file
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_int16.tobytes())
            
        logger.info(f"Audio saved to {filename}")
        
    def transcribe_audio(self, audio_data: Optional[np.ndarray] = None, 
                        audio_file: Optional[str] = None) -> str:
        """
        Transcribe audio data or audio file to text.
        
        Args:
            audio_data: NumPy array of audio data
            audio_file: Path to audio file
            
        Returns:
            Transcribed text
        """
        if not self.model:
            self.initialize()
            
        try:
            # Transcribe either audio data or audio file
            if audio_data is not None:
                # Create temporary file for audio data
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_filename = temp_file.name
                
                # Save audio data to temporary file
                self.save_audio_to_file(audio_data, temp_filename)
                
                # Transcribe audio file
                logger.info("Transcribing audio data")
                result = self.model.transcribe(
                    temp_filename, 
                    language=self.language if self.language else None,
                    fp16=False
                )
                
                # Clean up temporary file
                os.unlink(temp_filename)
                
            elif audio_file and os.path.exists(audio_file):
                # Transcribe provided audio file
                logger.info(f"Transcribing audio file: {audio_file}")
                result = self.model.transcribe(
                    audio_file, 
                    language=self.language if self.language else None,
                    fp16=False
                )
                
            else:
                logger.error("No audio data or valid audio file provided for transcription")
                return ""
                
            # Return transcribed text
            transcription = result["text"].strip()
            logger.info(f"Transcription: {transcription}")
            return transcription
            
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return ""
            
    def listen_and_transcribe(self, max_duration: int = 10) -> str:
        """
        Record audio from microphone and transcribe it to text.
        
        Args:
            max_duration: Maximum recording duration in seconds
            
        Returns:
            Transcribed text
        """
        # Record audio
        audio_data, _ = self.record_audio(duration=max_duration)
        
        # Transcribe audio
        if len(audio_data) > 0:
            return self.transcribe_audio(audio_data)
        else:
            logger.warning("No audio recorded")
            return ""
            
    def stop_recording(self):
        """Stop any ongoing recording."""
        self.is_recording = False
        logger.info("Recording stopped")
        
    def cleanup(self):
        """Release audio resources."""
        if self.audio:
            self.audio.terminate()
            self.audio = None
            
        logger.info("Speech-to-Text resources released")

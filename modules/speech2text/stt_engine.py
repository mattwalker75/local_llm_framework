"""
Speech-to-Text Engine using the following:

Python packages:
sounddevice
openai-whisper
scipy

on Mac:  brew install ffmpeg

This module provides a simple, clean interface for converting speech to text.
"""

import sounddevice as sd
import numpy as np
import whisper
import tempfile
import os
from scipy.io.wavfile import write
import time
from typing import Optional, List, Dict
import logging


class SpeechToText:
    """
    Speech-to-Text engine using openai-whisper.

    Provides a simple interface for converting speech to text with customizable
    speech recognition settings.

    Example:
        stt = SpeechToText()
        text = stt.listen()
    """
    def __init__(self,
                 sample_rate: int = 16000,
                 channels: int = 1,
                 dtype: str = "int16",
                 max_duration: int = 60,
                 silence_timeout: float = 1.5,
                 silence_threshold: int = 500,
                 chunk_duration: float = 0.1):
        """
        Initialize the Speech-to-Text engine.

        Args:
            sample_rate: Sample rate for audio recording (default: 16000).
            channels: Number of audio channels (default: 1).
            dtype: Data type for audio recording (default: "int16").
            max_duration: Maximum duration to record in seconds (default: 60).
            silence_timeout: Duration of silence to stop recording (default: 1.5 seconds).
            silence_threshold: Amplitude threshold to detect silence (default: 500).
            chunk_duration: Duration of each audio chunk to process (default: 0.1 seconds).
        """
        self.logger = logging.getLogger(__name__)

        try:
            self.sample_rate = sample_rate
            self.channels = channels
            self.dtype = dtype
            self.max_duration = max_duration
            self.silence_timeout = silence_timeout
            self.silence_threshold = silence_threshold
            self.chunk_duration = chunk_duration

            self.logger.info("Speech-to-Text engine initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize STT engine: {e}")
            raise
    
    def record_until_silence(self) -> np.ndarray:
        """
        Record audio from the microphone until silence is detected.

        Returns:
            Recorded audio data as a NumPy array.
        """
        self.logger.info("Starting audio recording...")

        recorded_chunks = []
        silence_start = None
        total_duration = 0.0
        chunk_size = int(self.sample_rate * self.chunk_duration)

        with sd.InputStream(samplerate=self.sample_rate,
                            channels=self.channels,
                            dtype=self.dtype) as stream:
            while total_duration < self.max_duration:
                chunk, _ = stream.read(chunk_size)
                recorded_chunks.append(chunk)

                amplitude = np.max(np.abs(chunk))
                if amplitude < self.silence_threshold:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start >= self.silence_timeout:
                        self.logger.info("Silence detected, stopping recording.")
                        break
                else:
                    silence_start = None

                total_duration += self.chunk_duration

        audio_data = np.concatenate(recorded_chunks, axis=0)
        self.logger.info("Audio recording completed.")
        return audio_data
    
    def transcribe_audio(self, audio_data: np.ndarray) -> str:
        """
        Transcribe audio data to text using Whisper.

        Args:
            audio_data: Recorded audio data as a NumPy array.

        Returns:
            Transcribed text from the audio data.
        """
        self.logger.info("Transcribing audio data...")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            write(temp_wav.name, self.sample_rate, audio_data)
            temp_wav_path = temp_wav.name

        model = whisper.load_model("base")
        result = model.transcribe(temp_wav_path, fp16=False)

        os.remove(temp_wav_path)

        self.logger.info("Transcription completed.")
        return result["text"]
    
    def listen(self) -> str:
        """
        Listen to microphone input and convert speech to text.

        Returns:
            Transcribed text from the recorded speech.
        """
        self.logger.info("Listening for speech...")
        audio_data = self.record_until_silence()
        text = self.transcribe_audio(audio_data)
        self.logger.info(f"Transcribed Text: {text}")
        return text
    
    

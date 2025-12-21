#!/usr/bin/env python

import sounddevice as sd
import numpy as np
import whisper
import tempfile
import os
from scipy.io.wavfile import write
import time

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"

MAX_DURATION = 60          # hard cap (seconds)
SILENCE_TIMEOUT = 1.5      # stop after this many seconds of silence
SILENCE_THRESHOLD = 500    # adjust if needed
CHUNK_DURATION = 0.1       # seconds

def rms(audio_chunk):
    return np.sqrt(np.mean(np.square(audio_chunk.astype(np.float32))))

def record_until_silence():
    frames = []
    silence_start = None
    start_time = time.time()

    print("🎙️ Listening...")

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=DTYPE
    ) as stream:

        while True:
            chunk, _ = stream.read(int(SAMPLE_RATE * CHUNK_DURATION))
            frames.append(chunk)

            volume = rms(chunk)

            if volume < SILENCE_THRESHOLD:
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start >= SILENCE_TIMEOUT:
                    print("🛑 Silence detected")
                    break
            else:
                silence_start = None

            if time.time() - start_time >= MAX_DURATION:
                print("⏱️ Max duration reached")
                break

    return np.concatenate(frames, axis=0)

def transcribe_audio(audio):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        write(tmp.name, SAMPLE_RATE, audio)
        temp_path = tmp.name

    model = whisper.load_model("base")
    result = model.transcribe(temp_path)

    os.remove(temp_path)
    return result["text"]

if __name__ == "__main__":
    audio = record_until_silence()
    text = transcribe_audio(audio)
    print("\nYou said:")
    print(text)




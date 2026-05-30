"""
Generate a loud alternating siren for drowsiness alerts.
"""
import os
import wave

import numpy as np

sample_rate = 44100
duration = 2.0
t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

# Alternating high/low tones for a noticeable siren
tone_a = np.sin(2 * np.pi * 880 * t)
tone_b = np.sin(2 * np.pi * 660 * t)
switch = (np.sin(2 * np.pi * 4 * t) > 0).astype(float)
siren = 0.9 * (tone_a * switch + tone_b * (1 - switch))

# Fade in/out to avoid clicks
fade_samples = int(0.02 * sample_rate)
envelope = np.ones_like(t)
envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
siren = siren * envelope

beep_int = np.int16(siren * 32767)

assets_dir = os.path.join(os.path.dirname(__file__), "frontend", "assets")
os.makedirs(assets_dir, exist_ok=True)
output_path = os.path.join(assets_dir, "alert-sound.wav")

with wave.open(output_path, "w") as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(sample_rate)
    wav_file.writeframes(beep_int.tobytes())

print(f"[OK] Alert sound generated: {output_path}")

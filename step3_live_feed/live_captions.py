import sounddevice as sd
import numpy as np
import whisper
import tempfile
import scipy.io.wavfile as wav
import threading
import queue
import time
import os
import tkinter as tk

from step4_live_segmentation.transcript_manager import TranscriptManager

stop_event = threading.Event()

transcript_manager = TranscriptManager()



# ---------------- CONFIG ----------------
DEVICE_NAME = "Stereo Mix"
SAMPLE_RATE = 48000
TARGET_SR = 16000
FRAME_SEC = 3
ENERGY_THRESHOLD = 0.01
buffer = []
SILENCE_LIMIT = 2
silence_count = 0
# ----------------------------------------

audio_queue = queue.Queue()
caption_queue = queue.Queue()

print("🧠 Loading Whisper model...")
model = whisper.load_model("small")
print("✅ Model loaded")

# ---------- AUDIO CALLBACK ----------
def audio_callback(indata, frames, time_info, status):
    global buffer, silence_count

    audio = indata[:, 0]

    # Better energy calculation (RMS)
    energy = np.sqrt(np.mean(audio**2))

    if energy > ENERGY_THRESHOLD:
        buffer.append(audio.copy())
        silence_count = 0
    else:
        silence_count += 1

    # If silence after speech → send full sentence
    if silence_count > SILENCE_LIMIT and buffer:
        full_audio = np.concatenate(buffer)
        audio_queue.put(full_audio)
        buffer.clear()

# ---------- WHISPER WORKER ----------
def whisper_worker():
    while not stop_event.is_set():
        audio = audio_queue.get()

        audio_16k = np.interp(
            np.linspace(0, len(audio), int(len(audio) * TARGET_SR / SAMPLE_RATE)),
            np.arange(len(audio)),
            audio
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            wav.write(f.name, TARGET_SR, audio_16k.astype(np.float32))
            path = f.name

        result = model.transcribe(path, fp16=False)
        os.remove(path)

        text = result["text"].strip()
        # REMOVE garbage
        if len(text) < 5:
            continue

        if any(char in text for char in ["♪", "…", "。", "،"]):
            continue
        if text:
            caption_queue.put(text)
            transcript_manager.add_entry(text)

# ---------- UI ----------
def ui_worker():
    root = tk.Tk()
    root.title("Live Captions")
    root.geometry("650x140")
    root.attributes("-topmost", True)

    text_box = tk.Text(
        root,
        font=("Segoe UI", 14),
        wrap="word",
        height=6
    )
    text_box.pack(expand=True, fill="both")
    text_box.insert("end", "Listening...\n")
    text_box.config(state="disabled")

    def update_caption():
        while not caption_queue.empty():
            text_box.config(state="normal")
            text_box.insert("end", caption_queue.get() + "\n")
            text_box.see("end")  # auto-scroll
            text_box.config(state="disabled")
        root.after(100, update_caption)

    update_caption()
    root.mainloop()

# ---------- DEVICE ----------
device_index = None
for i, dev in enumerate(sd.query_devices()):
    if DEVICE_NAME.lower() in dev["name"].lower():
        device_index = i
        break

if device_index is None:
    raise RuntimeError("Stereo Mix not found")

# ---------- START ----------
threading.Thread(target=whisper_worker, daemon=True).start()

try:
    with sd.InputStream(
        device=device_index,
        samplerate=SAMPLE_RATE,
        channels=1,
        callback=audio_callback,
        blocksize=int(SAMPLE_RATE * FRAME_SEC)
    ):
        ui_worker()

except KeyboardInterrupt:
    print("\n🛑 Stopping live transcription...")

finally:
    stop_event.set()
    transcript_manager.save()


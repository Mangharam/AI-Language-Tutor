import time
import numpy as np
import torch
from kokoro import KPipeline

SENTENCE = "Hello! How can I help you with your English today?"

print("Torch version:", torch.__version__)
print("Default CPU threads:", torch.get_num_threads())

print("\nLoading Kokoro pipeline...")
start = time.perf_counter()
pipeline = KPipeline(lang_code="a")
print(f"Pipeline loaded in {time.perf_counter() - start:.2f} seconds")

print("\nTesting same sentence 4 times:")
for i in range(4):
    start = time.perf_counter()
    chunks = [np.asarray(audio) for _, _, audio in pipeline(SENTENCE, voice="af_heart")]
    elapsed = time.perf_counter() - start
    audio_seconds = sum(len(chunk) for chunk in chunks) / 24000
    speed = elapsed / audio_seconds if audio_seconds else 0
    print(
        f"Call {i + 1}: {elapsed:.2f}s processing | "
        f"{audio_seconds:.2f}s audio | speed factor {speed:.2f}"
    )

print("\nTesting CPU thread counts:")
for count in (1, 2, 3, 4):
    torch.set_num_threads(count)
    start = time.perf_counter()
    chunks = [np.asarray(audio) for _, _, audio in pipeline(SENTENCE, voice="af_heart")]
    elapsed = time.perf_counter() - start
    audio_seconds = sum(len(chunk) for chunk in chunks) / 24000
    speed = elapsed / audio_seconds if audio_seconds else 0
    print(f"Threads {count}: {elapsed:.2f}s | speed factor {speed:.2f}")

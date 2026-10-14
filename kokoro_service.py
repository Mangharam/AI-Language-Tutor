import io
import torch
torch.set_num_threads(4)
import numpy as np
import soundfile as sf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from kokoro import KPipeline

app = FastAPI(title="Kokoro Voice Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


print("Loading Kokoro voice model...")
pipeline = KPipeline(lang_code="a")
print("Kokoro voice model loaded!")

# Warm up Kokoro before accepting real requests
try:
    print("Warming up Kokoro...")
    warmup_start = time.perf_counter()

    for _, _, audio in pipeline(
        "Hello.",
        voice="af_heart"
    ):
        pass

    print(
        f"Kokoro warm-up complete in "
        f"{time.perf_counter() - warmup_start:.2f}s"
    )
except Exception as exc:
    print(f"Kokoro warm-up failed: {exc}")

print("Kokoro voice service ready!")

class SpeechRequest(BaseModel):
    text: str
    voice: str = "af_heart"

@app.get("/health")
def health():
    return {"status": "ok", "service": "Kokoro TTS"}

@app.post("/tts")
def generate_speech(data: SpeechRequest):
    import time

    request_start = time.perf_counter()
    text = data.text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Text cannot be empty"
        )

    if len(text) > 1500:
        raise HTTPException(
            status_code=400,
            detail="Text is too long"
        )

    try:
        # 1. Kokoro inference
        inference_start = time.perf_counter()
        chunks = []

        for _, _, audio in pipeline(text, voice=data.voice):
            chunks.append(np.asarray(audio))

        print(
            f"KOKORO INFERENCE: "
            f"{time.perf_counter() - inference_start:.2f}s"
        )

        if not chunks:
            raise HTTPException(
                status_code=500,
                detail="No audio generated"
            )

        # 2. Combine audio chunks
        combine_start = time.perf_counter()
        audio_data = np.concatenate(chunks)

        print(
            f"AUDIO COMBINE: "
            f"{time.perf_counter() - combine_start:.2f}s"
        )

        # 3. Convert audio to WAV
        conversion_start = time.perf_counter()
        buffer = io.BytesIO()

        sf.write(
            buffer,
            audio_data,
            24000,
            format="WAV"
        )

        wav_data = buffer.getvalue()

        print(
            f"WAV CONVERSION: "
            f"{time.perf_counter() - conversion_start:.2f}s"
        )

        print(
            f"TOTAL TTS REQUEST: "
            f"{time.perf_counter() - request_start:.2f}s"
        )

        return Response(
            content=wav_data,
            media_type="audio/wav",
        )

    except HTTPException:
        raise

    except Exception as exc:
        print(f"KOKORO ERROR: {exc}")
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )

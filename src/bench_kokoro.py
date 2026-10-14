"""
Measures Kokoro on THIS computer, run it from the same virtual environment as your Kokoro service. Changes nothing.

    python bench_kokoro.py                 (everything else on the PC should be idle)
    python bench_kokoro.py --contend       (runs Ollama in the background at the same time, like your real app does)

It prints how long each synthesis takes for the same sentence, how many seconds of audio came out,
and the speed factor (seconds of work per second of audio; below 1.0 is faster than real time).
"""
import argparse
import http.client
import json
import threading
import time

import numpy as np

SENTENCE = "Hello! How can I help you with your English today?"


def ollama_load(stop):
    conn = http.client.HTTPConnection("127.0.0.1", 11434, timeout=120)
    body = json.dumps({"model": "qwen2.5:1.5b", "prompt": "Write a long story about a cat.", "stream": False,
                       "keep_alive": "30m", "options": {"num_predict": 80, "temperature": 0.7}}).encode()
    while not stop.is_set():
        try:
            conn.request("POST", "/api/generate", body=body, headers={"Content-Type": "application/json"})
            conn.getresponse().read()
        except Exception:
            time.sleep(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--contend", action="store_true")
    ap.add_argument("--voice", default="af_heart")
    a = ap.parse_args()

    try:
        import torch
        print("torch", torch.__version__, "| default threads:", torch.get_num_threads())
    except ImportError:
        torch = None

    from kokoro import KPipeline
    t0 = time.perf_counter()
    pipeline = KPipeline(lang_code="a")
    print(f"Pipeline loaded in {time.perf_counter() - t0:.1f}s\n")

    stop = threading.Event()
    if a.contend:
        threading.Thread(target=ollama_load, args=(stop,), daemon=True).start()
        print("Ollama is generating in the background (contention test).\n")
        time.sleep(2)

    def synth():
        start = time.perf_counter()
        chunks = [np.asarray(audio) for _, _, audio in pipeline(SENTENCE, voice=a.voice)]
        took = time.perf_counter() - start
        seconds = sum(len(c) for c in chunks) / 24000
        return took, seconds

    print("Same sentence, four times (call 1 includes one-time start-up work):")
    for i in range(4):
        took, secs = synth()
        print(f"  call {i + 1}: {took:6.2f}s of work for {secs:4.2f}s of audio  -> speed factor {took / secs:5.2f}")

    if torch is not None:
        print("\nThread count test (after warm-up):")
        for n in (1, 2, 3, 4):
            torch.set_num_threads(n)
            took, secs = synth()
            print(f"  torch threads={n}: {took:6.2f}s for {secs:4.2f}s of audio  -> speed factor {took / secs:5.2f}")

    stop.set()
    print("\nIf call 1 is slow but calls 2-4 are fast, the fix is a warm-up at start-up. "
          "If everything is slow only with --contend, the fix is to stop running the LLM and the voice at the same time.")


if __name__ == "__main__":
    main()

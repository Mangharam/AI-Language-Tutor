
import argparse
import json
import time
import urllib.request
import urllib.error

URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5:1.5b"


def run_test(prompt, threads=2, keep_alive="30m"):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "keep_alive": keep_alive,
        "options": {
            "num_predict": 20,
            "num_ctx": 1024,
            "num_thread": threads,
            "temperature": 0
        }
    }

    request = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    start = time.perf_counter()

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        print(f"ERROR: {exc}")
        print("Check karo ke Ollama run ho raha hai aur model available hai.")
        return

    wall = time.perf_counter() - start
    load = result.get("load_duration", 0) / 1e9
    prompt_seconds = result.get("prompt_eval_duration", 0) / 1e9
    gen_seconds = result.get("eval_duration", 0) / 1e9
    prompt_tokens = result.get("prompt_eval_count", 0)
    gen_tokens = result.get("eval_count", 0)

    prompt_tps = prompt_tokens / prompt_seconds if prompt_seconds else 0
    gen_tps = gen_tokens / gen_seconds if gen_seconds else 0
    overhead = wall - load - prompt_seconds - gen_seconds

    print(f"Threads: {threads}")
    print(f"Wall time: {wall:.2f}s")
    print(f"Model load: {load:.2f}s")
    print(f"Prompt processing: {prompt_seconds:.2f}s")
    print(f"Generation: {gen_seconds:.2f}s")
    print(f"Prompt tokens: {prompt_tokens}")
    print(f"Generated tokens: {gen_tokens}")
    print(f"Prompt speed: {prompt_tps:.2f} tokens/s")
    print(f"Generation speed: {gen_tps:.2f} tokens/s")
    print(f"Other overhead (approx.): {overhead:.2f}s")
    print("-" * 40)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--threads",
        default="2",
        help="Threads to test, e.g. 2 or 2,3,4"
    )
    args = parser.parse_args()

    try:
        thread_values = [int(x.strip()) for x in args.threads.split(",")]
        if any(x < 1 for x in thread_values):
            raise ValueError
    except ValueError:
        print("Invalid threads. Example: --threads 2,3,4")
        return

    print("Ollama benchmark starting...")
    print(f"Model: {MODEL}")
    print("First run may include model loading time.")
    print("=" * 40)

    for threads in thread_values:
        print(f"Testing with {threads} thread(s)...")
        run_test("Reply briefly and naturally: Hello, how are you?", threads)

    print("Benchmark finished.")


if __name__ == "__main__":
    main()

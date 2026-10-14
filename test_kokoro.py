from kokoro import KPipeline
import soundfile as sf

print("Loading Kokoro voice model...")

pipeline = KPipeline(lang_code="a")

text = "Hello Mangha! Welcome to your AI English language tutor. Let's practice speaking English together."

for i, (graphemes, phonemes, audio) in enumerate(
    pipeline(text, voice="af_heart")
):
    sf.write("kokoro_test.wav", audio, 24000)
    print("Audio saved as kokoro_test.wav")
    break

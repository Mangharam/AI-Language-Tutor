"""
Pronunciation clarity scoring from per-word recognizer confidence.

This measures how clearly the speech recognizer understood each word, so it is
an intelligibility signal, not an accent score. Works with any recognizer that
gives a probability per word (Faster-Whisper word_timestamps=True does).
"""
import re

CLEAR = 0.85   # at or above: clear
OKAY = 0.60    # at or above: partly clear, below: unclear
BANDS = [(90, "Very clear"), (75, "Clear"), (60, "Developing"), (0, "Needs work")]


def _clean(word: str) -> str:
    return re.sub(r"[^\w']", "", str(word).lower())


def band(score: float) -> str:
    for low, name in BANDS:
        if score >= low:
            return name
    return "Needs work"


def status(confidence: float) -> str:
    return "clear" if confidence >= CLEAR else "okay" if confidence >= OKAY else "unclear"


def normalize(speech_words):
    """Keep only entries shaped like {'word': str, 'confidence': number}."""
    items = []
    for w in speech_words or []:
        if isinstance(w, dict) and w.get("word") is not None and isinstance(w.get("confidence"), (int, float)):
            if _clean(w["word"]):
                items.append({"word": str(w["word"]).strip(), "confidence": max(0.0, min(1.0, float(w["confidence"])))})
    return items


def score_words(speech_words):
    """Sentence-level result, or None when there is no usable confidence data."""
    items = normalize(speech_words)
    if len(items) < 2:
        return None
    probs = [i["confidence"] for i in items]
    mean = sum(probs) / len(probs)
    unclear_fraction = sum(1 for p in probs if p < OKAY) / len(probs)
    score = round(100 * (0.7 * mean + 0.3 * (1 - unclear_fraction)))
    words = [{"word": i["word"], "confidence": round(i["confidence"], 2), "status": status(i["confidence"])} for i in items]
    to_practice = [w["word"].strip(".,!?;:\"") for w in sorted(words, key=lambda w: w["confidence"]) if w["status"] != "clear"][:3]
    return {"score": score, "band": band(score), "words": words, "to_practice": to_practice}


def extract_word_scores(segments):
    """Faster-Whisper segments (transcribed with word_timestamps=True) -> [{'word','confidence'}]."""
    out = []
    for seg in segments:
        for w in getattr(seg, "words", None) or []:
            text = (w.word or "").strip()
            if text:
                out.append({"word": text, "confidence": round(float(w.probability), 3)})
    return out

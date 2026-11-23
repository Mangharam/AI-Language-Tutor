"""
ai_services.py - drop next to main.py.

* Ollama client that serializes payloads correctly and reports WHY a call failed
* Speaking-transcript analysis with validated output and a real fallback
* Interview coach with per-user state (one question at a time)
"""
import json
import logging
import os
import re
import socket
import urllib.error
import urllib.request
from difflib import SequenceMatcher

log = logging.getLogger("tutor.ai")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")


# ------------------------------------------------------------------
# Ollama client
# ------------------------------------------------------------------

class OllamaError(Exception):
    """kind: serialization | unavailable | timeout | http_error | bad_response"""

    MESSAGES = {
        "serialization": "Internal error while preparing the AI request.",
        "unavailable": "The AI service is not running. Start Ollama and try again.",
        "timeout": "The AI took too long to answer. Please try again.",
        "http_error": "The AI service rejected the request (is the model installed?).",
        "bad_response": "The AI returned an unusable answer. Please try again.",
    }

    def __init__(self, kind, detail=""):
        super().__init__(f"{kind}: {detail}")
        self.kind = kind
        self.detail = detail

    @property
    def user_message(self):
        return self.MESSAGES.get(self.kind, "AI error.")


def _post(path, body, timeout):
    # The original bug: .encode() was called on a dict. Always json.dumps first.
    try:
        data = json.dumps(body).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise OllamaError("serialization", repr(exc))

    request = urllib.request.Request(
        OLLAMA_URL + path, data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise OllamaError("http_error", f"HTTP {exc.code}")
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, (socket.timeout, TimeoutError)):
            raise OllamaError("timeout", repr(exc.reason))
        raise OllamaError("unavailable", repr(exc.reason))
    except (socket.timeout, TimeoutError):
        raise OllamaError("timeout")
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise OllamaError("bad_response", repr(exc))


def ollama_chat(messages, *, num_predict=200, temperature=0.3,
                json_mode=False, timeout=90, model=None):
    body = {
        "model": model or DEFAULT_MODEL,
        "messages": messages,
        "stream": False,
        "keep_alive": "30m",
        "options": {"num_predict": num_predict, "num_ctx": 2048,
                    "temperature": temperature, "num_thread": 4},
    }
    if json_mode:
        body["format"] = "json"
    result = _post("/api/chat", body, timeout)
    text = str(result.get("message", {}).get("content", "")).strip()
    log.info("ollama ok: prompt_tokens=%s generated=%s seconds=%.2f",
             result.get("prompt_eval_count"), result.get("eval_count"),
             result.get("total_duration", 0) / 1e9)
    if result.get("done_reason") == "length":
        log.warning("ollama output hit num_predict limit (%s)", num_predict)
    return text


def extract_json(raw):
    if not raw:
        return None
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        data = json.loads(raw[start:end + 1])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _json_call(messages, **kw):
    """One call + ONE retry, only for unparseable output."""
    for attempt in (1, 2):
        raw = ollama_chat(messages, json_mode=True, **kw)
        data = extract_json(raw)
        if data is not None:
            return data
        log.warning("invalid JSON from model (attempt %d, %d chars)", attempt, len(raw))
    raise OllamaError("bad_response", "invalid JSON after retry")


def _norm(s):
    return re.sub(r"\s+", " ", str(s or "")).strip().casefold()


def split_sentences(value):
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+|\n+", value) if p.strip()]


# ------------------------------------------------------------------
# Speaking transcript analysis (text only - no pronunciation claims)
# ------------------------------------------------------------------

_SPEAK_SYSTEM = (
    "You are a careful, friendly English teacher for beginners. Analyse a "
    "spoken-English TRANSCRIPT (text only; never comment on pronunciation, "
    "accent or speed). Fix only real grammar, word-form and word-choice "
    "mistakes. Keep correct sentences unchanged. Keep the speaker's meaning. "
    "Return JSON only with keys: corrected_text (string), corrections (list of "
    "{original, corrected, category, explanation}; original must be copied "
    "exactly from the transcript; category is grammar|vocabulary|word_choice|"
    "spelling|punctuation; explanation max 20 words), overall_feedback "
    "(1-2 sentences about THIS transcript), vocabulary_suggestion, fluency_tip, "
    "practice_sentence (practises the same rule the speaker got wrong)."
)
_CATEGORIES = {"grammar", "vocabulary", "word_choice", "spelling", "punctuation"}


def _clean_corrections(items, transcript):
    """Keep only corrections grounded in the transcript."""
    out, seen = [], set()
    t = _norm(transcript)
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        o = str(item.get("original", "")).strip()
        c = str(item.get("corrected", "")).strip()
        if not o or not c or _norm(o) == _norm(c) or _norm(o) not in t or _norm(o) in seen:
            continue
        seen.add(_norm(o))
        cat = str(item.get("category", "grammar")).strip().lower()
        out.append({
            "original": o, "corrected": c,
            "category": cat if cat in _CATEGORIES else "grammar",
            "explanation": str(item.get("explanation", "")).strip()[:200],
        })
    return out[:30]


def _sentence_corrections(transcript, corrected_text, model_items):
    """Sentence-level diff (reliable) enriched with model explanations."""
    a, b = split_sentences(transcript), split_sentences(corrected_text)
    if len(a) != len(b):
        return None
    out = []
    for orig, fixed in zip(a, b):
        if _norm(orig) == _norm(fixed):
            continue
        expl, cat = "", "grammar"
        for m in model_items:
            if _norm(m["original"]) in _norm(orig):
                expl, cat = m["explanation"], m["category"]
                break
        out.append({"original": orig, "corrected": fixed,
                    "category": cat, "explanation": expl})
    return out


def analyze_transcript(text, fallback_corrector=None):
    """
    Returns dict: corrected_text, corrections, overall_feedback,
    vocabulary_suggestion, fluency_tip, practice_sentence, degraded, warning.
    Raises OllamaError only when the model failed AND no fallback exists.
    """
    try:
        data = _json_call(
            [{"role": "system", "content": _SPEAK_SYSTEM},
             {"role": "user", "content": f"TRANSCRIPT:\n{text}"}],
            num_predict=700, temperature=0.1, timeout=120)
    except OllamaError as exc:
        log.error("speaking analysis failed: %s", exc)
        if fallback_corrector is None:
            raise
        corrected = []
        for s in split_sentences(text):
            try:
                corrected.append(fallback_corrector(s) or s)
            except Exception:
                log.exception("fallback corrector failed")
                corrected.append(s)
        corrected_text = " ".join(corrected)
        return {
            "corrected_text": corrected_text,
            "corrections": _sentence_corrections(text, corrected_text, []) or [],
            "overall_feedback": "Detailed AI feedback is unavailable right now; "
                                "only a basic grammar check was done.",
            "vocabulary_suggestion": "", "fluency_tip": "", "practice_sentence": "",
            "degraded": True, "warning": exc.user_message,
        }

    corrected_text = str(data.get("corrected_text", "")).strip() or text
    model_items = _clean_corrections(data.get("corrections"), text)
    corrections = _sentence_corrections(text, corrected_text, model_items)
    if corrections is None:  # sentence counts differ -> trust grounded model items
        corrections = model_items

    def field(key, default):
        return str(data.get(key, "")).strip() or default

    return {
        "corrected_text": corrected_text,
        "corrections": corrections,
        "overall_feedback": field("overall_feedback", "Thank you for practising. Keep going one sentence at a time."),
        "vocabulary_suggestion": field("vocabulary_suggestion", ""),
        "fluency_tip": field("fluency_tip", "Speak in short sentences and pause between ideas."),
        "practice_sentence": field("practice_sentence", ""),
        "degraded": False, "warning": "",
    }


# ------------------------------------------------------------------
# Interview coach
# ------------------------------------------------------------------

ROLES = [  # (regex, key, label)
    (r"customer (support|service)", "customer_support", "customer support representative"),
    (r"call[- ]?cent(er|re)", "customer_support", "international call-center agent"),
    (r"technical support|tech support|it support", "technical_support", "technical support representative"),
    (r"\bhr\b|screening", "general", "HR screening"),
    (r"intern(ship)?", "general", "internship"),
    (r"admission|university", "general", "university admission"),
    (r"behaviou?ral", "general", "behavioral"),
    (r"speaking assessment", "general", "English speaking assessment"),
]

QUESTION_BANK = {
    "customer_support": [
        "Tell me about yourself and why you want to work in customer support.",
        "How would you help a customer who is angry about a late order?",
        "Tell me about a time you helped someone solve a problem.",
        "How do you stay calm when you are under pressure?",
        "What would you do if you did not know the answer to a customer's question?",
        "Why should we hire you for this position?",
    ],
    "technical_support": [
        "Tell me about yourself and why you want to work in technical support.",
        "How would you explain a technical problem to someone who is not technical?",
        "A customer says their internet is not working. What would you do first?",
        "Tell me about a time you learned a new technology quickly.",
        "How do you stay patient with a frustrated customer?",
        "Why should we hire you?",
    ],
    "general": [
        "Tell me about yourself.",
        "Why are you interested in this opportunity?",
        "What are your main strengths?",
        "Tell me about a time you worked in a team.",
        "Tell me about a challenge you solved.",
        "Where do you see yourself in three years?",
    ],
}

_START_RE = re.compile(r"\binterview\b")
_START_VERB = re.compile(r"\b(practi[sc]e|mock|act as|simulate|prepare|rehears\w*|ask me|interviewer)\b")
_STOP_RE = re.compile(r"\b(stop|end|finish|quit|exit|cancel)\b.{0,25}\b(interview|practi[sc]e|session)\b")

_COACH_SYSTEM = (
    "You are a kind, practical English interview coach. The student is a "
    "beginner/intermediate English learner. Evaluate the student's ANSWER to the "
    "interview QUESTION. Rules: never invent experience, skills or achievements "
    "the student did not mention; the improved answer must reuse only the "
    "student's own facts, in simple natural spoken English (max 60 words); if "
    "they lack experience, show honest transferable skills. Return JSON only: "
    '{"did_well": "...", "improve": "...", "improved_answer": "...", '
    '"useful_expression": "...", "next_question": "..."} '
    "next_question must be exactly ONE new question for this role, different "
    "from earlier ones."
)


def detect_interview_start(message):
    m = message.lower()
    return bool(_START_RE.search(m) and _START_VERB.search(m))


def detect_role(message):
    m = message.lower()
    for pattern, key, label in ROLES:
        if re.search(pattern, m):
            return key, label
    return "general", "general job interview"


def _ensure_table(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS interview_sessions (
        user_id TEXT PRIMARY KEY, role_key TEXT NOT NULL, role_label TEXT NOT NULL,
        question_no INTEGER NOT NULL, last_question TEXT NOT NULL,
        asked TEXT NOT NULL DEFAULT '[]', active INTEGER NOT NULL DEFAULT 1,
        updated_at TEXT NOT NULL)""")


def _one_question(text, asked, bank, idx):
    """Exactly one question, never a repeat; bank fallback otherwise."""
    q = ""
    for sent in re.findall(r"[^?]*\?", str(text or "").replace("\n", " ")):
        sent = re.split(r"(?<=[.!])\s+", sent.strip())[-1]  # drop "Okay!" style lead-ins
        if len(sent.split()) >= 4:
            q = sent
            break
    if q and all(SequenceMatcher(None, _norm(q), _norm(a)).ratio() < 0.8 for a in asked):
        return q
    unused = [b for b in bank if b not in asked]
    return unused[0] if unused else bank[idx % len(bank)]


def interview_turn(get_db, user_id, message, now):
    """Returns a reply string if the message belongs to interview mode, else None."""
    conn = get_db()
    try:
        _ensure_table(conn)
        row = conn.execute("SELECT * FROM interview_sessions WHERE user_id=? AND active=1",
                           (user_id,)).fetchone()

        if row and _STOP_RE.search(message.lower()):
            conn.execute("UPDATE interview_sessions SET active=0, updated_at=? WHERE user_id=?",
                         (now(), user_id))
            conn.commit()
            return ("Interview practice ended. Well done for practising! "
                    "Say 'practise an interview' whenever you want to start again.")

        if detect_interview_start(message):  # starts (or restarts) a session
            key, label = detect_role(message)
            first = QUESTION_BANK[key][0]
            conn.execute("""INSERT INTO interview_sessions
                (user_id, role_key, role_label, question_no, last_question, asked, active, updated_at)
                VALUES (?,?,?,?,?,?,1,?)
                ON CONFLICT(user_id) DO UPDATE SET role_key=excluded.role_key,
                role_label=excluded.role_label, question_no=1,
                last_question=excluded.last_question, asked=excluded.asked,
                active=1, updated_at=excluded.updated_at""",
                (user_id, key, label, 1, first, json.dumps([first]), now()))
            conn.commit()
            return (f"Absolutely! Let's practise together. I'll act as your {label} "
                    "interviewer, ask one question at a time, and give you friendly, "
                    "practical feedback on each answer. Say 'end interview' to stop.\n\n"
                    f"Question 1: {first}")

        if not row:
            return None

        if re.match(r"^(please |can you |could you )?(check|correct|fix)\b.{0,30}\b(english|grammar|sentences?)\b",
                    message.lower().strip()):
            return None  # let the normal grammar-check flow handle it

        # ---- an answer to the active question ----
        answer = message.strip()
        if len(answer.split()) < 3:
            return ("Try to answer in a full sentence or two, then I can give you "
                    f"feedback.\n\nQuestion {row['question_no']}: {row['last_question']}")

        asked = json.loads(row["asked"])
        bank = QUESTION_BANK[row["role_key"]]
        try:
            data = _json_call(
                [{"role": "system", "content": _COACH_SYSTEM},
                 {"role": "user", "content":
                  f"Role: {row['role_label']}\nQUESTION: {row['last_question']}\n"
                  f"ANSWER: {answer[:600]}\nEarlier questions: {' | '.join(asked[-5:])}"}],
                num_predict=450, temperature=0.3, timeout=90)
        except OllamaError as exc:
            log.error("interview feedback failed: %s", exc)
            # state NOT advanced, so the user can simply resend
            return (f"{exc.user_message} Your answer was not evaluated, so we are still on "
                    f"Question {row['question_no']}: {row['last_question']}")

        nxt = _one_question(data.get("next_question"), asked, bank, row["question_no"])
        n = row["question_no"] + 1
        asked.append(nxt)
        conn.execute("""UPDATE interview_sessions SET question_no=?, last_question=?,
                        asked=?, updated_at=? WHERE user_id=?""",
                     (n, nxt, json.dumps(asked), now(), user_id))
        conn.commit()

        def g(k, d):
            return str(data.get(k, "")).strip() or d

        return (f"**What you did well:** {g('did_well', 'You answered the question.')}\n\n"
                f"**What to improve:** {g('improve', 'Add one specific example.')}\n\n"
                f"**Improved answer:** {g('improved_answer', answer)}\n\n"
                f"**Useful expression:** {g('useful_expression', 'I would be happy to help.')}\n\n"
                f"**Next interview question:**\nQuestion {n}: {nxt}")
    finally:
        conn.close()


def reset_interview(get_db, user_id):
    """Safe to call even if the table was never created (e.g. Reset Progress)."""
    conn = get_db()
    try:
        _ensure_table(conn)
        conn.execute("DELETE FROM interview_sessions WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()

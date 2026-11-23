import json
import sqlite3
import pytest
import ai_services as ai


def chat_reply(obj):
    content = obj if isinstance(obj, str) else json.dumps(obj)
    return {"message": {"content": content}, "done_reason": "stop"}


@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "t.db")

    def get_db():
        c = sqlite3.connect(path)
        c.row_factory = sqlite3.Row
        return c
    return get_db


NOW = lambda: "2026-01-01T00:00:00"


def test_payload_is_serialized_not_a_dict(monkeypatch):
    """Regression for AttributeError: 'dict' object has no attribute 'encode'."""
    seen = {}

    class R:
        def read(self): return json.dumps(chat_reply("hi")).encode()
        def __enter__(self): return self
        def __exit__(self, *a): pass

    def fake_urlopen(req, timeout):
        seen["data"] = req.data
        return R()
    monkeypatch.setattr(ai.urllib.request, "urlopen", fake_urlopen)
    assert ai.ollama_chat([{"role": "user", "content": "x"}]) == "hi"
    assert isinstance(seen["data"], bytes) and json.loads(seen["data"])["stream"] is False


def test_unserializable_payload_gives_serialization_error():
    with pytest.raises(ai.OllamaError) as e:
        ai._post("/api/chat", {"x": object()}, 5)
    assert e.value.kind == "serialization"


def test_ollama_down_kind(monkeypatch):
    import urllib.error
    def boom(*a, **k): raise urllib.error.URLError(ConnectionRefusedError())
    monkeypatch.setattr(ai.urllib.request, "urlopen", boom)
    with pytest.raises(ai.OllamaError) as e:
        ai.ollama_chat([])
    assert e.value.kind == "unavailable"


def test_timeout_kind(monkeypatch):
    import socket
    def boom(*a, **k): raise socket.timeout()
    monkeypatch.setattr(ai.urllib.request, "urlopen", boom)
    with pytest.raises(ai.OllamaError) as e:
        ai.ollama_chat([])
    assert e.value.kind == "timeout"


def test_speaking_valid(monkeypatch):
    monkeypatch.setattr(ai, "_post", lambda *a, **k: chat_reply({
        "corrected_text": "Yesterday I went to university.",
        "corrections": [{"original": "Yesterday I go to university.",
                         "corrected": "Yesterday I went to university.",
                         "category": "grammar", "explanation": "Use past tense."},
                        {"original": "invented phrase", "corrected": "x", "category": "grammar"}],
        "overall_feedback": "Good.", "vocabulary_suggestion": "attend",
        "fluency_tip": "Slow down.", "practice_sentence": "Yesterday I went home."}))
    r = ai.analyze_transcript("Yesterday I go to university.")
    assert len(r["corrections"]) == 1 and not r["degraded"]
    assert r["corrections"][0]["explanation"] == "Use past tense."


def test_speaking_bad_json_retries_once_then_fallback(monkeypatch):
    calls = []
    def post(*a, **k):
        calls.append(1)
        return chat_reply("not json at all")
    monkeypatch.setattr(ai, "_post", post)
    r = ai.analyze_transcript("I go home.", fallback_corrector=lambda s: "I went home.")
    assert len(calls) == 2 and r["degraded"] and r["corrections"][0]["corrected"] == "I went home."


def test_speaking_ollama_down_without_fallback_raises(monkeypatch):
    def post(*a, **k): raise ai.OllamaError("unavailable")
    monkeypatch.setattr(ai, "_post", post)
    with pytest.raises(ai.OllamaError):
        ai.analyze_transcript("hello there")


def test_json_with_extra_text_is_extracted():
    assert ai.extract_json('Sure! {"a": 1} hope that helps') == {"a": 1}
    assert ai.extract_json("nothing") is None


def test_interview_flow(monkeypatch, db):
    msg = ("I have a job interview tomorrow for a customer support position. "
           "Act as my interviewer, ask one question at a time.")
    r = ai.interview_turn(db, "u1", msg, NOW)
    assert "Question 1:" in r and "Question 2" not in r

    monkeypatch.setattr(ai, "_post", lambda *a, **k: chat_reply({
        "did_well": "Clear start.", "improve": "Add an example.",
        "improved_answer": "I like helping people.", "useful_expression": "I am happy to help.",
        "next_question": "Okay! How do you handle an angry customer? Also, why us?"}))
    r = ai.interview_turn(db, "u1", "I like to help people and I speak English.", NOW)
    assert "What you did well" in r and "Question 2: How do you handle an angry customer?" in r
    assert r.split("Question 2:")[1].count("?") == 1

    # other user is isolated
    assert ai.interview_turn(db, "u2", "hello how are you", NOW) is None
    # stop
    assert "ended" in ai.interview_turn(db, "u1", "please end the interview", NOW)
    assert ai.interview_turn(db, "u1", "hello", NOW) is None


def test_interview_model_down_does_not_advance(monkeypatch, db):
    ai.interview_turn(db, "u1", "practise a customer support interview with me", NOW)
    def post(*a, **k): raise ai.OllamaError("unavailable")
    monkeypatch.setattr(ai, "_post", post)
    r = ai.interview_turn(db, "u1", "I am a good worker and I like people", NOW)
    assert "not evaluated" in r and "Question 1" in r


def test_interview_short_answer_and_repeat_question(monkeypatch, db):
    ai.interview_turn(db, "u1", "mock interview for customer service", NOW)
    assert "full sentence" in ai.interview_turn(db, "u1", "yes", NOW)
    monkeypatch.setattr(ai, "_post", lambda *a, **k: chat_reply({
        "next_question": "Tell me about yourself and why you want to work in customer support?"}))
    r = ai.interview_turn(db, "u1", "I am a student and I like helping people.", NOW)
    assert "How would you help a customer who is angry" in r  # repeat replaced from bank


def test_normal_chat_not_hijacked(db):
    assert ai.interview_turn(db, "u1", "What does 'resilient' mean?", NOW) is None


def test_reset_interview_works_without_table_and_clears_session(db):
    ai.reset_interview(db, "nobody")  # table did not exist: must not raise
    ai.interview_turn(db, "u1", "practise a customer support interview with me", NOW)
    ai.reset_interview(db, "u1")
    assert ai.interview_turn(db, "u1", "I am a student and I like people", NOW) is None


def test_check_my_english_during_interview_is_not_an_answer(db):
    ai.interview_turn(db, "u1", "practise a customer support interview with me", NOW)
    assert ai.interview_turn(db, "u1", "Check my English", NOW) is None

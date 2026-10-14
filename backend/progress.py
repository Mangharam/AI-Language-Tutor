"""Dashboard data: levels over time, mistakes, practice, review and pronunciation clarity."""
import sqlite3
from collections import defaultdict

import db
import pronunciation


def _rows(conn, sql, args=()):
    try:
        return conn.execute(sql, args).fetchall()
    except sqlite3.OperationalError:  # table not created yet
        return []


def get_dashboard(user_id: str):
    conn = sqlite3.connect(db.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        attempts = _rows(conn, "SELECT id, ts, has_errors FROM attempts WHERE user_id=? ORDER BY id", (user_id,))
        total = len(attempts)
        correct = sum(1 for a in attempts if not a["has_errors"])
        days = {a["ts"][:10] for a in attempts}

        levels = [dict(grammar=round(r["grammar"], 1), vocab=round(r["vocab"], 1), overall=round(r["overall"], 1))
                  for r in _rows(conn, "SELECT grammar, vocab, overall FROM (SELECT * FROM level_history WHERE user_id=? ORDER BY id DESC LIMIT 60) ORDER BY id", (user_id,))]

        errors = [{"category": r["category"], "count": r["n"]} for r in _rows(
            conn, "SELECT category, COUNT(*) AS n FROM errors WHERE user_id=? GROUP BY category ORDER BY n DESC, category", (user_id,))]

        practice = [{"category": r["category"], "right": r["right"], "total": r["total"]} for r in _rows(
            conn, "SELECT category, SUM(correct) AS right, COUNT(*) AS total FROM exercise_results WHERE user_id=? GROUP BY category ORDER BY category", (user_id,))]

        cards = _rows(conn, "SELECT reps, due FROM cards WHERE user_id=?", (user_id,))
        now = _rows(conn, "SELECT strftime('%Y-%m-%dT%H:%M:%f','now') AS t")
        now_iso = now[0]["t"] if now else ""
        review = {
            "total": len(cards),
            "due": sum(1 for c in cards if c["due"][:23] <= now_iso),
            "mastered": sum(1 for c in cards if c["reps"] >= 3),
        }

        # Pronunciation: group stored word confidences by attempt
        by_attempt = defaultdict(list)
        for r in _rows(conn, "SELECT attempt_id, word, confidence FROM speech_words WHERE user_id=? ORDER BY id", (user_id,)):
            by_attempt[r["attempt_id"]].append({"word": r["word"], "confidence": r["confidence"]})
        scores, word_stats = [], defaultdict(list)
        for attempt_id in sorted(by_attempt):
            result = pronunciation.score_words(by_attempt[attempt_id])
            if result:
                scores.append(result["score"])
            for w in by_attempt[attempt_id]:
                key = pronunciation._clean(w["word"])
                if key:
                    word_stats[key].append(w["confidence"])
        weak_words = sorted(
            ({"word": k, "avg": round(sum(v) / len(v), 2), "count": len(v)} for k, v in word_stats.items()
             if sum(v) / len(v) < pronunciation.CLEAR),
            key=lambda w: (w["avg"], -w["count"]))[:8]
        average = round(sum(scores) / len(scores)) if scores else None

        return {
            "totals": {
                "sentences": total,
                "correct": correct,
                "accuracy": round(100 * correct / total) if total else None,
                "days_practiced": len(days),
                "voice_sentences": len(scores),
            },
            "levels": levels,
            "errors": errors,
            "practice": practice,
            "review": review,
            "pronunciation": {
                "average": average,
                "band": pronunciation.band(average) if average is not None else None,
                "trend": scores[-30:],
                "words": weak_words,
            },
        }
    finally:
        conn.close()

import React, { useEffect, useRef, useState } from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8010";

const GREETING = {
  role: "tutor",
  reply:
    "Hello! Write me a sentence in English and I will check your grammar. Try telling me about your day.",
};

/* =========================================================
   USER
========================================================= */

function getUserId() {
  try {
    let id = localStorage.getItem("lt_user");

    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem("lt_user", id);
    }

    return id;
  } catch {
    return "default";
  }
}

/* =========================================================
   API
========================================================= */

async function apiFetch(path, options) {
  return fetch(`${API_BASE}${path}`, options);
}

async function post(path, body) {
  const response = await apiFetch(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

 
if (!response.ok) {
  const errorData = await response.json();
  console.error("Speaking feedback API error:", errorData);
  throw new Error(
    errorData.detail || `Request failed: ${response.status}`
  );
}


  return response.json();
}

/* =========================================================
   ICONS
========================================================= */

function Icon({ name, size = 20 }) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round",
    strokeLinejoin: "round",
  };

  const icons = {
    home: (
      <>
        <path d="M3 10.5 12 3l9 7.5" />
        <path d="M5 9.5V21h14V9.5" />
        <path d="M9 21v-6h6v6" />
      </>
    ),

    chat: (
      <path d="M20 11.5a7.5 7.5 0 0 1-8 7.5 8.5 8.5 0 0 1-4-.9L4 20l1.2-3.4A7.3 7.3 0 0 1 4 12c0-4.1 3.6-7.5 8-7.5s8 3.1 8 7Z" />
    ),

    mic: (
      <>
        <rect x="8" y="3" width="8" height="12" rx="4" />
        <path d="M5 11a7 7 0 0 0 14 0" />
        <path d="M12 18v3" />
        <path d="M9 21h6" />
      </>
    ),

    practice: (
      <>
        <path d="M5 4h14v16H5z" />
        <path d="m8 9 2 2 4-4" />
        <path d="M8 15h8" />
      </>
    ),

    review: (
      <>
        <path d="M4 6h16" />
        <path d="M4 12h16" />
        <path d="M4 18h10" />
      </>
    ),

    chart: (
      <>
        <path d="M4 19V5" />
        <path d="M4 19h16" />
        <path d="m7 15 3-4 3 2 5-7" />
      </>
    ),

    settings: (
      <>
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-1.8 1.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5V22h-2.6v-.1a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.9.3l-.1.1-1.8-1.8.1-.1A1.7 1.7 0 0 0 8 17a1.7 1.7 0 0 0-1.5-1H6v-2.6h.5A1.7 1.7 0 0 0 8 12a1.7 1.7 0 0 0-.3-1.9l-.1-.1 1.8-1.8.1.1a1.7 1.7 0 0 0 1.9.3 1.7 1.7 0 0 0 1-1.5V5h2.6v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1 1.8 1.8-.1.1A1.7 1.7 0 0 0 19 10a1.7 1.7 0 0 0 1.5 1h.5v2.6h-.5a1.7 1.7 0 0 0-1.1 1.4Z" />
      </>
    ),

    sun: (
      <>
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
      </>
    ),

    moon: (
      <path d="M20 15.5A8.5 8.5 0 0 1 8.5 4 8.7 8.7 0 1 0 20 15.5Z" />
    ),

    arrow: (
      <>
        <path d="M5 12h14" />
        <path d="m13 6 6 6-6 6" />
      </>
    ),

    send: (
      <>
        <path d="m22 2-7 20-4-9-9-4Z" />
        <path d="M22 2 11 13" />
      </>
    ),
        calendar: (
      <>
        <rect x="3" y="5" width="18" height="16" rx="3" />
        <path d="M8 3v4M16 3v4M3 10h18" />
        <path d="m9.5 15 2 2 3.5-3.5" />
      </>
    ),

    book: (
      <>
        <path d="M12 6.5C10.5 5 8 4.5 4 4.5v13c4 0 6.5.5 8 2 1.5-1.5 4-2 8-2v-13c-4 0-6.5.5-8 2Z" />
        <path d="M12 6.5v13" />
      </>
    ),

    refresh: (
      <>
        <path d="M20 11a8 8 0 0 0-14.5-4.5L4 8" />
        <path d="M4 4v4h4" />
        <path d="M4 13a8 8 0 0 0 14.5 4.5L20 16" />
        <path d="M20 20v-4h-4" />
      </>
    ),

    cards: (
      <>
        <rect x="3" y="7" width="14" height="13" rx="2.5" />
        <path d="M7 7V5.5A2.5 2.5 0 0 1 9.5 3H19a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2" />
        <path d="M7 12h6M7 15.5h4" />
      </>
    ),

    flame: (
      <path d="M12 22a6.5 6.5 0 0 0 6.5-6.5c0-3-1.8-5-3.2-6.6-.6-.7-1.1-1.5-1.3-2.9-2.9 1.4-4.2 4-4.2 6.2-1-.4-1.6-1.2-1.8-2.3C6.4 12 5.5 13.6 5.5 15.5A6.5 6.5 0 0 0 12 22Z" />
    ),
  };
  
  return <svg {...common}>{icons[name] || icons.chat}</svg>;
}

/* =========================================================
   PROGRESS CARDS
========================================================= */

function ProgressCards({ profile }) {
  if (!profile || !profile.total) {
    return (
      <div className="empty-progress">
        <span className="empty-icon">✦</span>

        <div>
          <strong>Your learning journey starts here</strong>

          <p>
            Send your first English sentence to start tracking progress.
          </p>
        </div>
      </div>
    );
  }

  const lv = profile.levels || {};

  return (
    <div className="progress-grid">
      <div className="stat-card level-card">
        <div className="stat-top">
          <span>Overall Level</span>
          <span className="stat-icon">✦</span>
        </div>

        <strong>{lv.overall?.cefr || "A1"}</strong>

        <div className="mini-progress">
          <span
            style={{
              width: `${lv.overall?.score ?? 0}%`,
            }}
          />
        </div>

        <small>
          {lv.overall?.score ?? 0}% progress
        </small>
      </div>

      <div className="stat-card">
        <div className="stat-top">
          <span>Accuracy</span>
          <span className="stat-icon">◎</span>
        </div>

        <strong>{profile.accuracy ?? 0}%</strong>

        <small>Correct first try</small>
      </div>

      <div className="stat-card">
        <div className="stat-top">
          <span>Sentences</span>
          <span className="stat-icon">⌁</span>
        </div>

        <strong>{profile.total ?? 0}</strong>

        <small>Total practiced</small>
      </div>

      <div className="stat-card">
        <div className="stat-top">
          <span>Recent Accuracy</span>
          <span className="stat-icon">↗</span>
        </div>

        <strong>{profile.recent_accuracy ?? 0}%</strong>

        <small>Last 10 sentences</small>
      </div>
    </div>
  );
}

/* =========================================================
   CORRECTION
========================================================= */

function Correction({ msg }) {
  const correction = msg.correction;

  if (!correction) {
    return null;
  }


if (!correction.has_errors) {
  return null;
}


  return (
    <div className="correction-box">
      <div className="correction-title">
        <span>AI Correction</span>
      </div>

      <div className="better-version">
        <small>Better version</small>

        <strong className="better-version-text">
          {correction.corrected}
        </strong>
      </div>

      {correction.changes?.length > 0 && (
        <div className="changes-list">
          {correction.changes.map((c, i) => (
            <div
              className="change-item"
              key={i}
            >
              <span className="change-tag">
                {c.category}
              </span>

              {c.type === "add" && (
                <span>
                  Add <b>{c.to}</b>
                </span>
              )}

              {c.type === "remove" && (
                <span>
                  Remove <s>{c.from}</s>
                </span>
              )}

              {c.type === "replace" && (
                <span>
                  <s>{c.from}</s> → <b>{c.to}</b>
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* =========================================================
   CHAT
========================================================= */

function ChatView({
  messages,
  input,
  setInput,
  send,
  loading,
  voice,
}) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  return (
    <div className="workspace">
      <div className="workspace-header">
        <div>
          <div className="eyebrow">
            AI LANGUAGE COACH
          </div>

          <h1>Let's improve your English.</h1>

          <p>
            Write naturally. I'll correct your grammar and help you improve.
          </p>
        </div>

        <div className="online-badge">
          <span />
          AI Online
        </div>
      </div>

      <div className="chat-area">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`message-row ${
              m.role === "user"
                ? "user-row"
                : ""
            }`}
          >
            {m.role === "tutor" && (
              <div className="avatar tutor-avatar">
                AI
              </div>
            )}

            <div
              className={`message ${m.role}`}
            >
              <div className="message-label">
                {m.role === "tutor"
                  ? "AI Tutor"
                  : "You"}
              </div>

              <p>{m.reply}</p>

              {m.role === "tutor" && (
                <Correction msg={m} />
              )}

              {m.highlights?.length > 0 && (
                <div className="word-highlights">
                  <small>Strong vocabulary</small>

                  <div>
                    {m.highlights.map((h) => (
                      <span key={h.word}>
                        {h.word} · {h.cefr}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {m.cards_added > 0 && (
                <div className="saved-note">
                  ✓ Saved {m.cards_added} word(s) to Review
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message-row">
            <div className="avatar tutor-avatar">
              AI
            </div>

            <div className="message tutor typing">
              <span />
              <span />
              <span />
            </div>
          </div>
        )}

        <div ref={endRef} />
      </div>

      <div className="composer-wrap">
        <div className="composer">
          <input
            value={input}
            onChange={(e) =>
              setInput(e.target.value)
            }
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                send();
              }
            }}
            placeholder="Write something in English..."
            aria-label="Your message"
            maxLength={500}
          />

          {voice.engine !== "none" && (
            <button
              className={`voice-btn ${
                voice.status === "recording"
                  ? "recording"
                  : ""
              }`}
              onClick={voice.toggle}
              disabled={
                voice.status === "processing" ||
                loading
              }
              title={
                voice.status === "recording"
                  ? "Stop recording"
                  : "Speak your sentence"
              }
            >
              <Icon
                name="mic"
                size={20}
              />
            </button>
          )}

          <button
            className="send-btn"
            onClick={send}
            disabled={
              loading ||
              !input.trim()
            }
          >
            <Icon
              name="send"
              size={19}
            />
          </button>
        </div>

        <div className="voice-status">
          {voice.status === "recording"
            ? "● Listening... press the microphone when you're finished."
            : voice.status === "processing"
            ? "Converting your speech to text..."
            : voice.message
            ? voice.message
            : voice.engine === "local"
            ? "Voice powered by Local Whisper"
            : voice.engine === "browser"
            ? "Voice powered by browser speech recognition"
            : "Type your sentence above"}
        </div>
      </div>
    </div>
  );
}



/* =========================================================
   SPEAKING — VOICE-FOCUSED AI CONVERSATION
========================================================= */

function Speaking({ voice, spokenText }) {
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [voiceLoading, setVoiceLoading] = useState(false);
  const [voiceError, setVoiceError] = useState("");
  const [aiReply, setAiReply] = useState("");
  const previousSpokenText = useRef("");
  const requestInProgress = useRef(false);

  /* =========================================================
     PLAY AI VOICE
  ========================================================= */

  async function speakWithKokoro(text) {
    if (!text?.trim()) return;

    setVoiceLoading(true);
    setVoiceError("");

    let audioUrl = null;
    const ttsStart = performance.now();

    try {
      console.time("KOKORO TTS GENERATION");

      const response = await fetch("http://127.0.0.1:8020/tts", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: text.trim(),
          voice: "af_heart",
        }),
      });

      console.timeEnd("KOKORO TTS GENERATION");

      if (!response.ok) {
        throw new Error(`Voice service error: ${response.status}`);
      }

      const audioBlob = await response.blob();

      console.log("Audio size:", audioBlob.size, "bytes");
      console.log("Audio type:", audioBlob.type);
      console.log(
        "Time until audio received:",
        ((performance.now() - ttsStart) / 1000).toFixed(2),
        "seconds"
      );

      if (!audioBlob.size) {
        throw new Error("The AI returned empty audio.");
      }

      audioUrl = URL.createObjectURL(audioBlob);

      const audio = new Audio(audioUrl);
      audio.volume = 1;
      audio.preload = "auto";

      await new Promise((resolve, reject) => {
        audio.onplay = () => {
          console.log("AI VOICE STARTED PLAYING");
        };

        audio.onended = () => {
          resolve();
        };

        audio.onerror = () => {
          reject(new Error("Unable to play AI voice."));
        };

        audio.play().catch(reject);
      });
    } catch (error) {
      console.error("Kokoro voice error:", error);

      setVoiceError(
        error?.message || "Unable to play AI voice."
      );
    } finally {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }

      setVoiceLoading(false);
    }
  }

  /* =========================================================
     GET AI RESPONSE
  ========================================================= */

  async function getFeedback(textToSend) {
    const message = textToSend?.trim();

    if (!message || requestInProgress.current) {
      return;
    }

    requestInProgress.current = true;
    setFeedbackLoading(true);
    setVoiceError("");

    try {
      console.time("CHAT API TOTAL");

      const result = await post("/api/chat", {
        user_id: getUserId(),
        message,
      });

      console.timeEnd("CHAT API TOTAL");

      if (result?.error) {
        throw new Error(
          typeof result.error === "string"
            ? result.error
            : "Unable to get an AI response."
        );
      }

      if (
        typeof result?.reply !== "string" ||
        !result.reply.trim()
      ) {
        throw new Error("The AI did not return a response.");
      }

      console.log("AI reply received:", result.reply);
      setAiReply(result.reply);
      await speakWithKokoro(result.reply);
    } catch (error) {
      console.error("Speaking practice error:", error);

      setVoiceError(
        error?.message || "Unable to get an AI response."
      );
    } finally {
      requestInProgress.current = false;
      setFeedbackLoading(false);
    }
  }

  /* =========================================================
     PROCESS NEW SPEECH
  ========================================================= */

  useEffect(() => {
    const text = spokenText?.trim();

    if (!text || text === previousSpokenText.current) {
      return;
    }

    previousSpokenText.current = text;
    getFeedback(text);
  }, [spokenText]);

  /* =========================================================
     STATUS
  ========================================================= */

  const statusText =
    voice.status === "recording"
      ? "Listening... Speak now"
      : voice.status === "processing"
      ? "Understanding your speech..."
      : voiceLoading
      ? "AI is speaking..."
      : feedbackLoading
      ? "Thinking..."
      : "Tap the microphone and start speaking";

  /* =========================================================
     UI
  ========================================================= */

  return (
    <div className="workspace speaking-workspace">
      <div className="workspace-header">
        <div>
          <div className="eyebrow">SPEAKING PRACTICE</div>

          <h1>Speak with confidence.</h1>

          <p>
            Have a natural English conversation with your AI tutor.
          </p>
        </div>

        <div className="online-badge">
          <span />
          AI Ready
        </div>
      </div>

      <div className="speaking-card">
        <div className="speaking-topic">
          <small>LET'S HAVE A CONVERSATION</small>

          <h2>
            Tell me about your day and what you learned.
          </h2>

          <p>
            Speak naturally. Your AI tutor will reply with voice.
          </p>
        </div>

        <button
          type="button"
          className={`big-mic-btn ${
            voice.status === "recording" ? "recording" : ""
          }`}
          onClick={() => voice.toggle()}
          disabled={
            voice.status === "processing" ||
            feedbackLoading ||
            voiceLoading
          }
          aria-label="Start speaking"
        >
          <Icon name="mic" size={42} />
        </button>

        <div className="speaking-status" aria-live="polite">
          {statusText}
        </div>

        {voice.message && (
          <div className="voice-error">
            {voice.message}
          </div>
        )}

        {voiceError && (
          <div className="voice-error" role="alert">
            {voiceError}
          </div>
        )}
        {aiReply && (
        <div className="speaking-feedback">
        <div className="eyebrow">AI TUTOR RESPONSE</div>
         <p>{aiReply}</p>
  </div>
)}
      </div>
    </div>
  );
}


/* =========================================================
   REVIEW
========================================================= */

function Review({ userId }) {
  const [data, setData] = useState(null);
  const [input, setInput] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  async function load() {
    setInput("");
    setResult(null);
    setError("");

    try {
      const r = await apiFetch(
        `/api/review/${userId}`
      );

      if (!r.ok) {
        throw new Error();
      }

      setData(await r.json());
    } catch {
      setError(
        "Could not load your review cards."
      );
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function check() {
    if (!input.trim() || result || !data?.card) {
      return;
    }

    try {
      setResult(
        await post(
          "/api/review/answer",
          {
            user_id: userId,
            card_id: data.card.id,
            answer: input,
          }
        )
      );
    } catch {
      setError(
        "Could not save your answer."
      );
    }
  }

  return (
    <div className="workspace">
      <div className="workspace-header">
        <div>
          <div className="eyebrow">
            SMART REVIEW
          </div>

          <h1>
            Remember what you learned.
          </h1>

          <p>
            Review difficult words and strengthen your vocabulary.
          </p>
        </div>
      </div>

      {error ? (
        <div className="feature-card">
          <h2>Something went wrong</h2>

          <p>{error}</p>

          <button
            className="primary-btn"
            onClick={load}
          >
            Try again
          </button>
        </div>
      ) : !data ? (
        <div className="feature-card loading-card">
          Loading review...
        </div>
      ) : !data.card ? (
        <div className="empty-review">
          <div className="empty-review-icon">
            ✓
          </div>

          <h2>
            {data.total_cards
              ? "You're all caught up!"
              : "No review words yet"}
          </h2>

          <p>
            {data.total_cards
              ? "Come back later. Your next review will appear here."
              : "Words you miss during practice will automatically appear here."}
          </p>

          <button
            className="primary-btn"
            onClick={load}
          >
            Check again
          </button>
        </div>
      ) : (
        <div className="review-card">
          <div className="review-count">
            {data.due_count} word
            {data.due_count === 1
              ? ""
              : "s"}{" "}
            due
          </div>

          <div className="review-icon">
            Aa
          </div>

          <h2>
            {data.card.sentence}
          </h2>

          <p className="hint">
            Hint: starts with{" "}
            <strong>
              {data.card.hint}
            </strong>
          </p>

          <div className="review-input">
            <input
              value={input}
              onChange={(e) =>
                setInput(e.target.value)
              }
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  check();
                }
              }}
              placeholder="Type the missing word..."
              disabled={!!result}
              autoFocus
            />

            <button
              onClick={check}
              disabled={
                !input.trim() ||
                !!result
              }
            >
              Check
            </button>
          </div>

          {result && (
            <div className="result-box">
              <strong>
                {result.correct
                  ? "Correct!"
                  : "Keep practicing!"}
              </strong>

              <p>
                The word is{" "}
                <b>{result.answer}</b>.{" "}
                {result.correct
                  ? `Next review in ${result.next_review_days} day(s).`
                  : "You'll see it again in 10 minutes."}
              </p>

              <button
                className="primary-btn"
                onClick={load}
              >
                Next card

                <Icon
                  name="arrow"
                  size={17}
                />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* =========================================================
   PRACTICE
========================================================= */

function Practice({ userId, onAnswered }) {
  const [data, setData] = useState(null);
  const [selected, setSelected] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadExercise() {
    setLoading(true);
    setError("");
    setSelected(null);
    setResult(null);

    try {
      const res = await apiFetch(`/api/learning-path/${userId}`);

      if (!res.ok) {
        throw new Error(
          `Server error ${res.status}`
        );
      }

      const json = await res.json();

      setData(json);
    } catch (err) {
      console.error(err);

      setError(
        "Could not load the practice exercise."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadExercise();
  }, []);

  async function answer(index) {
    if (
      selected !== null ||
      !data
    ) {
      return;
    }

    setSelected(index);

    try {
      const res = await apiFetch(
        `/api/exercise/${userId}/answer`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            answer: index,
          }),
        }
      );

      const json = await res.json();

      if (!res.ok) {
        throw new Error(
          json.detail ||
            "Answer submission failed"
        );
      }

      setResult(json);

      if (onAnswered) {
        onAnswered();
      }
    } catch (err) {
      console.error(err);

      setSelected(null);

      setError(
        "Could not submit your answer."
      );
    }
  }

  if (loading) {
    return (
      <div className="workspace">
        <div className="workspace-header">
          <div>
            <div className="eyebrow">
              PRACTICE LAB
            </div>

            <h1>
              Loading practice...
            </h1>
          </div>
        </div>

        <div className="feature-card loading-card">
          Preparing your exercise...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="workspace">
        <div className="workspace-header">
          <div>
            <div className="eyebrow">
              PRACTICE LAB
            </div>

            <h1>
              Practice your English.
            </h1>

            <p>
              Test your grammar with a quick exercise.
            </p>
          </div>
        </div>

        <div className="feature-card">
          <h2>
            Something went wrong
          </h2>

          <p>{error}</p>

          <button
            className="primary-btn"
            onClick={loadExercise}
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const question =
    data.question ||
    data.prompt ||
    data.sentence ||
    "Choose the correct answer.";

  const options =
    data.options ||
    data.choices ||
    [];

  return (
    <div className="workspace">
      <div className="workspace-header">
        <div>
          <div className="eyebrow">
            PRACTICE LAB
          </div>

          <h1>
            Test your English.
          </h1>

          <p>
            Complete a short exercise based on your current level.
          </p>
        </div>

        <div className="online-badge">
          <span />
          {data.level || "A1"} PRACTICE
        </div>
      </div>

      <div className="practice-panel">
        <div className="practice-panel-top">
          <div className="practice-icon">
            ?
          </div>

          <div>
            <span className="card-label">
              QUICK EXERCISE
            </span>

            <h3>{question}</h3>
          </div>
        </div>

        <div className="lesson-options">
          {options.map((option, index) => {
            const isSelected =
              selected === index;

            const isCorrect =
              result?.correct &&
              isSelected;

            return (
              <button
                key={index}
                className={`lesson-option ${
                  isSelected
                    ? "selected"
                    : ""
                } ${
                  isCorrect
                    ? "correct"
                    : ""
                }`}
                onClick={() =>
                  answer(index)
                }
                disabled={
                  selected !== null
                }
              >
                <span className="option-letter">
                  {String.fromCharCode(
                    65 + index
                  )}
                </span>

                <span className="option-text">
                  {option}
                </span>

                <Icon
                  name="arrow"
                  size={17}
                />
              </button>
            );
          })}
        </div>

        {result && (
          <div className="result-box">
            <strong>
              {result.correct
                ? "Correct! 🎉"
                : "Keep practicing!"}
            </strong>

            <p>
              {result.message ||
                (result.correct
                  ? "Excellent work. You got the answer right."
                  : "That's not quite right. Review the concept and try another exercise.")}
            </p>

            <button
              className="primary-btn"
              onClick={loadExercise}
            >
              Next exercise

              <Icon
                name="arrow"
                size={17}
              />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}


/* =========================================================
   COURSE / LESSONS
========================================================= */

function Course({ userId, recommendedLessonId = null }) {
  const LEVELS = [
    "A1",
    "A2",
    "B1",
    "B2",
    "C1",
    "C2",
  ];

  const [topics, setTopics] = useState([]);

  const [levels, setLevels] = useState([]);

  const [currentLevel, setCurrentLevel] =
    useState("A1");

  const [selectedLevel, setSelectedLevel] =
    useState("A1");

  const [lessonData, setLessonData] =
    useState(null);

  const [progress, setProgress] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [showAllLessons, setShowAllLessons] =
    useState(false);

  const [showAchievement, setShowAchievement] =
    useState(false);

  const [showNextCourse, setShowNextCourse] =
    useState(false);
  const recommendedOpenedRef = useRef(null);

  /* =======================================================
     LOAD COURSE
  ======================================================= */

  
useEffect(() => {
  loadCourse();
}, [userId]);

useEffect(() => {
  if (loading || recommendedLessonId == null) {
    return;
  }

  if (recommendedOpenedRef.current === recommendedLessonId) {
    return;
  }

  recommendedOpenedRef.current = recommendedLessonId;
  openLesson(recommendedLessonId);
}, [recommendedLessonId, loading]);


  async function loadCourse(requestedLevel = null) {
  setLoading(true);
  setError("");

  try {
    const res = await apiFetch(
      `/api/learning-path/${userId}`
    );

    if (!res.ok) {
      throw new Error("Could not load course");
    }

    const data = await res.json();

    const receivedTopics = data.topics || [];
    const receivedLevels = data.levels || [];

    setTopics(receivedTopics);
    setLevels(receivedLevels);

    const backendCurrentLevel =
      data.current_level ||
      data.level ||
      "A1";

    setCurrentLevel(backendCurrentLevel);

    if (
      requestedLevel &&
      LEVELS.includes(requestedLevel)
    ) {
      setSelectedLevel(requestedLevel);
    } else if (
      LEVELS.includes(backendCurrentLevel)
    ) {
      setSelectedLevel(backendCurrentLevel);
    }

    if (
      !requestedLevel &&
      receivedLevels.length > 0
    ) {
      const backendLevel =
        receivedLevels.find(
          (item) =>
            item.level === backendCurrentLevel
        );

      if (
        backendLevel &&
        backendLevel.unlocked
      ) {
        setSelectedLevel(
          backendCurrentLevel
        );
      }
    }

  } catch (err) {
    console.error(err);

    setError(
      "Could not load your learning path."
    );
  } finally {
    setLoading(false);
  }
}

  /* =======================================================
     SELECT LEVEL
  ======================================================= */

  async function selectLevel(level) {
    setError("");

    const levelInfo =
      levels.find(
        (item) =>
          item.level === level
      );

    if (
      levelInfo &&
      !levelInfo.unlocked
    ) {
      return;
    }

    setSelectedLevel(level);

    setLessonData(null);
    setProgress(null);

    setShowAllLessons(false);

    /*
     * Reload the course so the
     * latest progress is displayed.
     */

    await loadCourse(level);
  }

/* =======================================================
   OPEN LESSON
======================================================= */

async function openLesson(lessonId) {
  setError("");
  setLoading(true);

  try {
    const [lessonRes, progressRes] = await Promise.all([
      apiFetch(`/api/lesson/${lessonId}`),
      apiFetch(`/api/lesson-progress/${userId}/${lessonId}`),
    ]);

    if (!lessonRes.ok) {
      throw new Error(
        `Could not load lesson (${lessonRes.status})`
      );
    }

    if (!progressRes.ok) {
      throw new Error(
        `Could not load lesson progress (${progressRes.status})`
      );
    }

    const lesson = await lessonRes.json();
    const lessonProgress = await progressRes.json();

    if (lessonProgress.unlocked === false) {
      setLessonData(null);
      setProgress(null);
      setError("Complete the previous lesson first.");
      return;
    }

    setLessonData(lesson);
    setProgress(lessonProgress);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  } catch (err) {
    console.error("OPEN LESSON ERROR:", err);

    setError(
      err.message || "Could not open this lesson."
    );

    setLessonData(null);
    setProgress(null);
  } finally {
    setLoading(false);
  }
}
  /* =======================================================
     PRACTICE SUBMISSION
  ======================================================= */

  async function submitPractice(answer) {
    if (!lessonData) {
      return;
    }

    try {
      const res = await apiFetch(
        `/api/lesson-practice/${userId}/${lessonData.id}?answer=${encodeURIComponent(
          answer
        )}`,
        {
          method: "POST",
        }
      );


      const result =
        await res.json();


      if (!res.ok) {
        throw new Error(
          result.detail ||
            "Practice submission failed"
        );
      }


      if (result.correct) {

        alert(
          "Practice completed! 🎉"
        );


        const updated =
          await apiFetch(
            `/api/lesson-progress/${userId}/${lessonData.id}`
          );


        if (updated.ok) {
          setProgress(
            await updated.json()
          );
        }

      } else {

        alert(
          "Not quite. Try again."
        );
      }

    } catch (err) {
      console.error(err);

      alert(
        err.message ||
          "Could not submit practice."
      );
    }
  }


  /* =======================================================
   QUIZ SUBMISSION
======================================================= */

async function submitQuiz(answer) {
  if (!lessonData) {
    return;
  }

  try {
    const res = await apiFetch(
      `/api/lesson-quiz/${userId}/${lessonData.id}?answer=${encodeURIComponent(
        answer
      )}`,
      {
        method: "POST",
      }
    );

    const result = await res.json();

    if (!res.ok) {
      throw new Error(
        result.detail || "Quiz submission failed"
      );
    }

    if (result.correct) {
      alert("Quiz passed! 🎉 Lesson completed!");

      const updated = await apiFetch(
        `/api/lesson-progress/${userId}/${lessonData.id}`
      );

      if (updated.ok) {
        const updatedProgress = await updated.json();
        setProgress(updatedProgress);
      }

      /*
       * Refresh complete course.
       */
      await loadCourse(selectedLevel);

      /*
       * Close lesson so the
       * completed state is visible.
       */
      setLessonData(null);
      setProgress(null);

    } else {
      alert("Incorrect answer. Try again.");
    }

  } catch (err) {
    console.error(err);

    alert(
      err.message ||
        "Could not submit quiz."
    );
  }
}
  /* =======================================================
     LOADING
  ======================================================= */

  if (loading) {
    return (
      <div className="workspace course-page">

        <div className="workspace-header">

          <div>

            <div className="eyebrow">
              ENGLISH COURSE
            </div>

            <h1>
              Loading your course...
            </h1>

          </div>

        </div>

      </div>
    );
  }


  /* =======================================================
     ERROR
  ======================================================= */

  if (
    error &&
    topics.length === 0
  ) {
    return (
      <div className="workspace course-page">

        <div className="workspace-header">

          <div>

            <div className="eyebrow">
              ENGLISH COURSE
            </div>

            <h2>
              Something went wrong
            </h2>

            <p>
              {error}
            </p>

            <button
              className="primary-btn"
              onClick={() =>
                loadCourse()
              }
            >
              Try again
            </button>

          </div>

        </div>

      </div>
    );
  }


  /* =======================================================
     SELECTED LEVEL DATA
  ======================================================= */

  const selectedLevelTopics =
    topics.filter(
      (topic) =>
        topic.level ===
        selectedLevel
    );


  const selectedLevelInfo =
    levels.find(
      (item) =>
        item.level ===
        selectedLevel
    );


  const completedCount =
    selectedLevelTopics.filter(
      (topic) =>
        topic.completed
    ).length;


  const selectedLevelComplete =
    selectedLevelTopics.length > 0 &&
    completedCount ===
      selectedLevelTopics.length;


  const overallCompletedCount =
    topics.filter(
      (topic) =>
        topic.completed
    ).length;


  const overallCourseComplete =
    topics.length > 0 &&
    overallCompletedCount ===
      topics.length;


  const selectedProgress =
    selectedLevelInfo?.progress ??
    (
      selectedLevelTopics.length > 0
        ? Math.round(
            (
              completedCount /
              selectedLevelTopics.length
            ) * 100
          )
        : 0
    );


  /*
   * Find next level.
   */

  const selectedLevelIndex =
    LEVELS.indexOf(
      selectedLevel
    );


  const nextLevel =
    selectedLevelIndex >= 0 &&
    selectedLevelIndex <
      LEVELS.length - 1
      ? LEVELS[
          selectedLevelIndex + 1
        ]
      : null;


  const nextLevelInfo =
    nextLevel
      ? levels.find(
          (item) =>
            item.level ===
            nextLevel
        )
      : null;


  /* =======================================================
     LEVEL DISPLAY NAME
  ======================================================= */

  const levelDescription = {
    A1: "Beginner Foundation",
    A2: "Elementary English",
    B1: "Intermediate English",
    B2: "Upper-Intermediate English",
    C1: "Advanced English",
    C2: "English Mastery",
  };


  /* =======================================================
     LESSON DETAIL
  ======================================================= */

  if (lessonData) {
    return (
      <div className="workspace course-page">

        {/* =================================================
            LESSON TOP BAR
        ================================================= */}

        <div className="lesson-topbar">

          <button
            className="lesson-back-btn"
            onClick={() => {
              setLessonData(null);
              setProgress(null);
              setError("");
            }}
          >
            <span>
              ←
            </span>

            Back to lessons
          </button>


          <div className="lesson-progress-mini">

            <span>
              {progress?.practice_completed
                ? "2"
                : "1"}
            </span>

            <small>
              of 2 completed
            </small>

          </div>

        </div>


        {/* =================================================
            LESSON HERO
        ================================================= */}

        <div className="lesson-hero">

          <div className="lesson-hero-content">

            <div className="lesson-label">

              <span className="lesson-label-dot" />

              {lessonData.level || selectedLevel}{" "}
              • LESSON{" "}
              {lessonData.lesson_order}

            </div>


            <h1>
              {lessonData.title}
            </h1>


            <p>
              Master this topic with simple explanations,
              examples and practice.
            </p>

          </div>


          <div className="lesson-hero-icon">
            Aa
          </div>

        </div>


        {/* =================================================
            LEARN
        ================================================= */}

        <section className="lesson-section">

          <div className="section-heading">

            <div className="section-number">
              01
            </div>

            <div>

              <span>
                LEARN
              </span>

              <h2>
                Understand the concept
              </h2>

            </div>

          </div>


          <div className="lesson-explanation-card">

            <div className="explanation-icon">
              ✦
            </div>


            <div>

              <span className="card-label">
                SIMPLE EXPLANATION
              </span>


              <p>
                {lessonData.learn?.explanation ||
                  lessonData.explanation ||
                  "Study this English concept carefully and review the examples below."}
              </p>

            </div>

          </div>

        </section>


        {/* =================================================
            EXAMPLES
        ================================================= */}

        <section className="lesson-section">

          <div className="section-heading">

            <div className="section-number">
              02
            </div>

            <div>

              <span>
                EXAMPLES
              </span>

              <h2>
                See it in action
              </h2>

            </div>

          </div>


          <div className="lesson-examples">

            {(
              lessonData.learn?.examples ||
              lessonData.examples ||
              []
            ).map(
              (example, index) => (

                <div
                  className="lesson-example-card"
                  key={index}
                >

                  <div className="example-number">
                    {String(
                      index + 1
                    ).padStart(
                      2,
                      "0"
                    )}
                  </div>


                  <div className="example-content">

                    <span>
                      EXAMPLE
                    </span>

                    <p>
                      {example}
                    </p>

                  </div>


                  <div className="example-check">
                    ✓
                  </div>

                </div>

              )
            )}

          </div>

        </section>


        {/* =================================================
            PRACTICE
        ================================================= */}

        <section className="lesson-section">

          <div className="section-heading">

            <div className="section-number">
              03
            </div>

            <div>

              <span>
                PRACTICE
              </span>

              <h2>
                Test your understanding
              </h2>

            </div>

          </div>


          <div className="practice-panel">

            <div className="practice-panel-top">

              <div className="practice-icon">
                ?
              </div>


              <div>

                <span className="card-label">
                  QUICK PRACTICE
                </span>


                <h3>
                  {lessonData.practice?.question ||
                    lessonData.practice_question ||
                    "Choose the correct answer."}
                </h3>

              </div>

            </div>


            <div className="lesson-options">

              {(
                lessonData.practice?.options ||
                lessonData.practice_options ||
                []
              ).map(
                (option, index) => (

                  <button
                    key={index}
                    className="lesson-option"
                    onClick={() =>
                      submitPractice(
                        index
                      )
                    }
                  >

                    <span className="option-letter">

                      {String.fromCharCode(
                        65 + index
                      )}

                    </span>


                    <span className="option-text">
                      {option}
                    </span>


                    <Icon
                      name="arrow"
                      size={17}
                    />

                  </button>

                )
              )}

            </div>

          </div>

        </section>


        {/* =================================================
            PRACTICE SUCCESS
        ================================================= */}

        {progress?.practice_completed && (

          <div className="lesson-success">

            <div className="success-icon">
              ✓
            </div>


            <div>

              <span>
                PRACTICE COMPLETED
              </span>


              <h3>
                Great work! You're ready for the quiz.
              </h3>


              <p>
                You successfully completed the practice.
                Now test what you've learned.
              </p>

            </div>

          </div>

        )}


        {/* =================================================
            FINAL QUIZ
        ================================================= */}

        {progress?.practice_completed && (

          <section className="lesson-section quiz-section">

            <div className="section-heading">

              <div className="section-number">
                04
              </div>

              <div>

                <span>
                  FINAL QUIZ
                </span>

                <h2>
                  Complete the lesson
                </h2>

              </div>

            </div>


            <div className="quiz-panel">

              <div className="quiz-header">

                <div className="quiz-icon">
                  ✓
                </div>


                <div>

                  <span className="card-label">
                    LESSON QUIZ
                  </span>


                  <h3>
                    {lessonData.quiz?.question ||
                      lessonData.quiz_question ||
                      "Choose the correct answer."}
                  </h3>

                </div>

              </div>


              <div className="lesson-options">

                {(
                  lessonData.quiz?.options ||
                  lessonData.quiz_options ||
                  []
                ).map(
                  (option, index) => (

                    <button
                      key={index}
                      className="lesson-option"
                      onClick={() =>
                        submitQuiz(
                          index
                        )
                      }
                    >

                      <span className="option-letter">

                        {String.fromCharCode(
                          65 + index
                        )}

                      </span>


                      <span className="option-text">
                        {option}
                      </span>


                      <Icon
                        name="arrow"
                        size={17}
                      />

                    </button>

                  )
                )}

              </div>

            </div>

          </section>

        )}

      </div>
    );
  }


  /* =======================================================
     COURSE COMPLETION
  ======================================================= */

  if (
    selectedLevelComplete &&
    !showAllLessons
  ) {
    return (
      <div className="workspace course-page">

        <div className="course-completion-screen">

          <div className="completion-glow">
            ✦
          </div>


          <div className="completion-card">

            <div className="completion-icon">
              ✓
            </div>


            <div className="completion-eyebrow">
              LEVEL COMPLETED
            </div>


            <h2>
              {selectedLevel} English
            </h2>


            <p className="completion-message">
              Congratulations! You completed every
              lesson in your {selectedLevel} learning path.
            </p>


            <div className="completion-stats">

              <div className="completion-stat">

                <strong>
                  {completedCount}
                </strong>

                <span>
                  Lessons
                </span>

              </div>


              <div className="completion-stat">

                <strong>
                  100%
                </strong>

                <span>
                  Complete
                </span>

              </div>


              <div className="completion-stat">

                <strong>
                  {selectedLevel}
                </strong>

                <span>
                  Level
                </span>

              </div>

            </div>


            {/* =================================================
                ACTIONS
            ================================================= */}

            <div className="completion-actions">

              {nextLevel ? (

                <button
                  className="primary-btn completion-primary-btn"
                  onClick={() => {

                    setShowAllLessons(
                      false
                    );

                    setShowNextCourse(
                      false
                    );

                    setLessonData(
                      null
                    );

                    setProgress(
                      null
                    );

                    selectLevel(
                      nextLevel
                    );

                  }}
                >
                  <span>
                    →
                  </span>

                  Continue to{" "}
                  {nextLevel}

                </button>

              ) : (

                <button
                  className="primary-btn completion-primary-btn"
                  onClick={() =>
                    setShowAchievement(
                      true
                    )
                  }
                >
                  <span>
                    ✦
                  </span>

                  View Final Achievement
                </button>

              )}


              <button
                className="lesson-back-btn completion-review-btn"
                onClick={() =>
                  setShowAchievement(
                    true
                  )
                }
              >
                <span>
                  ✦
                </span>

                View Achievement
              </button>


              <button
                className="lesson-back-btn completion-review-btn"
                onClick={() =>
                  setShowAllLessons(
                    true
                  )
                }
              >
                Review all lessons

                <span>
                  →
                </span>

              </button>

            </div>

          </div>


          <div className="completion-footer">

            <span>
              ✓
            </span>

            You've completed your{" "}
            {selectedLevel} learning path.
            Keep practicing to improve your English.

          </div>

        </div>

      </div>
    );
  }


  /* =======================================================
     COURSE MAIN PAGE
  ======================================================= */

  return (
    <div className="workspace course-page">

      {/* =====================================================
          COURSE HEADER
      ===================================================== */}

      <div className="workspace-header">

        <div>

          <div className="eyebrow">
            ENGLISH COURSE
          </div>


          <h1>
            Learn English step by step.
          </h1>


          <p>
            Complete each lesson to unlock the next one.
          </p>

        </div>


        <div className="online-badge">

          <span />

          {selectedLevel} COURSE

        </div>

      </div>


      {/* =====================================================
          ERROR
      ===================================================== */}

      {error && (
        <div className="voice-error">
          {error}
        </div>
      )}


      {/* =====================================================
          CEFR LEVEL SELECTOR
      ===================================================== */}

      <div
        className="course-level-selector"
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(6, minmax(0, 1fr))",
          gap: "10px",
          marginBottom: "28px",
        }}
      >

        {LEVELS.map(
          (level) => {

            const info =
              levels.find(
                (item) =>
                  item.level ===
                  level
              );


            const unlocked =
              info
                ? info.unlocked
                : level === "A1";


            const completed =
              info
                ? info.completed_level
                : false;


            const progressValue =
              info?.progress ?? 0;


            return (
              <button
                key={level}
                type="button"
                disabled={!unlocked}
                onClick={() =>
                  selectLevel(
                    level
                  )
                }
                style={{
                  border:
                    selectedLevel ===
                    level
                      ? "2px solid currentColor"
                      : "1px solid rgba(255,255,255,0.12)",

                  borderRadius:
                    "14px",

                  padding:
                    "14px 10px",

                  background:
                    selectedLevel ===
                    level
                      ? "rgba(255,255,255,0.08)"
                      : "rgba(255,255,255,0.03)",

                  color:
                    unlocked
                      ? "inherit"
                      : "rgba(255,255,255,0.35)",

                  cursor:
                    unlocked
                      ? "pointer"
                      : "not-allowed",

                  opacity:
                    unlocked
                      ? 1
                      : 0.55,

                  textAlign:
                    "center",
                }}
              >

                <div
                  style={{
                    fontWeight:
                      800,
                    fontSize:
                      "16px",
                  }}
                >
                  {level}
                </div>


                <div
                  style={{
                    fontSize:
                      "11px",
                    marginTop:
                      "4px",
                    opacity:
                      0.7,
                  }}
                >
                  {completed
                    ? "✓ Completed"
                    : unlocked
                    ? `${progressValue}%`
                    : "🔒 Locked"}
                </div>

              </button>
            );
          }
        )}

      </div>


      {/* =====================================================
          COURSE HEADING
      ===================================================== */}

      <div className="course-container">

        <div className="course-heading">

          <div>

            <div className="course-kicker">
              {selectedLevel} COURSE
            </div>


            <h2>
              {selectedLevel} Learning Path
            </h2>


            <p>
              {levelDescription[
                selectedLevel
              ] ||
                "Build your English step by step."}
              {" "}
              Complete each lesson to unlock the next one.
            </p>

          </div>


          <div className="course-progress-badge">

            <span>
              ✦
            </span>


            <div>

              <strong>
                {completedCount}/
                {selectedLevelTopics.length}
              </strong>


              <small>
                Lessons
              </small>

            </div>

          </div>

        </div>


        {/* =====================================================
            LEVEL PROGRESS
        ===================================================== */}

        <div
          className="course-level-progress"
          style={{
            marginBottom:
              "26px",
          }}
        >

          <div
            style={{
              display:
                "flex",
              justifyContent:
                "space-between",
              alignItems:
                "center",
              marginBottom:
                "8px",
            }}
          >

            <span>
              {selectedLevel} Progress
            </span>


            <strong>
              {selectedProgress}%
            </strong>

          </div>


          <div
            style={{
              height:
                "7px",
              borderRadius:
                "999px",
              background:
                "rgba(255,255,255,0.08)",
              overflow:
                "hidden",
            }}
          >

            <div
              style={{
                width:
                  `${selectedProgress}%`,
                height:
                  "100%",
                borderRadius:
                  "999px",
                background:
                  "currentColor",
                transition:
                  "width 0.35s ease",
              }}
            />

          </div>

        </div>


        {/* =====================================================
            REVIEW BUTTON
        ===================================================== */}

        {selectedLevelComplete &&
          showAllLessons && (

            <button
              className="lesson-back-btn"
              style={{
                marginBottom:
                  "22px",
              }}
              onClick={() =>
                setShowAllLessons(
                  false
                )
              }
            >

              <span>
                ←
              </span>

              Back to completion

            </button>

          )}


        {/* =====================================================
            LESSON LIST
        ===================================================== */}

        <div className="course-lessons">

          {selectedLevelTopics.map(
            (topic, index) => {

              /*
               * Find previous lesson from
               * the COMPLETE course list,
               * not just selected level.
               */

              const globalIndex =
                topics.findIndex(
                  (item) =>
                    item.id ===
                    topic.id
                );


              const previousTopic =
                globalIndex > 0
                  ? topics[
                      globalIndex -
                        1
                    ]
                  : null;


              /*
               * First A1 lesson is unlocked.
               *
               * For every other lesson,
               * previous lesson must be complete.
               */

              const locked =
                !topic.completed &&
                previousTopic !==
                  null &&
                !previousTopic.completed;


              /*
               * Also respect backend
               * level locking.
               */

              const levelLocked =
                selectedLevelInfo &&
                !selectedLevelInfo.unlocked;


              const isLocked =
                locked ||
                levelLocked;


              return (
                <button
                  key={topic.id}
                  type="button"
                  className={`course-lesson ${
                    topic.completed
                      ? "completed"
                      : isLocked
                      ? "locked"
                      : "available"
                  }`}
                  disabled={
                    isLocked
                  }
                  onClick={() =>
                    openLesson(
                      topic.id
                    )
                  }
                >

                  {/* =================================================
                      LESSON NUMBER
                  ================================================= */}

                  <div className="course-lesson-number">

                    {topic.completed
                      ? "✓"
                      : index + 1}

                  </div>


                  {/* =================================================
                      LESSON CONTENT
                  ================================================= */}

                  <div className="course-lesson-content">

                    <div className="course-lesson-top">

                      <span className="course-category">
                        {topic.category}
                      </span>


                      <span className="course-level">
                        {topic.level}
                      </span>

                    </div>


                    <h3>
                      {topic.title}
                    </h3>


                    <p>

                      {topic.completed
                        ? "Lesson completed — great work!"
                        : isLocked
                        ? "Complete the previous lesson to unlock this."
                        : "Continue your English learning journey."}

                    </p>

                  </div>


                  {/* =================================================
                      ACTION
                  ================================================= */}

                  <div className="course-lesson-action">

                    {topic.completed ? (

                      <>

                        <span className="completed-text">
                          Completed
                        </span>


                        <span className="completed-check">
                          ✓
                        </span>

                      </>

                    ) : isLocked ? (

                      <>

                        <span className="lock-icon">
                          🔒
                        </span>


                        <span>
                          Locked
                        </span>

                      </>

                    ) : (

                      <>

                        <span>
                          Start
                        </span>


                        <Icon
                          name="arrow"
                          size={17}
                        />

                      </>

                    )}

                  </div>

                </button>
              );
            }
          )}

        </div>


        {/* =====================================================
            EMPTY LEVEL SAFETY
        ===================================================== */}

        {selectedLevelTopics.length ===
          0 && (

          <div
            className="feature-card"
            style={{
              marginTop:
                "20px",
            }}
          >

            <h2>
              {selectedLevel} is being prepared
            </h2>


            <p>
              Lessons for this level will appear here
              once they are available.
            </p>

          </div>

        )}

      </div>


      {/* =====================================================
          ACHIEVEMENT MODAL
      ===================================================== */}

      {showAchievement && (

        <div
          className="achievement-overlay"
          onClick={() =>
            setShowAchievement(
              false
            )
          }
        >

          <div
            className="achievement-modal"
            onClick={(e) =>
              e.stopPropagation()
            }
          >

            <button
              className="achievement-close"
              onClick={() =>
                setShowAchievement(
                  false
                )
              }
            >
              ×
            </button>


            <div className="achievement-stars">
              ✦
            </div>


            <div className="achievement-small-title">
              ACHIEVEMENT UNLOCKED
            </div>


            <h2>
              {selectedLevel} English
            </h2>


            <p className="achievement-subtitle">
              Level Completion
            </p>


            <div className="achievement-divider" />


            <div className="achievement-name">
              Mangha
            </div>


            <p className="achievement-text">
              Successfully completed all lessons
              in the {selectedLevel} English Course.
            </p>


            <div className="achievement-result">

              <div>

                <strong>
                  {completedCount}/
                  {selectedLevelTopics.length}
                </strong>

                <span>
                  LESSONS
                </span>

              </div>


              <div>

                <strong>
                  100%
                </strong>

                <span>
                  COMPLETE
                </span>

              </div>


              <div>

                <strong>
                  {selectedLevel}
                </strong>

                <span>
                  LEVEL
                </span>

              </div>

            </div>


            <div className="achievement-footer">

              <span>
                AI LANGUAGE TUTOR
              </span>


              <span>
                ✓ COMPLETED
              </span>

            </div>

          </div>

        </div>

      )}


      {/* =====================================================
          NEXT LEVEL MODAL
      ===================================================== */}

      {showNextCourse &&
        nextLevel && (

        <div
          className="achievement-overlay"
          onClick={() =>
            setShowNextCourse(
              false
            )
          }
        >

          <div
            className="achievement-modal next-course-modal"
            onClick={(e) =>
              e.stopPropagation()
            }
          >

            <button
              className="achievement-close"
              onClick={() =>
                setShowNextCourse(
                  false
                )
              }
            >
              ×
            </button>


            <div className="achievement-stars">
              →
            </div>


            <div className="achievement-small-title">
              NEXT LEARNING PATH
            </div>


            <h2>
              {nextLevel} English
            </h2>


            <p className="achievement-subtitle">
              {levelDescription[
                nextLevel
              ]}
            </p>


            <div className="achievement-divider" />


            <p className="achievement-text">
              You've completed your{" "}
              {selectedLevel} foundation.
              Your next step is the{" "}
              {nextLevel} learning path.
            </p>


            <div className="achievement-result">

              <div>

                <strong>
                  {nextLevelInfo?.total ||
                    0}
                </strong>

                <span>
                  LESSONS
                </span>

              </div>


              <div>

                <strong>
                  {nextLevel}
                </strong>

                <span>
                  LEVEL
                </span>

              </div>


              <div>

                <strong>
                  NEW
                </strong>

                <span>
                  PATH
                </span>

              </div>

            </div>


            <button
              className="primary-btn completion-primary-btn"
              style={{
                width:
                  "100%",
                marginTop:
                  "25px",
              }}
              onClick={() => {

                setShowNextCourse(
                  false
                );

                setSelectedLevel(
                  nextLevel
                );

                loadCourse(
                  nextLevel
                );

              }}
            >

              Start{" "}
              {nextLevel} Journey →

            </button>

          </div>

        </div>

      )}

    </div>
  );
}

/* =========================================================
   VOICE ENGINE
========================================================= */

function useVoice(onResult) {
  const [engine, setEngine] =
    useState("none");

  const [status, setStatus] =
    useState("idle");

  const [message, setMessage] =
    useState("");

  const recorder = useRef(null);
  const timer = useRef(null);
  const recognition = useRef(null);

  const audioContext = useRef(null);
  const analyser = useRef(null);
  const silenceAnimation = useRef(null);
  const silenceStarted = useRef(null);
  const hasSpoken = useRef(false);

 const MAX_RECORD_MS = 15000;
 const SILENCE_DELAY_MS = 700;
 const SILENCE_THRESHOLD = 0.018;

  useEffect(() => {
    const Browser =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition;

    if (Browser) {
      setEngine("browser");
    }

    apiFetch("/api/health")
      .then((r) => {
        if (!r.ok) {
          throw new Error();
        }

        return r.json();
      })
      .then(() => {
        if (
          window.MediaRecorder &&
          navigator.mediaDevices?.getUserMedia
        ) {
          setEngine("local");
        } else if (Browser) {
          setEngine("browser");
        }
      })
      .catch(() => {
        if (
          window.MediaRecorder &&
          navigator.mediaDevices?.getUserMedia
        ) {
          setEngine("local");
        } else if (Browser) {
          setEngine("browser");
        }
      });

    return () => {
      clearTimeout(timer.current);

      if (silenceAnimation.current) {
        cancelAnimationFrame(
          silenceAnimation.current
        );
      }

      if (audioContext.current) {
        audioContext.current
          .close()
          .catch(() => {});
      }
    };
  }, []);

  function cleanupAudioDetection() {
    if (silenceAnimation.current) {
      cancelAnimationFrame(
        silenceAnimation.current
      );

      silenceAnimation.current = null;
    }

    silenceStarted.current = null;
    hasSpoken.current = false;

    if (audioContext.current) {
      audioContext.current
        .close()
        .catch(() => {});

      audioContext.current = null;
    }

    analyser.current = null;
  }

  function monitorSilence(rec) {
    if (!analyser.current) {
      return;
    }

    const analyserNode =
      analyser.current;

    const data = new Uint8Array(
      analyserNode.fftSize
    );

    function checkAudio() {
      if (rec.state !== "recording") {
        return;
      }

      analyserNode.getByteTimeDomainData(
        data
      );

      let sum = 0;

      for (
        let i = 0;
        i < data.length;
        i++
      ) {
        const normalized =
          (data[i] - 128) / 128;

        sum +=
          normalized *
          normalized;
      }

      const rms = Math.sqrt(
        sum / data.length
      );

      if (rms > SILENCE_THRESHOLD) {
        hasSpoken.current = true;
        silenceStarted.current = null;
      } else if (hasSpoken.current) {
        if (!silenceStarted.current) {
          silenceStarted.current =
            Date.now();
        }

        if (
          Date.now() -
            silenceStarted.current >=
          SILENCE_DELAY_MS
        ) {
          rec.stop();
          return;
        }
      }

      silenceAnimation.current =
        requestAnimationFrame(
          checkAudio
        );
    }

    checkAudio();
  }

  async function startLocal() {
    try {
      const stream =
        await navigator.mediaDevices.getUserMedia({
          audio: true,
        });

      const mimeType =
        [
          "audio/webm;codecs=opus",
          "audio/webm",
          "audio/ogg;codecs=opus",
        ].find((t) =>
          MediaRecorder.isTypeSupported(t)
        ) || "";

      const rec =
        new MediaRecorder(
          stream,
          mimeType
            ? { mimeType }
            : undefined
        );

      const chunks = [];

      try {
        const AudioContext =
          window.AudioContext ||
          window.webkitAudioContext;

        if (AudioContext) {
          const context =
            new AudioContext();

          const source =
            context.createMediaStreamSource(
              stream
            );

          const analyserNode =
            context.createAnalyser();

          analyserNode.fftSize = 2048;

          analyserNode.smoothingTimeConstant =
            0.2;

          source.connect(
            analyserNode
          );

          audioContext.current =
            context;

          analyser.current =
            analyserNode;
        }
      } catch {
        // Recording still works.
      }

      rec.ondataavailable = (e) => {
        if (e.data.size) {
          chunks.push(e.data);
        }
      };

      rec.onstop = async () => {
        clearTimeout(timer.current);

        cleanupAudioDetection();

        stream
          .getTracks()
          .forEach((t) =>
            t.stop()
          );

        setStatus("processing");
        setMessage("");

        try {
          const blob = new Blob(
            chunks,
            {
              type: rec.mimeType,
            }
          );

          const formData =
            new FormData();

          const extension =
            rec.mimeType.includes(
              "ogg"
            )
              ? "ogg"
              : "webm";

          formData.append(
            "file",
            blob,
            `recording.${extension}`
          );

          const res =
            await apiFetch(
              "/api/transcribe",
              {
                method: "POST",
                body: formData,
              }
            );

          const data =
            await res.json();

          if (!res.ok) {
            throw new Error(
              data.detail ||
                "Transcription failed"
            );
          }

          if (!data.transcript) {
            setMessage(
              "I could not hear anything. Please try again."
            );
          } else {
            setMessage("");

            onResult(
              data.transcript,
              data.words
            );
          }
        } catch (err) {
          setMessage(
            String(
              err.message || err
            )
          );
        } finally {
          setStatus("idle");
        }
      };

      recorder.current = rec;

      rec.start();

      setStatus("recording");
      setMessage("");

      if (analyser.current) {
        monitorSilence(rec);
      }

      timer.current =
        setTimeout(() => {
          if (
            rec.state ===
            "recording"
          ) {
            rec.stop();
          }
        }, MAX_RECORD_MS);
    } catch {
      cleanupAudioDetection();

      setMessage(
        "Microphone blocked. Allow microphone access in your browser."
      );

      setStatus("idle");
    }
  }

  function startBrowser() {
    const Browser =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition;

    if (!Browser) {
      setMessage(
        "Speech recognition is not supported."
      );

      return;
    }

    const rec = new Browser();

    rec.lang = "en-US";
    rec.interimResults = false;
    rec.continuous = false;

    rec.onresult = (e) => {
      setMessage("");

      onResult(
        e.results[0][0]
          .transcript,
        null
      );
    };

    rec.onerror = (e) => {
      setMessage(
        e.error ===
          "not-allowed"
          ? "Microphone blocked. Allow microphone access."
          : `Speech recognition error: ${e.error}`
      );

      setStatus("idle");
    };

    rec.onend = () => {
      setStatus("idle");
    };

    recognition.current = rec;

    setMessage("");
    setStatus("recording");

    try {
      rec.start();
    } catch {
      setStatus("idle");

      setMessage(
        "Could not start speech recognition."
      );
    }
  }

  function toggle() {
    if (status === "processing") {
      return;
    }

    if (status === "recording") {
      if (engine === "local") {
        recorder.current?.stop();
      } else {
        recognition.current?.stop();
      }

      return;
    }

    if (engine === "local") {
      startLocal();
    } else {
      startBrowser();
    }
  }

  return {
    engine,
    status,
    message,
    toggle,
  };
}

function DailySpeakingPractice() {
  const topics = [
    {
      title: "My Daily Routine",
      prompt: "Tell me about your daily routine, from waking up to going to bed."
    },
    {
      title: "My University",
      prompt: "Talk about your university, your classes, and what you are learning."
    },
    {
      title: "My Future Goals",
      prompt: "Describe your career goals and explain why you chose Artificial Intelligence."
    },
    {
      title: "A Memorable Day",
      prompt: "Talk about a memorable day in your life and explain why it was special."
    },
    {
      title: "Technology and AI",
      prompt: "Explain how artificial intelligence can help people in everyday life."
    }
  ];

  const [topicIndex, setTopicIndex] = React.useState(0);
  const [transcript, setTranscript] = React.useState("");
  const [listening, setListening] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [result, setResult] = React.useState(null);
  const [error, setError] = React.useState("");
  const [speakingFeedback, setSpeakingFeedback] = React.useState(false);

  const recognitionRef = React.useRef(null);
  const audioRef = React.useRef(null);

  const topic = topics[topicIndex];

  function startRecording() {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setError(
        "Voice recognition is not supported in this browser. Please use the latest Google Chrome."
      );
      return;
    }

    setError("");

    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onstart = () => {
      setListening(true);
      setError("");
    };

    recognition.onresult = (event) => {
      let finalText = "";
      let interimText = "";

      for (let i = 0; i < event.results.length; i++) {
        const text = event.results[i][0].transcript;

        if (event.results[i].isFinal) {
          finalText += text + " ";
        } else {
          interimText += text;
        }
      }

      const previousFinal = Array.from(event.results)
        .filter((item) => item.isFinal)
        .map((item) => item[0].transcript)
        .join(" ")
        .trim();

      setTranscript(
        (previousFinal + (interimText ? " " + interimText : "")).trim()
      );
    };

    recognition.onerror = (event) => {
      if (event.error !== "no-speech" && event.error !== "aborted") {
        setError("Voice recognition error: " + event.error);
      }
    };

    recognition.onend = () => {
      setListening(false);
    };

    recognitionRef.current = recognition;
    recognition.start();
  }

  function stopRecording() {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }

    setListening(false);
  }

  async function getFeedback() {
    const text = transcript.trim();

    if (!text) {
      setError("Pehle apni speaking record karo ya text enter karo.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(
        "http://127.0.0.1:8010/api/speaking-feedback",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ text: text,
          user_id: getUserId()})
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Feedback generate nahi hua.");
      }

      setResult(data);
    } catch (err) {
      setError(
        err.message || "Backend se connection nahi ho raha. Backend check karo."
      );
    } finally {
      setLoading(false);
    }
  }

  async function playFeedback() {
    if (!result?.feedback) return;

    setSpeakingFeedback(true);
    setError("");

    try {
      const response = await fetch("http://127.0.0.1:8020/tts", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          text: result.feedback,
          voice: "af_heart"
        })
      });

      if (!response.ok) {
        throw new Error("Voice service response: " + response.status);
      }

      const blob = await response.blob();
      const audioUrl = URL.createObjectURL(blob);

      if (audioRef.current) {
        audioRef.current.pause();
        URL.revokeObjectURL(audioRef.current.src);
      }

      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
        setSpeakingFeedback(false);
      };

      audio.onerror = () => {
        URL.revokeObjectURL(audioUrl);
        setSpeakingFeedback(false);
        setError("Feedback audio play nahi ho saka.");
      };

      await audio.play();
    } catch (err) {
      setSpeakingFeedback(false);
      setError(
        "TTS service available nahi hai. Check karo ke Kokoro service port 8020 par chal rahi hai."
      );
    }
  }

  function nextTopic() {
    stopRecording();

    if (audioRef.current) {
      audioRef.current.pause();
    }

    setTopicIndex((current) => (current + 1) % topics.length);
    setTranscript("");
    setResult(null);
    setError("");
    setSpeakingFeedback(false);
  }

  React.useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }

      if (audioRef.current) {
        audioRef.current.pause();
      }
    };
  }, []);

  return (
    <div className="daily-practice">
      <div className="daily-practice-header">
        <div>
          <div className="daily-eyebrow">DAILY ENGLISH WORKOUT</div>
          <h1>Daily Speaking Practice</h1>
          <p>Speak naturally. Review your English. Improve every day.</p>
        </div>

        <div className="daily-topic-count">
          TOPIC {topicIndex + 1} / {topics.length}
        </div>
      </div>

      <section className="daily-topic-card">
        <div className="daily-eyebrow">TODAY'S TOPIC</div>
        <h2>{topic.title}</h2>
        <p>{topic.prompt}</p>
        <button type="button" onClick={nextTopic}>
          Next topic →
        </button>
      </section>

      <section className="daily-record-card">
        <h2>Your speaking session</h2>
        <p>
          Aaram se bolo. Jab complete ho jao, Stop dabao aur apna transcript
          review karo.
        </p>

        <div className="daily-record-actions">
          {!listening ? (
            <button type="button" onClick={startRecording}>
              🎙 Start speaking
            </button>
          ) : (
            <button type="button" onClick={stopRecording}>
              ⏹ Stop recording
            </button>
          )}

          <span className={listening ? "daily-live" : "daily-idle"}>
            {listening ? "Listening..." : "Ready to practise"}
          </span>
        </div>

        <label htmlFor="daily-transcript">Your transcript</label>
        <textarea
          id="daily-transcript"
          value={transcript}
          onChange={(event) => setTranscript(event.target.value)}
          placeholder="Your spoken English will appear here. You can also type your answer..."
          rows={7}
        />

        <div className="daily-record-actions">
          <button
            type="button"
            onClick={getFeedback}
            disabled={loading || listening || !transcript.trim()}
          >
            {loading ? "Analysing your English..." : "Get AI feedback"}
          </button>

          <button
            type="button"
            className="daily-secondary"
            onClick={() => {
              setTranscript("");
              setResult(null);
              setError("");
            }}
          >
            Clear
          </button>
        </div>

        {error && <p className="daily-error">{error}</p>}
      </section>

      {result && (
        <section className="daily-results">
          <div className="daily-results-heading">
            <div>
              <div className="daily-eyebrow">YOUR SESSION REPORT</div>
              <h2>Speaking feedback</h2>
            </div>

            <div className="daily-score">
              <strong>{result.grammar_score}</strong>
              <span>/100</span>
              <small>Estimated grammar score</small>
            </div>
          </div>

          <div className="daily-stat-grid">
            <div>
              <strong>{result.total_sentences}</strong>
              <span>Sentences</span>
            </div>
            <div>
              <strong>{result.error_count}</strong>
              <span>Corrections</span>
            </div>
          </div>

          <div className="daily-feedback-section">
            <h3>Corrected version</h3>
            <p>{result.corrected_text}</p>
          </div>

          {result.corrections?.length > 0 && (
            <div className="daily-feedback-section">
              <h3>Sentence corrections</h3>

              {result.corrections.map((item, index) => (
                <div className="daily-correction" key={index}>
                  <p className="daily-original">{item.original}</p>
                  <p className="daily-corrected">{item.corrected}</p>
                </div>
              ))}
            </div>
          )}

          <div className="daily-feedback-section">
            <h3>Coach's advice</h3>
            <p className="daily-coach-text">{result.feedback}</p>

            <button
              type="button"
              onClick={playFeedback}
              disabled={speakingFeedback}
            >
              {speakingFeedback
                ? "🔊 Playing feedback..."
                : "🔊 Listen to feedback"}
            </button>
          </div>

          <p className="daily-disclaimer">
            This is an estimated grammar score, not a certified measure of
            pronunciation or fluency.
          </p>
        </section>
      )}
    </div>
  );
}
function Vocabulary() {
  const [words, setWords] = useState(() => {
    try {
      const savedWords = localStorage.getItem("lt_vocabulary_words");

      if (savedWords) {
        const parsedWords = JSON.parse(savedWords);

        if (Array.isArray(parsedWords) && parsedWords.length > 0) {
          return parsedWords;
        }
      }
    } catch (error) {
      console.error("Vocabulary load error:", error);
    }

    return [
      {
        word: "Improve",
        meaning: "To become better",
        example: "I want to improve my English.",
        learned: false
      },
      {
        word: "Confident",
        meaning: "Believing in yourself",
        example: "I feel confident when I practice.",
        learned: false
      },
      {
        word: "Practice",
        meaning: "To do something repeatedly to get better",
        example: "I practice English every day.",
        learned: false
      }
    ];
  });

  const [index, setIndex] = useState(0);
  const [showMeaning, setShowMeaning] = useState(false);
  const [newWord, setNewWord] = useState("");
  const [newMeaning, setNewMeaning] = useState("");
  const [newExample, setNewExample] = useState("");
  const [formError, setFormError] = useState("");
    useEffect(() => {
    try {
      localStorage.setItem(
        "lt_vocabulary_words",
        JSON.stringify(words)
      );
    } catch (error) {
      console.error("Vocabulary save error:", error);
    }
  }, [words]);

  const current = words[index];
  const learnedCount = words.filter((word) => word.learned).length;

  function nextWord() {
    setIndex((index + 1) % words.length);
    setShowMeaning(false);
  }

  function previousWord() {
    setIndex((index - 1 + words.length) % words.length);
    setShowMeaning(false);
  }

  function markLearned() {
    setWords((previous) =>
      previous.map((word, i) =>
        i === index ? { ...word, learned: !word.learned } : word
      )
    );
  }

  function addWord(event) {
    event.preventDefault();

    if (!newWord.trim() || !newMeaning.trim() || !newExample.trim()) {
      setFormError("Please fill in all three fields.");
      return;
    }

    const exists = words.some(
      (word) => word.word.toLowerCase() === newWord.trim().toLowerCase()
    );

    if (exists) {
      setFormError("This word already exists.");
      return;
    }

    const updatedWords = [
      ...words,
      {
        word: newWord.trim(),
        meaning: newMeaning.trim(),
        example: newExample.trim(),
        learned: false
      }
    ];

    setWords(updatedWords);
    setIndex(updatedWords.length - 1);
    setShowMeaning(true);
    setNewWord("");
    setNewMeaning("");
    setNewExample("");
    setFormError("");
  }

  return (
    <div className="page-content">
      <h1>Vocabulary Flashcards</h1>
      <p>Learn new English words, one card at a time.</p>

      <div className="card">
        <p>Word {index + 1} of {words.length}</p>
        <p>Learned: {learnedCount} / {words.length}</p>

        <h2>{current.word}</h2>

        {showMeaning && (
          <div>
            <p><strong>Meaning:</strong> {current.meaning}</p>
            <p><strong>Example:</strong> {current.example}</p>
          </div>
        )}

        <button onClick={() => setShowMeaning(!showMeaning)}>
          {showMeaning ? "Hide Meaning" : "Show Meaning"}
        </button>

        <button
          onClick={markLearned}
          style={{ marginLeft: "10px" }}
        >
          {current.learned ? "Mark as Not Learned" : "Mark as Learned"}
        </button>

        <div style={{ display: "flex", gap: "10px", marginTop: "16px" }}>
          <button onClick={previousWord}>Previous</button>
          <button onClick={nextWord}>Next Word</button>
        </div>
      </div>

      <div className="card" style={{ marginTop: "24px" }}>
        <h2>Add New Word</h2>

        <form onSubmit={addWord}>
          <input
            value={newWord}
            onChange={(event) => setNewWord(event.target.value)}
            placeholder="English word"
          />

          <input
            value={newMeaning}
            onChange={(event) => setNewMeaning(event.target.value)}
            placeholder="Meaning"
            style={{ display: "block", marginTop: "10px" }}
          />

          <input
            value={newExample}
            onChange={(event) => setNewExample(event.target.value)}
            placeholder="Example sentence"
            style={{ display: "block", marginTop: "10px" }}
          />

          {formError && <p>{formError}</p>}

          <button type="submit" style={{ marginTop: "12px" }}>
            Add Word
          </button>
        </form>
      </div>
    </div>
  );
}
function DailyStreak() {
  const [streakData, setStreakData] = useState(() => {
    try {
      const saved = localStorage.getItem("lt_daily_streak");
      if (saved) return JSON.parse(saved);
    } catch (error) {
      console.error("Could not load streak:", error);
    }

    return {
      lastPracticeDate: "",
      streak: 0,
      totalPracticeDays: 0
    };
  });

  function getToday() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  function recordPractice() {
    const today = getToday();

    if (streakData.lastPracticeDate === today) {
      return;
    }

    const yesterdayDate = new Date();
    yesterdayDate.setDate(yesterdayDate.getDate() - 1);

    const year = yesterdayDate.getFullYear();
    const month = String(yesterdayDate.getMonth() + 1).padStart(2, "0");
    const day = String(yesterdayDate.getDate()).padStart(2, "0");
    const yesterday = `${year}-${month}-${day}`;

    const nextStreak =
      streakData.lastPracticeDate === yesterday
        ? streakData.streak + 1
        : 1;

    const updated = {
      lastPracticeDate: today,
      streak: nextStreak,
      totalPracticeDays: streakData.totalPracticeDays + 1
    };

    setStreakData(updated);
    localStorage.setItem("lt_daily_streak", JSON.stringify(updated));
  }

  return (
    <div className="page-content">
      <h1>Daily Learning Streak 🔥</h1>
      <p>Practice English every day and build your learning habit.</p>

      <div className="card">
        <h2>{streakData.streak} day(s)</h2>
        <p>Current streak</p>

        <h3>{streakData.totalPracticeDays}</h3>
        <p>Total practice days recorded</p>

        <p>Last practice: {streakData.lastPracticeDate || "Not started yet"}</p>

        <button onClick={recordPractice}>
          I Practiced Today
        </button>

        {streakData.lastPracticeDate === getToday() && (
          <p>Today's practice is recorded. Great job!</p>
        )}
      </div>
    </div>
  );
}
function SmartVocabularyRevision() {
  const STORAGE_KEY = "lt_vocabulary_words";
  const REVIEW_KEY = "lt_vocabulary_review";
  const [words, setWords] = React.useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  
  React.useEffect(() => {
    try {
      const savedReview = JSON.parse(
        localStorage.getItem(REVIEW_KEY) || "[]"
      );

      if (!Array.isArray(savedReview) || savedReview.length === 0) {
        return;
      }

      setWords((previous) => {
        const updated = [...previous];

        const existingWords = new Set(
          updated.map((item) =>
            (item.word || "").trim().toLowerCase()
          )
        );

        let changed = false;

        savedReview.forEach((item) => {
          const key = (item.word || "").trim().toLowerCase();

          if (!key || existingWords.has(key)) return;

          updated.push({
            id: `review-${key.replace(/\s+/g, "-")}`,
            word: item.word,
            meaning: item.meaning || "",
            romanMeaning: item.romanMeaning || "",
            example: item.example || "",
            reviewCount: 0,
            mastered: false,
            nextReview: new Date().toISOString().slice(0, 10),
            wrongCount: item.wrongCount || 1,
          });

          existingWords.add(key);
          changed = true;
        });

        return changed ? updated : previous;
      });
    } catch (error) {
      console.error("Revision import error:", error);
    }
  }, []);


  const [currentIndex, setCurrentIndex] = React.useState(0);
  const [showAnswer, setShowAnswer] = React.useState(false);
  const [searchTerm, setSearchTerm] = React.useState("");
  const [statusFilter, setStatusFilter] = React.useState("All");
  const today = [
  new Date().getFullYear(),
  String(new Date().getMonth() + 1).padStart(2, "0"),
  String(new Date().getDate()).padStart(2, "0"),
].join("-");

  React.useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(words));
  }, [words]);

  const newWords = words.filter(
    (word) => !word.reviewCount && !word.mastered
  );

  const learningWords = words.filter(
    (word) => (word.reviewCount || 0) > 0 && !word.mastered
  );

  const masteredWords = words.filter((word) => word.mastered);

  const dueWords = words.filter(
    (word) =>
      !word.mastered &&
      (!word.nextReview || word.nextReview <= today)
  );
    function getReviewLabel(word) {
    if (word.mastered) return "Mastered";

    if (!word.nextReview || word.nextReview <= today) {
      return "Due today";
    }

    const todayDate = new Date(`${today}T12:00:00`);
    const reviewDate = new Date(`${word.nextReview}T12:00:00`);

    const days = Math.round(
      (reviewDate - todayDate) / (1000 * 60 * 60 * 24)
    );

    if (days <= 0) return "Due today";
    if (days === 1) return "Due tomorrow";

    return `Due in ${days} days`;
  }
    const filteredWords = words.filter((word) => {
    const matchesSearch = (word.word || "")
      .toLowerCase()
      .includes(searchTerm.toLowerCase());

    const status = word.mastered
      ? "Mastered"
      : (word.reviewCount || 0) > 0
      ? "Learning"
      : "New";

    const matchesStatus =
      statusFilter === "All" || status === statusFilter;

    return matchesSearch && matchesStatus;
  });
  const currentWord =
    dueWords.length > 0
      ? dueWords[currentIndex % dueWords.length]
      : null;

  const progress =
    words.length > 0
      ? Math.round((masteredWords.length / words.length) * 100)
      : 0;

  function reviewWord(remembered) {
    if (!currentWord) return;

    const nextReviewDate = new Date();
    nextReviewDate.setDate(
      nextReviewDate.getDate() + (remembered ? 3 : 1)
    );

  const nextReview = [
  nextReviewDate.getFullYear(),
  String(nextReviewDate.getMonth() + 1).padStart(2, "0"),
  String(nextReviewDate.getDate()).padStart(2, "0"),
].join("-");

    setWords((previous) =>
      previous.map((word) => {
        if (word.id !== currentWord.id) return word;

        const reviewCount = (word.reviewCount || 0) + 1;

        return {
          ...word,
          reviewCount,
          nextReview,
          mastered: remembered && reviewCount >= 3,
        };
      })
    );

    setCurrentIndex(0);
    setShowAnswer(false);
  }

  return (
    
    <div className="page-content">
      <h1>Smart Vocabulary Revision</h1>
      <p>Build your vocabulary through regular revision.</p>

      <div className="card">
        <h2>Your Learning Progress</h2>

        <div className="svr-progress-track">
          <div
            className="svr-progress-fill"
            style={{ width: `${progress}%` }}
          />
        </div>
        
        <p>{progress}% mastered</p>

        <div className="svr-status-grid">
          <div className="svr-status-item">
            <strong>{newWords.length}</strong>
            <span>New</span>
          </div>

          <div className="svr-status-item">
            <strong>{learningWords.length}</strong>
            <span>Learning</span>
          </div>

          <div className="svr-status-item">
            <strong>{masteredWords.length}</strong>
            <span>Mastered</span>
          </div>
        </div>
      </div>

      <div className="card">
                 <>
            {words
              .filter((word) => !word.mastered)
              .map((word) => (
                <p key={word.id || word.word} className="svr-next-review">
                  <strong>{word.word}</strong>
                  {" — "}
                  {getReviewLabel(word)}
                </p>
              ))}
          </>
                <div className="svr-search-panel">
        <input
          type="search"
          placeholder="Search vocabulary..."
          value={searchTerm}
          onChange={(event) => setSearchTerm(event.target.value)}
        />

        <select
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value)}
        >
          <option value="All">All Words</option>
          <option value="New">New</option>
          <option value="Learning">Learning</option>
          <option value="Mastered">Mastered</option>
        </select>

        <p>{filteredWords.length} words found</p>

        {filteredWords.length > 0 ? (
          filteredWords.map((word) => (
          <div key={word.id || word.word} className="...">
              <strong>{word.word}</strong>
              <span>
                {word.mastered
                  ? "Mastered"
                  : word.nextReview
                  ? `Due ${word.nextReview}`
                  : "New"}
              </span>
            </div>
          ))
        ) : (
          <p>No matching words found.</p>
        )}
      </div>

        {currentWord ? (
          <>
            <h2>{currentWord.word}</h2>
              <p className="svr-next-review">
              {getReviewLabel(currentWord)}
            </p>

            {showAnswer ? (
              <>
                <p>
                  <strong>Meaning:</strong>{" "}
                  {currentWord.meaning || "Meaning not added yet"}
                </p>

                {currentWord.example && (
                  <p>
                    <strong>Example:</strong>{" "}
                    {currentWord.example}
                  </p>
                )}

                <p>
                  <strong>Previous reviews:</strong>{" "}
                  {currentWord.reviewCount || 0}
                </p>

                <button onClick={() => reviewWord(false)}>
                  Need More Practice
                </button>

                <button onClick={() => reviewWord(true)}>
                  I Remembered
                </button>
              </>
            ) : (
              <button onClick={() => setShowAnswer(true)}>
                Show Meaning
              </button>
            )}
          </>
        ) : (
          <>
            <h2>All caught up!</h2>
            <p>No words are due for revision today.</p>
          </>
        )}
      </div>
    </div>
  );
}

function VocabularyQuiz() {
  const STORAGE_KEY = "lt_vocabulary_words";
  const HISTORY_KEY = "lt_vocabulary_quiz_history";
  const REVIEW_KEY = "lt_vocabulary_review";

  const DAILY_WORD_BANK = [
  { word: "Improve", meaning: "To make something better", romanMeaning: "Behtar banana", example: "I want to improve my English." },
  { word: "Confident", meaning: "Feeling sure about yourself", romanMeaning: "Apne aap par bharosa hona", example: "I feel confident when I speak English." },
  { word: "Practice", meaning: "To do something repeatedly to get better", romanMeaning: "Mashq karna", example: "I practice English every day." },
  { word: "Study", meaning: "To learn about a subject", romanMeaning: "Parhna aur seekhna", example: "I study AI at university." },
  { word: "Education", meaning: "The process of learning", romanMeaning: "Taleem", example: "Education helps us build a better future." },
  { word: "Achieve", meaning: "To successfully reach a goal", romanMeaning: "Maqsad hasil karna", example: "I want to achieve my goals." },
  { word: "Curious", meaning: "Eager to learn or know something", romanMeaning: "Jaanne ka shauq rakhna", example: "I am curious about AI." },
  { word: "Develop", meaning: "To grow or improve something", romanMeaning: "Taraqqi dena ya barhana", example: "I want to develop new skills." },
  { word: "Knowledge", meaning: "Information and understanding", romanMeaning: "Ilm aur samajh", example: "Reading increases our knowledge." },
  { word: "Challenge", meaning: "A difficult task or problem", romanMeaning: "Mushkil kaam ya masla", example: "Learning English is a challenge." },
  { word: "Effort", meaning: "The energy used to do something", romanMeaning: "Koshish", example: "Success requires effort." },
  { word: "Reliable", meaning: "Able to be trusted", romanMeaning: "Bharose ke qabil", example: "He is a reliable friend." },
  { word: "Opportunity", meaning: "A chance to do something", romanMeaning: "Mauqa", example: "This internship is a great opportunity." },
  { word: "Progress", meaning: "Movement toward improvement", romanMeaning: "Behtari ki taraf taraqqi", example: "I can see my progress." },
  { word: "Patient", meaning: "Able to wait calmly", romanMeaning: "Sabr karne wala", example: "Be patient while learning." },
  { word: "Discover", meaning: "To find or learn something new", romanMeaning: "Daryaft karna ya nayi cheez jaan-na", example: "We discover new ideas through research." },
  { word: "Explain", meaning: "To make something clear", romanMeaning: "Samjhana", example: "Please explain this topic." },
  { word: "Useful", meaning: "Helpful or practical", romanMeaning: "Faida mand", example: "This book is useful for students." },
  { word: "Decision", meaning: "A choice you make", romanMeaning: "Faisla", example: "I made a good decision." },
  { word: "Organize", meaning: "To arrange things properly", romanMeaning: "Tarteeb dena", example: "I organize my study schedule." },
  { word: "Achievable", meaning: "Possible to accomplish", romanMeaning: "Jo hasil kiya ja sake", example: "My daily target is achievable." },
  { word: "Communicate", meaning: "To share information with others", romanMeaning: "Baat cheet karna ya maloomat dena", example: "We communicate through language." },
  { word: "Focus", meaning: "To give attention to something", romanMeaning: "Tawajjo dena", example: "I focus on my studies." },
  { word: "Habit", meaning: "Something you do regularly", romanMeaning: "Aadat", example: "Reading is a good habit." },
  { word: "Motivate", meaning: "To encourage someone to act", romanMeaning: "Hosla dena", example: "My goals motivate me." },
  { word: "Prepare", meaning: "To get ready for something", romanMeaning: "Tayari karna", example: "I prepare for my exams." },
  { word: "Solve", meaning: "To find an answer to a problem", romanMeaning: "Hal karna", example: "I solve programming problems." },
  { word: "Understand", meaning: "To know the meaning of something", romanMeaning: "Samajhna", example: "I understand the lesson." },
  { word: "Wisdom", meaning: "The ability to make good judgments", romanMeaning: "Samajh boojh aur danishmandi", example: "Experience can give us wisdom." },
  { word: "Consistent", meaning: "Doing something regularly", romanMeaning: "Lagataar aur pabandi se kaam karna", example: "Consistent practice builds skills." }
];


  function getTodayKey() {
    const date = new Date();
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  const todayKey = getTodayKey();


const [words] = React.useState(() => {
  try {
    return JSON.parse(
      localStorage.getItem(STORAGE_KEY) || "[]"
    ).filter((word) => word.word && word.meaning);
  } catch {
    return [];
  }
});

const [reviewWords, setReviewWords] = React.useState(() => {
  try {
    return JSON.parse(
      localStorage.getItem(REVIEW_KEY) || "[]"
    );
  } catch {
    return [];
  }
});

React.useEffect(() => {
  localStorage.setItem(
    REVIEW_KEY,
    JSON.stringify(reviewWords)
  );
}, [reviewWords]);

const [history, setHistory] = React.useState(() => {
  try {
    const saved = JSON.parse(
      localStorage.getItem(HISTORY_KEY) || "[]"
    );

    return saved.filter(
      (item) =>
        Number.isFinite(item.score) &&
        Number.isFinite(item.total) &&
        item.total > 0 &&
        item.score >= 0 &&
        item.score <= item.total
    );
  } catch {
    return [];
  }
});

React.useEffect(() => {
  localStorage.setItem(
    HISTORY_KEY,
    JSON.stringify(history)
  );
}, [history]);


  // Keep the user's saved words and fill the daily list
  // with date-based words until there are 10.
  const dailyWords = React.useMemo(() => {
    const result = [];
    const used = new Set();

    function addWord(word) {
      const key = word.word.trim().toLowerCase();

      if (key && !used.has(key) && result.length < 10) {
        used.add(key);
        result.push({
          ...word,
          word: word.word.trim(),
          meaning: word.meaning.trim(),
        });
      }
    }

   
    // Add today's bank words first so updated meanings and
    // Roman Urdu are displayed. Then include saved words.
    const startIndex = Math.floor(
      new Date(`${todayKey}T12:00:00`).getTime() /
      86400000
    ) % DAILY_WORD_BANK.length;

    for (
      let i = 0;
      i < DAILY_WORD_BANK.length && result.length < 10;
      i++
    ) {
      addWord(
        DAILY_WORD_BANK[
          (startIndex + i) % DAILY_WORD_BANK.length
        ]
      );
    }

    words.forEach(addWord);

    return result;
  }, [todayKey, words]);

  const [questions, setQuestions] = React.useState([]);
  const [currentIndex, setCurrentIndex] = React.useState(0);
  const [selectedAnswer, setSelectedAnswer] = React.useState("");
  const [score, setScore] = React.useState(0);
  const [finished, setFinished] = React.useState(false);
  const [answered, setAnswered] = React.useState(false);

  function shuffle(items) {
    const result = [...items];

    for (let i = result.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [result[i], result[j]] = [result[j], result[i]];
    }

    return result;
  }

  function startQuiz() {
    if (dailyWords.length < 4) return;

    const quiz = shuffle(dailyWords)
      .slice(0, 4)
      .map((word) => {
        const wrongAnswers = shuffle(
          dailyWords.filter(
            (item) => item.meaning !== word.meaning
          )
        )
          .slice(0, 3)
          .map((item) => item.meaning);

        return {
          ...word,
          options: shuffle([
            word.meaning,
            ...wrongAnswers,
          ]),
        };
      });

    setQuestions(quiz);
    setCurrentIndex(0);
    setSelectedAnswer("");
    setScore(0);
    setFinished(false);
    setAnswered(false);
  }


function submitAnswer() {
  if (!selectedAnswer || answered) return;

  const currentQuestion = questions[currentIndex];
  const isCorrect =
    selectedAnswer === currentQuestion.meaning;

  if (isCorrect) {
    setScore((previous) => previous + 1);
  } else {
    setReviewWords((previous) => {
      const wordKey = currentQuestion.word
        .trim()
        .toLowerCase();

      const existing = previous.find(
        (item) =>
          item.word?.trim().toLowerCase() === wordKey
      );

      if (existing) {
        return previous.map((item) =>
          item.word?.trim().toLowerCase() === wordKey
            ? {
                ...item,
                wrongCount: (item.wrongCount || 0) + 1,
                lastWrong: new Date().toISOString(),
              }
            : item
        );
      }

      return [
        ...previous,
        {
          word: currentQuestion.word,
          meaning: currentQuestion.meaning,
          romanMeaning: currentQuestion.romanMeaning || "",
          example: currentQuestion.example || "",
          wrongCount: 1,
          lastWrong: new Date().toISOString(),
        },
      ];
    });
  }

  setAnswered(true);
}


  function nextQuestion() {
    if (currentIndex + 1 >= questions.length) {
      const finalScore = Math.min(score, questions.length);
      const total = questions.length;

      const attempt = {
        id: Date.now(),
        date: new Date().toLocaleString(),
        day: todayKey,
        score: finalScore,
        total,
        accuracy: total > 0
          ? Math.round((finalScore / total) * 100)
          : 0,
      };

      setHistory((previous) =>
        [attempt, ...previous].slice(0, 20)
      );

      setFinished(true);
      return;
    }

    setCurrentIndex((previous) => previous + 1);
    setSelectedAnswer("");
    setAnswered(false);
  }

  const question = questions[currentIndex];

  const bestAttempt = history.reduce(
    (best, item) =>
      !best || item.accuracy > best.accuracy
        ? item
        : best,
    null
  );

  return (
    <div className="page-content">
      <h1>Vocabulary Learning</h1>
      <p>Learn 10 new English words, practice their meanings, and revise what you have learned.</p>

      <div className="card">
        <h2>Today's 10 Words</h2>
        <p>{todayKey}</p>

        <div className="daily-vocabulary-list">
          {dailyWords.map((word) => (
            <div
              className="vq-history-item"
              key={word.word.toLowerCase()}
            >
              <strong>{word.word}</strong>
              <p>{word.meaning}</p>
              {word.romanMeaning && (
              <p>
                <strong>Roman Urdu:</strong> {word.romanMeaning}
              </p>
            )}
              {word.example && (
                <p>Example: {word.example}</p>
              )}
            </div>
          ))}
        </div>

        {!finished && questions.length === 0 && (
          <>
            <h2>Ready for today's quiz?</h2>
            <p>Answer 4 questions from today's vocabulary.</p>
            <button
              onClick={startQuiz}
              disabled={dailyWords.length < 4}
            >
              Start Daily Quiz
            </button>
          </>
        )}

        {questions.length > 0 && !finished && question && (
          <>
            <p>
              Question {currentIndex + 1} of {questions.length}
            </p>

            <h2>What does "{question.word}" mean?</h2>

            <div className="vq-options">
              {question.options.map((option, index) => (
                <button
                  key={`${index}-${option}`}
                  className={
                    selectedAnswer === option
                      ? "vq-option selected"
                      : "vq-option"
                  }
                  disabled={answered}
                  onClick={() => setSelectedAnswer(option)}
                >
                  {option}
                </button>
              ))}
            </div>

            {!answered ? (
              <button
                disabled={!selectedAnswer}
                onClick={submitAnswer}
              >
                Check Answer
              </button>
            ) : (
              <>
                <p
                  className={
                    selectedAnswer === question.meaning
                      ? "vq-correct"
                      : "vq-incorrect"
                  }
                >
                  {selectedAnswer === question.meaning
                    ? "Correct answer!"
                    : `Correct meaning: ${question.meaning}`}
                </p>

                {question.example && (
                  <p>Example: {question.example}</p>
                )}

                <button onClick={nextQuestion}>
                  {currentIndex + 1 === questions.length
                    ? "See Results"
                    : "Next Question"}
                </button>
              </>
            )}
          </>
        )}

        {finished && (
          <>
            <h2>Quiz Completed!</h2>
            <p>
              Your score:{" "}
              <strong>{score} / {questions.length}</strong>
            </p>
            <p>
              Accuracy:{" "}
              <strong>
                {questions.length > 0
                  ? Math.round(
                      (score / questions.length) * 100
                    )
                  : 0}%
              </strong>
            </p>

            <button onClick={startQuiz}>Try Again</button>
          </>
        )}

        <div className="vq-history">
          <h2>Quiz History</h2>

          <p>
            Best Score:{" "}
            <strong>
              {bestAttempt
                ? `${bestAttempt.score} / ${bestAttempt.total} (${bestAttempt.accuracy}%)`
                : "No attempts yet"}
            </strong>
          </p>

          {history.length === 0 ? (
            <p>Complete a quiz to see your history.</p>
          ) : (
            history.map((item) => (
              <div
                key={item.id}
                className="vq-history-item"
              >
                <strong>
                  {item.score} / {item.total} ({item.accuracy}%)
                </strong>
                <p>{item.date}</p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
/* =========================================================
   APP
========================================================= */

export default function App() {
  const [userId] =
  useState(getUserId);
  const [nextLesson, setNextLesson] = useState(null);
  const [nextLessonLoading, setNextLessonLoading] = useState(true);
  const [nextLessonError, setNextLessonError] = useState("");
  const [selectedRecommendedLessonId, setSelectedRecommendedLessonId] = useState(null);
  
useEffect(() => {
  async function loadNextLesson() {
    setNextLessonLoading(true);
    setNextLessonError("");

    try {
      const res = await apiFetch(
        `/api/next-lesson/${encodeURIComponent(userId)}`
      );

      if (!res.ok) {
        throw new Error(`Server error ${res.status}`);
      }

      const json = await res.json();

      setNextLesson(json.recommendation || null);
    } catch (err) {
      console.error("Next lesson error:", err);
      setNextLessonError("Could not load your next lesson.");
    } finally {
      setNextLessonLoading(false);
    }
  }

  loadNextLesson();
}, [userId]);

  const [messages, setMessages] =
    useState([GREETING]);

  const [input, setInput] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [profile, setProfile] =
    useState(null);

  const [speakingText, setSpeakingText] =
    useState("");

  const [tab, setTab] =
    useState("chat");

  const [theme, setTheme] =
    useState(
      localStorage.getItem(
        "lt_theme"
      ) || "dark"
    );

  const [voiceWords, setVoiceWords] =
    useState(null);

  const [voiceText, setVoiceText] =
    useState("");

  /* =====================================================
     VOICE
  ===================================================== */

  
 
 
const voice = useVoice((text, words) => {
  setInput(text);
  setVoiceText(text);
  setVoiceWords(words);
  setSpeakingText(text);
});



  
  // Speak AI reply using free browser voice
  const speakAI = (text) => {
    if (!text || !("speechSynthesis" in window)) {
      return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.rate = 0.95;
    utterance.pitch = 1;

    window.speechSynthesis.speak(utterance);
  };


  /* =====================================================
     THEME
  ===================================================== */

  useEffect(() => {
    document.documentElement.dataset.theme =
      theme;

    localStorage.setItem(
      "lt_theme",
      theme
    );
  }, [theme]);

  /* =====================================================
     LOAD PROFILE
  ===================================================== */

  useEffect(() => {
    apiFetch(
      `/api/profile/${userId}`
    )
      .then((r) => r.json())
      .then(setProfile)
      .catch(() => {});
  }, [userId]);

  /* =====================================================
     REFRESH PROFILE
  ===================================================== */

  function refreshProfile() {
    apiFetch(
      `/api/profile/${userId}`
    )
      .then((r) => r.json())
      .then(setProfile)
      .catch(() => {});
  }

  /* =====================================================
     SEND CHAT
  ===================================================== */

  async function send() {
    const text = input.trim();

    if (!text || loading) {
      return;
    }

    setMessages((m) => [
      ...m,
      {
        role: "user",
        reply: text,
      },
    ]);

    setInput("");

    setVoiceWords(null);
    setVoiceText("");

    setLoading(true);

    try {
      const res =
        await apiFetch(
          "/api/chat",
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body: JSON.stringify({
              message: text,

              user_id: userId,

              speech_words:
                text === voiceText
                  ? voiceWords
                  : null,
            }),
          }
        );

      if (!res.ok) {
        throw new Error(
          `Server error ${res.status}`
        );
      }

      const data =
        await res.json();
      
      setProfile(
        data.profile
      );

      setMessages((m) => [
        ...m,
        {
          role: "tutor",
          ...data,
        },
      ]);
    } catch {
      setMessages((m) => [
        ...m,
        {
          role: "tutor",

          reply:
            "I could not reach the server. Please make sure the backend is running on port 8010.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  /* =====================================================
     RESET PROGRESS
  ===================================================== */

  async function resetProgress() {
    const confirmed =
      window.confirm(
        "Are you sure you want to reset your learning progress?"
      );

    if (!confirmed) {
      return;
    }

    try {
      const res =
        await apiFetch(
          `/api/profile/${userId}`,
          {
            method: "DELETE",
          }
        );

      const data =
        await res.json();

      setProfile(data);

      setMessages([GREETING]);

      setInput("");
    } catch {
      alert(
        "Could not reset your progress."
      );
    }
  }

  /* =====================================================
     NAVIGATION
  ===================================================== */

  const navigation = [
    {
      id: "dashboard",
      label: "Dashboard",
      icon: "home",
    },

    {
      id: "chat",
      label: "AI Tutor",
      icon: "chat",
    },

    {
      id: "speaking",
      label: "Speaking",
      icon: "mic",
    },

    {
      id: "daily-practice",
      label: "Daily Practice",
      icon: "calendar",
    },

    {
      id: "course",
      label: "Course",
      icon: "book",
    },

    {
      id: "practice",
      label: "Practice",
      icon: "practice",
    },

    {
      id: "review",
      label: "Review",
      icon: "refresh",
    },

    {
      id: "vocabulary",
      label: "Vocabulary",
      icon: "cards",
    },
    {
      id: "smart-review",
      label: "Vocabulary Revision",
      icon: "review"
    },
    {
      id: "vocabulary-quiz",
      label: "Daily Quiz",
      icon: "review"
    },
    {
      id: "streak",
      label: "Daily Streak",
      icon: "flame",
    },
  ];

  function selectTab(id) {
    setTab(id);
  }
  /* =====================================================
     DASHBOARD DATA
  ===================================================== */

  const grammarScore =
    profile?.levels?.grammar
      ?.score ?? 0;

  const vocabScore =
    profile?.levels?.vocab
      ?.score ?? 0;

  const overallScore =
    profile?.levels?.overall
      ?.score ??
    profile?.accuracy ??
    0;

  const weakAreas =
    profile?.weak_areas ?? [];

  /* =====================================================
     MAIN UI
  ===================================================== */

  return (
    <div className="app-shell">

      {/* =================================================
         SIDEBAR
      ================================================= */}

      <aside className="sidebar">

        <div className="brand">

          <div className="brand-mark">
            L
          </div>

          <div>
            <strong>
              LinguaAI
            </strong>

            <span>
              Language Coach
            </span>
          </div>

        </div>

        <div className="sidebar-label">
          LEARN
        </div>

        <nav className="navigation">

          {navigation.map(
            (item) => {

              const active =
                tab === item.id;

              return (
                <button
                  key={item.id}
                  className={`nav-item ${
                    active
                      ? "active"
                      : ""
                  }`}
                  onClick={() =>
                    selectTab(
                      item.id
                    )
                  }
                >

                  <Icon
                    name={item.icon}
                    size={19}
                  />

                  <span>
                    {item.label}
                  </span>

                  {item.id ===
                    "chat" && (
                    <span className="nav-dot" />
                  )}

                </button>
              );
            }
          )}

        </nav>

        <div className="sidebar-bottom">

          <button
            className="nav-item"
            onClick={
              resetProgress
            }
          >

            <Icon
              name="settings"
              size={19}
            />

            <span>
              Reset Progress
            </span>

          </button>

          <button
            className="theme-switch"
            onClick={() =>
              setTheme(
                theme === "dark"
                  ? "light"
                  : "dark"
              )
            }
          >

            <span>

              <Icon
                name={
                  theme ===
                  "dark"
                    ? "sun"
                    : "moon"
                }
                size={18}
              />

              {theme ===
              "dark"
                ? "Light mode"
                : "Dark mode"}

            </span>

            <div className="switch">
              <div />
            </div>

          </button>

          <div className="profile-mini">

            <div className="profile-avatar">
              M
            </div>

            <div>

              <strong>
                My Learning
              </strong>

              <span>
                {profile?.levels
                  ?.overall
                  ?.cefr ||
                  "A1"}{" "}
                learner
              </span>

            </div>

          </div>

        </div>

      </aside>

      {/* =================================================
         MAIN
      ================================================= */}

      <main className="main-content">

        {/* =================================================
           TOPBAR
        ================================================= */}

        <header className="topbar">

          <div className="mobile-brand">

            <div className="brand-mark">
              L
            </div>

            <strong>
              LinguaAI
            </strong>

          </div>

          <div className="topbar-right">

            <div className="streak">

              <span>
                ✦
              </span>

              <div>

                <strong>
                  {profile?.total ||
                    0}
                </strong>

                <small>
                  sentences
                </small>

              </div>

            </div>

            <button
              className="top-theme"
              onClick={() =>
                setTheme(
                  theme ===
                    "dark"
                    ? "light"
                    : "dark"
                )
              }
            >

              <Icon
                name={
                  theme ===
                  "dark"
                    ? "sun"
                    : "moon"
                }
                size={18}
              />

            </button>

          </div>

        </header>

        {/* =================================================
           DASHBOARD
        ================================================= */}

        {tab ===
          "dashboard" && (
          <div className="dashboard-view">

            <div className="workspace-header dashboard-heading">

              <div>

                <div className="eyebrow">
                  YOUR PROGRESS
                </div>

                <h1>
                  Welcome back. 👋
                </h1>

                <p>
                  Keep practicing and your English will get stronger every day.
                </p>

              </div>

            </div>

            {/* ================= STATS ================= */}

            <div className="stats-grid">

              <div className="stat-card">

                <span>
                  Total Attempts
                </span>

                <strong>
                  {profile?.total ??
                    0}
                </strong>

                <small>
                  Practice attempts
                </small>

              </div>

              <div className="stat-card">

                <span>
                  Accuracy
                </span>

                <strong>
                  {profile?.accuracy ??
                    0}
                  %
                </strong>

                <small>
                  Overall performance
                </small>

              </div>

              <div className="stat-card">

                <span>
                  Grammar
                </span>

                <strong>
                  {grammarScore}%
                </strong>

                <small>
                  Grammar performance
                </small>

              </div>

              <div className="stat-card">

                <span>
                  Vocabulary
                </span>

                <strong>
                  {vocabScore}%
                </strong>

                <small>
                  Vocabulary performance
                </small>

              </div>

            </div>

            {/* ================= SKILLS + WEAK AREAS ================= */}

            <div className="dashboard-grid">

              {/* SKILLS */}

              <div className="dashboard-card">

                <div className="card-title">

                  <div>

                    <h2>
                      Skill Progress
                    </h2>

                    <p>
                      Your current performance
                    </p>

                  </div>

                </div>

                {/* GRAMMAR */}

                <div className="skill-row">

                  <div className="skill-info">

                    <span>
                      Grammar
                    </span>

                    <strong>
                      {grammarScore}%
                    </strong>

                  </div>

                  <div className="progress-track">

                    <div
                      className="progress-fill"
                      style={{
                        width: `${grammarScore}%`,
                      }}
                    />

                  </div>

                </div>

                {/* VOCABULARY */}

                <div className="skill-row">

                  <div className="skill-info">

                    <span>
                      Vocabulary
                    </span>

                    <strong>
                      {vocabScore}%
                    </strong>

                  </div>

                  <div className="progress-track">

                    <div
                      className="progress-fill"
                      style={{
                        width: `${vocabScore}%`,
                      }}
                    />

                  </div>

                </div>

                {/* OVERALL */}

                <div className="skill-row">

                  <div className="skill-info">

                    <span>
                      Overall
                    </span>

                    <strong>
                      {overallScore}%
                    </strong>

                  </div>

                  <div className="progress-track">

                    <div
                      className="progress-fill"
                      style={{
                        width: `${overallScore}%`,
                      }}
                    />

                  </div>

                </div>

              </div>

              {/* WEAK AREAS */}

              <div className="dashboard-card">

                <div className="card-title">

                  <div>

                    <h2>
                      Weak Areas
                    </h2>

                    <p>
                      Topics that need more practice
                    </p>

                  </div>

                </div>

                {weakAreas.length >
                0 ? (
                  <div className="weak-list">

                    {weakAreas.map(
                      (
                        area,
                        index
                      ) => (
                        <div
                          className="weak-item"
                          key={`${area.category}-${index}`}
                        >

                          <div className="weak-number">
                            {index +
                              1}
                          </div>

                          <div className="weak-content">

                            <strong>
                              {String(
                                area.category ||
                                  "unknown"
                              )
                                .replace(
                                  "_",
                                  " "
                                )
                                .replace(
                                  /^\w/,
                                  (
                                    c
                                  ) =>
                                    c.toUpperCase()
                                )}
                            </strong>

                            <span>
                              {area.count}{" "}
                              error
                              {area.count !==
                              1
                                ? "s"
                                : ""}
                            </span>

                          </div>

                        </div>
                      )
                    )}

                  </div>
                ) : (
                  <div className="empty-state">
                    No weak areas yet.
                    Keep practicing!
                  </div>
                )}

              </div>

            </div>

            {/* ================= EXISTING PROGRESS ================= */}

            <ProgressCards
              profile={profile}
            />

            {/* ================= RECOMMENDATIONS ================= */}
            
<div className="dashboard-card next-lesson-card">
  <span className="feature-label">
    SMART NEXT LESSON
  </span>

  {nextLessonLoading ? (
    <p>Finding your next lesson...</p>
  ) : nextLessonError ? (
    <p>{nextLessonError}</p>
  ) : nextLesson ? (
    <>
      <h2>{nextLesson.title}</h2>

      <p>
        {nextLesson.topic_title} · Level {nextLesson.level}
      </p>

      <p>
        Continue your English learning journey with this lesson.
      </p>

      
    <button
    className="primary-btn"
    onClick={() => {
    setSelectedRecommendedLessonId(
      nextLesson?.lesson_id ?? null
    );
    setTab("course");
  }}
>
  Start lesson
</button>

    </>
  ) : (
    <p>Congratulations! All available lessons are completed.</p>
  )}
</div>


            <div className="dashboard-grid">

              <div className="dashboard-feature">

                <div className="feature-glow" />

                <div className="feature-content">

                  <span className="feature-label">
                    RECOMMENDED FOR YOU
                  </span>

                  <h2>
                    Practice speaking
                    <br />
                    with your AI tutor.
                  </h2>

                  <p>
                    Speak naturally and get instant feedback on your English.
                  </p>

                  <button
                    className="primary-btn"
                    onClick={() =>
                      setTab(
                        "speaking"
                      )
                    }
                  >
                    Start speaking

                    <Icon
                      name="arrow"
                      size={17}
                    />
                  </button>

                </div>

                <div className="feature-orb">

                  <Icon
                    name="mic"
                    size={50}
                  />

                </div>

              </div>

              <div className="quick-card">

                <div className="quick-icon">

                  <Icon
                    name="practice"
                    size={22}
                  />

                </div>

                <span>
                  Quick practice
                </span>

                <h3>
                  Test your grammar
                </h3>

                <p>
                  Take a short exercise based on your level.
                </p>

                <button
                  onClick={() =>
                    setTab(
                      "practice"
                    )
                  }
                >
                  Practice

                  <Icon
                    name="arrow"
                    size={16}
                  />
                </button>

              </div>

            </div>

          </div>
        )}

        {/* =================================================
           CHAT
        ================================================= */}

        {tab === "chat" && (
          <ChatView
            messages={messages}
            input={input}
            setInput={setInput}
            send={send}
            loading={loading}
            voice={voice}
          />
        )}

        {/* =================================================
           SPEAKING
        ================================================= */}

        {tab ===
          "speaking" && (
          <Speaking
            voice={voice}
            spokenText={
              speakingText
            }
          />
        )}

        {/* =================================================
           PRACTICE
        ================================================= */}

        {tab ===
          "practice" && (
          <Practice
            userId={userId}
            onAnswered={
              refreshProfile
            }
          />
        )}

{/* =================================================
   COURSE
================================================= */}

{tab === "course" && (
  <Course
    userId={userId}
    recommendedLessonId={selectedRecommendedLessonId}
  />
)}

{/* =================================================
   DAILY SPEAKING PRACTICE
================================================= */}

{tab === "daily-practice" && (
  <DailySpeakingPractice />
)}

{/* =================================================
   REVIEW
================================================= */}

{tab === "review" && (
  <Review
    userId={userId}
  />
)}
{/* =================================================
   VOCABULARY
================================================= */}

{tab === "vocabulary" && (
  <Vocabulary />
  
)}
{tab === "smart-review" && (
  <SmartVocabularyRevision />
)}
{tab === "vocabulary-quiz" && (
  <VocabularyQuiz />
)}
{/* =================================================
   DAILY LEARNING STREAK
================================================= */}

{tab === "streak" && (
  <DailyStreak />
)}
</main>

</div>
);
}

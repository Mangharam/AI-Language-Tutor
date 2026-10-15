import os
import time
import tempfile
import json
import urllib.request
import re
from difflib import SequenceMatcher

from concurrent.futures import ThreadPoolExecutor

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

from fastapi import FastAPI, HTTPException, UploadFile, File

from faster_whisper import WhisperModel

from fastapi.middleware.cors import CORSMiddleware

import sqlite3
import uuid

from datetime import datetime, timedelta

from typing import Optional

from dotenv import load_dotenv

from openai import OpenAI


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY is not configured.")

openai_client = (
    OpenAI(api_key=OPENAI_API_KEY)
    if OPENAI_API_KEY
    else None
)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="AI Language Tutor"
)

memory_executor = ThreadPoolExecutor(max_workers=1)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DB_PATH = os.path.join(
    BASE_DIR,
    "tutor.db"
)


# ============================================================
# AI MODELS
# ============================================================

print("Loading Whisper model...")

whisper_model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8"
)

print("Whisper model loaded successfully.")


# ------------------------------------------------------------
# Grammar Model
# ------------------------------------------------------------

GRAMMAR_MODEL_NAME = (
    "vennify/t5-base-grammar-correction"
)

print("Loading AI grammar model...")

grammar_tokenizer = AutoTokenizer.from_pretrained(
    GRAMMAR_MODEL_NAME
)

grammar_model = AutoModelForSeq2SeqLM.from_pretrained(
    GRAMMAR_MODEL_NAME
)

print("AI grammar model loaded successfully.")


# ============================================================
# DATABASE
# ============================================================

def get_db():

    conn = sqlite3.connect(
        DB_PATH
    )

    conn.row_factory = sqlite3.Row

    return conn


def now():

    return datetime.utcnow().isoformat()


def init_conversation_db():

    conn = get_db()

    try:

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS student_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                source TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(user_id, key)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                ts TEXT NOT NULL
            )
            """
        )

        conn.commit()

    finally:

        conn.close()


init_conversation_db()

# ============================================================
# LEARNING PATH SYSTEM
# ============================================================

LEARNING_TOPICS = [
    {
        "id": 1,
        "level": "A1",
        "title": "Pronouns",
        "category": "Grammar",
        "order": 1
    },
    {
        "id": 2,
        "level": "A1",
        "title": "am / is / are",
        "category": "Grammar",
        "order": 2
    },
    {
        "id": 3,
        "level": "A1",
        "title": "Articles: a / an / the",
        "category": "Grammar",
        "order": 3
    },
    {
        "id": 4,
        "level": "A1",
        "title": "Singular and Plural",
        "category": "Grammar",
        "order": 4
    },
    {
        "id": 5,
        "level": "A1",
        "title": "Subject-Verb Agreement",
        "category": "Grammar",
        "order": 5
    },
    {
        "id": 6,
        "level": "A1",
        "title": "Present Simple",
        "category": "Grammar",
        "order": 6
    },
    {
        "id": 7,
        "level": "A1",
        "title": "Present Continuous",
        "category": "Grammar",
        "order": 7
    },
    {
        "id": 8,
        "level": "A1",
        "title": "Basic Questions",
        "category": "Grammar",
        "order": 8
    },
    {
        "id": 9,
        "level": "A1",
        "title": "Daily Life Vocabulary",
        "category": "Vocabulary",
        "order": 9
    },
    {
        "id": 10,
        "level": "A1",
        "title": "University Vocabulary",
        "category": "Vocabulary",
        "order": 10
    }
]

# ============================================================
# CONNECT ERRORS TO LEARNING TOPICS
# ============================================================

def detect_learning_topic(error_category, original, corrected):

    text = (original + " " + corrected).lower()

    # Subject-Verb Agreement
    if (
        ("he go" in text)
        or ("she go" in text)
        or ("it go" in text)
        or ("he have" in text)
        or ("she have" in text)
        or ("he do" in text)
        or ("she do" in text)
        or error_category == "subject_verb_agreement"
    ):
        return 5

    # Present Simple
    if (
        "every day" in text
        or "everyday" in text
        or error_category == "present_simple"
    ):
        return 6

    # Present Continuous
    if (
        "playing" in text
        or "studying" in text
        or "working" in text
        or error_category == "present_continuous"
    ):
        return 7

    # Articles
    if (
        " a " in text
        or " an " in text
        or " the " in text
        or error_category == "article"
    ):
        return 3

    # Vocabulary
    if error_category == "word_choice":
        return 9

    # Default grammar topic
    if error_category == "grammar":
        return 5

    return None

def init_learning_path_db():

    conn = get_db()

    try:

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS learning_topics (
                id INTEGER PRIMARY KEY,
                level TEXT NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                topic_order INTEGER NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS student_learning (
                user_id TEXT NOT NULL,
                topic_id INTEGER NOT NULL,
                progress INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                last_score INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, topic_id)
            )
            """
        )

                # Add mistake_count to existing databases
        try:

            conn.execute(
                """
                ALTER TABLE student_learning
                ADD COLUMN mistake_count INTEGER DEFAULT 0
                """
            )

        except Exception:

            # Column already exists
            pass

        for topic in LEARNING_TOPICS:

            conn.execute(
                """
                INSERT OR IGNORE INTO learning_topics
                (id, level, title, category, topic_order)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    topic["id"],
                    topic["level"],
                    topic["title"],
                    topic["category"],
                    topic["order"]
                )
            )

        conn.commit()

    finally:

        conn.close()


init_learning_path_db()


# ============================================================
# COURSE / LESSON SYSTEM
# ============================================================

LESSONS = [

    # ========================================================
    # LESSON 1
    # ========================================================

    {
        "id": 1,
        "topic_id": 1,
        "level": "A1",
        "title": "Pronouns",
        "lesson_order": 1,

        "explanation": (
            "A pronoun is a word we use instead of a person's "
            "or thing's name."
        ),

        "examples": [
            "I am a student.",
            "You are my friend.",
            "He is a teacher.",
            "She is happy.",
            "It is a book.",
            "We are students.",
            "They are friends."
        ],

        "practice_question": "Choose the correct pronoun: ___ am a student.",

        "practice_options": [
            "I",
            "He",
            "They",
            "She"
        ],

        "practice_answer": 0,

        "quiz_question": "___ is my brother.",

        "quiz_options": [
            "She",
            "He",
            "They",
            "We"
        ],

        "quiz_answer": 1
    },


    # ========================================================
    # LESSON 2
    # ========================================================

    {
        "id": 2,
        "topic_id": 2,
        "level": "A1",
        "title": "am / is / are",
        "lesson_order": 2,

        "explanation": (
            "We use am, is, and are with different subjects. "
            "Use am with I, is with he, she, and it, "
            "and are with you, we, and they."
        ),

        "examples": [
            "I am a student.",
            "He is a teacher.",
            "She is happy.",
            "It is a book.",
            "You are my friend.",
            "We are students.",
            "They are friends."
        ],

        "practice_question": "Choose the correct verb: She ___ happy.",

        "practice_options": [
            "am",
            "is",
            "are",
            "be"
        ],

        "practice_answer": 1,

        "quiz_question": "Choose the correct sentence.",

        "quiz_options": [
            "I is a student.",
            "She are happy.",
            "They are students.",
            "He am a teacher."
        ],

        "quiz_answer": 2
    },


    # ========================================================
    # LESSON 3
    # ========================================================

    {
        "id": 3,
        "topic_id": 3,
        "level": "A1",
        "title": "Articles: a / an / the",
        "lesson_order": 3,

        "explanation": (
            "We use a and an for one non-specific person, "
            "place, animal, or thing. Use a before a consonant sound "
            "and an before a vowel sound. We use the when we talk "
            "about a specific person, place, animal, or thing."
        ),

        "examples": [
            "I have a book.",
            "She is a teacher.",
            "He ate an apple.",
            "I saw an elephant.",
            "The book is on the table.",
            "The sun is bright."
        ],

        "practice_question": "Choose the correct article: I have ___ apple.",

        "practice_options": [
            "a",
            "an",
            "the",
            "no article"
        ],

        "practice_answer": 1,

        "quiz_question": "Choose the correct sentence.",

        "quiz_options": [
            "I have an book.",
            "She is a teacher.",
            "He ate a apple.",
            "I saw an dog."
        ],

        "quiz_answer": 1
    },


    # ========================================================
    # LESSON 4
    # ========================================================

    {
        "id": 4,
        "topic_id": 4,
        "level": "A1",
        "title": "Singular and Plural",
        "lesson_order": 4,

        "explanation": (
            "Singular means one person, animal, place, or thing. "
            "Plural means more than one. Usually, we add 's' "
            "to make a noun plural."
        ),

        "examples": [
            "I have one book.",
            "I have two books.",
            "She has one cat.",
            "They have two cats.",
            "This is a student.",
            "These are students."
        ],

        "practice_question": "Choose the plural form: one book, two ___.",

        "practice_options": [
            "book",
            "books",
            "bookes",
            "booking"
        ],

        "practice_answer": 1,

        "quiz_question": "Choose the correct sentence.",

        "quiz_options": [
            "I have two book.",
            "She has three cat.",
            "They have two books.",
            "He has one books."
        ],

        "quiz_answer": 2
    },


    # ========================================================
    # LESSON 5
    # ========================================================

    {
        "id": 5,
        "topic_id": 5,
        "level": "A1",
        "title": "Subject-Verb Agreement",
        "lesson_order": 5,

        "explanation": (
            "Subject-verb agreement means the verb must match "
            "the subject. With he, she, and it, we usually add "
            "'s' or 'es' to the verb in the present simple."
        ),

        "examples": [
            "I play football.",
            "You play football.",
            "He plays football.",
            "She reads a book.",
            "It works well.",
            "We study English.",
            "They study English."
        ],

        "practice_question": "Choose the correct verb: He ___ English every day.",

        "practice_options": [
            "study",
            "studies",
            "studying",
            "studied"
        ],

        "practice_answer": 1,

        "quiz_question": "Choose the correct sentence.",

        "quiz_options": [
            "She play tennis.",
            "He plays tennis.",
            "They plays tennis.",
            "I plays tennis."
        ],

        "quiz_answer": 1
    },


    # ========================================================
    # LESSON 6
    # ========================================================

    {
        "id": 6,
        "topic_id": 6,
        "level": "A1",
        "title": "Present Simple",
        "lesson_order": 6,

        "explanation": (
            "We use the present simple to talk about habits, "
            "routines, facts, and things that happen regularly. "
            "With he, she, and it, the verb usually takes 's' or 'es'."
        ),

        "examples": [
            "I wake up early.",
            "You study every day.",
            "He goes to university.",
            "She drinks tea.",
            "We play football.",
            "They work together."
        ],

        "practice_question": "Choose the correct sentence.",

        "practice_options": [
            "He go to school every day.",
            "He goes to school every day.",
            "He going to school every day.",
            "He gone to school every day."
        ],

        "practice_answer": 1,

        "quiz_question": "Choose the correct verb: She ___ English every day.",

        "quiz_options": [
            "study",
            "studies",
            "studying",
            "studied"
        ],

        "quiz_answer": 1
    },


    # ========================================================
    # LESSON 7
    # ========================================================

    {
        "id": 7,
        "topic_id": 7,
        "level": "A1",
        "title": "Present Continuous",
        "lesson_order": 7,

        "explanation": (
            "We use the present continuous to talk about "
            "something happening now. We use am, is, or are "
            "with the verb ending in '-ing'."
        ),

        "examples": [
            "I am studying.",
            "You are reading.",
            "He is playing football.",
            "She is cooking.",
            "We are learning English.",
            "They are watching TV."
        ],

        "practice_question": "Choose the correct sentence.",

        "practice_options": [
            "I am study.",
            "I am studying.",
            "I studying.",
            "I studies."
        ],

        "practice_answer": 1,

        "quiz_question": "She ___ watching TV now.",

        "quiz_options": [
            "am",
            "is",
            "are",
            "be"
        ],

        "quiz_answer": 1
    },


    # ========================================================
    # LESSON 8
    # ========================================================

    {
        "id": 8,
        "topic_id": 8,
        "level": "A1",
        "title": "Basic Questions",
        "lesson_order": 8,

        "explanation": (
            "Basic questions help us ask for information. "
            "Common question words include what, where, who, "
            "when, why, and how."
        ),

        "examples": [
            "What is your name?",
            "Where do you live?",
            "Who is your teacher?",
            "When do you study?",
            "Why are you happy?",
            "How are you?"
        ],

        "practice_question": "Choose the correct question.",

        "practice_options": [
            "What your name is?",
            "What is your name?",
            "What are your name?",
            "What name your is?"
        ],

        "practice_answer": 1,

        "quiz_question": "___ do you live?",

        "quiz_options": [
            "What",
            "Where",
            "Who",
            "Why"
        ],

        "quiz_answer": 1
    },


    # ========================================================
    # LESSON 9
    # ========================================================

    {
        "id": 9,
        "topic_id": 9,
        "level": "A1",
        "title": "Daily Life Vocabulary",
        "lesson_order": 9,

        "explanation": (
            "Daily life vocabulary includes common words we use "
            "when talking about our everyday activities, such as "
            "wake up, eat, study, work, sleep, and go."
        ),

        "examples": [
            "I wake up at seven o'clock.",
            "I eat breakfast in the morning.",
            "I go to university.",
            "I study English.",
            "I do my homework.",
            "I sleep at night."
        ],

        "practice_question": "Choose the correct word: I ___ breakfast every morning.",

        "practice_options": [
            "eat",
            "sleep",
            "study",
            "go"
        ],

        "practice_answer": 0,

        "quiz_question": "Choose the correct sentence.",

        "quiz_options": [
            "I sleep breakfast.",
            "I eat breakfast.",
            "I breakfast eat.",
            "I eating breakfast."
        ],

        "quiz_answer": 1
    },


    # ========================================================
    # LESSON 10
    # ========================================================

    {
        "id": 10,
        "topic_id": 10,
        "level": "A1",
        "title": "University Vocabulary",
        "lesson_order": 10,

        "explanation": (
            "University vocabulary includes common words used "
            "in university life, such as class, teacher, student, "
            "lecture, assignment, exam, and subject."
        ),

        "examples": [
            "I attend my AI class.",
            "My teacher explains the topic.",
            "I study with my classmates.",
            "I have an assignment.",
            "I prepare for my exam.",
            "Operating Systems is my subject."
        ],

        "practice_question": "Choose the correct word: I attend my university ___.",

        "practice_options": [
            "class",
            "sleep",
            "food",
            "house"
        ],

        "practice_answer": 0,

        "quiz_question": "Choose the correct sentence.",

        "quiz_options": [
            "I study my subject.",
            "I subject my study.",
            "My study subject I.",
            "Subject I study my."
        ],

        "quiz_answer": 0
    }

]

# ============================================================
# FUNCTIONAL LESSON GENERATOR FOR A2 -> C2
# ============================================================

LEVEL_LESSON_TOPICS = {

    "A2": [
        ("Past Simple", "Grammar"),
        ("Past Continuous", "Grammar"),
        ("Future with Will", "Grammar"),
        ("Going to", "Grammar"),
        ("Present Perfect", "Grammar"),
        ("Comparatives", "Grammar"),
        ("Superlatives", "Grammar"),
        ("Modal Verbs", "Grammar"),
        ("Countable and Uncountable Nouns", "Grammar"),
        ("Quantifiers", "Grammar"),
        ("Prepositions in Context", "Grammar"),
        ("Everyday Conversations", "Speaking"),
    ],

    "B1": [
        ("Present Perfect vs Past Simple", "Grammar"),
        ("Past Perfect", "Grammar"),
        ("Future Forms", "Grammar"),
        ("First Conditional", "Grammar"),
        ("Second Conditional", "Grammar"),
        ("Passive Voice", "Grammar"),
        ("Reported Speech", "Grammar"),
        ("Relative Clauses", "Grammar"),
        ("Gerunds and Infinitives", "Grammar"),
        ("Modals of Possibility", "Grammar"),
        ("Phrasal Verbs", "Vocabulary"),
        ("Linking Words", "Writing"),
        ("Formal Emails", "Writing"),
        ("Opinion Writing", "Writing"),
        ("Speaking and Discussion", "Speaking"),
    ],

    "B2": [
        ("Advanced Tenses", "Grammar"),
        ("Perfect Continuous", "Grammar"),
        ("Third Conditional", "Grammar"),
        ("Mixed Conditionals", "Grammar"),
        ("Advanced Passive Voice", "Grammar"),
        ("Advanced Reported Speech", "Grammar"),
        ("Inversion", "Grammar"),
        ("Modal Perfects", "Grammar"),
        ("Advanced Relative Clauses", "Grammar"),
        ("Advanced Articles", "Grammar"),
        ("Collocations", "Vocabulary"),
        ("Academic Vocabulary", "Vocabulary"),
        ("Argumentative Writing", "Writing"),
        ("Professional Communication", "Speaking"),
        ("Debate and Discussion", "Speaking"),
    ],

    "C1": [
        ("Advanced Grammar", "Grammar"),
        ("Complex Sentence Structures", "Grammar"),
        ("Advanced Inversion", "Grammar"),
        ("Cleft Sentences", "Grammar"),
        ("Hedging", "Grammar"),
        ("Advanced Modals", "Grammar"),
        ("Nominalisation", "Grammar"),
        ("Academic Collocations", "Vocabulary"),
        ("Idiomatic English", "Vocabulary"),
        ("Advanced Phrasal Verbs", "Vocabulary"),
        ("Academic Writing", "Writing"),
        ("Report Writing", "Writing"),
        ("Presentations", "Speaking"),
        ("Professional English", "Speaking"),
        ("Advanced Speaking", "Speaking"),
    ],

    "C2": [
        ("Mastery of Tenses", "Grammar"),
        ("Nuanced Modality", "Grammar"),
        ("Advanced Conditionals", "Grammar"),
        ("Discourse Grammar", "Grammar"),
        ("Register and Tone", "Vocabulary"),
        ("Pragmatics", "Speaking"),
        ("Idiomatic Language", "Vocabulary"),
        ("Advanced Collocations", "Vocabulary"),
        ("Subtle Word Choice", "Vocabulary"),
        ("Academic Argumentation", "Writing"),
        ("Research Writing", "Writing"),
        ("Critical Analysis", "Writing"),
        ("Professional Negotiation", "Speaking"),
        ("Advanced Presentation", "Speaking"),
        ("C2 Mastery Assessment", "Assessment"),
    ]
}


# Advanced lessons are created by initialize_advanced_course() below.

# ============================================================
# INITIALIZE COURSE DATABASE
# ============================================================

def init_course_db():

    conn = get_db()

    try:

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY,
                topic_id INTEGER NOT NULL,
                level TEXT NOT NULL,
                title TEXT NOT NULL,
                lesson_order INTEGER NOT NULL,
                explanation TEXT NOT NULL,
                examples TEXT NOT NULL,
                practice_question TEXT NOT NULL,
                practice_options TEXT NOT NULL,
                practice_answer INTEGER NOT NULL,
                quiz_question TEXT NOT NULL,
                quiz_options TEXT NOT NULL,
                quiz_answer INTEGER NOT NULL
            )
            """
        )


        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS student_lessons (
                user_id TEXT NOT NULL,
                lesson_id INTEGER NOT NULL,
                practice_completed INTEGER DEFAULT 0,
                quiz_score INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, lesson_id)
            )
            """
        )


        for lesson in LESSONS:

            conn.execute(
                """
                INSERT OR IGNORE INTO lessons
                (
                    id,
                    topic_id,
                    level,
                    title,
                    lesson_order,
                    explanation,
                    examples,
                    practice_question,
                    practice_options,
                    practice_answer,
                    quiz_question,
                    quiz_options,
                    quiz_answer
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lesson["id"],
                    lesson["topic_id"],
                    lesson["level"],
                    lesson["title"],
                    lesson["lesson_order"],
                    lesson["explanation"],
                    json.dumps(lesson["examples"]),
                    lesson["practice_question"],
                    json.dumps(lesson["practice_options"]),
                    lesson["practice_answer"],
                    lesson["quiz_question"],
                    json.dumps(lesson["quiz_options"]),
                    lesson["quiz_answer"]
                )
            )


        conn.commit()

    finally:

        conn.close()


# Initialize course database
init_course_db()


# ============================================================
# RECORD LEARNING ERROR
# ============================================================

def record_learning_error(user_id, topic_id):

    if not topic_id:
        return

    conn = get_db()

    try:

        existing = conn.execute(
            """
            SELECT progress, completed, mistake_count
            FROM student_learning
            WHERE user_id = ? AND topic_id = ?
            """,
            (user_id, topic_id)
        ).fetchone()


        if existing:

            mistake_count = existing["mistake_count"] + 1

            conn.execute(
                """
                UPDATE student_learning
                SET mistake_count = ?,
                    completed = 0
                WHERE user_id = ? AND topic_id = ?
                """,
                (
                    mistake_count,
                    user_id,
                    topic_id
                )
            )


        else:

            conn.execute(
                """
                INSERT INTO student_learning
                (
                    user_id,
                    topic_id,
                    progress,
                    completed,
                    last_score,
                    mistake_count
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    topic_id,
                    0,
                    0,
                    0,
                    1
                )
            )


        conn.commit()

    finally:

        conn.close()

# ============================================================
# STUDENT MEMORY
# ============================================================

ALLOWED_MEMORY_KEYS = {
    "name",
    "field",
    "goal",
    "interests",
    "native_language",
    "degree",
    "university",
    "study_context"
}


def get_student_memory(user_id):

    conn = get_db()

    try:

        rows = conn.execute(
            """
            SELECT key, value
            FROM student_memory
            WHERE user_id = ?
            ORDER BY key
            """,
            (user_id,)
        ).fetchall()

        return {
            row["key"]: row["value"]
            for row in rows
        }

    finally:

        conn.close()


def save_student_memory(
    user_id,
    key,
    value,
    source="conversation"
):

    if key not in ALLOWED_MEMORY_KEYS:
        return

    value = str(value).strip()

    if not value:
        return

    conn = get_db()

    try:

        conn.execute(
            """
            INSERT INTO student_memory
            (user_id, key, value, source, updated_at)
            VALUES (?, ?, ?, ?, ?)

            ON CONFLICT(user_id, key)
            DO UPDATE SET
                value = excluded.value,
                source = excluded.source,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                key,
                value,
                source,
                now()
            )
        )

        conn.commit()

    finally:

        conn.close()


# ============================================================
# CONVERSATION MEMORY
# ============================================================

def get_conversation_history(
    user_id,
    limit=6
):

    conn = get_db()

    try:

        rows = conn.execute(
            """
            SELECT role, message
            FROM conversation_messages
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                user_id,
                limit
            )
        ).fetchall()

        return list(
            reversed(rows)
        )

    finally:

        conn.close()


def save_conversation_message(
    user_id,
    role,
    message
):

    conn = get_db()

    try:

        conn.execute(
            """
            INSERT INTO conversation_messages
            (user_id, role, message, ts)
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                role,
                message,
                now()
            )
        )

        conn.commit()

    finally:

        conn.close()


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text):

    return " ".join(
        text.strip().lower().split()
    )


def normalize_grammar_text(text):

    return normalize_text(
        text
    ).rstrip(".!?")


# ============================================================
# GRAMMAR CORRECTION
# ============================================================

def correct_grammar_with_ai(sentence):

    try:
        t0 = time.perf_counter()
        inputs = grammar_tokenizer(
            "grammar: " + sentence,
            return_tensors="pt",
            truncation=True,
            max_length=256
        )

        
        outputs = grammar_model.generate(
        **inputs,
        max_new_tokens=64,
        num_beams=1,
        do_sample=False
)


        corrected = grammar_tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        ).strip()

        if not corrected:

            return sentence, []

        if (
            normalize_grammar_text(corrected)
            ==
            normalize_grammar_text(sentence)
        ):

            return sentence, []

        if len(corrected) > max(
            len(sentence) * 2,
            len(sentence) + 80
        ):

            return sentence, []

        changes = [
            {
                "category": "grammar",
                "type": "replace",
                "from": sentence,
                "to": corrected
            }
        ]
        print(
            f"[SPEED TEST] Grammar: "
            f"{time.perf_counter() - t0:.2f}s"
)
        return corrected, changes

    except Exception as e:

        print(
            "GRAMMAR MODEL ERROR:",
            repr(e)
        )

        return sentence, []


# ============================================================
# NATURAL ENGLISH + CONTEXT-AWARE CORRECTION
# ============================================================

def improve_natural_english(
    sentence,
    corrected,
    history=None
):

    try:

        # --------------------------------------------------------
        # STEP 1: Basic comparison
        # --------------------------------------------------------

        original_normalized = normalize_grammar_text(
            sentence
        )

        corrected_normalized = normalize_grammar_text(
            corrected
        )

        # If grammar model did not change anything,
        # the sentence is already correct.
        if original_normalized == corrected_normalized:

            return {
                "corrected": sentence,
                "has_errors": False,
                "confidence": 1.0
            }


        # --------------------------------------------------------
        # STEP 2: Prevent unnecessary "and" corrections
        # --------------------------------------------------------
        #
        # Example:
        #
        # My name is Mangha.
        # I study Artificial Intelligence.
        #
        # This is already grammatically valid.
        #
        # Do NOT force:
        #
        # My name is Mangha and I study Artificial Intelligence.
        #
        # --------------------------------------------------------

        original_parts = [
            part.strip()
            for part in re.split(
                r"[.!?]+",
                sentence
            )
            if part.strip()
        ]

        corrected_parts = [
            part.strip()
            for part in re.split(
                r"[.!?]+",
                corrected
            )
            if part.strip()
        ]


        if len(original_parts) >= 2:

            # If every part looks like a normal sentence,
            # don't automatically join them together.

            valid_parts = True

            for part in original_parts:

                words = re.findall(
                    r"[A-Za-z']+",
                    part
                )

                if len(words) < 2:

                    valid_parts = False

                    break


            if valid_parts:

                # Check whether the grammar model mainly
                # joined the sentences together.

                original_words = re.findall(
                    r"[A-Za-z']+",
                    sentence.lower()
                )

                corrected_words = re.findall(
                    r"[A-Za-z']+",
                    corrected.lower()
                )


                original_without_and = [
                    word
                    for word in original_words
                ]

                corrected_without_and = [
                    word
                    for word in corrected_words
                    if word != "and"
                ]


                if (
                    original_without_and
                    ==
                    corrected_without_and
                ):

                    return {
                        "corrected": sentence,
                        "has_errors": False,
                        "confidence": 0.98
                    }


        # --------------------------------------------------------
        # STEP 3: Build conversation history
        # --------------------------------------------------------

        history_text = ""

        if history:

            history_text = (
                "Previous conversation:\n"
            )

            for row in history[-3:]:

                role = (
                    "Student"
                    if row["role"] == "user"
                    else "Tutor"
                )

                history_text += (
                    f"{role}: "
                    f"{row['message']}\n"
                )


        # --------------------------------------------------------
        # STEP 4: Qwen natural English analysis
        # --------------------------------------------------------


        prompt = f"""
You are an accurate English grammar correction engine.

Rules:
- Preserve the student's meaning and personal facts.
- Correct real grammar, spelling, punctuation, and word-form mistakes.
- Keep already-correct sentences unchanged.
- Do not join separate sentences.
- Do not change names or invent information.
- Return only valid JSON. No markdown or extra explanation.

Examples:

Input: My name is Mangha. I study Artificial Intelligence.
Output: {{"corrected": "My name is Mangha. I study Artificial Intelligence.", "has_errors": false, "confidence": 1.0}}

Input: I am studing Artificial Intelligence.
Output: {{"corrected": "I am studying Artificial Intelligence.", "has_errors": true, "confidence": 1.0}}

Input: He go to university every day.
Output: {{"corrected": "He goes to university every day.", "has_errors": true, "confidence": 1.0}}

Input: I went to university today.
Output: {{"corrected": "I went to university today.", "has_errors": false, "confidence": 1.0}}

Recent conversation:
{history_text}

Original sentence:
{sentence}

Grammar model correction:
{corrected}

Return JSON:
{{"corrected": "final sentence", "has_errors": true, "confidence": 0.95}}
"""
        
       
        payload = json.dumps({
            "model": "qwen2.5:1.5b",
            "prompt": prompt,
            "stream": False,
            "keep_alive": "10m",
            "options": {
                "num_predict": 20,
                "num_ctx": 1024,
                "temperature": 0
            }
        }).encode("utf-8")


        request = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=payload,
            headers={
                "Content-Type": "application/json"
            },
            method="POST"
        )


        with urllib.request.urlopen(
            request,
            timeout=60
        ) as response:

            result = json.loads(
                response.read().decode("utf-8")
            )


        raw = result.get(
            "response",
            ""
        ).strip()


        print("[DEBUG] Natural Qwen response received")


        # --------------------------------------------------------
        # STEP 6: Empty response fallback
        # --------------------------------------------------------

        if not raw:

            final_text = corrected

            has_errors = (
                normalize_grammar_text(
                    sentence
                )
                !=
                normalize_grammar_text(
                    final_text
                )
            )

            return {
                "corrected": final_text,
                "has_errors": has_errors,
                "confidence": 0.5
            }


        # --------------------------------------------------------
        # STEP 7: Extract JSON
        # --------------------------------------------------------

        try:

            if (
                "{"
                in raw
                and
                "}"
                in raw
            ):

                raw = raw[
                    raw.find("{"):
                    raw.rfind("}") + 1
                ]


            data = json.loads(
                raw
            )


        except Exception as e:

            print(
                "NATURAL JSON ERROR:",
                repr(e)
            )

            print(
                "RAW NATURAL RESPONSE:",
                raw
            )


            final_text = corrected

            has_errors = (
                normalize_grammar_text(
                    sentence
                )
                !=
                normalize_grammar_text(
                    final_text
                )
            )


            return {
                "corrected": final_text,
                "has_errors": has_errors,
                "confidence": 0.5
            }


        # --------------------------------------------------------
        # STEP 8: Get final correction
        # --------------------------------------------------------

        final_text = str(
            data.get(
                "corrected",
                corrected
            )
        ).strip()


        if not final_text:

            final_text = corrected


        # --------------------------------------------------------
        # STEP 9: IMPORTANT
        # Never trust Qwen's has_errors value blindly.
        #
        # We compare the actual original and final sentence.
        # --------------------------------------------------------

        has_errors = (
            normalize_grammar_text(
                sentence
            )
            !=
            normalize_grammar_text(
                final_text
            )
        )


        # --------------------------------------------------------
        # STEP 10: Confidence
        # --------------------------------------------------------

        confidence = data.get(
            "confidence",
            0.5
        )


        try:

            confidence = float(
                confidence
            )

        except Exception:

            confidence = 0.5


        confidence = max(
            0.0,
            min(
                1.0,
                confidence
            )
        )


        # --------------------------------------------------------
        # STEP 11: Safety check
        # --------------------------------------------------------
        #
        # If Qwen makes a huge unexpected change,
        # prefer the grammar model result.
        #
        # --------------------------------------------------------

        if len(final_text) > max(
            len(sentence) * 2,
            len(sentence) + 100
        ):

            final_text = corrected

            has_errors = (
                normalize_grammar_text(
                    sentence
                )
                !=
                normalize_grammar_text(
                    final_text
                )
            )

            confidence = 0.5


        # --------------------------------------------------------
        # FINAL RESULT
        # --------------------------------------------------------

        return {
            "corrected": final_text,
            "has_errors": has_errors,
            "confidence": confidence
        }


    except Exception as e:

        print(
            "NATURAL ENGLISH ERROR:",
            repr(e)
        )


        final_text = corrected


        has_errors = (
            normalize_grammar_text(
                sentence
            )
            !=
            normalize_grammar_text(
                final_text
            )
        )


        return {
            "corrected": final_text,
            "has_errors": has_errors,
            "confidence": 0.5
        }


# ============================================================
# ERROR CATEGORY CLASSIFICATION
# ============================================================

def classify_error_category(
    original,
    corrected
):
    if (
        normalize_grammar_text(original)
        ==
        normalize_grammar_text(corrected)
    ):
        return None

    original_words = re.findall(
        r"[A-Za-z']+",
        original
    )

    corrected_words = re.findall(
        r"[A-Za-z']+",
        corrected
    )

    original_lower = [
        word.lower()
        for word in original_words
    ]

    corrected_lower = [
        word.lower()
        for word in corrected_words
    ]

    matcher = SequenceMatcher(
        None,
        original_lower,
        corrected_lower
    )

    # ============================================================
    # 1. SPELLING
    # ============================================================

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():

        if tag == "replace":

            old_words = original_words[i1:i2]
            new_words = corrected_words[j1:j2]

            if len(old_words) == len(new_words):

                for old, new in zip(
                    old_words,
                    new_words
                ):

                    similarity = SequenceMatcher(
                        None,
                        old.lower(),
                        new.lower()
                    ).ratio()

                    if (
                        old.lower() != new.lower()
                        and similarity >= 0.70
                    ):
                        return "spelling"


    # ============================================================
    # 2. SUBJECT-VERB / VERB FORM
    # ============================================================
    #
    # Examples:
    #
    # He go      -> He goes
    # She walk   -> She walks
    # He play    -> He plays
    # They goes  -> They go
    #
    # These are GRAMMAR errors, not word choice.
    # ============================================================

    subject_words = {
        "he",
        "she",
        "it",
        "this",
        "that"
    }

    for i, word in enumerate(original_lower):

        if word in subject_words:

            # Check the next word
            if i + 1 < len(original_lower):

                old_verb = original_lower[i + 1]

                if i + 1 < len(corrected_lower):

                    new_verb = corrected_lower[i + 1]

                    if old_verb != new_verb:

                        common_pairs = {
                            ("go", "goes"),
                            ("do", "does"),
                            ("have", "has"),
                            ("watch", "watches"),
                            ("play", "plays"),
                            ("work", "works"),
                            ("study", "studies"),
                            ("read", "reads"),
                            ("eat", "eats"),
                            ("drink", "drinks"),
                            ("like", "likes"),
                            ("want", "wants"),
                            ("need", "needs"),
                            ("live", "lives"),
                            ("speak", "speaks"),
                            ("write", "writes"),
                            ("learn", "learns"),
                            ("goes", "go"),
                            ("does", "do"),
                            ("has", "have")
                        }

                        if (
                            old_verb,
                            new_verb
                        ) in common_pairs:

                            return "grammar"


    # ============================================================
    # 3. PUNCTUATION
    # ============================================================

    original_letters = re.sub(
        r"[^\w\s]",
        "",
        original.lower()
    )

    corrected_letters = re.sub(
        r"[^\w\s]",
        "",
        corrected.lower()
    )

    if (
        original_letters
        ==
        corrected_letters
        and original != corrected
    ):
        return "punctuation"


    # ============================================================
    # 4. WORD CHOICE
    # ============================================================

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():

        if tag == "replace":

            old_words = original_words[i1:i2]
            new_words = corrected_words[j1:j2]

            if old_words and new_words:

                similarity_scores = []

                for old in old_words:

                    for new in new_words:

                        similarity_scores.append(
                            SequenceMatcher(
                                None,
                                old.lower(),
                                new.lower()
                            ).ratio()
                        )

                if similarity_scores:

                    max_similarity = max(
                        similarity_scores
                    )

                    if max_similarity < 0.70:

                        return "word_choice"


  # --------------------------------------------------------
# DEFAULT
# --------------------------------------------------------
    return "grammar"
    # --------------------------------------------------------
    # SPELLING
    # --------------------------------------------------------

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():

        if tag == "replace":

            old_words = original_words[i1:i2]

            new_words = corrected_words[j1:j2]

            if len(old_words) == len(new_words):

                for old, new in zip(
                    old_words,
                    new_words
                ):

                    similarity = SequenceMatcher(
                        None,
                        old.lower(),
                        new.lower()
                    ).ratio()

                    if (
                        old.lower() != new.lower()
                        and similarity >= 0.70
                    ):

                        return "spelling"

    # --------------------------------------------------------
    # PUNCTUATION
    # --------------------------------------------------------

    original_letters = re.sub(
        r"[^\w\s]",
        "",
        original.lower()
    )

    corrected_letters = re.sub(
        r"[^\w\s]",
        "",
        corrected.lower()
    )

    if (
        original_letters
        ==
        corrected_letters
        and original != corrected
    ):

        return "punctuation"

    # --------------------------------------------------------
    # WORD CHOICE
    # --------------------------------------------------------

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():

        if tag == "replace":

            old_words = original_words[i1:i2]

            new_words = corrected_words[j1:j2]

            if old_words and new_words:

                similarity_scores = []

                for old in old_words:

                    for new in new_words:

                        similarity_scores.append(
                            SequenceMatcher(
                                None,
                                old.lower(),
                                new.lower()
                            ).ratio()
                        )

                if similarity_scores:

                    max_similarity = max(
                        similarity_scores
                    )

                    if max_similarity < 0.70:

                        return "word_choice"


    # --------------------------------------------------------
    # GRAMMAR
    # --------------------------------------------------------

    return "grammar"



def get_grammar_explanation(message, corrected):
    original = message.strip().rstrip(".!?")
    fixed = corrected.strip().rstrip(".!?")

    original_words = original.lower().split()
    fixed_words = fixed.lower().split()

    # Common past-tense corrections
    past_tense_pairs = {
        ("go", "went"),
        ("come", "came"),
        ("eat", "ate"),
        ("see", "saw"),
        ("do", "did"),
        ("have", "had"),
        ("is", "was"),
        ("are", "were"),
        ("write", "wrote"),
        ("take", "took"),
        ("buy", "bought"),
        ("make", "made"),
        ("speak", "spoke"),
    }

    for old, new in past_tense_pairs:
        if old in original_words and new in fixed_words:
            return (
                f"Because you are talking about the past, "
                f"use '{new}' instead of '{old}'."
            )

    # Safe fallback: do not invent an explanation
    return "The corrected sentence fixes a grammar mistake."


# ============================================================
# LOCAL AI TUTOR RESPONSE - OPTIMIZED
# ============================================================

def generate_local_tutor_response(
    message,
    corrected,
    history=None
):
    try:
        has_error = (
            normalize_grammar_text(message)
            != normalize_grammar_text(corrected)
        )

        # Keep only the latest few conversation messages
        history_lines = []

        if history:
            for row in history[-4:]:
                role = (
                    "Student"
                    if row["role"] == "user"
                    else "Tutor"
                )
                history_lines.append(
                    f"{role}: {row['message']}"
                )

        history_text = "\n".join(history_lines)

        if has_error:
            grammar_instruction = f"""
        Start with "Good attempt!"
        Then write exactly:
        Corrected: {corrected}
        Briefly explain the main mistake in one simple sentence.
        Do not say the original sentence is correct.
        """
        else:
            grammar_instruction = """
        Confirm the sentence is correct with a short positive response.
        Ask one relevant follow-up question.
        """

        
        
        prompt = f"""You are a friendly English tutor. Use simple English and reply in 1-3 short sentences.

Student message: {message}
Corrected sentence: {corrected}
Has grammar errors: {has_error}

Rules:
- Explain only the error in the student's original sentence.
- Never discuss words that do not appear in the original sentence.
- Make sure the explanation matches the corrected sentence.
- Answer the student's actual question first.
- If there are errors, start with "Good attempt!" and write exactly: Corrected: {corrected}
- Briefly explain the main mistake in simple words.
- If there are no errors, encourage the student and ask one relevant follow-up question.
- Use recent conversation for context.
- Never invent personal information.

Recent conversation:
{history_text}

Tutor:"""


        payload = json.dumps({
            "model": "qwen2.5:1.5b",
            "prompt": prompt,
            "stream": False,
            "keep_alive": "10m",
            "options": {
                "num_predict": 20,
                "temperature": 0.2
            }
        }).encode("utf-8")

        request = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=payload,
            headers={
                "Content-Type": "application/json"
            },
            method="POST"
        )

        
        qwen_start = time.perf_counter()

        with urllib.request.urlopen(
            request,
            timeout=60
        ) as response:

            result = json.loads(
                response.read().decode("utf-8")
            )

        print(
            "[NATURAL QWEN API TIME]",
            round(time.perf_counter() - qwen_start, 2),
            "seconds"
        )
        
        if has_error:
            explanation = get_grammar_explanation(
                message,
                corrected
            )

            return (
                f"Good attempt!\n"
                f"Corrected: {corrected}\n"
                f"{explanation}"
            )


        reply = result.get("response", "").strip()
        print(
        "[QWEN STATS]",
        "prompt_eval_count =", result.get("prompt_eval_count"),
        "| eval_count =", result.get("eval_count"),
        "| load_duration =", round(
        result.get("load_duration", 0) / 1_000_000_000, 2
    ),
    "sec"
)

        if reply:
            return reply

        if has_error:
            return f"Good attempt!\nCorrected: {corrected}"

        return "That's correct! Keep practicing."

   
    except Exception as e:
        print("OLLAMA ERROR:", repr(e))

        if hasattr(e, "read"):
            try:
                print(
                    "OLLAMA ERROR DETAILS:",
                    e.read().decode("utf-8")
                )
            except Exception:
                pass

        if (
            normalize_grammar_text(message)
            != normalize_grammar_text(corrected)
        ):
            return f"Good attempt!\nCorrected: {corrected}"

        return "That's correct! Keep practicing."


# ============================================================
# STUDENT MEMORY EXTRACTION
# ============================================================

def extract_student_memory(
    user_id,
    message
):

    try:

        prompt = f"""
You extract simple facts that a student clearly states about themselves.

Allowed keys:
name, field, goal, interests, native_language, degree, university, study_context

Rules:

- Only save facts clearly stated by the student.
- Do not guess or infer.
- Do not save questions.
- Remember education-related facts when clearly stated.
- "I am doing my bachelor's degree" means degree = "bachelor's degree".
- "I study at SMIU" means university = "SMIU".
- "I study Artificial Intelligence" means field = "Artificial Intelligence".
- Combine related education facts into study_context only when clearly stated.
- Never invent a degree, university, location, or field.
- Return ONLY valid JSON.
- If there is no personal fact, return {{}}.

Student message:
{message}

Examples:

"My name is Mangha"
-> {{"name": "Mangha"}}

"I study Artificial Intelligence"
-> {{"field": "Artificial Intelligence"}}

"I want to become an AI engineer"
-> {{"goal": "AI engineer"}}

"I like football and coding"
-> {{"interests": "football, coding"}}

"I am doing my bachelor's degree"
-> {{"degree": "bachelor's degree"}}

"I study at SMIU"
-> {{"university": "SMIU"}}

"I am a university student studying Artificial Intelligence"
-> {{"study_context": "university student studying Artificial Intelligence"}}

JSON:
"""

        payload = json.dumps(
            {
                "model": "qwen2.5:1.5b",
                "prompt": prompt,
                "stream": False
            }
        ).encode("utf-8")

        request = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=payload,
            headers={
                "Content-Type": "application/json"
            },
            method="POST"
        )

        with urllib.request.urlopen(
            request,
            timeout=60
        ) as response:

            result = json.loads(
                response.read().decode("utf-8")
            )

        raw = result.get(
            "response",
            ""
        ).strip()

        if not raw:

            return

        try:

            if "{" in raw and "}" in raw:

                raw = raw[
                    raw.find("{"):
                    raw.rfind("}") + 1
                ]

            memory = json.loads(raw)

        except Exception as e:

            print(
                "MEMORY JSON ERROR:",
                repr(e)
            )

            print(
                "RAW MEMORY RESPONSE:",
                raw
            )

            return

        if not isinstance(
            memory,
            dict
        ):

            return

        for key, value in memory.items():

            if (
                key in ALLOWED_MEMORY_KEYS
                and value
            ):

                save_student_memory(
                    user_id,
                    key,
                    value,
                    source="conversation"
                )

    except Exception as e:

        print(
            "MEMORY EXTRACTION ERROR:",
            repr(e)
        )


# ============================================================
# INTENT DETECTION + NATURAL CHAT
# ============================================================

def fallback_message_intent(message):
    """
    Returns 'chat' for normal conversation/questions and 'learn'
    when the user clearly wants English correction or practice.
    """
    text = message.strip().lower()
    normalized = re.sub(r"\s+", " ", text)

    learning_requests = [
        "correct my grammar", "correct this sentence",
        "check my grammar", "check this sentence",
        "fix my sentence", "correct my english",
        "is this sentence correct", "what is wrong with this sentence",
        "grammar practice", "let me practice grammar",
        "practice english", "test my english",
        "give me a grammar exercise", "explain this grammar mistake",
        "why is this sentence wrong", "correct the following",
    ]
    if any(phrase in normalized for phrase in learning_requests):
        return "learn"

    # Questions and everyday conversation should be answered, not corrected.
    question_starts = (
        "who ", "what ", "when ", "where ", "why ", "how ",
        "can ", "could ", "would ", "will ", "should ",
        "do ", "does ", "did ", "is ", "are ", "am ",
        "was ", "were ", "have ", "has ", "had ",
        "may ", "might ", "which ", "whose "
    )
    casual_phrases = (
        "hello", "hi", "hey", "good morning", "good evening",
        "how are you", "what's up", "whats up", "thank you",
        "thanks", "are you crazy", "you are crazy",
        "who made this platform", "what can i learn here",
        "what can i do here", "tell me a joke", "i am bored",
        "listen", "guess what", "that's funny", "thats funny"
    )

    if (
        normalized.endswith("?")
        or normalized.startswith(question_starts)
        or any(phrase in normalized for phrase in casual_phrases)
    ):
        return "chat"

    # A simple statement may be a learning attempt; let the grammar
    # correction system handle it unless the classifier says otherwise.
    return "learn"


def detect_message_intent(message, history=None):
    """
    Ask the local Ollama model whether the user is chatting or
    explicitly practising English. Falls back to simple rules if Ollama
    is unavailable or returns an invalid label.
    """
    fallback = fallback_message_intent(message)

    history_text = ""
    if history:
        history_text = "\n".join(
            f"{'User' if row['role'] == 'user' else 'Tutor'}: {row['message']}"
            for row in history[-4:]
        )

    prompt = f"""
Classify the user's message for an English-learning app.
Return exactly one word: CHAT or LEARN.

CHAT means:
- The user is asking an ordinary question or wants an answer.
- The user is greeting, joking, chatting, venting, using slang, or being rude.
- The user asks about the app, the AI, everyday life, or any general topic.
- The user has not explicitly asked for correction or a grammar exercise.
- Do NOT classify something as LEARN merely because the English has mistakes.

LEARN means:
- The user explicitly asks to correct/check/improve a sentence or grammar.
- The user asks for a grammar explanation or an English exercise.
- The user appears to be submitting a practice sentence for correction.

Examples:
Message: "Can you help me with some grammar topics?"
CHAT
Message: "Why are you not understanding me?"
CHAT
Message: "Who made this platform?"
CHAT
Message: "Are you crazy?"
CHAT
Message: "Someone called me a bad name."
CHAT
Message: "Correct this sentence: he go to school."
LEARN
Message: "He go to school every day." 
LEARN
Message: "Please check my English: I am studing AI."
LEARN

Recent context:
{history_text}

Current message:
{message}

Label:"""

    try:
        payload = json.dumps({
            "model": "qwen2.5:1.5b",
            "prompt": prompt,
            "stream": False,
            "keep_alive": "10m",
            "options": {
                "num_predict": 3,
                "temperature": 0
            }
        }).encode("utf-8")

        request = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))

        label = result.get("response", "").strip().upper()
        if re.search(r"\bCHAT\b", label):
            return "chat"
        if re.search(r"\bLEARN\b", label):
            return "learn"

    except Exception as e:
        print("INTENT DETECTION FALLBACK:", repr(e))

    return fallback


def generate_natural_chat_reply(message, history=None):
    """Answer the user naturally. Never add unsolicited grammar correction."""
    history_text = ""
    if history:
        history_text = "\n".join(
            f"{'User' if row['role'] == 'user' else 'AI Tutor'}: {row['message']}"
            for row in history[-6:]
        )

    prompt = f"""
You are the friendly conversational assistant inside an AI Language Coach app.
Reply naturally to what the user actually means, in simple English.
Do not correct grammar, spelling, punctuation, or word choice unless the user asks.
Do not say "Good attempt", "Corrected:", or give grammar feedback during normal chat.
Answer questions directly. If the user is joking or rude, stay calm and friendly.
Keep the reply concise (1-3 sentences). Do not pretend to know facts you do not know.
If asked what this app can teach, mention English grammar, vocabulary, speaking,
writing, pronunciation and everyday conversation only as available features if relevant.
If asked who made this particular app, explain that it is the user's AI Language Coach project;
do not claim that OpenAI made this specific app.

Recent conversation:
{history_text}

User message: {message}

Natural reply:"""

    try:
        payload = json.dumps({
            "model": "qwen2.5:1.5b",
            "prompt": prompt,
            "stream": False,
            "keep_alive": "10m",
            "options": {
                "num_predict": 100,
                "temperature": 0.4
            }
        }).encode("utf-8")

        request = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))

        reply = result.get("response", "").strip()
        if reply:
            return reply

    except Exception as e:
        print("NATURAL CHAT ERROR:", repr(e))

    # Helpful fallback if the local chat model is unavailable.
    if message.strip().endswith("?"):
        return "That's a good question. I'll do my best to help—could you tell me a little more about what you mean?"
    return "I'm listening. Tell me a little more."


# ============================================================
# CHAT API
# ============================================================

@app.post("/api/chat")
def chat(data: dict):
    chat_start = time.perf_counter()
    message = str(
        data.get(
            "message",
            ""
        )
    ).strip()

    user_id = data.get(
        "user_id",
        "guest"
    )

    # --------------------------------------------------------
    # Message length
    # --------------------------------------------------------

    if len(message) > 500:

        return {
            "reply": (
                "Your message is too long. "
                "Please send one or two sentences "
                "(500 characters at most)."
            ),

            "profile": get_profile_data(
                user_id
            ),

            "deltas": {
                "grammar": 0,
                "vocab": 0
            },

            "accuracy": 100,

            "correction": {
                "has_errors": False,
                "corrected": "",
                "changes": [],
                "category": None,
                "confidence": 1.0
            },

            "highlights": [],

            "cards_added": 0
        }

    # --------------------------------------------------------
    # Empty message
    # --------------------------------------------------------

    if not message:

        return {
            "reply": (
                "Please write a sentence in English."
            ),

            "profile": get_profile_data(
                user_id
            ),

            "deltas": {
                "grammar": 0,
                "vocab": 0
            },

            "accuracy": 100,

            "correction": {
                "has_errors": False,
                "corrected": "",
                "changes": [],
                "category": None,
                "confidence": 1.0
            },

            "highlights": [],

            "cards_added": 0
        }

    # --------------------------------------------------------
    # Conversation history
    # --------------------------------------------------------

    history = get_conversation_history(
        user_id,
        limit=6
    )
    # --------------------------------------------------------
    # Decide whether this is conversation or English practice
    # --------------------------------------------------------

    intent = detect_message_intent(message, history)
    print("[CHAT INTENT]", intent)

    if intent == "chat":
        # Normal chat: answer the message and do not run grammar correction.
        final_corrected = message
        natural_confidence = 1.0
        has_errors = False
        error_category = None
        changes = []
        reply = generate_natural_chat_reply(message, history)

    else:
        # Learning mode: run grammar correction.
        t1 = time.perf_counter()
        corrected, changes = correct_grammar_with_ai(message)

        print(
            f"[SPEED TEST] Grammar: "
            f"{time.perf_counter() - t1:.2f}s"
        )

        final_corrected = corrected
        natural_confidence = 0.95

        has_errors = (
            normalize_grammar_text(message)
            != normalize_grammar_text(final_corrected)
        )

        error_category = None
        if has_errors:
            error_category = classify_error_category(
                message,
                final_corrected
            )
            print("FINAL ERROR CATEGORY:", error_category)

            if changes:
                for change in changes:
                    change["category"] = error_category or change.get(
                        "category", "grammar"
                    )
                    change["from"] = message
                    change["to"] = final_corrected
            else:
                changes = [{
                    "category": error_category or "grammar",
                    "type": "replace",
                    "from": message,
                    "to": final_corrected
                }]
        else:
            changes = []

        if has_errors and changes:
            for change in changes:
                topic_id = detect_learning_topic(
                    change.get("category", "grammar"),
                    message,
                    final_corrected
                )
                record_learning_error(user_id, topic_id)

        t1 = time.perf_counter()
        reply = generate_local_tutor_response(
            message,
            final_corrected,
            history
        )
        print(
            f"[SPEED TEST] Tutor reply: "
            f"{time.perf_counter() - t1:.2f}s"
        )

    # --------------------------------------------------------
    # Save conversation
    # --------------------------------------------------------

    save_conversation_message(
        user_id,
        "user",
        message
    )

    save_conversation_message(
        user_id,
        "assistant",
        reply
    )

    # --------------------------------------------------------
    # Extract memory
    # --------------------------------------------------------

    memory_executor.submit(
    extract_student_memory,
    user_id,
    message
    )
    

    if intent == "learn":
        # --------------------------------------------------------
        # Save learning attempt
        # --------------------------------------------------------

        conn = get_db()

        try:

            cur = conn.execute(
                """
                INSERT INTO attempts
                (user_id, ts, original, corrected, has_errors)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    now(),
                    message,
                    final_corrected,
                    int(has_errors)
                )
            )

            attempt_id = cur.lastrowid

            # ----------------------------------------------------
            # Save errors
            # ----------------------------------------------------

            for change in changes:

                conn.execute(
                    """
                    INSERT INTO errors
                    (attempt_id, user_id, category, from_text, to_text)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        attempt_id,
                        user_id,
                        change["category"],
                        change["from"],
                        change["to"]
                    )
                )

            conn.commit()

        finally:

            conn.close()

    # --------------------------------------------------------
    # Current attempt accuracy
    # --------------------------------------------------------

    if intent == "chat":
        # Casual conversation is not a grammar-learning attempt.
        accuracy = 100

    elif has_errors:
        accuracy = max(
            60,
            100 - (len(changes) * 10)
        )

    else:
        accuracy = 100

    # --------------------------------------------------------
    # CATEGORY-BASED DELTAS
    # --------------------------------------------------------

    deltas = {
        "grammar": 0,
        "vocab": 0
    }

    if has_errors:

        if error_category == "grammar":

            deltas["grammar"] = -1

        elif error_category in [
            "vocabulary",
            "word_choice"
        ]:

            deltas["vocab"] = -1

    elif intent == "learn":

        deltas["grammar"] = 1

    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    return {

        "reply": reply,

        "profile": get_profile_data(
            user_id
        ),

        "deltas": deltas,

        "accuracy": accuracy,

        "correction": {

            "has_errors": has_errors,

            "corrected": final_corrected,

            "changes": changes,

            "category": error_category,

            "confidence": natural_confidence
        },

        "highlights": [],

        "cards_added": 0
    }


# ============================================================
# PROFILE
# ============================================================

def get_profile_data(user_id):

    conn = get_db()

    try:

        total = conn.execute(
            """
            SELECT COUNT(*)
            FROM attempts
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()[0]

        error_attempts = conn.execute(
            """
            SELECT COUNT(*)
            FROM attempts
            WHERE user_id = ?
            AND has_errors = 1
            """,
            (user_id,)
        ).fetchone()[0]

        if total == 0:

            accuracy = 100

        else:

            accuracy = max(
                0,
                round(
                    (
                        (
                            total
                            -
                            error_attempts
                        )
                        /
                        total
                    )
                    * 100
                )
            )

        # ----------------------------------------------------
        # Weak areas
        # ----------------------------------------------------

        category_rows = conn.execute(
            """
            SELECT category, COUNT(*) AS count
            FROM errors
            WHERE user_id = ?
            GROUP BY category
            ORDER BY count DESC
            """,
            (user_id,)
        ).fetchall()

        weak_areas = [
            {
                "category": row["category"],
                "count": row["count"]
            }
            for row in category_rows
        ]

        # ----------------------------------------------------
        # Grammar errors
        # ----------------------------------------------------

        grammar_errors = conn.execute(
            """
            SELECT COUNT(*)
            FROM errors
            WHERE user_id = ?
            AND category = 'grammar'
            """,
            (user_id,)
        ).fetchone()[0]

        # ----------------------------------------------------
        # Spelling errors
        # ----------------------------------------------------

        spelling_errors = conn.execute(
            """
            SELECT COUNT(*)
            FROM errors
            WHERE user_id = ?
            AND category = 'spelling'
            """,
            (user_id,)
        ).fetchone()[0]

        # ----------------------------------------------------
        # Vocabulary errors
        # ----------------------------------------------------

        vocabulary_errors = conn.execute(
            """
            SELECT COUNT(*)
            FROM errors
            WHERE user_id = ?
            AND category IN (
                'vocabulary',
                'word_choice'
            )
            """,
            (user_id,)
        ).fetchone()[0]

        # ----------------------------------------------------
        # Scores
        # ----------------------------------------------------

        grammar_score = max(
            0,
            100 - (
                grammar_errors * 10
            )
        )

        spelling_score = max(
            0,
            100 - (
                spelling_errors * 10
            )
        )

        vocabulary_score = max(
            0,
            100 - (
                vocabulary_errors * 10
            )
        )

        return {

            "total": total,

            "accuracy": accuracy,

            "recent_accuracy": accuracy,

            "levels": {

                "grammar": {
                    "cefr": "A1",
                    "score": grammar_score
                },

                "vocab": {
                    "cefr": "A1",
                    "score": vocabulary_score
                },

                "overall": {
                    "cefr": "A1",
                    "score": accuracy,
                    "provisional": True
                }
            },

            "weak_areas": weak_areas
        }

    finally:

        conn.close()

# ============================================================
# LEARNING PATH API
# ============================================================

@app.get("/api/learning-path/{user_id}")
def get_learning_path(user_id: str):

    conn = get_db()

    try:
        topic_rows = conn.execute(
            """
            SELECT
                id,
                level,
                title,
                category,
                topic_order
            FROM learning_topics
            ORDER BY
                CASE level
                    WHEN 'A1' THEN 1
                    WHEN 'A2' THEN 2
                    WHEN 'B1' THEN 3
                    WHEN 'B2' THEN 4
                    WHEN 'C1' THEN 5
                    WHEN 'C2' THEN 6
                    ELSE 99
                END,
                topic_order
            """
        ).fetchall()

        topics = []

        for topic in topic_rows:
            lessons = conn.execute(
                """
                SELECT id
                FROM lessons
                WHERE topic_id = ?
                ORDER BY lesson_order
                """,
                (topic["id"],)
            ).fetchall()

            total_lessons = len(lessons)
            completed_lessons = 0
            last_score = None

            for lesson in lessons:
                progress_row = conn.execute(
                    """
                    SELECT completed, quiz_score
                    FROM student_lessons
                    WHERE user_id = ?
                    AND lesson_id = ?
                    """,
                    (user_id, lesson["id"])
                ).fetchone()

                if progress_row:
                    if progress_row["completed"]:
                        completed_lessons += 1

                    if progress_row["quiz_score"] is not None:
                        last_score = progress_row["quiz_score"]

            progress_percent = (
                round(completed_lessons / total_lessons * 100)
                if total_lessons > 0
                else 0
            )

            topic_completed = (
                total_lessons > 0
                and completed_lessons == total_lessons
            )

            topics.append({
                "id": topic["id"],
                "level": topic["level"],
                "title": topic["title"],
                "category": topic["category"],
                "topic_order": topic["topic_order"],
                "progress": progress_percent,
                "completed": topic_completed,
                "last_score": last_score,
                "mistake_count": 0
            })

        # ----------------------------------------------------
        # LEVELS
        # ----------------------------------------------------

        level_order = ["A1", "A2", "B1", "B2", "C1", "C2"]
        levels = []

        for index, level in enumerate(level_order):
            level_topics = [
                topic for topic in topics
                if topic["level"] == level
            ]

            total = len(level_topics)
            completed_count = sum(
                1 for topic in level_topics
                if topic["completed"]
            )

            progress_percent = (
                round(completed_count / total * 100)
                if total > 0
                else 0
            )

            completed_level = (
                total > 0 and completed_count == total
            )

            if level == "A1":
                unlocked = True
            else:
                previous_level = level_order[index - 1]
                previous_topics = [
                    topic for topic in topics
                    if topic["level"] == previous_level
                ]

                unlocked = (
                    len(previous_topics) > 0
                    and all(
                        topic["completed"]
                        for topic in previous_topics
                    )
                )

            levels.append({
                "level": level,
                "unlocked": unlocked,
                "completed_level": completed_level,
                "progress": progress_percent,
                "completed": completed_count,
                "total": total
            })

        # ----------------------------------------------------
        # CURRENT LEVEL
        # ----------------------------------------------------

        current_level = "A1"

        for level_info in levels:
            if (
                level_info["unlocked"]
                and not level_info["completed_level"]
            ):
                current_level = level_info["level"]
                break

        # ----------------------------------------------------
        # NEXT LEVEL
        # ----------------------------------------------------

        current_index = level_order.index(current_level)

        next_level = (
            level_order[current_index + 1]
            if current_index < len(level_order) - 1
            else None
        )

        # ----------------------------------------------------
        # COURSE COMPLETE
        # ----------------------------------------------------

        course_complete = all(
            level_info["completed_level"]
            for level_info in levels
            if level_info["total"] > 0
        )

        return {
            "current_level": current_level,
            "next_level": next_level,
            "course_complete": course_complete,
            "levels": levels,
            "topics": topics
        }

    finally:
        conn.close()


# ============================================================
# SMART NEXT LESSON RECOMMENDATION
# ============================================================

@app.get("/api/next-lesson/{user_id}")
def get_next_lesson(user_id: str):

    conn = get_db()

    try:
        level_order = ["A1", "A2", "B1", "B2", "C1", "C2"]

        lessons = conn.execute(
            """
            SELECT
                l.id,
                l.topic_id,
                l.level,
                l.title,
                l.lesson_order,
                t.title AS topic_title,
                COALESCE(sl.completed, 0) AS completed,
                sl.quiz_score
            FROM lessons AS l
            JOIN learning_topics AS t
                ON t.id = l.topic_id
            LEFT JOIN student_lessons AS sl
                ON sl.lesson_id = l.id
                AND sl.user_id = ?
            ORDER BY
                CASE l.level
                    WHEN 'A1' THEN 1
                    WHEN 'A2' THEN 2
                    WHEN 'B1' THEN 3
                    WHEN 'B2' THEN 4
                    WHEN 'C1' THEN 5
                    WHEN 'C2' THEN 6
                    ELSE 99
                END,
                t.topic_order,
                l.lesson_order
            """,
            (user_id,)
        ).fetchall()

        if not lessons:
            return {
                "success": True,
                "recommendation": None,
                "message": "No lessons are available yet."
            }

        # Check completion status for each level
        completed_by_level = {}

        for level in level_order:
            level_lessons = [
                lesson for lesson in lessons
                if lesson["level"] == level
            ]

            completed_by_level[level] = (
                bool(level_lessons)
                and all(
                    lesson["completed"]
                    for lesson in level_lessons
                )
            )

        # Recommend the first incomplete lesson
        # from an unlocked level
        for lesson in lessons:
            level = lesson["level"]

            if lesson["completed"]:
                continue

            if level not in level_order:
                continue

            level_index = level_order.index(level)

            if level_index > 0:
                previous_levels = [
                    previous_level
                    for previous_level in level_order[:level_index]
                    if any(
                        item["level"] == previous_level
                        for item in lessons
                    )
                ]

                previous_levels_complete = all(
                    completed_by_level[previous_level]
                    for previous_level in previous_levels
                )

                if not previous_levels_complete:
                    continue

            return {
                "success": True,
                "recommendation": {
                    "lesson_id": lesson["id"],
                    "title": lesson["title"],
                    "level": level,
                    "topic_id": lesson["topic_id"],
                    "topic_title": lesson["topic_title"],
                    "lesson_order": lesson["lesson_order"],
                    "last_score": lesson["quiz_score"]
                },
                "message": "Continue learning with this lesson."
            }

        return {
            "success": True,
            "recommendation": None,
            "message": "Congratulations! All available lessons are completed."
        }

    finally:
        conn.close()


# ============================================================
# LESSON API
# ============================================================

@app.get("/api/lesson/{lesson_id}")
def get_lesson(lesson_id: int):

    conn = get_db()

    try:

        lesson = conn.execute(
            """
            SELECT *
            FROM lessons
            WHERE id = ?
            """,
            (lesson_id,)
        ).fetchone()

        if not lesson:
            raise HTTPException(
                status_code=404,
                detail="Lesson not found"
            )

        return {
            "id": lesson["id"],
            "topic_id": lesson["topic_id"],
            "level": lesson["level"],
            "title": lesson["title"],
            "lesson_order": lesson["lesson_order"],

            "learn": {
                "explanation": lesson["explanation"],
                "examples": json.loads(
                    lesson["examples"]
                )
            },

            "practice": {
                "question": lesson["practice_question"],
                "options": json.loads(
                    lesson["practice_options"]
                )
            },

            "quiz": {
                "question": lesson["quiz_question"],
                "options": json.loads(
                    lesson["quiz_options"]
                )
            }
        }

    finally:
        conn.close()


# ============================================================
# LESSON PROGRESS
# ============================================================

@app.get("/api/lesson-progress/{user_id}/{lesson_id}")
def get_lesson_progress(
    user_id: str,
    lesson_id: int
):

    conn = get_db()

    try:

        lesson = conn.execute(
            """
            SELECT id
            FROM lessons
            WHERE id = ?
            """,
            (lesson_id,)
        ).fetchone()

        if not lesson:
            raise HTTPException(
                status_code=404,
                detail="Lesson not found"
            )

        progress = conn.execute(
            """
            SELECT
                practice_completed,
                quiz_score,
                completed
            FROM student_lessons
            WHERE user_id = ? AND lesson_id = ?
            """,
            (user_id, lesson_id)
        ).fetchone()


        if lesson_id == 1:

            unlocked = True

        else:

            previous = conn.execute(
                """
                SELECT completed
                FROM student_lessons
                WHERE user_id = ? AND lesson_id = ?
                """,
                (user_id, lesson_id - 1)
            ).fetchone()

            unlocked = (
                previous is not None
                and bool(previous["completed"])
            )


        if not progress:

            return {
                "lesson_id": lesson_id,
                "practice_completed": False,
                "quiz_score": 0,
                "completed": False,
                "unlocked": unlocked
            }


        return {
            "lesson_id": lesson_id,
            "practice_completed": bool(
                progress["practice_completed"]
            ),
            "quiz_score": progress["quiz_score"],
            "completed": bool(
                progress["completed"]
            ),
            "unlocked": unlocked
        }

    finally:
        conn.close()
# ============================================================
# PRACTICE SUBMISSION
# ============================================================

# ============================================================
# PRACTICE SUBMISSION
# ============================================================

@app.post("/api/lesson-practice/{user_id}/{lesson_id}")
def submit_lesson_practice(
    user_id: str,
    lesson_id: int,
    answer: int
):

    conn = get_db()

    try:

        lesson = conn.execute(
            """
            SELECT practice_answer
            FROM lessons
            WHERE id = ?
            """,
            (lesson_id,)
        ).fetchone()

        if not lesson:

            raise HTTPException(
                status_code=404,
                detail="Lesson not found"
            )


        correct = (
            answer == lesson["practice_answer"]
        )


        if correct:

            conn.execute(
                """
                INSERT INTO student_lessons
                (
                    user_id,
                    lesson_id,
                    practice_completed,
                    quiz_score,
                    completed
                )
                VALUES (?, ?, 1, 0, 0)

                ON CONFLICT(user_id, lesson_id)
                DO UPDATE SET
                    practice_completed = 1
                """,
                (
                    user_id,
                    lesson_id
                )
            )

            conn.commit()


        return {
            "correct": correct,
            "practice_completed": correct
        }


    finally:

        conn.close()

# ============================================================
# PRACTICE SUBMISSION
# ============================================================

@app.post("/api/lesson-practice/{user_id}/{lesson_id}")
def submit_lesson_practice(
    user_id: str,
    lesson_id: int,
    answer: int
):

    conn = get_db()

    try:

        lesson = conn.execute(
            """
            SELECT practice_answer
            FROM lessons
            WHERE id = ?
            """,
            (lesson_id,)
        ).fetchone()

        if not lesson:

            raise HTTPException(
                status_code=404,
                detail="Lesson not found"
            )

        correct = answer == lesson["practice_answer"]

        if correct:

            conn.execute(
                """
                INSERT INTO student_lessons
                (
                    user_id,
                    lesson_id,
                    practice_completed,
                    quiz_score,
                    completed
                )
                VALUES (?, ?, 1, 0, 0)

                ON CONFLICT(user_id, lesson_id)
                DO UPDATE SET
                    practice_completed = 1
                """,
                (user_id, lesson_id)
            )

        conn.commit()

        return {
            "correct": correct,
            "practice_completed": correct
        }

    finally:

        conn.close()
# ============================================================
# QUIZ SUBMISSION
# ============================================================

@app.post("/api/lesson-quiz/{user_id}/{lesson_id}")
def submit_lesson_quiz(
    user_id: str,
    lesson_id: int,
    answer: int
):

    conn = get_db()

    try:

        # Get correct quiz answer
        lesson = conn.execute(
            """
            SELECT quiz_answer
            FROM lessons
            WHERE id = ?
            """,
            (lesson_id,)
        ).fetchone()

        if not lesson:
            raise HTTPException(
                status_code=404,
                detail="Lesson not found"
            )

        # Check quiz answer
        correct = answer == lesson["quiz_answer"]

        quiz_score = 100 if correct else 0

        # Get existing lesson progress
        practice = conn.execute(
            """
            SELECT practice_completed
            FROM student_lessons
            WHERE user_id = ? AND lesson_id = ?
            """,
            (user_id, lesson_id)
        ).fetchone()

        # If practice record does not exist,
        # keep practice as incomplete.
        practice_completed = (
            bool(practice["practice_completed"])
            if practice
            else False
        )

        # Lesson is completed when quiz is correct.
        # Practice completion is also preserved.
        completed = correct

        conn.execute(
            """
            INSERT INTO student_lessons
            (
                user_id,
                lesson_id,
                practice_completed,
                quiz_score,
                completed
            )
            VALUES (?, ?, ?, ?, ?)

            ON CONFLICT(user_id, lesson_id)
            DO UPDATE SET
                practice_completed = ?,
                quiz_score = ?,
                completed = ?
            """,
            (
                user_id,
                lesson_id,
                int(practice_completed),
                quiz_score,
                int(completed),

                int(practice_completed),
                quiz_score,
                int(completed)
            )
        )

        conn.commit()

        return {
            "correct": correct,
            "quiz_score": quiz_score,
            "practice_completed": practice_completed,
            "completed": completed
        }

    finally:

        conn.close()
# ============================================================
# PROFILE API
# ============================================================

@app.get("/api/profile/{user_id}")
def profile(user_id: str):

    return get_profile_data(
        user_id
    )


@app.delete("/api/profile/{user_id}")
def delete_profile(user_id: str):

    conn = get_db()

    try:

        conn.execute(
            "DELETE FROM errors WHERE user_id = ?",
            (user_id,)
        )

        conn.execute(
            "DELETE FROM attempts WHERE user_id = ?",
            (user_id,)
        )

        conn.execute(
            "DELETE FROM skills WHERE user_id = ?",
            (user_id,)
        )

        conn.execute(
            "DELETE FROM level_history WHERE user_id = ?",
            (user_id,)
        )

        conn.execute(
            "DELETE FROM exercise_results WHERE user_id = ?",
            (user_id,)
        )

        conn.execute(
            "DELETE FROM cards WHERE user_id = ?",
            (user_id,)
        )

        conn.execute(
            "DELETE FROM speech_words WHERE user_id = ?",
            (user_id,)
        )

        conn.execute(
            "DELETE FROM conversation_messages WHERE user_id = ?",
            (user_id,)
        )

        conn.execute(
            "DELETE FROM student_memory WHERE user_id = ?",
            (user_id,)
        )

        conn.commit()

    finally:

        conn.close()

    return get_profile_data(
        user_id
    )


# ============================================================
# EXERCISES
# ============================================================

EXERCISES = [

    {
        "id": 1,
        "category": "Grammar",
        "level": "A1",
        "question": "She ___ to school every day.",
        "options": [
            "go",
            "goes",
            "going",
            "gone"
        ],
        "answer": 1,
        "why": (
            "With 'She', we use 'goes' "
            "in the simple present."
        )
    },

    {
        "id": 2,
        "category": "Vocabulary",
        "level": "A1",
        "question": "What is the opposite of 'hot'?",
        "options": [
            "warm",
            "cold",
            "big",
            "fast"
        ],
        "answer": 1,
        "why": (
            "'Cold' is the opposite "
            "of 'hot'."
        )
    },

    {
        "id": 3,
        "category": "Grammar",
        "level": "A2",
        "question": (
            "They ___ playing football yesterday."
        ),
        "options": [
            "was",
            "is",
            "were",
            "are"
        ],
        "answer": 2,
        "why": (
            "With 'They' in the past continuous, "
            "we use 'were'."
        )
    },

    {
        "id": 4,
        "category": "Vocabulary",
        "level": "A2",
        "question": (
            "Choose the word closest to 'happy'."
        ),
        "options": [
            "sad",
            "angry",
            "glad",
            "tired"
        ],
        "answer": 2,
        "why": (
            "'Glad' has a similar meaning "
            "to 'happy'."
        )
    }
]


@app.get("/api/exercise/{user_id}")
def get_exercise(user_id: str):

    exercise = EXERCISES[
        0
    ]

    return {

        "id": exercise["id"],

        "category": exercise["category"],

        "level": exercise["level"],

        "question": exercise["question"],

        "options": exercise["options"]
    }


@app.post("/api/exercise/answer")
def exercise_answer(data: dict):

    user_id = data.get(
        "user_id",
        "guest"
    )

    exercise_id = int(
        data.get(
            "exercise_id",
            1
        )
    )

    choice = int(
        data.get(
            "choice",
            0
        )
    )

    exercise = next(
        (
            x
            for x in EXERCISES
            if x["id"] == exercise_id
        ),
        None
    )

    if exercise is None:

        raise HTTPException(
            status_code=404,
            detail="Exercise not found"
        )

    correct = (
        choice
        ==
        exercise["answer"]
    )

    conn = get_db()

    try:

        conn.execute(
            """
            INSERT INTO exercise_results
            (user_id, ts, exercise_id, category, level, correct)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                now(),
                exercise_id,
                exercise["category"],
                exercise["level"],
                int(correct)
            )
        )

        conn.commit()

    finally:

        conn.close()

    return {

        "correct": correct,

        "answer_index": exercise["answer"],

        "why": exercise["why"]
    }


# ============================================================
# REVIEW
# ============================================================

@app.get("/api/review/{user_id}")
def review(user_id: str):

    conn = get_db()

    try:

        card = conn.execute(
            """
            SELECT *
            FROM cards
            WHERE user_id = ?
            AND due <= ?
            ORDER BY due
            LIMIT 1
            """,
            (
                user_id,
                now()
            )
        ).fetchone()

        total = conn.execute(
            """
            SELECT COUNT(*)
            FROM cards
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()[0]

        due = conn.execute(
            """
            SELECT COUNT(*)
            FROM cards
            WHERE user_id = ?
            AND due <= ?
            """,
            (
                user_id,
                now()
            )
        ).fetchone()[0]

        if card:

            card_data = {

                "id": card["id"],

                "sentence": card["sentence"],

                "hint": card["answer"]
            }

        else:

            card_data = None

        return {

            "due_count": due,

            "total_cards": total,

            "card": card_data
        }

    finally:

        conn.close()


@app.post("/api/review/answer")
def review_answer(data: dict):

    user_id = data.get(
        "user_id",
        "guest"
    )

    card_id = int(
        data.get("card_id")
    )

    answer = str(
        data.get(
            "answer",
            ""
        )
    ).strip()

    conn = get_db()

    try:

        card = conn.execute(
            """
            SELECT *
            FROM cards
            WHERE id = ?
            AND user_id = ?
            """,
            (
                card_id,
                user_id
            )
        ).fetchone()

        if not card:

            raise HTTPException(
                status_code=404,
                detail="Card not found"
            )

        correct = (
            answer.lower()
            ==
            card["answer"].lower()
        )

        days = (
            2
            if correct
            else 1
        )

        due = (
            datetime.utcnow()
            +
            timedelta(days=days)
        ).isoformat()

        conn.execute(
            """
            UPDATE cards
            SET due = ?,
                reps = reps + 1
            WHERE id = ?
            AND user_id = ?
            """,
            (
                due,
                card_id,
                user_id
            )
        )

        conn.commit()

        return {

            "correct": correct,

            "answer": card["answer"],

            "next_review_days": days
        }

    finally:

        conn.close()


# ============================================================

# SPEECH / WHISPER
# ============================================================

@app.post("/api/transcribe")
async def transcribe(
    file: UploadFile = File(...)
):
    temp_path = None
    t0 = time.perf_counter()

    try:
        audio_data = await file.read()

        if not audio_data:
            raise HTTPException(
                status_code=400,
                detail="No audio data received"
            )

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".webm"
        ) as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name

        print(
            f"[SPEED TEST] Audio read/save: "
            f"{time.perf_counter() - t0:.2f}s"
        )

        whisper_start = time.perf_counter()

        segments, info = whisper_model.transcribe(
            temp_path,
            beam_size=1,
            language="en",
            vad_filter=True
        )

        transcript = " ".join(
            segment.text.strip()
            for segment in segments
        ).strip()

        print(
            f"[SPEED TEST] Whisper transcription: "
            f"{time.perf_counter() - whisper_start:.2f}s"
        )

        print(f"[SPEECH RESULT] {transcript!r}")

        return {
            "transcript": transcript,
            "words": transcript.split()
        }

    except HTTPException:
        raise

    except Exception as e:
        print("TRANSCRIBE ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=f"Speech recognition error: {str(e)}"
        )

    finally:
        print(
            f"[SPEED TEST] Total endpoint time: "
            f"{time.perf_counter() - t0:.2f}s"
        )

        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "stt": "whisper"
    }

# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "message":
        "AI Language Tutor backend is running"
    }


# ============================================================
# OPENAI TEST
# ============================================================

@app.get("/api/ai-test")
def ai_test():

    if not openai_client:

        raise HTTPException(
            status_code=500,
            detail=(
                "OPENAI_API_KEY is not configured"
            )
        )

    try:

        response = (
            openai_client.responses.create(
                model="gpt-5-mini",
                input=(
                    "You are an English tutor. "
                    "Say hello to the student "
                    "in one short sentence."
                )
            )
        )

        return {

            "success": True,

            "reply": response.output_text
        }

    except Exception as e:

        print(
            "OPENAI ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
# ============================================================
# A2 -> C2 COURSE LESSONS
# ============================================================

COURSE_LEVELS = {
    "A1": [
        "Pronouns",
        "am / is / are",
        "Articles: a / an / the",
        "Singular and Plural",
        "Subject-Verb Agreement",
        "Present Simple",
        "Present Continuous",
        "Basic Questions",
        "Daily Life Vocabulary",
        "University Vocabulary",
    ],

    "A2": [
        "Past Simple",
        "Past Continuous",
        "Future: will and going to",
        "Present Perfect",
        "Comparatives and Superlatives",
        "Modal Verbs",
        "Countable and Uncountable Nouns",
        "Quantifiers",
        "Prepositions in Context",
        "Adverbs of Frequency",
        "Everyday Conversations",
        "Paragraph Writing",
    ],

    "B1": [
        "Present Perfect vs Past Simple",
        "Past Perfect",
        "Future Forms",
        "First Conditional",
        "Second Conditional",
        "Relative Clauses",
        "Gerunds and Infinitives",
        "Reported Speech",
        "Passive Voice",
        "Phrasal Verbs",
        "Academic Vocabulary",
        "Opinion Writing",
    ],

    "B2": [
        "Advanced Tenses",
        "Mixed Conditionals",
        "Advanced Passive Voice",
        "Causative Structures",
        "Advanced Reported Speech",
        "Modal Verbs of Deduction",
        "Complex Relative Clauses",
        "Inversion",
        "Advanced Phrasal Verbs",
        "Collocations",
        "Formal English",
        "Essay Writing",
    ],

    "C1": [
        "Advanced Sentence Structures",
        "Emphasis and Cleft Sentences",
        "Advanced Conditionals",
        "Subjunctive Mood",
        "Nuanced Modal Verbs",
        "Advanced Linking Devices",
        "Academic Grammar",
        "Advanced Vocabulary",
        "Idioms and Expressions",
        "Professional Communication",
        "Critical Reading",
        "Advanced Essay Writing",
    ],

    "C2": [
        "Mastering Complex Grammar",
        "Advanced Inversion",
        "Ellipsis and Substitution",
        "Discourse Analysis",
        "Advanced Collocations",
        "Idiomatic Language",
        "Register and Tone",
        "Academic Writing Mastery",
        "Professional Writing Mastery",
        "Critical Analysis",
        "Advanced Speaking",
        "English Proficiency Mastery",
    ],
}


# ============================================================
# LESSON CONTENT
# ============================================================

LESSON_CONTENT = {

    # ========================================================
    # A2
    # ========================================================

    "Past Simple": {
        "explanation": "Use the Past Simple to talk about completed actions in the past. Regular verbs usually take -ed, while irregular verbs have special forms.",
        "examples": [
            "I visited my friend yesterday.",
            "She watched a movie last night.",
            "They went to Karachi last week."
        ],
        "practice_question": "Which sentence is correct?",
        "practice_options": [
            "I go to university yesterday.",
            "I went to university yesterday.",
            "I going to university yesterday.",
            "I have go to university yesterday."
        ],
        "practice_answer": 1,
        "quiz_question": "Choose the correct past form: She ___ her homework last night.",
        "quiz_options": [
            "do",
            "does",
            "did",
            "doing"
        ],
        "quiz_answer": 2
    },

    "Past Continuous": {
        "explanation": "Use the Past Continuous for an action that was happening at a particular time in the past. It uses was or were + verb-ing.",
        "examples": [
            "I was studying at 8 PM.",
            "They were playing football.",
            "She was cooking when I called."
        ],
        "practice_question": "Choose the correct sentence.",
        "practice_options": [
            "I was study yesterday.",
            "I was studying yesterday.",
            "I were studying yesterday.",
            "I studying was yesterday."
        ],
        "practice_answer": 1,
        "quiz_question": "They ___ watching TV when I arrived.",
        "quiz_options": [
            "was",
            "were",
            "are",
            "is"
        ],
        "quiz_answer": 1
    },

    "Future: will and going to": {
        "explanation": "Use will for predictions, promises and quick decisions. Use going to for plans or intentions that already exist.",
        "examples": [
            "I will help you.",
            "I think it will rain.",
            "I am going to study tonight."
        ],
        "practice_question": "Which sentence shows a planned action?",
        "practice_options": [
            "I am going to visit Lahore next week.",
            "I visited Lahore yesterday.",
            "I visit Lahore every day.",
            "I was visiting Lahore."
        ],
        "practice_answer": 0,
        "quiz_question": "I have already planned it. I ___ study tonight.",
        "quiz_options": [
            "am going to",
            "went",
            "was",
            "have"
        ],
        "quiz_answer": 0
    },

    "Present Perfect": {
        "explanation": "Use the Present Perfect for experiences, recent actions, or actions connected to the present. It uses have or has + past participle.",
        "examples": [
            "I have finished my homework.",
            "She has visited Islamabad.",
            "They have never seen snow."
        ],
        "practice_question": "Choose the correct sentence.",
        "practice_options": [
            "I have finished my work.",
            "I has finished my work.",
            "I have finish my work.",
            "I finished have my work."
        ],
        "practice_answer": 0,
        "quiz_question": "She ___ completed the assignment.",
        "quiz_options": [
            "have",
            "has",
            "having",
            "had"
        ],
        "quiz_answer": 1
    },

    "Comparatives and Superlatives": {
        "explanation": "Comparatives compare two things. Superlatives compare three or more things. Common forms are bigger, more beautiful, biggest and most beautiful.",
        "examples": [
            "Ali is taller than Ahmed.",
            "This book is more interesting than that one.",
            "She is the best student in the class."
        ],
        "practice_question": "Choose the correct comparative form.",
        "practice_options": [
            "more tall",
            "taller",
            "tallest",
            "most tall"
        ],
        "practice_answer": 1,
        "quiz_question": "This is ___ movie I have ever watched.",
        "quiz_options": [
            "better",
            "best",
            "the best",
            "good"
        ],
        "quiz_answer": 2
    },

    "Modal Verbs": {
        "explanation": "Modal verbs such as can, could, should, must and may express ability, advice, possibility, permission or obligation.",
        "examples": [
            "I can swim.",
            "You should study regularly.",
            "Students must attend the exam."
        ],
        "practice_question": "Which modal gives advice?",
        "practice_options": [
            "should",
            "must",
            "can",
            "may"
        ],
        "practice_answer": 0,
        "quiz_question": "You ___ drink more water. It is good advice.",
        "quiz_options": [
            "should",
            "mustn't",
            "can't",
            "wouldn't"
        ],
        "quiz_answer": 0
    },

    "Countable and Uncountable Nouns": {
        "explanation": "Countable nouns can be counted, such as books and students. Uncountable nouns cannot normally be counted individually, such as water and information.",
        "examples": [
            "I have three books.",
            "She needs some water.",
            "We received useful information."
        ],
        "practice_question": "Which noun is uncountable?",
        "practice_options": [
            "book",
            "student",
            "water",
            "apple"
        ],
        "practice_answer": 2,
        "quiz_question": "Which sentence is correct?",
        "quiz_options": [
            "I need some information.",
            "I need an information.",
            "I need informations.",
            "I need many information."
        ],
        "quiz_answer": 0
    },

    "Quantifiers": {
        "explanation": "Quantifiers tell us about quantity. Common examples include some, any, much, many, a lot of, few and little.",
        "examples": [
            "I have many books.",
            "There is much water.",
            "She has a few friends."
        ],
        "practice_question": "Which word is normally used with countable plural nouns?",
        "practice_options": [
            "many",
            "much",
            "little",
            "less"
        ],
        "practice_answer": 0,
        "quiz_question": "There are ___ students in the classroom.",
        "quiz_options": [
            "much",
            "many",
            "little",
            "less"
        ],
        "quiz_answer": 1
    },

    "Prepositions in Context": {
        "explanation": "Prepositions show relationships of time, place and direction. Common examples are in, on, at, to, from and between.",
        "examples": [
            "I live in Karachi.",
            "The class starts at 9 AM.",
            "The book is on the table."
        ],
        "practice_question": "Choose the correct preposition: I live ___ Karachi.",
        "practice_options": [
            "at",
            "on",
            "in",
            "to"
        ],
        "practice_answer": 2,
        "quiz_question": "The meeting starts ___ Monday.",
        "quiz_options": [
            "in",
            "on",
            "at",
            "from"
        ],
        "quiz_answer": 1
    },

    "Adverbs of Frequency": {
        "explanation": "Adverbs of frequency describe how often something happens. Common examples are always, usually, often, sometimes, rarely and never.",
        "examples": [
            "I always study at night.",
            "She usually walks to university.",
            "He never drinks coffee."
        ],
        "practice_question": "Which word means 100% of the time?",
        "practice_options": [
            "never",
            "sometimes",
            "always",
            "rarely"
        ],
        "practice_answer": 2,
        "quiz_question": "I ___ go to university on weekdays.",
        "quiz_options": [
            "always",
            "never",
            "rarely",
            "nothing"
        ],
        "quiz_answer": 0
    },

    "Everyday Conversations": {
        "explanation": "Everyday English helps you communicate naturally in common situations such as greetings, shopping, asking for help and making requests.",
        "examples": [
            "Could you help me, please?",
            "How are you doing?",
            "Could I have a cup of tea?"
        ],
        "practice_question": "Which is a polite request?",
        "practice_options": [
            "Give me water.",
            "Could you give me some water, please?",
            "Water now.",
            "You give water."
        ],
        "practice_answer": 1,
        "quiz_question": "What is a polite way to ask for help?",
        "quiz_options": [
            "Help me.",
            "Could you help me, please?",
            "You help.",
            "I need help you."
        ],
        "quiz_answer": 1
    },

    "Paragraph Writing": {
        "explanation": "A good paragraph usually has a topic sentence, supporting sentences and a concluding sentence. Keep ideas connected and clear.",
        "examples": [
            "My university is an important part of my life.",
            "I attend classes and learn new skills there.",
            "Therefore, university helps me prepare for my future."
        ],
        "practice_question": "What usually introduces the main idea of a paragraph?",
        "practice_options": [
            "Topic sentence",
            "Random sentence",
            "Question only",
            "Title only"
        ],
        "practice_answer": 0,
        "quiz_question": "Which sentence is best as a topic sentence?",
        "quiz_options": [
            "I like many things.",
            "My university helps me develop useful skills.",
            "Yesterday was Monday.",
            "The weather is hot."
        ],
        "quiz_answer": 1
    },


    # ========================================================
    # B1
    # ========================================================

    "Present Perfect vs Past Simple": {
        "explanation": "Use Past Simple for completed actions at a finished past time. Use Present Perfect when the exact past time is not important or the action is connected to the present.",
        "examples": [
            "I visited Lahore last year.",
            "I have visited Lahore three times.",
            "She finished the project yesterday."
        ],
        "practice_question": "Choose the correct sentence.",
        "practice_options": [
            "I have seen him yesterday.",
            "I saw him yesterday.",
            "I see him yesterday.",
            "I had see him yesterday."
        ],
        "practice_answer": 1,
        "quiz_question": "I ___ this movie three times.",
        "quiz_options": [
            "saw",
            "have seen",
            "see",
            "was seeing"
        ],
        "quiz_answer": 1
    },

    "Past Perfect": {
        "explanation": "Use Past Perfect to show that one past action happened before another past action. It uses had + past participle.",
        "examples": [
            "I had finished dinner before he arrived.",
            "She had left when I called.",
            "They had already started the class."
        ],
        "practice_question": "Choose the correct form.",
        "practice_options": [
            "had finished",
            "has finished",
            "have finish",
            "was finish"
        ],
        "practice_answer": 0,
        "quiz_question": "When I arrived, the class ___ already started.",
        "quiz_options": [
            "has",
            "had",
            "was",
            "have"
        ],
        "quiz_answer": 1
    },

    "Future Forms": {
        "explanation": "English uses different future forms for different meanings. Will, going to and Present Continuous can describe predictions, plans and arrangements.",
        "examples": [
            "I will call you later.",
            "I am going to study tonight.",
            "I am meeting my teacher tomorrow."
        ],
        "practice_question": "Which sentence describes a fixed arrangement?",
        "practice_options": [
            "I am meeting my teacher tomorrow.",
            "I think it will rain.",
            "I will help you.",
            "I may go."
        ],
        "practice_answer": 0,
        "quiz_question": "I have already decided my plan. I ___ start tomorrow.",
        "quiz_options": [
            "am going to",
            "was",
            "have",
            "did"
        ],
        "quiz_answer": 0
    },

    "First Conditional": {
        "explanation": "The First Conditional describes a real or possible future situation. It uses if + Present Simple, followed by will + base verb.",
        "examples": [
            "If it rains, I will stay home.",
            "If you study, you will pass.",
            "If she calls, I will answer."
        ],
        "practice_question": "Choose the correct sentence.",
        "practice_options": [
            "If I study, I will pass.",
            "If I studied, I will pass.",
            "If I study, I passed.",
            "If I studying, I pass."
        ],
        "practice_answer": 0,
        "quiz_question": "If you work hard, you ___ succeed.",
        "quiz_options": [
            "will",
            "would",
            "did",
            "had"
        ],
        "quiz_answer": 0
    },

    "Second Conditional": {
        "explanation": "The Second Conditional talks about unreal, unlikely or imaginary situations in the present or future.",
        "examples": [
            "If I had more money, I would travel.",
            "If I were you, I would study.",
            "If she lived here, we would meet often."
        ],
        "practice_question": "Choose the correct sentence.",
        "practice_options": [
            "If I were rich, I would travel.",
            "If I am rich, I would travel.",
            "If I was rich, I will travel.",
            "If I rich, I travel."
        ],
        "practice_answer": 0,
        "quiz_question": "If I had more time, I ___ learn another language.",
        "quiz_options": [
            "will",
            "would",
            "can",
            "did"
        ],
        "quiz_answer": 1
    },

    "Relative Clauses": {
        "explanation": "Relative clauses give extra information about a person or thing. Common relative words are who, which, that, whose and where.",
        "examples": [
            "The man who lives here is my teacher.",
            "This is the book that I bought.",
            "Karachi is the city where I live."
        ],
        "practice_question": "Which word is commonly used for people?",
        "practice_options": [
            "who",
            "where",
            "which only",
            "when"
        ],
        "practice_answer": 0,
        "quiz_question": "The student ___ won the prize is my friend.",
        "quiz_options": [
            "who",
            "where",
            "when",
            "what"
        ],
        "quiz_answer": 0
    },

    "Gerunds and Infinitives": {
        "explanation": "A gerund is a verb ending in -ing used as a noun. An infinitive usually uses to + base verb. Different verbs are followed by different forms.",
        "examples": [
            "I enjoy reading.",
            "She wants to learn.",
            "They decided to leave."
        ],
        "practice_question": "Choose the correct sentence.",
        "practice_options": [
            "I enjoy to read.",
            "I enjoy reading.",
            "I enjoying read.",
            "I enjoy read."
        ],
        "practice_answer": 1,
        "quiz_question": "She wants ___ English.",
        "quiz_options": [
            "learning",
            "to learn",
            "learned",
            "learns"
        ],
        "quiz_answer": 1
    },

    "Reported Speech": {
        "explanation": "Reported speech tells someone what another person said without using the exact original words. Tenses often move back when the reporting verb is in the past.",
        "examples": [
            "He said, 'I am tired.'",
            "He said that he was tired.",
            "She said that she liked English."
        ],
        "practice_question": "Choose the correct reported sentence.",
        "practice_options": [
            "He said that he was tired.",
            "He said that he is tired yesterday.",
            "He said he tired.",
            "He say he was tired."
        ],
        "practice_answer": 0,
        "quiz_question": "She said, 'I am busy.' Reported: She said that she ___ busy.",
        "quiz_options": [
            "is",
            "was",
            "were",
            "be"
        ],
        "quiz_answer": 1
    },

    "Passive Voice": {
        "explanation": "Passive voice focuses on the action or receiver rather than the person doing it. It uses a form of be + past participle.",
        "examples": [
            "The letter was written by Ali.",
            "The work is completed.",
            "English is spoken around the world."
        ],
        "practice_question": "Choose the passive sentence.",
        "practice_options": [
            "Ali wrote the letter.",
            "The letter was written by Ali.",
            "Ali is writing.",
            "Ali writes letters."
        ],
        "practice_answer": 1,
        "quiz_question": "The project ___ completed yesterday.",
        "quiz_options": [
            "was",
            "were",
            "is",
            "has"
        ],
        "quiz_answer": 0
    },

    "Phrasal Verbs": {
        "explanation": "Phrasal verbs combine a verb with a particle such as up, out, on or off. Their meanings can be different from the original verb.",
        "examples": [
            "Please turn off the light.",
            "I wake up at 7 AM.",
            "She gave up smoking."
        ],
        "practice_question": "What does 'wake up' mean?",
        "practice_options": [
            "Go to sleep",
            "Stop working",
            "Stop sleeping",
            "Run away"
        ],
        "practice_answer": 2,
        "quiz_question": "Please ___ the lights before leaving.",
        "quiz_options": [
            "turn off",
            "wake up",
            "give up",
            "look after"
        ],
        "quiz_answer": 0
    },

    "Academic Vocabulary": {
        "explanation": "Academic vocabulary is useful in university study and formal writing. Words such as analyze, evaluate, evidence and significant are common.",
        "examples": [
            "We need to analyze the data.",
            "The evidence supports the theory.",
            "This result is significant."
        ],
        "practice_question": "Which word means to examine something carefully?",
        "practice_options": [
            "analyze",
            "sleep",
            "arrive",
            "borrow"
        ],
        "practice_answer": 0,
        "quiz_question": "Researchers ___ the data before writing the report.",
        "quiz_options": [
            "analyze",
            "sleep",
            "borrow",
            "forget"
        ],
        "quiz_answer": 0
    },

    "Opinion Writing": {
        "explanation": "Opinion writing presents your viewpoint and supports it with reasons and examples. Useful phrases include I believe, in my opinion and because.",
        "examples": [
            "In my opinion, students should learn programming.",
            "I believe technology improves education.",
            "One reason is that it saves time."
        ],
        "practice_question": "Which phrase clearly introduces an opinion?",
        "practice_options": [
            "In my opinion",
            "Yesterday",
            "At the table",
            "For example only"
        ],
        "practice_answer": 0,
        "quiz_question": "Which sentence expresses an opinion?",
        "quiz_options": [
            "In my opinion, online learning is useful.",
            "The class starts at 9 AM.",
            "Karachi is in Pakistan.",
            "The book has 200 pages."
        ],
        "quiz_answer": 0
    },
}


# ============================================================
# GENERIC CONTENT FOR B2-C2
# ============================================================

GENERIC_CONTENT = {

    "Advanced Tenses": (
        "Advanced tenses help describe actions with precise relationships in time.",
        ["I had been studying before the exam.", "She will have finished the project by Friday.", "They have been working since morning."],
        "Which tense shows an action continuing up to a point in the past?",
        ["Past Perfect Continuous", "Present Simple", "Future Simple", "Past Simple"],
        0,
        "By next month, she ___ here for two years.",
        ["will have been working", "worked", "works", "is work"],
        0
    ),

    "Mixed Conditionals": (
        "Mixed conditionals combine different time references to describe relationships between past and present situations.",
        ["If I had studied harder, I would have a better job now.", "If she were more careful, she would not have made that mistake."],
        "Mixed conditionals connect different time periods.",
        ["True", "False", "Only past", "Only future"],
        0,
        "If I had taken the course, I ___ more confident now.",
        ["would be", "will be", "was", "am"],
        0
    ),

    "Advanced Passive Voice": (
        "Advanced passive structures allow formal English to focus on processes, results and reported information.",
        ["The problem is believed to have been solved.", "He was expected to complete the work."],
        "Which structure is passive?",
        ["The report was completed.", "The team completed the report.", "They complete reports.", "They are completing reports."],
        0,
        "The suspect is believed ___ left the country.",
        ["to have", "having", "has", "had"],
        0
    ),

    "Causative Structures": (
        "Causative structures describe situations where one person causes another person to do something or arranges for something to be done.",
        ["I had my car repaired.", "She got her computer fixed."],
        "Which sentence shows a causative structure?",
        ["I had my phone repaired.", "I repaired my phone myself.", "My phone is new.", "I use my phone."],
        0,
        "I had my laptop ___ yesterday.",
        ["repaired", "repair", "repairing", "repairs"],
        0
    ),

    "Advanced Reported Speech": (
        "Advanced reported speech uses reporting verbs such as admit, deny, suggest, recommend and warn.",
        ["He admitted making a mistake.", "She suggested that we leave early."],
        "Which verb can introduce reported advice?",
        ["recommend", "sleep", "arrive", "borrow"],
        0,
        "She recommended ___ earlier.",
        ["leaving", "leave", "left", "to left"],
        0
    ),

    "Modal Verbs of Deduction": (
        "Modal verbs of deduction express how certain we are about a situation. Must shows strong certainty, while might and could show possibility.",
        ["He must be tired.", "She might be at home.", "They can't be serious."],
        "Which modal shows strong deduction?",
        ["must", "might", "could", "may"],
        0,
        "He has not slept all night. He ___ be tired.",
        ["must", "mightn't", "can't", "would"],
        0
    ),

    "Complex Relative Clauses": (
        "Complex relative clauses provide detailed information and can use which, whom, whose and prepositions.",
        ["The professor, whom I met yesterday, teaches linguistics.", "The project, which was completed last week, was successful."],
        "Which relative word can refer to a person as an object?",
        ["whom", "where", "when", "which only"],
        0,
        "The researcher, ___ we interviewed, published a new paper.",
        ["whom", "where", "when", "which"],
        0
    ),

    "Inversion": (
        "Inversion changes the normal word order and is often used for emphasis or formal style.",
        ["Never have I seen such a view.", "Rarely does he make mistakes."],
        "Which sentence uses inversion?",
        ["Never have I seen this.", "I have never seen this.", "I see this.", "I saw this."],
        0,
        "Rarely ___ such an interesting lecture.",
        ["do I attend", "I attend", "I attended", "attend I"],
        0
    ),

    "Advanced Phrasal Verbs": (
        "Advanced phrasal verbs are common in natural English and professional communication.",
        ["The meeting was called off.", "We need to carry out the experiment.", "She came up with a solution."],
        "What does 'carry out' mean?",
        ["perform", "cancel", "sleep", "remove"],
        0,
        "The researchers will ___ an experiment.",
        ["carry out", "give up", "turn off", "wake up"],
        0
    ),

    "Collocations": (
        "Collocations are words that naturally occur together, such as make a decision, take responsibility and conduct research.",
        ["make a decision", "conduct research", "take responsibility"],
        "Which is the natural collocation?",
        ["make a decision", "do a decision", "create a decision", "build a decision"],
        0,
        "Researchers ___ research before publishing.",
        ["conduct", "make", "do a", "build"],
        0
    ),

    "Formal English": (
        "Formal English is appropriate for academic, professional and official communication. It avoids slang and overly casual expressions.",
        ["I would appreciate your response.", "Please find the requested document attached."],
        "Which sentence is more formal?",
        ["I would appreciate your response.", "Send me this now.", "Give me that.", "What's up?"],
        0,
        "Choose the formal sentence.",
        ["I would like to request further information.", "Give me more info.", "Tell me stuff.", "Send it fast."],
        0
    ),

    "Essay Writing": (
        "A strong essay normally includes an introduction, clear thesis, body paragraphs with evidence and a conclusion.",
        ["The introduction presents the main argument.", "Body paragraphs explain and support the thesis."],
        "Where is the main argument usually presented?",
        ["Introduction", "Random paragraph", "Conclusion only", "Title"],
        0,
        "A strong essay should have a clear ___.",
        ["thesis", "random idea", "greeting", "question only"],
        0
    ),

    "Advanced Sentence Structures": (
        "Advanced sentence structures combine clauses and ideas clearly using coordination, subordination and other complex patterns.",
        ["Although it was difficult, she completed the project.", "Having finished the work, he went home."],
        "Which sentence is complex?",
        ["Although it was difficult, she completed the project.", "She worked.", "He ran.", "They slept."],
        0,
        "___ the assignment, she submitted it.",
        ["Having completed", "Complete", "Completing has", "Completed has"],
        0
    ),

    "Emphasis and Cleft Sentences": (
        "Cleft sentences highlight particular information. Common structures include It is...that and What...is...",
        ["It was Ali who solved the problem.", "What I need is more time."],
        "Which sentence uses a cleft structure?",
        ["It was Ali who solved the problem.", "Ali solved the problem.", "Ali is solving it.", "Ali solves problems."],
        0,
        "___ I need is more practice.",
        ["What", "Which", "Who", "Where"],
        0
    ),

    "Advanced Conditionals": (
        "Advanced conditionals express hypothetical, unreal, past and mixed situations with precise meanings.",
        ["Had I known, I would have acted differently.", "Were she here, she could help us."],
        "Which phrase can replace 'If I had known' in formal English?",
        ["Had I known", "Have I known", "Did I know", "Knowing I"],
        0,
        "Had I known about the problem, I ___ earlier.",
        ["would have acted", "will act", "act", "acted"],
        0
    ),

    "Subjunctive Mood": (
        "The subjunctive is used in formal English for recommendations, demands, wishes and hypothetical situations.",
        ["It is essential that he be present.", "I suggest that she study more."],
        "Which sentence uses the formal subjunctive?",
        ["It is essential that he be present.", "He is present.", "He was present.", "He will present."],
        0,
        "It is important that every student ___ on time.",
        ["be", "is", "was", "being"],
        0
    ),

    "Nuanced Modal Verbs": (
        "Advanced modal verbs communicate subtle differences in certainty, obligation, possibility and politeness.",
        ["You might want to reconsider.", "You must have misunderstood.", "She may have forgotten."],
        "Which phrase is a polite suggestion?",
        ["You might want to reconsider.", "You must reconsider.", "Reconsider now.", "You will reconsider."],
        0,
        "He ___ have forgotten the meeting.",
        ["may", "mustn't", "can't", "shall"],
        0
    ),

    "Advanced Linking Devices": (
        "Advanced linking devices connect ideas logically and make academic writing more coherent.",
        ["Nevertheless, the results were positive.", "Furthermore, the study provides useful evidence."],
        "Which word shows contrast?",
        ["Nevertheless", "Furthermore", "Therefore", "Similarly"],
        0,
        "The evidence was limited; ___, the conclusion was useful.",
        ["nevertheless", "because", "similarly", "firstly"],
        0
    ),

    "Academic Grammar": (
        "Academic grammar uses precise structures, formal vocabulary, passive constructions and careful qualification.",
        ["The results indicate that further research is required.", "It has been suggested that the method is effective."],
        "Which sentence is more academic?",
        ["The results indicate that further research is required.", "The results are cool.", "The study is kinda good.", "This thing works."],
        0,
        "The findings ___ that further research is necessary.",
        ["indicate", "go", "make", "come"],
        0
    ),

    "Advanced Vocabulary": (
        "Advanced vocabulary allows speakers and writers to express precise meanings, relationships and arguments.",
        ["The evidence is compelling.", "The results were inconclusive.", "The proposal is feasible."],
        "What does 'feasible' mean?",
        ["possible and practical", "impossible", "unclear", "unrelated"],
        0,
        "The plan is realistic and ___.",
        ["feasible", "impossible", "random", "irrelevant"],
        0
    ),

    "Idioms and Expressions": (
        "Idioms are expressions whose meanings are not always literal. They are common in natural English.",
        ["Break the ice means to make people feel more comfortable.", "Once in a blue moon means very rarely."],
        "What does 'break the ice' mean?",
        ["Start a friendly conversation", "Break something", "Become angry", "Leave a place"],
        0,
        "If something happens 'once in a blue moon', it happens ___.",
        ["very rarely", "every day", "every hour", "always"],
        0
    ),

    "Professional Communication": (
        "Professional communication should be clear, respectful, concise and appropriate for the workplace.",
        ["I would like to schedule a meeting.", "Thank you for your time and consideration."],
        "Which is appropriate in professional communication?",
        ["I would like to schedule a meeting.", "Yo, meet me.", "Come here now.", "What's up boss?"],
        0,
        "Choose the professional closing.",
        ["Kind regards", "Bye bro", "See ya", "Later"],
        0
    ),

    "Critical Reading": (
        "Critical reading means analyzing an author's argument, evidence, assumptions, purpose and reliability.",
        ["Ask what evidence supports the claim.", "Identify whether the source is reliable."],
        "What should you examine when reading critically?",
        ["Evidence", "Font color only", "Page size only", "Number of pictures"],
        0,
        "Critical reading requires evaluating the author's ___.",
        ["evidence", "font", "background color", "page length"],
        0
    ),

    "Advanced Essay Writing": (
        "Advanced essays require a precise thesis, logical organization, strong evidence, cohesion and careful academic language.",
        ["A strong thesis guides the entire essay.", "Each paragraph should contribute to the central argument."],
        "What guides an academic essay?",
        ["A clear thesis", "Random ideas", "A greeting", "A joke"],
        0,
        "Every body paragraph should support the central ___.",
        ["argument", "greeting", "title", "question"],
        0
    ),

    "Mastering Complex Grammar": (
        "Complex grammar combines advanced clauses, tense relationships, conditionals, passive structures and precise modifiers.",
        ["Having completed the research, the team published its findings.", "Although the method was complex, the results were reliable."],
        "Which structure adds a dependent clause?",
        ["Although the method was complex", "The results", "The team", "Research"],
        0,
        "Although the task was difficult, she ___ it.",
        ["completed", "complete", "completing", "has complete"],
        0
    ),

    "Advanced Inversion": (
        "Advanced inversion places an auxiliary verb before the subject, often after negative or restrictive expressions.",
        ["Under no circumstances should you share the password.", "Not only did she pass, but she also achieved the highest score."],
        "Which sentence uses advanced inversion?",
        ["Under no circumstances should you do that.", "You should not do that.", "You do that.", "You did that."],
        0,
        "Not only ___ the exam, but she also received the highest score.",
        ["did she pass", "she passed", "passed she", "has she pass"],
        0
    ),

    "Ellipsis and Substitution": (
        "Ellipsis removes words that are understood from context. Substitution replaces repeated words with forms such as one, ones, do and so.",
        ["I ordered the large coffee, and she ordered the small one.", "I think so."],
        "What does ellipsis do?",
        ["It omits understood words.", "It adds random words.", "It changes every verb.", "It removes meaning."],
        0,
        "I prefer the blue shirt to the red ___.",
        ["one", "ones", "do", "so"],
        0
    ),

    "Discourse Analysis": (
        "Discourse analysis examines how language works across sentences and conversations, including coherence, context and speaker intention.",
        ["Analyze how ideas connect across a paragraph.", "Consider the speaker's purpose and context."],
        "What does discourse analysis examine?",
        ["Language in context", "Spelling only", "Letters only", "Numbers only"],
        0,
        "Discourse analysis considers language and its ___.",
        ["context", "font", "color", "size"],
        0
    ),

    "Advanced Collocations": (
        "Advanced collocations are natural combinations of words used by proficient speakers and writers.",
        ["pose a challenge", "reach a conclusion", "draw a distinction"],
        "Which is a natural collocation?",
        ["reach a conclusion", "make a conclusion always", "build a conclusion", "cook a conclusion"],
        0,
        "Researchers often ___ a distinction between the two concepts.",
        ["draw", "cook", "sleep", "break"],
        0
    ),

    "Idiomatic Language": (
        "Idiomatic language uses expressions with meanings that cannot always be understood literally.",
        ["The proposal was a long shot.", "She went the extra mile to help the team."],
        "What does 'go the extra mile' mean?",
        ["Make an additional effort", "Walk one mile", "Stop working", "Leave early"],
        0,
        "He went the extra mile to help us. This means he ___.",
        ["made extra effort", "left immediately", "did nothing", "became angry"],
        0
    ),

    "Register and Tone": (
        "Register refers to the level and style of language used in a situation. Tone communicates attitude such as confidence, respect or urgency.",
        ["Formal language is suitable for academic writing.", "A friendly tone is suitable for casual conversation."],
        "What does register describe?",
        ["Language style for a situation", "Grammar errors only", "Pronunciation only", "Spelling only"],
        0,
        "Academic writing normally uses a ___ register.",
        ["formal", "slang", "casual", "text-message"],
        0
    ),

    "Academic Writing Mastery": (
        "Academic writing mastery requires logical arguments, precise language, evidence, cohesion and appropriate academic conventions.",
        ["The evidence suggests a significant relationship.", "Further research is required to confirm the findings."],
        "What is important in academic writing?",
        ["Evidence and logical argument", "Slang", "Random opinions", "Informal jokes"],
        0,
        "Academic claims should normally be supported by ___.",
        ["evidence", "rumors", "jokes", "guesses"],
        0
    ),

    "Professional Writing Mastery": (
        "Professional writing should communicate information efficiently while maintaining accuracy, clarity, professionalism and an appropriate tone.",
        ["Please find attached the requested report.", "I would appreciate your feedback by Friday."],
        "Which quality is essential in professional writing?",
        ["Clarity", "Confusion", "Slang", "Randomness"],
        0,
        "Professional emails should be clear and ___.",
        ["concise", "confusing", "random", "informal always"],
        0
    ),

    "Critical Analysis": (
        "Critical analysis evaluates ideas rather than simply describing them. It considers evidence, strengths, weaknesses and alternative explanations.",
        ["The argument is supported by strong evidence.", "However, the sample size limits the conclusion."],
        "What does critical analysis evaluate?",
        ["Evidence and arguments", "Font color", "Page size", "Pictures only"],
        0,
        "Critical analysis should consider strengths and ___.",
        ["weaknesses", "colors", "fonts", "titles"],
        0
    ),

    "Advanced Speaking": (
        "Advanced speaking requires fluency, accurate grammar, varied vocabulary, clear pronunciation and the ability to explain complex ideas.",
        ["In my view, the main advantage is...", "There are several factors that should be considered."],
        "What is important in advanced speaking?",
        ["Fluency and clear communication", "Only memorization", "Only speed", "Only vocabulary"],
        0,
        "An advanced speaker should communicate complex ideas ___.",
        ["clearly", "randomly", "silently", "incorrectly"],
        0
    ),

    "English Proficiency Mastery": (
        "English proficiency mastery combines grammar, vocabulary, reading, writing, listening and speaking skills in real communication.",
        ["A proficient speaker can adapt language to different situations.", "Strong English requires both accuracy and effective communication."],
        "What does English proficiency include?",
        ["Multiple communication skills", "Grammar only", "Vocabulary only", "Speaking speed only"],
        0,
        "High English proficiency requires accurate and effective ___.",
        ["communication", "silence", "guessing", "translation only"],
        0
    ),
}


# ============================================================
# CREATE/FIX A2-C2 COURSE
# ============================================================

def initialize_advanced_course():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:

        # ----------------------------------------------------
        # Find highest existing IDs
        # ----------------------------------------------------

        cursor.execute(
            "SELECT COALESCE(MAX(id), 0) FROM lessons"
        )
        max_lesson_id = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COALESCE(MAX(id), 0) FROM learning_topics"
        )
        max_topic_id = cursor.fetchone()[0]

        lesson_id = max_lesson_id
        topic_id = max_topic_id

        # ----------------------------------------------------
        # Add A2 -> C2
        # ----------------------------------------------------

        for level in [
            "A2",
            "B1",
            "B2",
            "C1",
            "C2"
        ]:

            lesson_titles = COURSE_LEVELS[level]

            for order, title in enumerate(
                lesson_titles,
                start=1
            ):

                # ------------------------------------------------
                # Get lesson if it already exists
                # ------------------------------------------------

                cursor.execute(
                    """
                    SELECT id, topic_id
                    FROM lessons
                    WHERE level = ?
                    AND title = ?
                    """,
                    (
                        level,
                        title
                    )
                )

                existing_lesson = cursor.fetchone()

                # ------------------------------------------------
                # Get topic if it already exists
                # ------------------------------------------------

                cursor.execute(
                    """
                    SELECT id
                    FROM learning_topics
                    WHERE level = ?
                    AND title = ?
                    """,
                    (
                        level,
                        title
                    )
                )

                existing_topic = cursor.fetchone()

                # ------------------------------------------------
                # Create topic if missing
                # ------------------------------------------------

                if existing_topic:

                    current_topic_id = existing_topic[0]

                else:

                    topic_id += 1
                    current_topic_id = topic_id

                    cursor.execute(
                        """
                        INSERT INTO learning_topics
                        (
                            id,
                            level,
                            title,
                            category,
                            topic_order
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            current_topic_id,
                            level,
                            title,
                            "Grammar",
                            order
                        )
                    )

                # ------------------------------------------------
                # Get content
                # ------------------------------------------------

                if title in LESSON_CONTENT:

                    content = LESSON_CONTENT[title]

                    explanation = content[
                        "explanation"
                    ]

                    examples = json.dumps(
                        content["examples"]
                    )

                    practice_question = content[
                        "practice_question"
                    ]

                    practice_options = json.dumps(
                        content["practice_options"]
                    )

                    practice_answer = content[
                        "practice_answer"
                    ]

                    quiz_question = content[
                        "quiz_question"
                    ]

                    quiz_options = json.dumps(
                        content["quiz_options"]
                    )

                    quiz_answer = content[
                        "quiz_answer"
                    ]

                elif title in GENERIC_CONTENT:

                    content = GENERIC_CONTENT[title]

                    explanation = content[0]

                    examples = json.dumps(
                        content[1]
                    )

                    practice_question = content[2]

                    practice_options = json.dumps(
                        content[3]
                    )

                    practice_answer = content[4]

                    quiz_question = content[5]

                    quiz_options = json.dumps(
                        content[6]
                    )

                    quiz_answer = content[7]

                else:

                    # Safety fallback
                    explanation = (
                        f"This lesson covers {title} "
                        "and helps improve advanced English."
                    )

                    examples = json.dumps([
                        f"This is an example of {title}.",
                        f"Practice {title} in real communication."
                    ])

                    practice_question = (
                        f"Which option relates to {title}?"
                    )

                    practice_options = json.dumps([
                        title,
                        "Another topic",
                        "Something else",
                        "None"
                    ])

                    practice_answer = 0

                    quiz_question = (
                        f"Choose the best answer about {title}."
                    )

                    quiz_options = json.dumps([
                        title,
                        "Another topic",
                        "Something else",
                        "None"
                    ])

                    quiz_answer = 0

                # ------------------------------------------------
                # Existing lesson
                # ------------------------------------------------

                if existing_lesson:

                    current_lesson_id = existing_lesson[0]

                    cursor.execute(
                        """
                        UPDATE lessons
                        SET
                            topic_id = ?,
                            lesson_order = ?,
                            explanation = ?,
                            examples = ?,
                            practice_question = ?,
                            practice_options = ?,
                            practice_answer = ?,
                            quiz_question = ?,
                            quiz_options = ?,
                            quiz_answer = ?
                        WHERE id = ?
                        """,
                        (
                            current_topic_id,
                            order,
                            explanation,
                            examples,
                            practice_question,
                            practice_options,
                            practice_answer,
                            quiz_question,
                            quiz_options,
                            quiz_answer,
                            current_lesson_id
                        )
                    )

                # ------------------------------------------------
                # New lesson
                # ------------------------------------------------

                else:

                    lesson_id += 1
                    current_lesson_id = lesson_id

                    cursor.execute(
                        """
                        INSERT INTO lessons
                        (
                            id,
                            topic_id,
                            level,
                            title,
                            lesson_order,
                            explanation,
                            examples,
                            practice_question,
                            practice_options,
                            practice_answer,
                            quiz_question,
                            quiz_options,
                            quiz_answer
                        )
                        VALUES (
                            ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?,
                            ?, ?, ?
                        )
                        """,
                        (
                            current_lesson_id,
                            current_topic_id,
                            level,
                            title,
                            order,
                            explanation,
                            examples,
                            practice_question,
                            practice_options,
                            practice_answer,
                            quiz_question,
                            quiz_options,
                            quiz_answer
                        )
                    )

        # ----------------------------------------------------
        # Save everything
        # ----------------------------------------------------

        conn.commit()

        print("")
        print("==============================================")
        print("A2-C2 COURSE INITIALIZED SUCCESSFULLY")
        print("==============================================")
        print("A1 preserved")
        print("A2: 12 lessons")
        print("B1: 12 lessons")
        print("B2: 12 lessons")
        print("C1: 12 lessons")
        print("C2: 12 lessons")
        print("Total advanced lessons: 60")
        print("Lesson content added")
        print("Practice added")
        print("Quiz added")
        print("==============================================")
        print("")

    except Exception as e:

        conn.rollback()

        print("")
        print("==============================================")
        print("COURSE INITIALIZATION ERROR")
        print("==============================================")
        print(e)
        print("==============================================")
        print("")

    finally:

        conn.close()


# ============================================================
# RUN COURSE INITIALIZATION
# ============================================================

initialize_advanced_course()
import argparse
import sys
import requests


def test(name, condition, details=""):
    if condition:
        print(f"PASS: {name}")
        return True

    print(f"FAIL: {name}")
    if details:
        print(f"      {details}")
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--api",
        default="http://127.0.0.1:8010"
    )
    args = parser.parse_args()

    api = args.api.rstrip("/")
    user_id = "smoke-test-user"

    results = []

    # 1. Health
    try:
        r = requests.get(
            f"{api}/api/health",
            timeout=10
        )

        data = r.json()

        results.append(
            test(
                "GET /api/health",
                r.status_code == 200
                and data.get("status") == "ok",
                str(data)
            )
        )

    except Exception as e:
        results.append(
            test(
                "GET /api/health",
                False,
                repr(e)
            )
        )

    # 2. Profile
    try:
        r = requests.get(
            f"{api}/api/profile/{user_id}",
            timeout=10
        )

        data = r.json()

        results.append(
            test(
                "GET /api/profile/{user_id}",
                r.status_code == 200
                and "total" in data
                and "accuracy" in data
                and "levels" in data,
                str(data)
            )
        )

    except Exception as e:
        results.append(
            test(
                "GET /api/profile/{user_id}",
                False,
                repr(e)
            )
        )

    # 3. Chat - correct sentence
    try:
        r = requests.post(
            f"{api}/api/chat",
            json={
                "user_id": user_id,
                "message": "I am learning English."
            },
            timeout=120
        )

        data = r.json()

        results.append(
            test(
                "POST /api/chat - correct sentence",
                r.status_code == 200
                and "reply" in data
                and "profile" in data
                and "correction" in data,
                str(data)
            )
        )

    except Exception as e:
        results.append(
            test(
                "POST /api/chat - correct sentence",
                False,
                repr(e)
            )
        )

    # 4. Chat - grammar correction
    try:
        r = requests.post(
            f"{api}/api/chat",
            json={
                "user_id": user_id,
                "message": "He go to school every day."
            },
            timeout=120
        )

        data = r.json()
        correction = data.get("correction", {})

        results.append(
            test(
                "POST /api/chat - grammar correction",
                r.status_code == 200
                and correction.get("has_errors") is True
                and correction.get("corrected"),
                str(data)
            )
        )

    except Exception as e:
        results.append(
            test(
                "POST /api/chat - grammar correction",
                False,
                repr(e)
            )
        )

    # 5. Chat - empty message
    try:
        r = requests.post(
            f"{api}/api/chat",
            json={
                "user_id": user_id,
                "message": ""
            },
            timeout=10
        )

        data = r.json()

        results.append(
            test(
                "POST /api/chat - empty message",
                r.status_code == 200
                and "reply" in data,
                str(data)
            )
        )

    except Exception as e:
        results.append(
            test(
                "POST /api/chat - empty message",
                False,
                repr(e)
            )
        )

    # 6. Exercise
    try:
        r = requests.get(
            f"{api}/api/exercise/{user_id}",
            timeout=10
        )

        data = r.json()

        results.append(
            test(
                "GET /api/exercise/{user_id}",
                r.status_code == 200
                and "id" in data
                and "question" in data
                and "options" in data,
                str(data)
            )
        )

    except Exception as e:
        results.append(
            test(
                "GET /api/exercise/{user_id}",
                False,
                repr(e)
            )
        )

    # 7. Review
    try:
        r = requests.get(
            f"{api}/api/review/{user_id}",
            timeout=10
        )

        data = r.json()

        results.append(
            test(
                "GET /api/review/{user_id}",
                r.status_code == 200
                and "due_count" in data
                and "total_cards" in data,
                str(data)
            )
        )

    except Exception as e:
        results.append(
            test(
                "GET /api/review/{user_id}",
                False,
                repr(e)
            )
        )

    # 8. Root
    try:
        r = requests.get(
            f"{api}/",
            timeout=10
        )

        results.append(
            test(
                "GET /",
                r.status_code == 200,
                r.text
            )
        )

    except Exception as e:
        results.append(
            test(
                "GET /",
                False,
                repr(e)
            )
        )

    # 9. Profile after chat
    try:
        r = requests.get(
            f"{api}/api/profile/{user_id}",
            timeout=10
        )

        data = r.json()

        results.append(
            test(
                "Profile updates after chat",
                r.status_code == 200
                and data.get("total", 0) >= 1,
                str(data)
            )
        )

    except Exception as e:
        results.append(
            test(
                "Profile updates after chat",
                False,
                repr(e)
            )
        )

    # 10. Conversation memory
    try:
        requests.post(
            f"{api}/api/chat",
            json={
                "user_id": user_id,
                "message": "I study artificial intelligence."
            },
            timeout=120
        )

        r = requests.post(
            f"{api}/api/chat",
            json={
                "user_id": user_id,
                "message": "What do I study?"
            },
            timeout=120
        )

        data = r.json()
        reply = data.get("reply", "").lower()

        results.append(
            test(
                "Conversation memory",
                r.status_code == 200
                and (
                    "artificial intelligence" in reply
                    or "artificial" in reply
                ),
                reply
            )
        )

    except Exception as e:
        results.append(
            test(
                "Conversation memory",
                False,
                repr(e)
            )
        )

    # 11. Transcribe endpoint exists
    try:
        r = requests.post(
            f"{api}/api/transcribe",
            timeout=10
        )

        results.append(
            test(
                "POST /api/transcribe exists",
                r.status_code in (400, 422),
                f"HTTP {r.status_code}"
            )
        )

    except Exception as e:
        results.append(
            test(
                "POST /api/transcribe exists",
                False,
                repr(e)
            )
        )

    # 12. Invalid profile user
    try:
        r = requests.get(
            f"{api}/api/profile/smoke-nonexistent-user",
            timeout=10
        )

        results.append(
            test(
                "Profile handles new user",
                r.status_code == 200,
                r.text
            )
        )

    except Exception as e:
        results.append(
            test(
                "Profile handles new user",
                False,
                repr(e)
            )
        )

    # 13. Chat response contract
    try:
        r = requests.post(
            f"{api}/api/chat",
            json={
                "user_id": user_id,
                "message": "I like learning English."
            },
            timeout=120
        )

        data = r.json()

        required = [
            "reply",
            "profile",
            "deltas",
            "correction",
            "highlights",
            "cards_added"
        ]

        results.append(
            test(
                "Chat response contract",
                r.status_code == 200
                and all(key in data for key in required),
                str(data)
            )
        )

    except Exception as e:
        results.append(
            test(
                "Chat response contract",
                False,
                repr(e)
            )
        )

    passed = sum(results)
    total = len(results)

    print()
    print(f"RESULT: {passed}/{total} tests passed.")

    if passed != total:
        sys.exit(1)


if __name__ == "__main__":
    main()
import os, json, urllib.request, urllib.error
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
MAX_HISTORY = 20
MAX_MESSAGE = 12000

SYSTEM_PROMPT = """You are MedAI, a cautious medical information assistant.
Give clear, evidence-aware educational information. Do not claim certainty or diagnose from limited information.
For emergencies, advise immediate local emergency care. Ask useful follow-up questions when needed.
Explain symptoms, medicines, labs, first aid, prevention and general health.
Mention important contraindications/interactions when relevant. Never tell users to stop or change prescribed treatment without a clinician.
Respond in the user's language. This app is educational and does not replace a qualified clinician."""
def gemini(message, history):
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured on the server.")

    contents = []
    for item in (history or [])[-MAX_HISTORY:]:
        if not isinstance(item, dict):
            continue

        role = "model" if item.get("role") == "model" else "user"
        text = str(item.get("text", "")).strip()

        if text:
            contents.append({
                "role": role,
                "parts": [{"text": text[:MAX_MESSAGE]}]
            })

    if not contents or contents[-1]["parts"][0]["text"] != message:
        contents.append({
            "role": "user",
            "parts": [{"text": message}]
        })

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

    payload = {
        "systemInstruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.35,
            "maxOutputTokens": 1800
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        },
        method="POST"
    )

    # Retry temporary Gemini server errors
    max_retries = 3

    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                data = json.loads(response.read().decode("utf-8"))
                break

        except urllib.error.HTTPError as e:
            try:
                detail = e.read().decode("utf-8")
            except Exception:
                detail = ""

            # Temporary errors: retry automatically
            if e.code in (429, 500, 502, 503, 504) and attempt < max_retries:
                import time
                time.sleep(2 ** attempt)
                continue

            raise RuntimeError(
                f"Gemini API error ({e.code}). {detail[:500]}"
            )

        except Exception as e:
            if attempt < max_retries:
                import time
                time.sleep(2 ** attempt)
                continue

            raise RuntimeError(f"AI connection error: {e}")

    candidates = data.get("candidates") or []

    if not candidates:
        raise RuntimeError("The AI returned no answer.")

    parts = (candidates[0].get("content") or {}).get("parts") or []

    answer = "".join(
        p.get("text", "")
        for p in parts
        if isinstance(p, dict)
    ).strip()

    return answer or "No answer was returned."

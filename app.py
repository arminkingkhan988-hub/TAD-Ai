from flask import Flask, request, jsonify
import os
import json
import urllib.request
import urllib.error

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = "gemini-2.5-flash"

GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)


@app.route("/")
def home():
    return "MedAI is running successfully!"


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/chat", methods=["POST"])
def chat():
    if not GEMINI_API_KEY:
        return jsonify({
            "error": "GEMINI_API_KEY is not configured"
        }), 500

    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({
            "error": "Message is required"
        }), 400

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": message
                    }
                ]
            }
        ]
    }

    body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        GEMINI_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))

        text = (
            result
            .get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        if not text:
            return jsonify({
                "error": "Gemini returned an empty response"
            }), 502

        return jsonify({
            "reply": text
        })

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="ignore")

        return jsonify({
            "error": f"Gemini API error: HTTP {e.code}",
            "details": error_body
        }), e.code

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=False
    )

import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

MODEL = "gemini-2.5-flash"

URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    + MODEL
    + ":generateContent"
)


@app.route("/")
def home():
    return """
    <h1>MedAI</h1>
    <p>MedAI is running successfully.</p>
    """


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "MedAI"
    })


@app.route("/api/chat", methods=["POST"])
def chat():

    try:
        data = request.get_json(silent=True) or {}

        message = data.get("message", "").strip()

        if not message:
            return jsonify({
                "error": "پیغام ولیکه."
            }), 400

        if not API_KEY:
            return jsonify({
                "error": "GEMINI_API_KEY په Vercel کې نه دی تنظیم شوی."
            }), 500

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                "You are MedAI. "
                                "Answer the user in the same language "
                                "the user uses.\n\n"
                                "User:\n" + message
                            )
                        }
                    ]
                }
            ]
        }

        response = requests.post(
            URL,
            params={"key": API_KEY},
            json=payload,
            timeout=50
        )

        if response.status_code != 200:
            return jsonify({
                "error": "Gemini API error",
                "status": response.status_code,
                "details": response.text[:1000]
            }), 502

        result = response.json()

        candidates = result.get("candidates", [])

        if not candidates:
            return jsonify({
                "error": "Gemini ځواب ورنه کړ."
            }), 502

        parts = candidates[0].get(
            "content", {}
        ).get(
            "parts", []
        )

        answer = ""

        for part in parts:
            if part.get("text"):
                answer += part["text"]

        if not answer:
            return jsonify({
                "error": "خالي ځواب ترلاسه شو."
            }), 502

        return jsonify({
            "answer": answer
        })

    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Gemini وخت ختم شو، بیا هڅه وکړه."
        }), 504

    except Exception as e:
        print("ERROR:", repr(e))

        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )

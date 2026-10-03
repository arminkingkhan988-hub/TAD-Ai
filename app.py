import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

MODEL = "gemini-2.5-flash"

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    + MODEL
    + ":generateContent"
)


@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MedAI</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f5f5f5;
                margin: 0;
                padding: 30px;
            }

            .box {
                max-width: 700px;
                margin: auto;
                background: white;
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 5px 25px rgba(0,0,0,.08);
            }

            h1 {
                color: #10a37f;
            }

            textarea {
                width: 100%;
                min-height: 120px;
                box-sizing: border-box;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 10px;
                font-size: 16px;
            }

            button {
                margin-top: 10px;
                padding: 12px 20px;
                border: 0;
                border-radius: 10px;
                background: #10a37f;
                color: white;
                cursor: pointer;
                font-size: 16px;
            }

            #answer {
                margin-top: 20px;
                padding: 15px;
                background: #f0f0f0;
                border-radius: 10px;
                white-space: pre-wrap;
            }
        </style>
    </head>

    <body>

        <div class="box">

            <h1>🩺 MedAI</h1>

            <p>خپل سوال ولیکه:</p>

            <textarea
                id="message"
                placeholder="مثلاً: د انسان زړه څنګه کار کوي؟"
            ></textarea>

            <br>

            <button onclick="sendMessage()">
                Send
            </button>

            <div id="answer"></div>

        </div>

        <script>

        async function sendMessage() {

            const message =
                document.getElementById("message").value.trim();

            const answer =
                document.getElementById("answer");

            if (!message) {
                answer.textContent = "مهرباني وکړئ سوال ولیکئ.";
                return;
            }

            answer.textContent = "⏳ فکر کوي...";

            try {

                const response = await fetch(
                    "/api/chat",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            message: message
                        })
                    }
                );

                const data = await response.json();

                if (!response.ok) {
                    answer.textContent =
                        "خطا: " +
                        (data.error || "Unknown error");
                    return;
                }

                answer.textContent =
                    data.answer || "ځواب نشته.";

            } catch (error) {

                answer.textContent =
                    "Connection error: " +
                    error.message;
            }
        }

        </script>

    </body>
    </html>
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

        message = data.get("message", "")

        if not isinstance(message, str):
            message = ""

        message = message.strip()

        if not message:
            return jsonify({
                "error": "مهرباني وکړئ سوال ولیکئ."
            }), 400

        if not API_KEY:
            return jsonify({
                "error": "GEMINI_API_KEY په Vercel کې پیدا نه شو."
            }), 500

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                "You are MedAI, a helpful AI assistant. "
                                "Answer in the same language as the user. "
                                "If the user writes Pashto, answer in Pashto. "
                                "If the user writes Dari, answer in Dari. "
                                "If the user writes English, answer in English. "
                                "For medical questions, provide general "
                                "educational information and recommend a "
                                "qualified healthcare professional when "
                                "appropriate.\n\n"
                                "User question:\n"
                                + message
                            )
                        }
                    ]
                }
            ]
        }

        response = requests.post(
            GEMINI_URL,
            params={
                "key": API_KEY
            },
            headers={
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=45
        )

        print(
            "Gemini status:",
            response.status_code
        )

        if response.status_code != 200:

            return jsonify({
                "error": "Gemini API خطا ورکړ.",
                "status": response.status_code,
                "details": response.text[:2000]
            }), 502

        result = response.json()

        candidates = result.get(
            "candidates",
            []
        )

        if not candidates:

            return jsonify({
                "error": "Gemini هېڅ ځواب ورنه کړ.",
                "details": result
            }), 502

        content = candidates[0].get(
            "content",
            {}
        )

        parts = content.get(
            "parts",
            []
        )

        answer_parts = []

        for part in parts:

            text = part.get("text")

            if text:
                answer_parts.append(text)

        answer = "\n".join(
            answer_parts
        ).strip()

        if not answer:

            return jsonify({
                "error": "Gemini خالي ځواب ورکړ."
            }), 502

        return jsonify({
            "answer": answer
        })

    except requests.exceptions.Timeout:

        return jsonify({
            "error": "Gemini ته د غوښتنې وخت ختم شو. بیا هڅه وکړئ."
        }), 504

    except requests.exceptions.RequestException as error:

        print(
            "Request error:",
            repr(error)
        )

        return jsonify({
            "error": "Gemini سره اتصال ونه شو."
        }), 502

    except Exception as error:

        print(
            "Server error:",
            repr(error)
        )

        return jsonify({
            "error": str(error)
        }), 500


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=False
    )

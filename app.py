from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>MedAI</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 30px auto;
                padding: 20px;
                background: #f5f7fa;
            }
            h1 { text-align: center; }
            p { text-align: center; }
            textarea {
                width: 100%;
                height: 100px;
                padding: 14px;
                box-sizing: border-box;
                border: 1px solid #ccc;
                border-radius: 10px;
                font-size: 16px;
            }
            button {
                margin-top: 10px;
                padding: 14px 25px;
                border: 0;
                border-radius: 10px;
                cursor: pointer;
                font-size: 16px;
            }
            #answer {
                background: white;
                padding: 20px;
                border-radius: 12px;
                margin-top: 20px;
                white-space: pre-wrap;
                line-height: 1.8;
            }
        </style>
    </head>

    <body>
        <h1>🩺 MedAI</h1>
        <p>ستاسو د طبي زده کړو هوښیار مرستیال</p>

        <textarea id="msg" placeholder="مثلاً: Bacteria څه شی دی؟"></textarea>
        <button onclick="send()">پوښتنه</button>

        <div id="answer"></div>

        <script>
        async function send() {
            const msg = document.getElementById("msg").value.trim();
            const answer = document.getElementById("answer");

            if (!msg) {
                answer.innerText = "مهرباني وکړئ خپله پوښتنه ولیکئ.";
                return;
            }

            answer.innerText = "⏳ ځواب چمتو کېږي...";

            try {
                const r = await fetch("/chat", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({message: msg})
                });

                const d = await r.json();
                answer.innerText = d.answer || d.error || "ستونزه رامنځته شوه.";
            } catch (e) {
                answer.innerText = "❌ د سرور سره د اړیکې ستونزه رامنځته شوه.";
            }
        }
        </script>
    </body>
    </html>
    """

@app.route("/chat", methods=["POST"])
def chat():
    message = request.json.get("message", "").strip()

    if not message:
        return jsonify({"error": "پوښتنه ولیکئ."}), 400

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return jsonify({"error": "GEMINI_API_KEY پیدا نه شو."}), 500

    prompt = f"""
You are MedAI, an educational medical information assistant.

Answer the user's medical question clearly and safely.

Support Pashto, Dari, and English. Reply in the user's language.

For medical questions, use useful headings when appropriate:
Definition
Causes
Types
Risk factors
Signs and symptoms
Diagnosis
Treatment
Prevention
Complications
Important points

Do not diagnose a person from symptoms alone.
Do not claim to replace a doctor or emergency medical care.
Do not invent medical facts.
For urgent symptoms, advise appropriate medical care.

User question:
{message}
"""

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-2.5-flash-lite:generateContent?key=" + api_key
    )

    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ]
            },
            timeout=60
        )

        data = response.json()

        if response.status_code != 200:
            return jsonify({
                "error": "Gemini API خطا ورکړه: " + str(data)
            }), 500

        answer = data["candidates"][0]["content"]["parts"][0]["text"]

        return jsonify({"answer": answer})

    except Exception as e:
        return jsonify({
            "error": "د AI سره د اړیکې ستونزه: " + str(e)
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
)

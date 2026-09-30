from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)


@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html lang="ps" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MedAI</title>

        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f5f7fa;
                margin: 0;
                padding: 20px;
            }

            .container {
                max-width: 850px;
                margin: auto;
            }

            h1 {
                text-align: center;
                color: #1677ff;
                margin-bottom: 5px;
            }

            .subtitle {
                text-align: center;
                color: #555;
                margin-bottom: 25px;
            }

            textarea {
                width: 100%;
                height: 130px;
                padding: 15px;
                box-sizing: border-box;
                border: 1px solid #ccc;
                border-radius: 12px;
                font-size: 17px;
                resize: vertical;
                direction: auto;
            }

            button {
                width: 100%;
                margin-top: 12px;
                padding: 15px;
                background: #1677ff;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 18px;
                cursor: pointer;
            }

            button:hover {
                background: #0f5dcc;
            }

            #answer {
                background: white;
                margin-top: 20px;
                padding: 22px;
                border-radius: 12px;
                line-height: 2;
                white-space: pre-wrap;
                direction: auto;
                min-height: 50px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }

            .warning {
                margin-top: 20px;
                padding: 15px;
                background: #fff4d6;
                border-radius: 10px;
                color: #6b5200;
                line-height: 1.8;
            }
        </style>
    </head>

    <body>
        <div class="container">

            <h1>🩺 MedAI</h1>

            <div class="subtitle">
                ستاسو د طبي زده کړو هوښیار مرستیال
            </div>

            <textarea
                id="msg"
                placeholder="مثلاً: Bacteria څه شی دی؟">
            </textarea>

            <button onclick="sendQuestion()">
                پوښتنه
            </button>

            <div id="answer">
                ستاسو ځواب به دلته ښکاره شي.
            </div>

            <div class="warning">
                ⚠️ MedAI د طبي زده کړو او معلوماتو لپاره دی.
                دا د ډاکټر بدیل نه دی. د جدي یا بیړنیو نښو په صورت کې
                له روغتیايي مسلکي کس سره اړیکه ونیسئ.
            </div>

        </div>


        <script>
        async function sendQuestion() {

            const message =
                document.getElementById("msg").value.trim();

            const answer =
                document.getElementById("answer");

            if (!message) {
                answer.innerText =
                    "مهرباني وکړئ خپله طبي پوښتنه ولیکئ.";
                return;
            }

            answer.innerText =
                "⏳ مهرباني وکړئ، ځواب چمتو کېږي...";

            try {

                const response = await fetch("/chat", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        message: message
                    })
                });

                const data = await response.json();

                if (data.answer) {
                    answer.innerText = data.answer;
                } else {
                    answer.innerText =
                        data.error || "یوه ستونزه رامنځته شوه.";
                }

            } catch (error) {

                answer.innerText =
                    "❌ د سرور سره د اړیکې ستونزه رامنځته شوه.";
            }
        }
        </script>

    </body>
    </html>
    """


@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json(silent=True) or {}

    message = data.get("message", "").strip()

    if not message:
        return jsonify({
            "error": "مهرباني وکړئ پوښتنه ولیکئ."
        }), 400

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return jsonify({
            "error": "GEMINI_API_KEY پیدا نه شو."
        }), 500


    prompt = f"""
You are MedAI, an educational medical information assistant.

Your job is to provide clear, accurate, educational medical information.

IMPORTANT RULES:

1. Support Pashto, Dari, and English.
2. Always answer in the same language as the user's question.
3. Use simple language that students can understand.
4. Do not diagnose a person from symptoms alone.
5. Do not pretend to be a doctor.
6. Do not claim that the answer replaces medical care.
7. Do not invent medical facts.
8. For emergency symptoms, advise the user to seek urgent medical care.
9. Be careful with medicines. Do not give personalized prescription or dosage instructions as if the patient has been examined.

For general medical topics, organize the answer with useful headings when appropriate:

Definition
Causes
Types
Risk Factors
Signs and Symptoms
Diagnosis
Treatment
Prevention
Complications
Important Points

If some headings are not relevant, do not force them.

User question:
{message}
"""


    # Gemini API
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-3.5-flash-lite:generateContent?key="
        + api_key
    )


    try:

        response = requests.post(
            url,
            headers={
                "Content-Type": "application/json"
            },
            json={
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            },
            timeout=60
        )


        data = response.json()


        if response.status_code != 200:

            return jsonify({
                "error": "Gemini API خطا ورکړه: "
                + str(data)
            }), 500


        candidates = data.get("candidates", [])

        if not candidates:

            return jsonify({
                "error": "Gemini هېڅ ځواب رانه کړ."
            }), 500


        content = candidates[0].get("content", {})

        parts = content.get("parts", [])

        if not parts:

            return jsonify({
                "error": "د Gemini ځواب خالي دی."
            }), 500


        answer = parts[0].get("text", "")


        if not answer:

            return jsonify({
                "error": "AI ځواب پیدا نه شو."
            }), 500


        return jsonify({
            "answer": answer
        })


    except requests.exceptions.Timeout:

        return jsonify({
            "error": "د AI ځواب ډېر وخت ونیو. بیا هڅه وکړئ."
        }), 504


    except Exception as e:

        return jsonify({
            "error": "د AI سره د اړیکې ستونزه: "
            + str(e)
        }), 500


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )

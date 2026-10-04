import os
import requests

from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MedAI</title>
</head>
<body>

<h1>🩺 MedAI</h1>

<textarea id="message" rows="5" cols="50"
placeholder="پیغام ولیکئ..."></textarea>

<br><br>

<button onclick="sendMessage()">Send</button>

<pre id="answer"></pre>

<script>
async function sendMessage() {

    const message =
        document.getElementById("message").value;

    const answer =
        document.getElementById("answer");

    answer.textContent = "MedAI is thinking...";

    try {

        const response = await fetch("/api/chat", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: message
            })
        });

        const data = await response.json();

        if (!response.ok) {
            answer.textContent =
                JSON.stringify(data, null, 2);
            return;
        }

        answer.textContent =
            data.answer;

    } catch (error) {

        answer.textContent =
            "Connection error: " + error;
    }
}
</script>

</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/health")
def health():
    return jsonify({
        "service": "MedAI",
        "status": "ok"
    })


@app.route("/api/chat", methods=["POST"])
def chat():

    if not GEMINI_API_KEY:
        return jsonify({
            "error": "GEMINI_API_KEY is missing."
        }), 500

    data = request.get_json(silent=True) or {}

    message = str(
        data.get("message", "")
    ).strip()

    if not message:
        return jsonify({
            "error": "Message is required."
        }), 400

    url = (
        "https://generativelanguage.googleapis.com"
        "/v1beta/interactions"
    )

    payload = {
        "model": "gemini-3.8-flash",
        "input": message
    }

    try:

        response = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY
            },
            json=payload,
            timeout=90
        )

        try:
            result = response.json()
        except Exception:
            result = {
                "raw": response.text
            }

        if response.status_code != 200:

            return jsonify({
                "error": "Gemini API error",
                "status_code": response.status_code,
                "details": result
            }), 502

        answer = result.get(
            "output_text",
            ""
        )

        if not answer:

            parts = []

            for step in result.get(
                "steps",
                []
            ):

                if step.get(
                    "type"
                ) != "model_output":
                    continue

                for item in step.get(
                    "content",
                    []
                ):

                    if item.get(
                        "type"
                    ) == "text":

                        text = item.get(
                            "text",
                            ""
                        )

                        if text:
                            parts.append(text)

            answer = "\n".join(parts)

        if not answer:

            return jsonify({
                "error": "Gemini returned no text.",
                "details": result
            }), 502

        return jsonify({
            "answer": answer
        })

    except Exception as e:

        return jsonify({
            "error": "Server error",
            "details": str(e)
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        )
    )

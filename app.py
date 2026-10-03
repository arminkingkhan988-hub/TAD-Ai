from flask import Flask, request, jsonify, render_template_string
import os
import json
import urllib.request
import urllib.error

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = "gemini-3.8-flash"

GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)


HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MedAI Test</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f5f7fb;
        }

        .container {
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
        }

        .header {
            background: white;
            padding: 25px;
            border-radius: 18px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.08);
            margin-bottom: 20px;
        }

        .header h1 {
            margin: 0 0 8px;
            color: #1677ff;
        }

        .chat {
            background: white;
            min-height: 400px;
            padding: 20px;
            border-radius: 18px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        }

        .message {
            padding: 14px 16px;
            margin: 12px 0;
            border-radius: 14px;
            line-height: 1.6;
            white-space: pre-wrap;
        }

        .user {
            background: #e8f1ff;
            margin-left: 20%;
        }

        .ai {
            background: #f0f2f5;
            margin-right: 10%;
        }

        .input-area {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }

        input {
            flex: 1;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 12px;
            font-size: 16px;
        }

        button {
            border: none;
            background: #1677ff;
            color: white;
            padding: 15px 22px;
            border-radius: 12px;
            cursor: pointer;
            font-size: 16px;
        }

        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .status {
            margin-top: 12px;
            color: #666;
            font-size: 14px;
        }
    </style>
</head>

<body>

<div class="container">

    <div class="header">
        <h1>🩺 MedAI</h1>
        <p>Gemini API Test Chat</p>
    </div>

    <div class="chat" id="chat">

        <div class="message ai">
            سلام! زه MedAI یم. یو پیغام راولېږه.
        </div>

    </div>

    <div class="input-area">

        <input
            id="message"
            type="text"
            placeholder="Type your message..."
            onkeydown="handleKey(event)"
        >

        <button id="sendButton" onclick="sendMessage()">
            Send
        </button>

    </div>

    <div class="status" id="status"></div>

</div>


<script>

function handleKey(event) {

    if (event.key === "Enter") {
        sendMessage();
    }

}


function addMessage(text, type) {

    const chat = document.getElementById("chat");

    const div = document.createElement("div");

    div.className = "message " + type;

    div.textContent = text;

    chat.appendChild(div);

    chat.scrollTop = chat.scrollHeight;
}


async function sendMessage() {

    const input = document.getElementById("message");
    const button = document.getElementById("sendButton");
    const status = document.getElementById("status");

    const message = input.value.trim();

    if (!message) {
        return;
    }

    addMessage(message, "user");

    input.value = "";

    button.disabled = true;

    status.textContent = "MedAI is thinking...";

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

            throw new Error(
                data.error || "API request failed"
            );

        }


        addMessage(
            data.reply || "No response received.",
            "ai"
        );


        status.textContent = "Ready";


    } catch (error) {

        addMessage(
            "Error: " + error.message,
            "ai"
        );

        status.textContent = "Error";

    }


    button.disabled = false;

    input.focus();

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
        "status": "ok"
    })


@app.route("/api/chat", methods=["POST"])
def chat():

    if not GEMINI_API_KEY:
        return jsonify({
            "error": "GEMINI_API_KEY is not configured in Vercel."
        }), 500


    data = request.get_json(silent=True) or {}

    message = str(
        data.get("message", "")
    ).strip()


    if not message:
        return jsonify({
            "error": "Message is required."
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

        with urllib.request.urlopen(
            req,
            timeout=30
        ) as response:

            result = json.loads(
                response.read().decode("utf-8")
            )


        candidates = result.get(
            "candidates",
            []
        )


        if not candidates:

            return jsonify({
                "error": "Gemini returned no candidates.",
                "details": result
            }), 502


        parts = candidates[0].get(
            "content",
            {}
        ).get(
            "parts",
            []
        )


        text = "".join(
            part.get("text", "")
            for part in parts
        ).strip()


        if not text:

            return jsonify({
                "error": "Gemini returned an empty response."
            }), 502


        return jsonify({
            "reply": text
        })


    except urllib.error.HTTPError as e:

        error_body = e.read().decode(
            "utf-8",
            errors="ignore"
        )

        return jsonify({
            "error": f"Gemini API error: HTTP {e.code}",
            "details": error_body
        }), e.code


    except urllib.error.URLError as e:

        return jsonify({
            "error": "Could not connect to Gemini.",
            "details": str(e)
        }), 502


    except Exception as e:

        return jsonify({
            "error": "Server error.",
            "details": str(e)
        }), 500


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                "5000"
            )
        ),
        debug=False
    )

import os
import requests

from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.8-flash"

SYSTEM_PROMPT = """
You are MedAI, a helpful AI assistant.

Answer general questions, medical questions, education,
science, coding, mathematics, history, business and technology.

Support Pashto, Dari and English.

Always answer in the same language as the user.

For medical questions:
- Give general educational information.
- Do not claim to diagnose the user.
- For serious or emergency symptoms, recommend professional medical care.
"""

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MedAI</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f5f7fb;
            color: #111827;
        }

        header {
            height: 64px;
            background: white;
            border-bottom: 1px solid #ddd;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
        }

        .logo {
            font-size: 22px;
            font-weight: bold;
            color: #2563eb;
        }

        button {
            border: 0;
            border-radius: 10px;
            padding: 10px 14px;
            cursor: pointer;
        }

        .new-chat {
            background: #fee2e2;
            color: #b91c1c;
        }

        .chat {
            max-width: 900px;
            margin: auto;
            padding: 30px 15px 130px;
        }

        .welcome {
            text-align: center;
            margin-top: 15vh;
        }

        .welcome h1 {
            font-size: 38px;
        }

        .welcome p {
            color: #6b7280;
        }

        .message {
            display: flex;
            margin: 18px 0;
        }

        .user {
            justify-content: flex-end;
        }

        .bubble {
            max-width: 80%;
            padding: 14px 16px;
            border-radius: 16px;
            line-height: 1.6;
            white-space: pre-wrap;
        }

        .user .bubble {
            background: #2563eb;
            color: white;
        }

        .assistant .bubble {
            background: white;
            border: 1px solid #ddd;
        }

        .composer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            border-top: 1px solid #ddd;
            padding: 12px;
        }

        .composer-inner {
            max-width: 900px;
            margin: auto;
            display: flex;
            gap: 10px;
        }

        textarea {
            flex: 1;
            resize: none;
            min-height: 52px;
            border: 1px solid #ccc;
            border-radius: 14px;
            padding: 14px;
            font-size: 15px;
        }

        .send {
            background: #2563eb;
            color: white;
            min-width: 70px;
        }

        .thinking {
            color: #777;
            font-style: italic;
        }

        body.dark {
            background: #111827;
            color: white;
        }

        body.dark header,
        body.dark .composer,
        body.dark .assistant .bubble {
            background: #1f2937;
            color: white;
            border-color: #374151;
        }

        @media (max-width: 600px) {
            .bubble {
                max-width: 90%;
            }

            .welcome h1 {
                font-size: 30px;
            }
        }
    </style>
</head>

<body>

<header>
    <div class="logo">🩺 MedAI</div>

    <div>
        <button onclick="toggleDark()">🌙</button>
        <button class="new-chat" onclick="newChat()">New Chat</button>
    </div>
</header>

<div class="chat" id="chat">

    <div class="welcome" id="welcome">
        <h1>How can I help you?</h1>
        <p>
            Ask me anything — Medical, Science, Coding,
            Education and more.
        </p>
    </div>

</div>

<div class="composer">

    <div class="composer-inner">

        <textarea
            id="message"
            placeholder="Message MedAI..."
            onkeydown="handleKey(event)"
        ></textarea>

        <button
            class="send"
            id="sendButton"
            onclick="sendMessage()"
        >
            Send
        </button>

    </div>

</div>

<script>

let conversation = [];

function addMessage(role, text) {

    const chat = document.getElementById("chat");

    const message = document.createElement("div");
    message.className = "message " + role;

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    bubble.textContent = text;

    message.appendChild(bubble);
    chat.appendChild(message);

    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: "smooth"
    });
}


function showThinking() {

    const chat = document.getElementById("chat");

    const message = document.createElement("div");

    message.className = "message assistant";
    message.id = "thinking";

    const bubble = document.createElement("div");

    bubble.className = "bubble thinking";
    bubble.textContent = "MedAI is thinking...";

    message.appendChild(bubble);
    chat.appendChild(message);
}


function removeThinking() {

    const thinking = document.getElementById("thinking");

    if (thinking) {
        thinking.remove();
    }
}


async function sendMessage() {

    const input = document.getElementById("message");
    const button = document.getElementById("sendButton");

    const message = input.value.trim();

    if (!message) {
        return;
    }

    input.value = "";
    button.disabled = true;

    const welcome = document.getElementById("welcome");

    if (welcome) {
        welcome.remove();
    }

    addMessage("user", message);

    conversation.push({
        role: "user",
        content: message
    });

    showThinking();

    try {

        const response = await fetch("/api/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: message,
                history: conversation.slice(-10)
            })

        });

        const data = await response.json();

        removeThinking();

        if (!response.ok) {

            addMessage(
                "assistant",
                "Error: " +
                (data.error || "Unknown error")
            );

            console.log(data);

            return;
        }

        const answer =
            data.answer ||
            "No answer received.";

        addMessage(
            "assistant",
            answer
        );

        conversation.push({
            role: "assistant",
            content: answer
        });

    } catch (error) {

        removeThinking();

        addMessage(
            "assistant",
            "Connection error. Please try again."
        );

        console.error(error);

    } finally {

        button.disabled = false;
        input.focus();
    }
}


function handleKey(event) {

    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {

        event.preventDefault();

        sendMessage();
    }
}


function newChat() {

    conversation = [];

    document.getElementById("chat").innerHTML = `
        <div class="welcome" id="welcome">
            <h1>How can I help you?</h1>
            <p>
                Ask me anything — Medical, Science,
                Coding, Education and more.
            </p>
        </div>
    `;
}


function toggleDark() {

    document.body.classList.toggle("dark");

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
            "error": "GEMINI_API_KEY is missing in Vercel."
        }), 500

    data = request.get_json(silent=True) or {}

    message = str(
        data.get("message", "")
    ).strip()

    history = data.get("history", [])

    if not message:
        return jsonify({
            "error": "Message is required."
        }), 400

    conversation_text = ""

    if isinstance(history, list):

        for item in history[-10:]:

            if not isinstance(item, dict):
                continue

            role = str(
                item.get("role", "user")
            )

            content = str(
                item.get("content", "")
            ).strip()

            if content:

                conversation_text += (
                    f"\n{role.upper()}: {content}"
                )

    prompt = (
        SYSTEM_PROMPT
        + "\n\nConversation history:"
        + conversation_text
        + "\n\nCurrent user question:"
        + message
    )

    url = (
        "https://generativelanguage.googleapis.com"
        "/v1beta/interactions"
    )

    payload = {
        "model": GEMINI_MODEL,
        "input": prompt
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
                "raw_response": response.text
            }

        if response.status_code != 200:
    return jsonify({
        "error": "Gemini API error",
        "status_code": response.status_code,
        "details": result,
        "raw_response": response.text
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

            answer = "\n".join(
                parts
            ).strip()

        if not answer:

            return jsonify({

                "error":
                    "Gemini returned no text.",

                "details":
                    result

            }), 502

        return jsonify({
            "answer": answer
        })

    except requests.Timeout:

        return jsonify({
            "error":
                "Gemini request timed out."
        }), 504

    except requests.RequestException as e:

        return jsonify({

            "error":
                "Could not connect to Gemini.",

            "details":
                str(e)

        }), 502

    except Exception as e:

        return jsonify({

            "error":
                "Unexpected server error.",

            "details":
                str(e)

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

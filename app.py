import os
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "openai/gpt-oss-20b"

SYSTEM_PROMPT = """
You are MedAI, a helpful AI assistant.

Rules:
- Answer in the same language as the user.
- Support Pashto, Dari, and English.
- You can answer general questions about education, science, coding,
  mathematics, technology, history, business, writing, and medicine.
- For medical questions, provide general educational information only.
- Do not pretend to be a doctor.
- For emergencies, advise the user to contact local emergency medical services
  or a qualified healthcare professional.
- Be clear, friendly, accurate, and concise.
"""

HTML = """
<!DOCTYPE html>
<html lang="en">
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

.app {
    max-width: 900px;
    margin: auto;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

.header {
    padding: 18px;
    background: #111827;
    color: white;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header h1 {
    margin: 0;
    font-size: 22px;
}

button {
    border: 0;
    border-radius: 10px;
    padding: 10px 14px;
    cursor: pointer;
}

.new-chat {
    background: white;
    color: #111827;
}

.chat {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
}

.message {
    margin: 12px 0;
    padding: 13px 15px;
    border-radius: 14px;
    max-width: 85%;
    white-space: pre-wrap;
    line-height: 1.6;
}

.user {
    background: #2563eb;
    color: white;
    margin-left: auto;
}

.ai {
    background: white;
    border: 1px solid #e5e7eb;
}

.input-area {
    padding: 15px;
    background: white;
    border-top: 1px solid #ddd;
    display: flex;
    gap: 10px;
}

textarea {
    flex: 1;
    resize: none;
    min-height: 50px;
    max-height: 150px;
    padding: 13px;
    border: 1px solid #d1d5db;
    border-radius: 12px;
    font-size: 16px;
}

.send {
    background: #2563eb;
    color: white;
    min-width: 80px;
}

.loading {
    opacity: 0.6;
}

@media (max-width: 600px) {
    .message {
        max-width: 95%;
    }

    .input-area {
        padding: 10px;
    }
}
</style>
</head>

<body>

<div class="app">

    <div class="header">
        <h1>🤖 MedAI</h1>
        <button class="new-chat" onclick="newChat()">New Chat</button>
    </div>

    <div id="chat" class="chat">
        <div class="message ai">
            👋 سلام! زه MedAI یم. څه مرسته درسره وکړم؟
        </div>
    </div>

    <div class="input-area">
        <textarea
            id="message"
            placeholder="Type your message..."
            onkeydown="handleKey(event)"
        ></textarea>

        <button class="send" onclick="sendMessage()">
            Send
        </button>
    </div>

</div>

<script>

let messages = [];

function addMessage(text, type) {
    const chat = document.getElementById("chat");

    const div = document.createElement("div");
    div.className = "message " + type;
    div.textContent = text;

    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;

    return div;
}

async function sendMessage() {

    const input = document.getElementById("message");
    const text = input.value.trim();

    if (!text) return;

    addMessage(text, "user");

    messages.push({
        role: "user",
        content: text
    });

    input.value = "";

    const loading = addMessage("⏳ Thinking...", "ai");
    loading.classList.add("loading");

    try {

        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                messages: messages
            })
        });

        const data = await response.json();

        loading.remove();

        if (!response.ok) {
            addMessage(
                "❌ " + (data.error || "Something went wrong."),
                "ai"
            );
            return;
        }

        const answer = data.answer || "No answer received.";

        addMessage(answer, "ai");

        messages.push({
            role: "assistant",
            content: answer
        });

    } catch (error) {

        loading.remove();

        addMessage(
            "❌ Connection error. Please try again.",
            "ai"
        );
    }
}

function handleKey(event) {

    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function newChat() {

    messages = [];

    document.getElementById("chat").innerHTML = `
        <div class="message ai">
            👋 سلام! زه MedAI یم. نوی چټ پیل شو. څه مرسته درسره وکړم؟
        </div>
    `;
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


@app.route("/chat", methods=["POST"])
def chat():

    if not GROQ_API_KEY:
        return jsonify({
            "error": "GROQ_API_KEY is not configured in Vercel."
        }), 500

    data = request.get_json(silent=True) or {}

    user_messages = data.get("messages", [])

    if not user_messages:
        return jsonify({
            "error": "No message provided."
        }), 400

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    for msg in user_messages[-20:]:

        role = msg.get("role")
        content = msg.get("content")

        if role in ["user", "assistant"] and content:
            messages.append({
                "role": role,
                "content": str(content)
            })

    try:

        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1200
            },
            timeout=55
        )

        if response.status_code == 429:
            return jsonify({
                "error": "Groq rate limit reached. Please try again later."
            }), 429

        if response.status_code in [401, 403]:
            return jsonify({
                "error": "Groq API key is invalid or not authorized."
            }), response.status_code

        if response.status_code >= 400:
            try:
                details = response.json()
            except Exception:
                details = response.text

            return jsonify({
                "error": "Groq API error",
                "details": details
            }), response.status_code

        result = response.json()

        answer = (
            result.get("choices", [{}])[0]
            .get("message", {})
            .get("content")
        )

        if not answer:
            return jsonify({
                "error": "No answer returned by Groq."
            }), 500

        return jsonify({
            "answer": answer
        })

    except requests.exceptions.Timeout:

        return jsonify({
            "error": "Groq request timed out. Please try again."
        }), 504

    except Exception as e:

        return jsonify({
            "error": "Server error",
            "details": str(e)
        }), 500


if __name__ == "__main__":
    app.run()

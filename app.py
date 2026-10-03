import os
import requests

from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.8-flash"

SYSTEM_PROMPT = """
You are MedAI, a helpful AI assistant.

You can answer general questions, not only medical questions.

Supported languages:
- Pashto
- Dari
- English

Always answer in the same language as the user's question unless the
user asks for another language.

You can help with:
- General knowledge
- Education
- Science
- Mathematics
- Programming and coding
- Writing and translation
- History
- Business
- Technology
- Everyday questions
- Medical information

Medical safety:
- Give general educational information, not a diagnosis.
- Do not claim certainty about a medical condition.
- Encourage the user to contact a qualified healthcare professional when
  symptoms may be serious.
- For emergencies, advise seeking emergency medical care immediately.

Be clear, helpful, respectful, and concise.
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
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        header {
            height: 64px;
            background: #ffffff;
            border-bottom: 1px solid #e5e7eb;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
            position: sticky;
            top: 0;
            z-index: 10;
        }

        .logo {
            font-size: 21px;
            font-weight: 700;
            color: #2563eb;
        }

        .header-buttons {
            display: flex;
            gap: 8px;
        }

        button {
            border: none;
            cursor: pointer;
            border-radius: 10px;
            padding: 10px 14px;
            font-size: 14px;
        }

        .secondary {
            background: #eef2ff;
            color: #1e40af;
        }

        .danger {
            background: #fee2e2;
            color: #b91c1c;
        }

        .chat {
            flex: 1;
            width: 100%;
            max-width: 900px;
            margin: 0 auto;
            padding: 25px 18px 130px;
        }

        .welcome {
            text-align: center;
            margin-top: 12vh;
        }

        .welcome h1 {
            font-size: 38px;
            margin-bottom: 10px;
        }

        .welcome p {
            color: #6b7280;
            font-size: 16px;
        }

        .message {
            display: flex;
            margin: 18px 0;
        }

        .message.user {
            justify-content: flex-end;
        }

        .bubble {
            max-width: 80%;
            padding: 13px 16px;
            border-radius: 16px;
            line-height: 1.6;
            white-space: pre-wrap;
        }

        .user .bubble {
            background: #2563eb;
            color: white;
            border-bottom-right-radius: 5px;
        }

        .assistant .bubble {
            background: white;
            border: 1px solid #e5e7eb;
            border-bottom-left-radius: 5px;
        }

        .actions {
            margin-top: 8px;
        }

        .copy {
            background: transparent;
            color: #6b7280;
            padding: 4px 8px;
            font-size: 12px;
        }

        .composer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(255,255,255,.96);
            border-top: 1px solid #e5e7eb;
            padding: 14px;
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
            min-height: 50px;
            max-height: 150px;
            border: 1px solid #d1d5db;
            border-radius: 14px;
            padding: 14px;
            font-size: 15px;
            outline: none;
            font-family: inherit;
        }

        textarea:focus {
            border-color: #2563eb;
        }

        .send {
            background: #2563eb;
            color: white;
            min-width: 75px;
        }

        .send:disabled {
            opacity: .5;
            cursor: not-allowed;
        }

        .thinking {
            color: #6b7280;
            font-style: italic;
        }

        .error {
            color: #b91c1c;
        }

        .quick-prompts {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            justify-content: center;
            margin-top: 25px;
        }

        .prompt {
            background: white;
            border: 1px solid #e5e7eb;
            color: #374151;
        }

        body.dark {
            background: #111827;
            color: #f9fafb;
        }

        body.dark header,
        body.dark .composer {
            background: #1f2937;
            border-color: #374151;
        }

        body.dark .assistant .bubble,
        body.dark textarea,
        body.dark .prompt {
            background: #1f2937;
            color: #f9fafb;
            border-color: #374151;
        }

        body.dark .welcome p {
            color: #9ca3af;
        }

        @media (max-width: 600px) {
            header {
                padding: 0 12px;
            }

            .welcome h1 {
                font-size: 30px;
            }

            .bubble {
                max-width: 90%;
            }

            .chat {
                padding-left: 10px;
                padding-right: 10px;
            }

            .composer-inner {
                gap: 6px;
            }

            .send {
                min-width: 60px;
            }
        }
    </style>
</head>

<body>
<div class="app">

    <header>
        <div class="logo">🩺 MedAI</div>

        <div class="header-buttons">
            <button class="secondary" onclick="toggleDark()">
                🌙
            </button>

            <button class="danger" onclick="newChat()">
                New Chat
            </button>
        </div>
    </header>

    <main class="chat" id="chat">

        <div class="welcome" id="welcome">
            <h1>How can I help you?</h1>
            <p>
                Ask anything — medical, education, science, coding,
                mathematics, or general questions.
            </p>

            <div class="quick-prompts">
                <button class="prompt"
                    onclick="usePrompt('Explain artificial intelligence simply.')">
                    🤖 AI
                </button>

                <button class="prompt"
                    onclick="usePrompt('What are common causes of headache?')">
                    🩺 Medical
                </button>

                <button class="prompt"
                    onclick="usePrompt('Explain photosynthesis.')">
                    🔬 Science
                </button>

                <button class="prompt"
                    onclick="usePrompt('Help me write Python code.')">
                    💻 Coding
                </button>
            </div>
        </div>

    </main>

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

</div>

<script>
let conversation = [];

function addMessage(role, text) {
    const chat = document.getElementById("chat");
    const welcome = document.getElementById("welcome");

    if (welcome) {
        welcome.remove();
    }

    const wrapper = document.createElement("div");
    wrapper.className = "message " + role;

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    bubble.textContent = text;

    wrapper.appendChild(bubble);

    if (role === "assistant") {
        const actions = document.createElement("div");
        actions.className = "actions";

        const copy = document.createElement("button");
        copy.className = "copy";
        copy.textContent = "📋 Copy";

        copy.onclick = function() {
            navigator.clipboard.writeText(text);
            copy.textContent = "✓ Copied";
        };

        actions.appendChild(copy);
        bubble.appendChild(actions);
    }

    chat.appendChild(wrapper);

    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: "smooth"
    });
}

function showThinking() {
    const chat = document.getElementById("chat");

    const wrapper = document.createElement("div");
    wrapper.className = "message assistant";
    wrapper.id = "thinking";

    const bubble = document.createElement("div");
    bubble.className = "bubble thinking";
    bubble.textContent = "MedAI is thinking...";

    wrapper.appendChild(bubble);
    chat.appendChild(wrapper);

    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: "smooth"
    });
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
                history: conversation.slice(-12)
            })
        });

        const data = await response.json();

        removeThinking();

        if (!response.ok) {
            addMessage(
                "assistant",
                "Error: " + (data.error || "Something went wrong.")
            );
            return;
        }

        const answer = data.answer || "No answer received.";

        addMessage("assistant", answer);

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
    } finally {
        button.disabled = false;
        input.focus();
    }
}

function handleKey(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function usePrompt(text) {
    const input = document.getElementById("message");
    input.value = text;
    input.focus();
}

function newChat() {
    conversation = [];

    const chat = document.getElementById("chat");

    chat.innerHTML = `
        <div class="welcome" id="welcome">
            <h1>How can I help you?</h1>
            <p>
                Ask anything — medical, education, science, coding,
                mathematics, or general questions.
            </p>
        </div>
    `;
}

function toggleDark() {
    document.body.classList.toggle("dark");

    localStorage.setItem(
        "medai_dark",
        document.body.classList.contains("dark")
    );
}

if (localStorage.getItem("medai_dark") === "true") {
    document.body.classList.add("dark");
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
            "error": "GEMINI_API_KEY is not configured on the server."
        }), 500

    data = request.get_json(silent=True) or {}

    message = str(data.get("message", "")).strip()
    history = data.get("history", [])

    if not message:
        return jsonify({
            "error": "Message is required."
        }), 400

    if not isinstance(history, list):
        history = []

    conversation_text = ""

    for item in history[-12:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role", "user")
        content = str(item.get("content", "")).strip()

        if not content:
            continue

        conversation_text += (
            f"\n{role.upper()}: {content}\n"
        )

    prompt = (
        SYSTEM_PROMPT
        + "\n\nConversation history:"
        + conversation_text
        + "\n\nCurrent user question:\n"
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
        response = None

        for attempt in range(3):
            response = requests.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": GEMINI_API_KEY
                },
                json=payload,
                timeout=60
            )

            if response.status_code != 503:
                break

        if response is None:
            return jsonify({
                "error": "No response from Gemini."
            }), 502

        if response.status_code != 200:
            try:
                error_data = response.json()
            except Exception:
                error_data = {
                    "message": response.text[:500]
                }

            return jsonify({
                "error": "Gemini API error",
                "details": error_data
            }), response.status_code

        result = response.json()

        answer_parts = []

        for step in result.get("steps", []):
            if step.get("type") != "model_output":
                continue

            for item in step.get("content", []):
                if item.get("type") == "text":
                    text = item.get("text", "")

                    if text:
                        answer_parts.append(text)

        answer = "\n".join(answer_parts).strip()

        if not answer:
            answer = "I could not generate an answer. Please try again."

        return jsonify({
            "answer": answer
        })

    except requests.Timeout:
        return jsonify({
            "error": "Gemini request timed out. Please try again."
        }), 504

    except requests.RequestException as e:
        return jsonify({
            "error": "Could not connect to Gemini.",
            "details": str(e)
        }), 502

    except Exception as e:
        return jsonify({
            "error": "Unexpected server error.",
            "details": str(e)
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )

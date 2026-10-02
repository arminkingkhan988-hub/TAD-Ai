import os
import json
import urllib.request
import urllib.error

from flask import Flask, request, jsonify, render_template_string


# =========================================================
# FLASK APP
# IMPORTANT: Vercel must find this top-level "app" variable
# =========================================================

app = Flask(__name__)


# =========================================================
# CONFIG
# =========================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# Current Gemini model used by the official Gemini API examples.
GEMINI_MODEL = os.environ.get(
    "GEMINI_MODEL",
    "gemini-3.8-flash"
).strip()

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)


# =========================================================
# MEDICAL SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are MedAI, a careful AI medical information assistant.

Rules:

1. Give general medical information and education.
2. Do not claim to be a doctor.
3. Do not give a certain diagnosis.
4. Do not tell the user to stop or change prescription medicine
   without professional medical advice.
5. For serious or emergency symptoms, clearly recommend urgent
   medical attention.
6. If the user may have a life-threatening emergency such as:
   - severe chest pain
   - severe difficulty breathing
   - unconsciousness
   - seizure
   - severe bleeding
   - stroke-like symptoms
   - severe allergic reaction
   - poisoning
   recommend contacting local emergency services or going to
   the nearest emergency department immediately.
7. Explain medical terms in simple language.
8. Mention when seeing a doctor is appropriate.
9. If the user asks about medicine, explain common uses,
   common precautions, and important safety considerations,
   but avoid unsafe personalized prescribing.
10. Never pretend that an AI response replaces an examination,
    laboratory testing, or a licensed healthcare professional.
11. If the user writes in Pashto, answer in Pashto.
12. If the user writes in English, answer in English.
13. If the user writes in Dari/Persian, answer in Dari/Persian.
14. Keep answers useful and reasonably concise.
"""


# =========================================================
# GEMINI FUNCTION
# =========================================================

def ask_gemini(message, history=None):
    """
    Send user message + limited conversation history to Gemini.
    """

    if not GEMINI_API_KEY:
        return (
            "GEMINI_API_KEY is not configured. "
            "Please add GEMINI_API_KEY to your Vercel Environment Variables."
        )

    if history is None:
        history = []

    contents = []

    # Add previous conversation
    for item in history[-12:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role")
        text = item.get("text", "")

        if not text:
            continue

        if role == "user":
            contents.append({
                "role": "user",
                "parts": [
                    {"text": str(text)}
                ]
            })

        elif role in ("assistant", "model"):
            contents.append({
                "role": "model",
                "parts": [
                    {"text": str(text)}
                ]
            })

    # Current user message
    contents.append({
        "role": "user",
        "parts": [
            {
                "text": str(message)
            }
        ]
    })

    payload = {
        "system_instruction": {
            "parts": [
                {
                    "text": SYSTEM_PROMPT
                }
            ]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 1200
        }
    }

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        GEMINI_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read().decode("utf-8")
            result = json.loads(raw)

        candidates = result.get("candidates", [])

        if not candidates:
            return "Gemini did not return a response."

        candidate = candidates[0]

        content = candidate.get("content", {})
        parts = content.get("parts", [])

        texts = []

        for part in parts:
            if isinstance(part, dict) and part.get("text"):
                texts.append(part["text"])

        answer = "\n".join(texts).strip()

        if not answer:
            return "No text response was returned by Gemini."

        return answer

    except urllib.error.HTTPError as e:
        try:
            error_body = e.read().decode("utf-8")
        except Exception:
            error_body = ""

        print("Gemini HTTP Error:", e.code, error_body)

        if e.code == 400:
            return "Gemini API request was invalid. Please check the model name and API configuration."

        if e.code == 401 or e.code == 403:
            return "Gemini API key is invalid or does not have permission."

        if e.code == 404:
            return (
                f"Gemini model '{GEMINI_MODEL}' was not found. "
                "Check GEMINI_MODEL in Vercel Environment Variables."
            )

        if e.code == 429:
            return "Gemini API rate limit was reached. Please try again later."

        return f"Gemini API error: HTTP {e.code}"

    except urllib.error.URLError as e:
        print("Gemini URL Error:", e)
        return "Could not connect to Gemini API."

    except Exception as e:
        print("Gemini Error:", repr(e))
        return "An unexpected server error occurred."


# =========================================================
# HOME PAGE
# =========================================================

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>MedAI - Medical AI Assistant</title>

    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        :root {
            --bg: #f4f7fb;
            --card: #ffffff;
            --text: #172033;
            --muted: #6b7280;
            --primary: #1677ff;
            --primary-dark: #075ccc;
            --border: #e5e7eb;
            --user: #1677ff;
            --assistant: #eef4ff;
            --danger: #dc2626;
            --shadow: 0 15px 40px rgba(15, 23, 42, 0.10);
        }

        body.dark {
            --bg: #0f172a;
            --card: #111827;
            --text: #f3f4f6;
            --muted: #9ca3af;
            --primary: #3b82f6;
            --primary-dark: #60a5fa;
            --border: #263244;
            --assistant: #172554;
            --shadow: 0 15px 40px rgba(0, 0, 0, 0.35);
        }

        body {
            min-height: 100vh;
            background: var(--bg);
            color: var(--text);
            font-family:
                Inter,
                system-ui,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;
        }

        .app {
            max-width: 1100px;
            margin: 0 auto;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        header {
            padding: 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            border-bottom: 1px solid var(--border);
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo {
            width: 48px;
            height: 48px;
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--primary);
            color: white;
            font-size: 25px;
            font-weight: 800;
        }

        .brand h1 {
            font-size: 21px;
        }

        .brand p {
            color: var(--muted);
            font-size: 13px;
            margin-top: 2px;
        }

        .header-actions {
            display: flex;
            gap: 8px;
        }

        button {
            border: 0;
            cursor: pointer;
            font-family: inherit;
        }

        .icon-btn {
            width: 42px;
            height: 42px;
            border-radius: 12px;
            background: var(--card);
            border: 1px solid var(--border);
            color: var(--text);
            font-size: 18px;
        }

        main {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 18px;
        }

        .notice {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 14px;
            margin-bottom: 14px;
            color: var(--muted);
            font-size: 13px;
            line-height: 1.6;
        }

        .notice strong {
            color: var(--text);
        }

        .quick-tools {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-bottom: 16px;
        }

        .quick-btn {
            background: var(--card);
            color: var(--text);
            border: 1px solid var(--border);
            border-radius: 15px;
            padding: 13px 8px;
            font-size: 13px;
            transition: 0.2s;
        }

        .quick-btn:hover {
            transform: translateY(-2px);
            border-color: var(--primary);
        }

        .chat {
            flex: 1;
            min-height: 420px;
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 22px;
            box-shadow: var(--shadow);
            padding: 18px;
            overflow-y: auto;
        }

        .message {
            display: flex;
            margin-bottom: 15px;
        }

        .message.user {
            justify-content: flex-end;
        }

        .bubble {
            max-width: 82%;
            padding: 13px 15px;
            border-radius: 18px;
            line-height: 1.65;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 14px;
        }

        .assistant .bubble {
            background: var(--assistant);
            color: var(--text);
            border-bottom-left-radius: 5px;
        }

        .user .bubble {
            background: var(--user);
            color: white;
            border-bottom-right-radius: 5px;
        }

        .typing {
            color: var(--muted);
            font-size: 13px;
            padding: 10px;
        }

        .input-area {
            margin-top: 14px;
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 10px;
            display: flex;
            gap: 8px;
            align-items: flex-end;
        }

        textarea {
            flex: 1;
            min-height: 52px;
            max-height: 160px;
            resize: vertical;
            border: 0;
            outline: 0;
            background: transparent;
            color: var(--text);
            font-family: inherit;
            font-size: 14px;
            padding: 12px;
        }

        .send-btn {
            width: 50px;
            height: 50px;
            border-radius: 15px;
            background: var(--primary);
            color: white;
            font-size: 19px;
        }

        .send-btn:hover {
            background: var(--primary-dark);
        }

        .voice-btn {
            width: 50px;
            height: 50px;
            border-radius: 15px;
            background: var(--bg);
            border: 1px solid var(--border);
            color: var(--text);
            font-size: 18px;
        }

        .bottom-tools {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 10px;
            gap: 10px;
        }

        .small-btn {
            background: transparent;
            color: var(--muted);
            font-size: 12px;
            padding: 7px;
        }

        .emergency {
            margin-top: 10px;
            padding: 12px;
            border-radius: 14px;
            background: rgba(220, 38, 38, 0.08);
            color: var(--danger);
            font-size: 12px;
            line-height: 1.5;
        }

        @media (max-width: 700px) {
            .quick-tools {
                grid-template-columns: repeat(2, 1fr);
            }

            .bubble {
                max-width: 90%;
            }

            main {
                padding: 10px;
            }

            header {
                padding: 12px 10px;
            }
        }
    </style>
</head>

<body>

<div class="app">

    <header>
        <div class="brand">
            <div class="logo">✚</div>

            <div>
                <h1>MedAI</h1>
                <p>Medical AI Assistant</p>
            </div>
        </div>

        <div class="header-actions">
            <button
                class="icon-btn"
                onclick="toggleDarkMode()"
                title="Dark mode"
            >
                🌙
            </button>

            <button
                class="icon-btn"
                onclick="clearChat()"
                title="Clear chat"
            >
                🗑️
            </button>
        </div>
    </header>


    <main>

        <div class="notice">
            <strong>⚕️ Medical information only:</strong>
            MedAI provides general health information and is not a
            replacement for a doctor, examination, diagnosis, or emergency care.
        </div>


        <div class="quick-tools">

            <button
                class="quick-btn"
                onclick="quickAsk('I have some symptoms. Help me understand what they could mean and when I should see a doctor.')"
            >
                🩺 Symptoms
            </button>

            <button
                class="quick-btn"
                onclick="quickAsk('Please explain this medicine, its common uses, important precautions, and common side effects.')"
            >
                💊 Medicine
            </button>

            <button
                class="quick-btn"
                onclick="quickAsk('I have a laboratory test result. Explain what the test usually measures and what high or low results can mean. I will provide the values.')"
            >
                🧪 Lab Report
            </button>

            <button
                class="quick-btn"
                onclick="quickAsk('What symptoms should be treated as a medical emergency?')"
            >
                🚨 Emergency
            </button>

        </div>


        <div id="chat" class="chat">

            <div class="message assistant">
                <div class="bubble">
                    👋 Hello! I am MedAI.

                    I can help explain symptoms, medicines,
                    laboratory tests, general health questions,
                    and when medical attention may be appropriate.

                    How can I help you today?
                </div>
            </div>

        </div>


        <div id="typing" class="typing" style="display:none;">
            MedAI is thinking...
        </div>


        <div class="input-area">

            <button
                class="voice-btn"
                onclick="startVoice()"
                title="Voice input"
            >
                🎤
            </button>

            <textarea
                id="message"
                placeholder="Write your medical question..."
                onkeydown="handleKey(event)"
            ></textarea>

            <button
                class="send-btn"
                onclick="sendMessage()"
                title="Send"
            >
                ➤
            </button>

        </div>


        <div class="bottom-tools">

            <button
                class="small-btn"
                onclick="exportChat()"
            >
                📥 Export Chat
            </button>

            <button
                class="small-btn"
                onclick="speakLastAnswer()"
            >
                🔊 Read Last Answer
            </button>

        </div>


        <div class="emergency">
            🚨 If you have severe chest pain, severe breathing difficulty,
            unconsciousness, seizure, severe bleeding, stroke-like symptoms,
            severe allergic reaction, poisoning, or another life-threatening
            emergency, seek emergency medical care immediately.
        </div>

    </main>

</div>


<script>

const chatElement = document.getElementById("chat");
const messageInput = document.getElementById("message");
const typingElement = document.getElementById("typing");

let conversation = [];
let lastAssistantAnswer = "";


function addMessage(role, text) {

    const wrapper = document.createElement("div");

    wrapper.className = "message " + role;

    const bubble = document.createElement("div");

    bubble.className = "bubble";

    bubble.textContent = text;

    wrapper.appendChild(bubble);

    chatElement.appendChild(wrapper);

    chatElement.scrollTop = chatElement.scrollHeight;
}


function saveConversation() {

    localStorage.setItem(
        "medai_conversation",
        JSON.stringify(conversation)
    );
}


function loadConversation() {

    try {

        const saved = localStorage.getItem(
            "medai_conversation"
        );

        if (!saved) {
            return;
        }

        conversation = JSON.parse(saved);

        if (!Array.isArray(conversation)) {
            conversation = [];
            return;
        }

        for (const item of conversation) {

            if (
                item &&
                (item.role === "user" || item.role === "assistant") &&
                item.text
            ) {
                addMessage(item.role, item.text);

                if (item.role === "assistant") {
                    lastAssistantAnswer = item.text;
                }
            }
        }

    } catch (error) {

        console.error(error);

        conversation = [];
    }
}


function addToConversation(role, text) {

    conversation.push({
        role: role,
        text: text
    });

    if (conversation.length > 20) {
        conversation = conversation.slice(-20);
    }

    saveConversation();
}


async function sendMessage() {

    const message = messageInput.value.trim();

    if (!message) {
        return;
    }

    messageInput.value = "";

    addMessage("user", message);

    addToConversation("user", message);

    typingElement.style.display = "block";

    try {

        const history = conversation
            .slice(0, -1)
            .slice(-12);

        const response = await fetch("/api/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: message,
                history: history
            })

        });


        const data = await response.json();


        if (!response.ok) {

            throw new Error(
                data.error || "Request failed"
            );

        }


        const answer = data.answer || "No answer returned.";

        lastAssistantAnswer = answer;

        addMessage("assistant", answer);

        addToConversation("assistant", answer);


    } catch (error) {

        console.error(error);

        const errorMessage =
            "Sorry, something went wrong. Please try again.";

        addMessage("assistant", errorMessage);

        addToConversation(
            "assistant",
            errorMessage
        );

    } finally {

        typingElement.style.display = "none";

        messageInput.focus();
    }
}


function quickAsk(text) {

    messageInput.value = text;

    messageInput.focus();

    sendMessage();
}


function handleKey(event) {

    if (event.key === "Enter" && !event.shiftKey) {

        event.preventDefault();

        sendMessage();
    }
}


function clearChat() {

    if (!confirm("Clear chat history?")) {
        return;
    }

    conversation = [];

    lastAssistantAnswer = "";

    localStorage.removeItem(
        "medai_conversation"
    );

    chatElement.innerHTML = "";

    addMessage(
        "assistant",
        "👋 Hello! I am MedAI. How can I help you?"
    );
}


function toggleDarkMode() {

    document.body.classList.toggle("dark");

    localStorage.setItem(
        "medai_dark",
        document.body.classList.contains("dark")
    );
}


function loadDarkMode() {

    const dark =
        localStorage.getItem("medai_dark") === "true";

    if (dark) {
        document.body.classList.add("dark");
    }
}


function exportChat() {

    if (!conversation.length) {

        alert("There is no chat to export.");

        return;
    }

    let text = "MedAI Chat\n";
    text += "====================\n\n";

    for (const item of conversation) {

        const role =
            item.role === "user"
                ? "You"
                : "MedAI";

        text += role + ":\n";
        text += item.text + "\n\n";
    }

    const blob = new Blob(
        [text],
        { type: "text/plain;charset=utf-8" }
    );

    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");

    link.href = url;

    link.download = "medai-chat.txt";

    link.click();

    URL.revokeObjectURL(url);
}


function speakLastAnswer() {

    if (!lastAssistantAnswer) {

        alert("There is no answer to read.");

        return;
    }

    if (!("speechSynthesis" in window)) {

        alert(
            "Voice output is not supported by this browser."
        );

        return;
    }

    window.speechSynthesis.cancel();

    const utterance =
        new SpeechSynthesisUtterance(
            lastAssistantAnswer
        );

    utterance.lang = "en-US";

    window.speechSynthesis.speak(
        utterance
    );
}


function startVoice() {

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if (!SpeechRecognition) {

        alert(
            "Voice input is not supported by this browser."
        );

        return;
    }

    const recognition =
        new SpeechRecognition();

    recognition.lang = "en-US";

    recognition.interimResults = false;

    recognition.maxAlternatives = 1;


    recognition.onstart = function() {

        messageInput.placeholder =
            "Listening...";
    };


    recognition.onresult = function(event) {

        const transcript =
            event.results[0][0].transcript;

        messageInput.value = transcript;
    };


    recognition.onerror = function(event) {

        console.error(
            "Speech recognition error:",
            event.error
        );
    };


    recognition.onend = function() {

        messageInput.placeholder =
            "Write your medical question...";
    };


    recognition.start();
}


loadDarkMode();
loadConversation();

</script>

</body>
</html>
"""


# =========================================================
# ROUTES
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return render_template_string(HTML)


@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "ok",
        "service": "MedAI",
        "gemini_configured": bool(GEMINI_API_KEY),
        "model": GEMINI_MODEL
    })


@app.route("/api/chat", methods=["POST"])
def chat():

    if not request.is_json:
        return jsonify({
            "error": "Request must be JSON."
        }), 400

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Invalid JSON body."
        }), 400

    message = str(
        data.get("message", "")
    ).strip()

    history = data.get(
        "history",
        []
    )

    if not message:
        return jsonify({
            "error": "Message is required."
        }), 400

    if len(message) > 8000:
        return jsonify({
            "error": "Message is too long."
        }), 400

    if not isinstance(history, list):
        history = []

    # Limit history size for safety/performance
    history = history[-12:]

    answer = ask_gemini(
        message,
        history
    )

    return jsonify({
        "answer": answer,
        "model": GEMINI_MODEL
    })


# =========================================================
# LOCAL DEVELOPMENT
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            "5000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )

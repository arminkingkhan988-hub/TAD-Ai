from flask import Flask

app = Flask(__name__)
import os
import json
import urllib.request
import urllib.error

from flask import Flask, request, jsonify, render_template_string

# IMPORTANT: Vercel looks for this top-level Flask instance.
app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash").strip()

SYSTEM_PROMPT = """
You are MedAI, a medical information assistant.

Give clear, useful, cautious medical information.
You are not a replacement for a doctor or emergency service.

For emergencies, tell the user to contact local emergency medical services
or go to the nearest emergency department.

Do not claim certainty when symptoms can have multiple causes.
Do not diagnose with certainty from symptoms alone.
Ask relevant follow-up questions when necessary.

For medicines, explain common uses, important precautions, common side effects,
and advise the user to confirm dosing with a doctor or pharmacist.

Answer in the language used by the user.
"""


def ask_gemini(message, history):
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured on the server.")

    contents = []

    if isinstance(history, list):
        for item in history[-20:]:
            if not isinstance(item, dict):
                continue

            role = item.get("role")
            text = item.get("text")

            if role not in ("user", "model"):
                continue

            if not isinstance(text, str):
                continue

            text = text.strip()

            if not text:
                continue

            contents.append(
                {
                    "role": role,
                    "parts": [{"text": text[:12000]}],
                }
            )

    # Prevent accidentally sending the current user message twice.
    already_added = False

    if contents:
        last = contents[-1]

        if last.get("role") == "user":
            parts = last.get("parts") or []

            if parts and parts[0].get("text") == message:
                already_added = True

    if not already_added:
        contents.append(
            {
                "role": "user",
                "parts": [{"text": message[:12000]}],
            }
        )

    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/{GEMINI_MODEL}:generateContent"
    )

    payload = {
        "systemInstruction": {
            "parts": [
                {
                    "text": SYSTEM_PROMPT
                }
            ]
        },
        "contents": contents,
    }

    body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=55) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw)

    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")

        try:
            error_data = json.loads(error_body)
            error_message = (
                error_data.get("error", {}).get("message")
                or error_body
            )
        except Exception:
            error_message = error_body

        raise RuntimeError(
            f"Gemini API error ({exc.code}): {error_message[:500]}"
        )

    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Network error while contacting Gemini: {exc.reason}"
        )

    candidates = data.get("candidates") or []

    if not candidates:
        raise RuntimeError("Gemini returned no answer.")

    content = candidates[0].get("content") or {}
    parts = content.get("parts") or []

    answer = ""

    for part in parts:
        if isinstance(part, dict):
            text = part.get("text", "")

            if isinstance(text, str):
                answer += text

    answer = answer.strip()

    if not answer:
        raise RuntimeError("Gemini returned an empty answer.")

    return answer


@app.get("/")
def home():
    return render_template_string(
        """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <title>MedAI</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f5f7fb;
            color: #172033;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            background: #ffffff;
            border-radius: 18px;
            padding: 22px;
            margin-bottom: 18px;
            box-shadow: 0 5px 25px rgba(0,0,0,.06);
        }

        .header h1 {
            margin: 0 0 6px;
            font-size: 30px;
        }

        .header p {
            margin: 0;
            color: #64748b;
        }

        .chat {
            background: white;
            border-radius: 18px;
            padding: 18px;
            min-height: 450px;
            box-shadow: 0 5px 25px rgba(0,0,0,.06);
        }

        #messages {
            min-height: 350px;
            max-height: 60vh;
            overflow-y: auto;
            padding: 5px;
        }

        .message {
            margin: 12px 0;
            padding: 13px 15px;
            border-radius: 14px;
            white-space: pre-wrap;
            line-height: 1.55;
        }

        .user {
            background: #e8f0ff;
            margin-left: 15%;
        }

        .ai {
            background: #f1f5f9;
            margin-right: 10%;
        }

        .input-row {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }

        textarea {
            flex: 1;
            resize: vertical;
            min-height: 55px;
            max-height: 180px;
            border: 1px solid #d7dee8;
            border-radius: 13px;
            padding: 14px;
            font-size: 16px;
            outline: none;
        }

        button {
            border: 0;
            border-radius: 12px;
            padding: 0 18px;
            font-size: 15px;
            cursor: pointer;
            background: #2563eb;
            color: white;
        }

        button:disabled {
            opacity: .6;
            cursor: not-allowed;
        }

        .tools {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 14px;
        }

        .tool {
            background: #eef2ff;
            color: #1e40af;
            padding: 8px 12px;
            border-radius: 10px;
            border: 0;
            cursor: pointer;
        }

        .status {
            margin-top: 10px;
            color: #64748b;
            font-size: 14px;
        }

        @media (max-width: 600px) {
            .container {
                padding: 10px;
            }

            .header h1 {
                font-size: 25px;
            }

            .input-row {
                flex-direction: column;
            }

            button {
                min-height: 48px;
            }

            .user {
                margin-left: 5%;
            }

            .ai {
                margin-right: 5%;
            }
        }
    </style>
</head>

<body>

<div class="container">

    <div class="header">
        <h1>ðŸ©º MedAI</h1>
        <p>AI Medical Information Assistant</p>
    </div>

    <div class="chat">

        <div id="messages">
            <div class="message ai">
                Hello! I am MedAI. Tell me about your symptoms, medicine,
                lab report, or medical question.
            </div>
        </div>

        <div class="tools">
            <button class="tool" onclick="quickAsk('Explain my symptoms and possible causes.')">
                Symptoms
            </button>

            <button class="tool" onclick="quickAsk('Explain this medicine and its common precautions.')">
                Medicine
            </button>

            <button class="tool" onclick="quickAsk('Help me understand my laboratory report.')">
                Lab Report
            </button>

            <button class="tool" onclick="quickAsk('What should I do in a medical emergency?')">
                Emergency
            </button>

            <button class="tool" onclick="startVoice()">
                ðŸŽ¤ Voice
            </button>

            <button class="tool" onclick="toggleSpeech()">
                ðŸ”Š Voice Output
            </button>

            <button class="tool" onclick="toggleDark()">
                ðŸŒ™ Dark
            </button>
        </div>

        <div class="input-row">
            <textarea
                id="input"
                placeholder="Write your medical question..."
                onkeydown="handleKey(event)"
            ></textarea>

            <button id="send" onclick="sendMessage()">
                Send
            </button>
        </div>

        <div id="status" class="status"></div>

    </div>
</div>


<script>
let history = [];
let speakingEnabled = true;

function addMessage(role, text) {
    const messages = document.getElementById("messages");

    const div = document.createElement("div");

    div.className =
        "message " + (role === "user" ? "user" : "ai");

    div.textContent = text;

    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}


function handleKey(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}


function quickAsk(text) {
    document.getElementById("input").value = text;
    sendMessage();
}


async function sendMessage() {
    const input = document.getElementById("input");
    const send = document.getElementById("send");
    const status = document.getElementById("status");

    const message = input.value.trim();

    if (!message) {
        return;
    }

    addMessage("user", message);

    input.value = "";
    send.disabled = true;
    status.textContent = "MedAI is thinking...";

    const oldHistory = history.slice(-20);

    try {
        const response = await fetch("/api/chat", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: message,
                history: oldHistory
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Server error"
            );
        }

        const answer = data.answer || "No answer received.";

        addMessage("model", answer);

        history.push({
            role: "user",
            text: message
        });

        history.push({
            role: "model",
            text: answer
        });

        if (speakingEnabled) {
            speak(answer);
        }

        status.textContent = "";

    } catch (error) {
        addMessage(
            "model",
            "Error: " + error.message
        );

        status.textContent = "";
    }

    send.disabled = false;
    input.focus();
}


async function startVoice() {
    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        alert("Voice input is not supported by this browser.");
        return;
    }

    const recognition = new SpeechRecognition();

    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = function() {
        document.getElementById("status").textContent =
            "Listening...";
    };

    recognition.onresult = function(event) {
        const text =
            event.results[0][0].transcript;

        document.getElementById("input").value = text;

        document.getElementById("status").textContent =
            "Voice captured.";
    };

    recognition.onerror = function(event) {
        document.getElementById("status").textContent =
            "Voice error: " + event.error;
    };

    recognition.onend = function() {
        setTimeout(function() {
            document.getElementById("status").textContent = "";
        }, 1500);
    };

    recognition.start();
}


function speak(text) {
    if (!("speechSynthesis" in window)) {
        return;
    }

    window.speechSynthesis.cancel();

    const utterance =
        new SpeechSynthesisUtterance(text);

    utterance.rate = 0.95;
    utterance.pitch = 1;

    window.speechSynthesis.speak(utterance);
}


function toggleSpeech() {
    speakingEnabled = !speakingEnabled;

    document.getElementById("status").textContent =
        speakingEnabled
            ? "Voice output enabled."
            : "Voice output disabled.";

    setTimeout(function() {
        document.getElementById("status").textContent = "";
    }, 1500);
}


function toggleDark() {
    const body = document.body;

    if (body.dataset.dark === "1") {
        body.dataset.dark = "0";

        body.style.background = "#f5f7fb";
        body.style.color = "#172033";

    } else {
        body.dataset.dark = "1";

        body.style.background = "#0f172a";
        body.style.color = "#f8fafc";
    }
}
</script>

</body>
</html>
"""
    )


@app.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "gemini_configured": bool(GEMINI_API_KEY),
        }
    )


@app.post("/api/chat")
def chat():
    try:
        data = request.get_json(silent=True) or {}

        message = data.get("message", "")
        history = data.get("history", [])

        if not isinstance(message, str):
            return jsonify(
                {"error": "Message must be text."}
            ), 400

        message = message.strip()

        if not message:
            return jsonify(
                {"error": "Please enter a message."}
            ), 400

        if len(message) > 12000:
            return jsonify(
                {"error": "Message is too long."}
            ), 400

        answer = ask_gemini(message, history)

        return jsonify(
            {
                "answer": answer
            }
        )

    except Exception as exc:
        return jsonify(
            {
                "error": str(exc)
            }
        ), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )

import os
import re
import time
import json
import html
import logging
import urllib.request
import urllib.error
from collections import defaultdict, deque

from flask import Flask, request, jsonify, render_template_string


# ============================================================
# MEDAI - SINGLE FILE FLASK APPLICATION
# ============================================================

app = Flask(__name__)

# -------------------------
# Configuration
# -------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()

MAX_MESSAGE_LENGTH = 12000
MAX_HISTORY_MESSAGES = 20
RATE_LIMIT = 25
RATE_WINDOW = 60

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("medai")

rate_store = defaultdict(deque)


# ============================================================
# MEDICAL SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = r"""
You are MedAI, a medical information assistant.

IMPORTANT SAFETY RULES:
1. You are not a doctor and do not replace professional medical care.
2. Never claim certainty when the information is uncertain.
3. Do not diagnose a patient definitively from symptoms alone.
4. Do not prescribe controlled medicines.
5. Do not recommend changing or stopping prescription medicines without a clinician.
6. For emergencies, clearly advise contacting local emergency services or going to the nearest emergency department.
7. If symptoms suggest a potentially dangerous condition, explain the warning signs and recommend urgent evaluation.
8. Be especially careful with children, pregnancy, elderly people, severe allergies, chest pain, stroke symptoms, severe breathing problems, poisoning, major bleeding, seizures, unconsciousness, and suicidal/self-harm situations.
9. Ask relevant follow-up questions when necessary.
10. Give practical next steps.
11. Do not invent laboratory values, drug interactions, diagnoses, or medical guidelines.
12. Clearly distinguish general information from personalized medical advice.
13. If the user provides lab values, explain what they commonly mean, but do not make a definitive diagnosis.
14. For medicines, discuss common uses, common side effects, important warnings, and the need to follow the prescribed label.
15. For drug interactions, explain that a complete medication list, dose, age, pregnancy status, and conditions may be needed.
16. Never encourage dangerous self-treatment.

LANGUAGE:
- Reply in the same language as the user.
- If the user writes Pashto, reply in clear Pashto.
- If the user writes English, reply in English.
- Use simple language where possible.

STYLE:
- Use short headings.
- Use bullets when useful.
- Be concise but medically useful.
- Avoid unnecessary repetition.

EMERGENCY:
If the user reports severe chest pain, severe difficulty breathing, blue lips, sudden weakness/numbness on one side, severe bleeding, unconsciousness, seizure, suspected poisoning, severe allergic reaction, or another obvious emergency:
- Tell them to seek emergency medical care immediately.
- Do not delay emergency care with lengthy explanations.

Always include an appropriate safety note when giving personalized medical information.
"""


# ============================================================
# RATE LIMITING
# ============================================================

def get_client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def rate_limited(ip):
    now = time.time()
    q = rate_store[ip]

    while q and now - q[0] > RATE_WINDOW:
        q.popleft()

    if len(q) >= RATE_LIMIT:
        return True

    q.append(now)
    return False


# ============================================================
# SECURITY HEADERS
# ============================================================

@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(self), geolocation=()"
    )
    response.headers["Cache-Control"] = "no-store"

    response.headers["Content-Security-Policy"] = (
        "default-src 'self' 'unsafe-inline' https: data: blob:; "
        "script-src 'self' 'unsafe-inline' https:; "
        "style-src 'self' 'unsafe-inline' https:; "
        "img-src 'self' data: https: blob:; "
        "connect-src 'self' https:; "
        "font-src 'self' https: data:;"
    )

    return response


# ============================================================
# GEMINI API
# ============================================================

def clean_history(history):
    if not isinstance(history, list):
        return []

    cleaned = []

    for item in history[-MAX_HISTORY_MESSAGES:]:
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

        text = text[:MAX_MESSAGE_LENGTH]

        cleaned.append({
            "role": role,
            "parts": [{"text": text}]
        })

    return cleaned


def call_gemini(message, history=None):
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured on the server."
        )

    message = message.strip()

    if not message:
        raise ValueError("Empty message.")

    if len(message) > MAX_MESSAGE_LENGTH:
        raise ValueError("Message is too long.")

    contents = clean_history(history or [])

    # Prevent accidentally duplicating the current user message.
    if not contents or contents[-1].get("role") != "user":
        contents.append({
            "role": "user",
            "parts": [{"text": message}]
        })

    elif contents[-1]["parts"][0]["text"].strip() != message:
        contents.append({
            "role": "user",
            "parts": [{"text": message}]
        })

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        + GEMINI_MODEL
        + ":generateContent?key="
        + GEMINI_API_KEY
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
        "generationConfig": {
            "temperature": 0.25,
            "topP": 0.9,
            "maxOutputTokens": 4096
        }
    }

    body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "MedAI/1.0"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=55) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw)

    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")

        logger.error(
            "Gemini HTTP %s: %s",
            exc.code,
            error_body[:2000]
        )

        if exc.code in (400, 401, 403):
            raise RuntimeError(
                "Gemini API key, model, or request configuration is invalid."
            )

        if exc.code == 429:
            raise RuntimeError(
                "Gemini API rate limit was reached. Please try again shortly."
            )

        raise RuntimeError(
            "Gemini service returned an error."
        )

    except urllib.error.URLError as exc:
        logger.error("Gemini network error: %s", exc)
        raise RuntimeError(
            "Could not connect to Gemini."
        )

    except Exception as exc:
        logger.exception("Unexpected Gemini error")
        raise RuntimeError(
            "Unexpected AI service error."
        )

    candidates = data.get("candidates") or []

    if not candidates:
        error = data.get("error", {})
        logger.error("Gemini returned no candidates: %s", error)
        raise RuntimeError(
            "The AI service did not return an answer."
        )

    candidate = candidates[0] or {}

    content = candidate.get("content") or {}
    parts = content.get("parts") or []

    texts = []

    for part in parts:
        if not isinstance(part, dict):
            continue

        text = part.get("text")

        if isinstance(text, str) and text.strip():
            texts.append(text.strip())

    answer = "\n\n".join(texts).strip()

    if not answer:
        raise RuntimeError(
            "The AI service returned an empty answer."
        )

    return answer


# ============================================================
# ROUTES
# ============================================================

@app.route("/", methods=["GET"])
def home():
    return render_template_string(PAGE)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "MedAI",
        "gemini_configured": bool(GEMINI_API_KEY),
        "model": GEMINI_MODEL
    })


@app.route("/api/chat", methods=["POST"])
def api_chat():
    ip = get_client_ip()

    if rate_limited(ip):
        return jsonify({
            "ok": False,
            "error": "Too many requests. Please wait a little and try again."
        }), 429

    try:
        data = request.get_json(silent=True) or {}

        message = data.get("message", "")
        history = data.get("history", [])

        if not isinstance(message, str):
            return jsonify({
                "ok": False,
                "error": "Invalid message."
            }), 400

        message = message.strip()

        if not message:
            return jsonify({
                "ok": False,
                "error": "Please enter a message."
            }), 400

        if len(message) > MAX_MESSAGE_LENGTH:
            return jsonify({
                "ok": False,
                "error": "Message is too long."
            }), 400

        answer = call_gemini(message, history)

        return jsonify({
            "ok": True,
            "answer": answer
        })

    except ValueError as exc:
        return jsonify({
            "ok": False,
            "error": str(exc)
        }), 400

    except RuntimeError as exc:
        return jsonify({
            "ok": False,
            "error": str(exc)
        }), 502

    except Exception:
        logger.exception("Chat endpoint error")

        return jsonify({
            "ok": False,
            "error": "Server error. Please try again."
        }), 500


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):
        return jsonify({
            "ok": False,
            "error": "API endpoint not found."
        }), 404

    return render_template_string(PAGE), 200


@app.errorhandler(500)
def server_error(error):
    if request.path.startswith("/api/"):
        return jsonify({
            "ok": False,
            "error": "Internal server error."
        }), 500

    return "MedAI server error", 500


# ============================================================
# FRONTEND
# ============================================================

PAGE = r"""
<!DOCTYPE html>
<html lang="ps" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="theme-color" content="#0f766e">
<meta name="description" content="MedAI - AI Medical Assistant">

<title>MedAI - AI Medical Assistant</title>

<style>
:root{
    --bg:#f5f7fb;
    --panel:#ffffff;
    --panel2:#f8fafc;
    --text:#172033;
    --muted:#667085;
    --border:#e5e7eb;
    --primary:#0f766e;
    --primary2:#115e59;
    --accent:#14b8a6;
    --danger:#dc2626;
    --warning:#d97706;
    --shadow:0 12px 35px rgba(15,23,42,.08);
}

*{
    box-sizing:border-box;
}

html,body{
    margin:0;
    padding:0;
    width:100%;
    height:100%;
    font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Tahoma,
        Arial,
        sans-serif;
}

body{
    background:var(--bg);
    color:var(--text);
}

body.dark{
    --bg:#07111f;
    --panel:#0d1b2a;
    --panel2:#102235;
    --text:#e6edf5;
    --muted:#9aaabd;
    --border:#22364a;
    --primary:#14b8a6;
    --primary2:#0f766e;
    --accent:#2dd4bf;
    --shadow:0 12px 35px rgba(0,0,0,.25);
}

button,
textarea,
input,
select{
    font:inherit;
}

button{
    cursor:pointer;
}

.app{
    display:flex;
    min-height:100vh;
}

.sidebar{
    width:290px;
    flex:0 0 290px;
    background:var(--panel);
    border-left:1px solid var(--border);
    padding:18px;
    display:flex;
    flex-direction:column;
    gap:15px;
    position:fixed;
    right:0;
    top:0;
    bottom:0;
    z-index:50;
    overflow-y:auto;
}

.brand{
    display:flex;
    align-items:center;
    gap:12px;
    padding:8px;
}

.logo{
    width:46px;
    height:46px;
    border-radius:15px;
    background:linear-gradient(135deg,#0f766e,#14b8a6);
    display:flex;
    align-items:center;
    justify-content:center;
    color:white;
    font-size:25px;
    font-weight:900;
    box-shadow:0 10px 25px rgba(20,184,166,.25);
}

.brand h1{
    margin:0;
    font-size:22px;
}

.brand small{
    color:var(--muted);
}

.side-section{
    display:flex;
    flex-direction:column;
    gap:5px;
}

.side-title{
    color:var(--muted);
    font-size:12px;
    font-weight:800;
    padding:8px;
}

.tool{
    border:0;
    background:transparent;
    color:var(--text);
    border-radius:12px;
    padding:10px 12px;
    text-align:right;
    display:flex;
    align-items:center;
    gap:10px;
    transition:.2s;
}

.tool:hover,
.tool.active{
    background:rgba(20,184,166,.12);
    color:var(--primary);
}

.tool .icon{
    width:25px;
    text-align:center;
}

.side-bottom{
    margin-top:auto;
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:8px;
}

.small-btn{
    border:1px solid var(--border);
    background:var(--panel2);
    color:var(--text);
    padding:9px;
    border-radius:11px;
}

.main{
    margin-right:290px;
    min-width:0;
    width:calc(100% - 290px);
    display:flex;
    flex-direction:column;
    min-height:100vh;
}

.topbar{
    height:70px;
    border-bottom:1px solid var(--border);
    background:var(--panel);
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:0 22px;
    position:sticky;
    top:0;
    z-index:30;
}

.top-left{
    display:flex;
    align-items:center;
    gap:10px;
}

.mobile-menu{
    display:none;
    border:1px solid var(--border);
    background:var(--panel2);
    color:var(--text);
    border-radius:10px;
    padding:9px 12px;
}

.status{
    display:flex;
    align-items:center;
    gap:7px;
    color:var(--muted);
    font-size:13px;
}

.dot{
    width:9px;
    height:9px;
    border-radius:50%;
    background:#22c55e;
}

.top-actions{
    display:flex;
    gap:8px;
}

.icon-btn{
    border:1px solid var(--border);
    background:var(--panel2);
    color:var(--text);
    border-radius:11px;
    width:40px;
    height:40px;
}

.content{
    width:100%;
    max-width:1050px;
    margin:0 auto;
    padding:30px 20px 100px;
}

.hero{
    background:
        radial-gradient(circle at top right,rgba(20,184,166,.2),transparent 35%),
        var(--panel);
    border:1px solid var(--border);
    box-shadow:var(--shadow);
    border-radius:25px;
    padding:30px;
    margin-bottom:18px;
}

.hero h2{
    margin:0 0 8px;
    font-size:30px;
}

.hero p{
    color:var(--muted);
    margin:0;
    line-height:1.8;
}

.warning{
    background:rgba(220,38,38,.08);
    color:var(--danger);
    border:1px solid rgba(220,38,38,.18);
    border-radius:14px;
    padding:13px;
    margin-top:18px;
    line-height:1.7;
    font-size:13px;
}

.quick{
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:10px;
    margin-top:20px;
}

.quick button{
    border:1px solid var(--border);
    background:var(--panel2);
    color:var(--text);
    padding:12px;
    border-radius:13px;
    text-align:right;
}

.quick button:hover{
    border-color:var(--accent);
}

.chat{
    display:flex;
    flex-direction:column;
    gap:14px;
}

.message{
    max-width:86%;
    padding:15px 17px;
    border-radius:18px;
    line-height:1.8;
    white-space:pre-wrap;
    word-break:break-word;
}

.message.user{
    align-self:flex-start;
    background:var(--primary);
    color:white;
    border-bottom-left-radius:5px;
}

.message.ai{
    align-self:flex-end;
    background:var(--panel);
    border:1px solid var(--border);
    box-shadow:var(--shadow);
    border-bottom-right-radius:5px;
}

.msg-tools{
    display:flex;
    gap:6px;
    margin-top:9px;
    direction:ltr;
}

.msg-tools button{
    border:1px solid var(--border);
    background:var(--panel2);
    color:var(--muted);
    border-radius:8px;
    padding:4px 8px;
    font-size:12px;
}

.composer{
    position:fixed;
    left:0;
    right:290px;
    bottom:0;
    background:linear-gradient(to top,var(--bg) 72%,transparent);
    padding:18px 20px;
    z-index:25;
}

.composer-inner{
    max-width:1050px;
    margin:auto;
    display:flex;
    gap:9px;
    align-items:end;
    background:var(--panel);
    border:1px solid var(--border);
    box-shadow:var(--shadow);
    padding:10px;
    border-radius:18px;
}

textarea{
    resize:none;
    min-height:48px;
    max-height:160px;
    flex:1;
    border:0;
    outline:0;
    background:transparent;
    color:var(--text);
    padding:10px;
    line-height:1.6;
}

.send{
    border:0;
    background:var(--primary);
    color:white;
    border-radius:13px;
    min-width:48px;
    height:48px;
    font-size:19px;
}

.send:hover{
    background:var(--primary2);
}

.voice{
    border:1px solid var(--border);
    background:var(--panel2);
    color:var(--text);
    border-radius:13px;
    width:48px;
    height:48px;
}

.voice.recording{
    background:var(--danger);
    color:white;
    animation:pulse 1s infinite;
}

@keyframes pulse{
    50%{transform:scale(1.06)}
}

.empty{
    text-align:center;
    color:var(--muted);
    padding:35px 10px;
}

.typing{
    display:flex;
    align-items:center;
    gap:5px;
}

.typing span{
    width:7px;
    height:7px;
    border-radius:50%;
    background:var(--muted);
    animation:bounce 1s infinite;
}

.typing span:nth-child(2){animation-delay:.15s}
.typing span:nth-child(3){animation-delay:.3s}

@keyframes bounce{
    0%,100%{transform:translateY(0)}
    50%{transform:translateY(-5px)}
}

.overlay{
    display:none;
    position:fixed;
    inset:0;
    background:rgba(0,0,0,.45);
    z-index:45;
}

.modal{
    position:fixed;
    inset:0;
    display:none;
    align-items:center;
    justify-content:center;
    z-index:100;
    padding:20px;
}

.modal.show{
    display:flex;
}

.modal-card{
    width:min(600px,100%);
    max-height:90vh;
    overflow:auto;
    background:var(--panel);
    border:1px solid var(--border);
    border-radius:22px;
    padding:22px;
    box-shadow:0 25px 70px rgba(0,0,0,.25);
}

.modal-head{
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin-bottom:15px;
}

.modal-head h3{
    margin:0;
}

.close{
    border:1px solid var(--border);
    background:var(--panel2);
    color:var(--text);
    width:38px;
    height:38px;
    border-radius:10px;
}

.form{
    display:grid;
    gap:10px;
}

.form input,
.form select{
    width:100%;
    border:1px solid var(--border);
    background:var(--panel2);
    color:var(--text);
    border-radius:11px;
    padding:11px;
    outline:none;
}

.primary-btn{
    border:0;
    background:var(--primary);
    color:white;
    border-radius:11px;
    padding:12px 15px;
}

.list{
    display:grid;
    gap:9px;
}

.list-item{
    border:1px solid var(--border);
    background:var(--panel2);
    border-radius:12px;
    padding:12px;
    display:flex;
    justify-content:space-between;
    gap:10px;
    align-items:center;
}

.danger-btn{
    border:1px solid rgba(220,38,38,.25);
    background:rgba(220,38,38,.08);
    color:var(--danger);
    border-radius:9px;
    padding:7px 9px;
}

.tool-grid{
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:10px;
}

.tool-card{
    border:1px solid var(--border);
    background:var(--panel2);
    border-radius:15px;
    padding:15px;
    cursor:pointer;
    transition:.2s;
}

.tool-card:hover{
    transform:translateY(-2px);
    border-color:var(--accent);
}

.tool-card strong{
    display:block;
    margin-bottom:5px;
}

.tool-card span{
    color:var(--muted);
    font-size:12px;
}

.toast{
    position:fixed;
    bottom:90px;
    left:50%;
    transform:translateX(-50%) translateY(20px);
    background:#111827;
    color:white;
    padding:11px 16px;
    border-radius:10px;
    opacity:0;
    pointer-events:none;
    transition:.25s;
    z-index:200;
}

.toast.show{
    opacity:1;
    transform:translateX(-50%) translateY(0);
}

@media(max-width:900px){
    .sidebar{
        transform:translateX(100%);
        transition:.25s;
    }

    .sidebar.open{
        transform:translateX(0);
    }

    .main{
        margin-right:0;
        width:100%;
    }

    .composer{
        right:0;
    }

    .mobile-menu{
        display:block;
    }

    .overlay.show{
        display:block;
    }

    .quick{
        grid-template-columns:repeat(2,1fr);
    }

    .tool-grid{
        grid-template-columns:repeat(2,1fr);
    }
}

@media(max-width:600px){
    .content{
        padding:18px 12px 110px;
    }

    .hero{
        padding:20px;
        border-radius:19px;
    }

    .hero h2{
        font-size:24px;
    }

    .quick{
        grid-template-columns:1fr 1fr;
    }

    .tool-grid{
        grid-template-columns:1fr 1fr;
    }

    .message{
        max-width:94%;
    }

    .status{
        display:none;
    }

    .topbar{
        padding:0 12px;
    }

    .composer{
        padding:10px;
    }

    .composer-inner{
        border-radius:15px;
    }
}
</style>
</head>

<body>

<div class="overlay" id="overlay" onclick="closeSidebar()"></div>

<div class="app">

    <aside class="sidebar" id="sidebar">

        <div class="brand">
            <div class="logo">✚</div>
            <div>
                <h1>MedAI</h1>
                <small>AI Medical Assistant</small>
            </div>
        </div>

        <div class="side-section">

            <div class="side-title">AI TOOLS</div>

            <button class="tool active" onclick="selectTool('AI Medical Chat', '')">
                <span class="icon">💬</span>
                <span>AI Medical Chat</span>
            </button>

            <button class="tool" onclick="selectTool('Symptoms Checker','زما نښې دا دي: ')">
                <span class="icon">🩺</span>
                <span>Symptoms Checker</span>
            </button>

            <button class="tool" onclick="selectTool('Vital Signs','زما vital signs دا دي: ')">
                <span class="icon">❤️</span>
                <span>Vital Signs</span>
            </button>

            <button class="tool" onclick="selectTool('Disease Compare','د لاندې دوو ناروغیو پرتله راته وکړه: ')">
                <span class="icon">⚖️</span>
                <span>Disease Compare</span>
            </button>

            <button class="tool" onclick="selectTool('Doctor Assistant','د ډاکټر په توګه نه، بلکې د طبي معلوماتو مرستیال په توګه، زما پوښتنه دا ده: ')">
                <span class="icon">👨‍⚕️</span>
                <span>Doctor Assistant</span>
            </button>

            <button class="tool" onclick="selectTool('Lab Report','زما د لابراتوار راپور تشریح کړه: ')">
                <span class="icon">🧪</span>
                <span>Lab Report</span>
            </button>

            <button class="tool" onclick="selectTool('Medicine Info','د دې درملو په اړه معلومات راکړه: ')">
                <span class="icon">💊</span>
                <span>Medicine Info</span>
            </button>

            <button class="tool" onclick="selectTool('Medical Dictionary','دا طبي اصطلاح په ساده ژبه تشریح کړه: ')">
                <span class="icon">📖</span>
                <span>Medical Dictionary</span>
            </button>

            <button class="tool" onclick="selectTool('Emergency Checker','ایا دا حالت بیړنی دی؟ زما نښې: ')">
                <span class="icon">🚨</span>
                <span>Emergency Checker</span>
            </button>

            <button class="tool" onclick="selectTool('Drug Interaction','زما درمل دا دي، احتمالي interactions تشریح کړه: ')">
                <span class="icon">🔗</span>
                <span>Drug Interaction</span>
            </button>

            <button class="tool" onclick="selectTool('First Aid','د دې حالت لپاره لومړنۍ مرستې څه دي؟ ')">
                <span class="icon">🆘</span>
                <span>First Aid</span>
            </button>

            <button class="tool" onclick="selectTool('Risk Assessment','زما روغتیايي خطرونه په دې معلوماتو کې وارزوه: ')">
                <span class="icon">📊</span>
                <span>Risk Assessment</span>
            </button>

            <button class="tool" onclick="selectTool('Health Report','زما د روغتیا لنډ راپور جوړ کړه: ')">
                <span class="icon">📋</span>
                <span>Health Report</span>
            </button>

            <button class="tool" onclick="selectTool('Medical Quiz','ما ته یو طبي Quiz جوړ کړه.')">
                <span class="icon">🧠</span>
                <span>Medical Quiz</span>
            </button>

            <button class="tool" onclick="selectTool('Medical Glossary','د مهمو طبي اصطلاحاتو یو glossary جوړ کړه.')">
                <span class="icon">📚</span>
                <span>Medical Glossary</span>
            </button>

            <button class="tool" onclick="selectTool('Medical Images','د دې طبي موضوع لپاره د انځور/diagram تشریحي prompt جوړ کړه: ')">
                <span class="icon">🖼️</span>
                <span>Medical Images</span>
            </button>

        </div>

        <div class="side-section">

            <div class="side-title">PERSONAL</div>

            <button class="tool" onclick="openHistory()">
                <span class="icon">🕘</span>
                <span>History</span>
            </button>

            <button class="tool" onclick="openFavorites()">
                <span class="icon">⭐</span>
                <span>Favorites</span>
            </button>

            <button class="tool" onclick="openTracker()">
                <span class="icon">📈</span>
                <span>Health Tracker</span>
            </button>

            <button class="tool" onclick="openReminders()">
                <span class="icon">⏰</span>
                <span>Medicine Reminders</span>
            </button>

        </div>

        <div class="side-bottom">
            <button class="small-btn" onclick="toggleDark()">🌙 Dark</button>
            <button class="small-btn" onclick="newChat()">＋ New</button>
        </div>

    </aside>

    <main class="main">

        <header class="topbar">

            <div class="top-left">

                <button class="mobile-menu" onclick="toggleSidebar()">
                    ☰
                </button>

                <div class="status">
                    <span class="dot"></span>
                    <span>MedAI Online</span>
                </div>

            </div>

            <div class="top-actions">
                <button class="icon-btn" onclick="openHistory()" title="History">🕘</button>
                <button class="icon-btn" onclick="openFavorites()" title="Favorites">⭐</button>
                <button class="icon-btn" onclick="toggleDark()" title="Dark mode">🌙</button>
            </div>

        </header>

        <section class="content">

            <div class="hero">

                <h2 id="heroTitle">ستاسو روغتیايي AI مرستیال</h2>

                <p id="heroText">
                    خپلې روغتیايي پوښتنې ولیکئ. MedAI به د عمومي طبي معلوماتو،
                    نښو، درملو، لابراتوار او لومړنیو مرستو په اړه مرسته وکړي.
                </p>

                <div class="warning">
                    ⚠️ MedAI د ډاکټر بدیل نه دی. د جدي یا بیړنیو نښو په صورت کې
                    سمدستي مسلکي طبي مرسته وغواړئ.
                </div>

                <div class="quick">

                    <button onclick="quickPrompt('د سر درد عام لاملونه او د خطر نښې تشریح کړه.')">
                        🤕 سر درد
                    </button>

                    <button onclick="quickPrompt('د وینې فشار په اړه عمومي معلومات راکړه.')">
                        ❤️ د وینې فشار
                    </button>

                    <button onclick="quickPrompt('د شکر ناروغۍ عامې نښې او د تشخیص عمومي لارې تشریح کړه.')">
                        🩸 شکر
                    </button>

                    <button onclick="quickPrompt('د زکام او فلو ترمنځ توپیر تشریح کړه.')">
                        🤧 زکام / فلو
                    </button>

                </div>

            </div>

            <div class="chat" id="chat">

                <div class="empty" id="emptyState">
                    👋 سلام! زه MedAI یم.<br>
                    خپله طبي پوښتنه ولیکئ یا له پورته tools څخه یو انتخاب کړئ.
                </div>

            </div>

        </section>

    </main>

</div>


<div class="composer">

    <div class="composer-inner">

        <button class="voice" id="voiceBtn" onclick="toggleVoice()" title="Voice input">
            🎙️
        </button>

        <textarea
            id="message"
            placeholder="خپله روغتیايي پوښتنه ولیکئ..."
            rows="1"
            onkeydown="handleKey(event)"
        ></textarea>

        <button class="send" onclick="sendMessage()" title="Send">
            ➤
        </button>

    </div>

</div>


<!-- MODAL -->

<div class="modal" id="modal">

    <div class="modal-card">

        <div class="modal-head">

            <h3 id="modalTitle">MedAI</h3>

            <button class="close" onclick="closeModal()">
                ✕
            </button>

        </div>

        <div id="modalBody"></div>

    </div>

</div>


<div class="toast" id="toast"></div>


<script>
"use strict";


/* ==========================================================
   STATE
========================================================== */

let messages = [];
let favorites = JSON.parse(localStorage.getItem("medai_favorites") || "[]");
let historyItems = JSON.parse(localStorage.getItem("medai_history") || "[]");
let tracker = JSON.parse(localStorage.getItem("medai_tracker") || "[]");
let reminders = JSON.parse(localStorage.getItem("medai_reminders") || "[]");

let currentTool = "AI Medical Chat";

let recognition = null;
let recording = false;
let continuousVoice = false;

const chat = document.getElementById("chat");
const messageBox = document.getElementById("message");


/* ==========================================================
   INIT
========================================================== */

document.addEventListener("DOMContentLoaded", () => {

    if(localStorage.getItem("medai_dark") === "1"){
        document.body.classList.add("dark");
    }

    autoResize();

    setInterval(checkReminders, 30000);

});


/* ==========================================================
   UI HELPERS
========================================================== */

function showToast(text){

    const el = document.getElementById("toast");

    el.textContent = text;
    el.classList.add("show");

    setTimeout(() => {
        el.classList.remove("show");
    }, 2400);
}


function toggleDark(){

    document.body.classList.toggle("dark");

    localStorage.setItem(
        "medai_dark",
        document.body.classList.contains("dark") ? "1" : "0"
    );
}


function toggleSidebar(){

    document.getElementById("sidebar").classList.toggle("open");
    document.getElementById("overlay").classList.toggle("show");
}


function closeSidebar(){

    document.getElementById("sidebar").classList.remove("open");
    document.getElementById("overlay").classList.remove("show");
}


function autoResize(){

    messageBox.style.height = "auto";

    messageBox.style.height =
        Math.min(messageBox.scrollHeight, 160) + "px";
}


messageBox.addEventListener("input", autoResize);


function handleKey(event){

    if(event.key === "Enter" && !event.shiftKey){

        event.preventDefault();
        sendMessage();

    }
}


/* ==========================================================
   TOOLS
========================================================== */

function selectTool(name, prefix){

    currentTool = name;

    messageBox.value = prefix || "";

    autoResize();
    messageBox.focus();

    document.querySelectorAll(".tool").forEach(btn => {
        btn.classList.remove("active");
    });

    if(window.innerWidth <= 900){
        closeSidebar();
    }

    document.getElementById("heroTitle").textContent = name;

    const descriptions = {
        "AI Medical Chat":
            "عمومي طبي معلومات او روغتیايي پوښتنې له MedAI سره شریکې کړئ.",
        "Symptoms Checker":
            "خپلې نښې ولیکئ؛ MedAI به احتمالي لاملونه، خطر نښې او راتلونکي ګامونه تشریح کړي.",
        "Vital Signs":
            "د وینې فشار، نبض، تودوخې، SpO₂ او نورو vital signs په اړه معلومات ترلاسه کړئ.",
        "Disease Compare":
            "د دوو ناروغیو نښې، توپیرونه، خطر نښې او عمومي تشخیص پرتله کړئ.",
        "Doctor Assistant":
            "د طبي پوښتنو، differential considerations او د ډاکټر سره د خبرو د چمتووالي لپاره مرسته.",
        "Lab Report":
            "خپل lab values ولیکئ او د هغوی عمومي معنا تشریح کړئ.",
        "Medicine Info":
            "د درملو عام استعمالونه، side effects او مهم احتیاطونه وپوښتئ.",
        "Medical Dictionary":
            "پیچلې طبي اصطلاحات په ساده ژبه زده کړئ.",
        "Emergency Checker":
            "د خطرناکو نښو په اړه بیړنی حالت وڅېړئ.",
        "Drug Interaction":
            "د خپلو درملو احتمالي interactions په اړه عمومي معلومات واخلئ.",
        "First Aid":
            "د عامو بیړنیو حالتونو لپاره د لومړنیو مرستو عمومي لارښوونې.",
        "Risk Assessment":
            "د روغتیايي خطر فکتورونو عمومي ارزونه.",
        "Health Report":
            "د ورکړل شوو معلوماتو پر بنسټ یو منظم health summary جوړ کړئ.",
        "Medical Quiz":
            "د طبي زده کړې لپاره quiz او پوښتنې.",
        "Medical Glossary":
            "د طبي اصطلاحاتو منظم glossary.",
        "Medical Images":
            "د طبي diagram یا انځور لپاره تشریحي prompt."
    };

    document.getElementById("heroText").textContent =
        descriptions[name] || descriptions["AI Medical Chat"];
}


function quickPrompt(text){

    messageBox.value = text;
    autoResize();
    sendMessage();
}


/* ==========================================================
   CHAT
========================================================== */

function addMessage(role, text, save=true){

    if(document.getElementById("emptyState")){
        document.getElementById("emptyState").remove();
    }

    const wrapper = document.createElement("div");

    wrapper.className =
        "message " + (role === "user" ? "user" : "ai");

    const content = document.createElement("div");

    content.textContent = text;

    wrapper.appendChild(content);

    if(role === "model"){

        const tools = document.createElement("div");

        tools.className = "msg-tools";

        const copy = document.createElement("button");

        copy.textContent = "Copy";

        copy.onclick = () => {

            navigator.clipboard.writeText(text)
                .then(() => showToast("کاپي شو."))
                .catch(() => showToast("Copy ناکام شو."));

        };

        const fav = document.createElement("button");

        fav.textContent =
            favorites.includes(text) ? "★ Saved" : "☆ Favorite";

        fav.onclick = () => toggleFavorite(text, fav);

        const speak = document.createElement("button");

        speak.textContent = "🔊";

        speak.onclick = () => speakText(text);

        tools.appendChild(copy);
        tools.appendChild(fav);
        tools.appendChild(speak);

        wrapper.appendChild(tools);
    }

    chat.appendChild(wrapper);

    chat.scrollTop = chat.scrollHeight;

    if(save){

        messages.push({
            role: role,
            text: text
        });

    }
}


function showTyping(){

    const el = document.createElement("div");

    el.id = "typing";
    el.className = "message ai";

    el.innerHTML =
        '<div class="typing"><span></span><span></span><span></span></div>';

    chat.appendChild(el);

    chat.scrollTop = chat.scrollHeight;
}


function removeTyping(){

    const el = document.getElementById("typing");

    if(el){
        el.remove();
    }
}


async function sendMessage(){

    const text = messageBox.value.trim();

    if(!text){
        return;
    }

    if(text.length > 12000){

        showToast("پیغام ډېر اوږد دی.");
        return;

    }

    addMessage("user", text);

    messageBox.value = "";
    autoResize();

    showTyping();

    try{

        const historyForServer = messages
            .slice(-20)
            .map(x => ({
                role:
                    x.role === "user"
                        ? "user"
                        : "model",
                text:x.text
            }));

        const response = await fetch("/api/chat", {

            method:"POST",

            headers:{
                "Content-Type":"application/json"
            },

            body:JSON.stringify({
                message:text,
                history:historyForServer
            })

        });

        const data = await response.json();

        removeTyping();

        if(!response.ok || !data.ok){

            throw new Error(
                data.error || "Server error"
            );

        }

        addMessage("model", data.answer);

        saveHistory();

        if(continuousVoice){

            speakText(data.answer);

        }

    }catch(error){

        removeTyping();

        addMessage(
            "model",
            "بښنه، د AI خدمت سره اړیکه کې ستونزه راغله.\n\n" +
            "تفصیل: " +
            (error.message || "Unknown error")
        );

    }
}


/* ==========================================================
   HISTORY
========================================================== */

function saveHistory(){

    if(!messages.length){
        return;
    }

    const firstUser =
        messages.find(x => x.role === "user");

    if(!firstUser){
        return;
    }

    const item = {
        id:Date.now(),
        title:firstUser.text.slice(0,80),
        date:new Date().toLocaleString(),
        messages:messages.slice()
    };

    historyItems.unshift(item);

    historyItems =
        historyItems.slice(0,100);

    localStorage.setItem(
        "medai_history",
        JSON.stringify(historyItems)
    );
}


function openHistory(){

    const items = historyItems;

    let body = "";

    if(!items.length){

        body =
            '<div class="empty">تر اوسه history نشته.</div>';

    }else{

        body =
            '<div class="list">';

        items.forEach(item => {

            const div =
                document.createElement("div");

            div.className = "list-item";

            const left =
                document.createElement("div");

            left.innerHTML =
                "<strong>" +
                escapeHtml(item.title) +
                "</strong><br>" +
                "<small>" +
                escapeHtml(item.date) +
                "</small>";

            const load =
                document.createElement("button");

            load.className = "small-btn";
            load.textContent = "Open";

            load.onclick = () => loadHistory(item.id);

            div.appendChild(left);
            div.appendChild(load);

            document.body.appendChild(div);

            body += div.outerHTML;

            div.remove();

        });

        body += "</div>";

        body +=
            '<br><button class="danger-btn" onclick="clearHistory()">Clear History</button>';
    }

    openModal(
        "History",
        body
    );
}


function loadHistory(id){

    const item =
        historyItems.find(x => x.id === id);

    if(!item){
        return;
    }

    newChat(false);

    messages = item.messages.slice();

    messages.forEach(m => {

        addMessage(
            m.role === "user" ? "user" : "model",
            m.text,
            false
        );

    });

    closeModal();

    showToast("History خلاص شو.");
}


function clearHistory(){

    historyItems = [];

    localStorage.removeItem("medai_history");

    closeModal();

    showToast("History پاک شو.");
}


function exportHistory(){

    const data =
        historyItems
            .map(item =>
                "\n" +
                item.date +
                "\n" +
                item.title +
                "\n" +
                item.messages
                    .map(m =>
                        (m.role === "user" ? "User: " : "MedAI: ") +
                        m.text
                    )
                    .join("\n")
            )
            .join("\n\n--------------------\n\n");

    const blob =
        new Blob(
            [data || "No history"],
            {type:"text/plain;charset=utf-8"}
        );

    const url =
        URL.createObjectURL(blob);

    const a =
        document.createElement("a");

    a.href = url;
    a.download = "medai-history.txt";

    a.click();

    URL.revokeObjectURL(url);
}


/* ==========================================================
   FAVORITES
========================================================== */

function toggleFavorite(text, button){

    const index =
        favorites.indexOf(text);

    if(index >= 0){

        favorites.splice(index,1);

        if(button){
            button.textContent = "☆ Favorite";
        }

        showToast("Favorite حذف شو.");

    }else{

        favorites.unshift(text);

        if(button){
            button.textContent = "★ Saved";
        }

        showToast("Favorite ته اضافه شو.");

    }

    localStorage.setItem(
        "medai_favorites",
        JSON.stringify(favorites)
    );
}


function openFavorites(){

    let body = "";

    if(!favorites.length){

        body =
            '<div class="empty">تر اوسه favorites نشته.</div>';

    }else{

        body = '<div class="list">';

        favorites.forEach((text,index) => {

            body +=
                '<div class="list-item">' +
                '<div>' +
                escapeHtml(text).replace(/\n/g,"<br>") +
                '</div>' +
                '<button class="danger-btn" onclick="removeFavorite(' +
                index +
                ')">حذف</button>' +
                '</div>';

        });

        body += "</div>";
    }

    openModal(
        "Favorites",
        body
    );
}


function removeFavorite(index){

    favorites.splice(index,1);

    localStorage.setItem(
        "medai_favorites",
        JSON.stringify(favorites)
    );

    openFavorites();
}


/* ==========================================================
   TRACKER
========================================================== */

function openTracker(){

    let rows = "";

    tracker.slice().reverse().forEach(item => {

        rows +=
            '<div class="list-item">' +
            '<div>' +
            "<strong>" +
            escapeHtml(item.date) +
            "</strong><br>" +
            escapeHtml(item.value) +
            "</div>" +
            "</div>";

    });

    openModal(
        "Health Tracker",
        `
        <form class="form" onsubmit="saveTracker(event)">
            <input
                id="trackerValue"
                placeholder="مثلاً: BP 120/80, Pulse 72, Weight 70kg"
                required
            >

            <button class="primary-btn">
                Save Health Record
            </button>
        </form>

        <br>

        <div class="list">
            ${rows || '<div class="empty">تر اوسه record نشته.</div>'}
        </div>
        `
    );
}


function saveTracker(event){

    event.preventDefault();

    const value =
        document.getElementById("trackerValue").value.trim();

    if(!value){
        return;
    }

    tracker.push({
        date:new Date().toLocaleString(),
        value:value
    });

    tracker =
        tracker.slice(-200);

    localStorage.setItem(
        "medai_tracker",
        JSON.stringify(tracker)
    );

    openTracker();

    showToast("Health record خوندي شو.");
}


/* ==========================================================
   REMINDERS
========================================================== */

function openReminders(){

    let rows = "";

    reminders.forEach((item,index) => {

        rows +=
            '<div class="list-item">' +
            '<div>' +
            "<strong>" +
            escapeHtml(item.name) +
            "</strong><br>" +
            "<small>" +
            escapeHtml(item.time) +
            "</small>" +
            "</div>" +
            '<button class="danger-btn" onclick="deleteReminder(' +
            index +
            ')">حذف</button>' +
            '</div>';

    });

    openModal(
        "Medicine Reminders",
        `
        <form class="form" onsubmit="saveReminder(event)">
            <input id="reminderName" placeholder="د درمل نوم" required>
            <input id="reminderTime" type="time" required>
            <button class="primary-btn">
                Add Reminder
            </button>
        </form>

        <br>

        <div class="list">
            ${
                rows ||
                '<div class="empty">تر اوسه reminder نشته.</div>'
            }
        </div>

        <br>

        <small style="color:var(--muted)">
            یادونه: دا reminder یوازې هغه وخت notification ورکوي چې
            پاڼه خلاصه وي او browser notification اجازه ولري.
        </small>
        `
    );
}


function saveReminder(event){

    event.preventDefault();

    const name =
        document.getElementById("reminderName").value.trim();

    const time =
        document.getElementById("reminderTime").value;

    if(!name || !time){
        return;
    }

    reminders.push({
        name:name,
        time:time,
        lastAlert:""
    });

    localStorage.setItem(
        "medai_reminders",
        JSON.stringify(reminders)
    );

    if("Notification" in window &&
       Notification.permission === "default"){

        Notification.requestPermission();

    }

    openReminders();

    showToast("Reminder اضافه شو.");
}


function deleteReminder(index){

    reminders.splice(index,1);

    localStorage.setItem(
        "medai_reminders",
        JSON.stringify(reminders)
    );

    openReminders();
}


function checkReminders(){

    const now =
        new Date();

    const current =
        String(now.getHours()).padStart(2,"0") +
        ":" +
        String(now.getMinutes()).padStart(2,"0");

    const dateKey =
        now.toDateString();

    let changed = false;

    reminders.forEach(item => {

        if(
            item.time === current &&
            item.lastAlert !== dateKey
        ){

            item.lastAlert = dateKey;
            changed = true;

            showToast(
                "💊 د درملو وخت: " + item.name
            );

            if(
                "Notification" in window &&
                Notification.permission === "granted"
            ){

                new Notification(
                    "MedAI Medicine Reminder",
                    {
                        body:"د درملو وخت: " + item.name
                    }
                );

            }

        }

    });

    if(changed){

        localStorage.setItem(
            "medai_reminders",
            JSON.stringify(reminders)
        );

    }
}


/* ==========================================================
   VOICE INPUT
========================================================== */

function setupRecognition(){

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if(!SpeechRecognition){

        showToast(
            "ستاسو browser voice input نه ملاتړ کوي."
        );

        return null;
    }

    const r =
        new SpeechRecognition();

    r.lang = "ps-AF";

    r.interimResults = true;
    r.continuous = continuousVoice;

    r.onstart = () => {

        recording = true;

        document
            .getElementById("voiceBtn")
            .classList.add("recording");

    };

    r.onresult = event => {

        let transcript = "";

        for(
            let i = event.resultIndex;
            i < event.results.length;
            i++
        ){

            transcript +=
                event.results[i][0].transcript;

        }

        messageBox.value = transcript;

        autoResize();

    };

    r.onerror = event => {

        recording = false;

        document
            .getElementById("voiceBtn")
            .classList.remove("recording");

        showToast(
            "Voice error: " +
            event.error
        );

    };

    r.onend = () => {

        recording = false;

        document
            .getElementById("voiceBtn")
            .classList.remove("recording");

        if(
            continuousVoice &&
            messageBox.value.trim()
        ){

            sendMessage();

        }

        if(continuousVoice){

            setTimeout(() => {

                if(continuousVoice){

                    try{

                        recognition.start();

                    }catch(e){}

                }

            },700);

        }

    };

    return r;
}


function toggleVoice(){

    if(!recognition){

        recognition =
            setupRecognition();

        if(!recognition){
            return;
        }

    }

    if(recording){

        try{
            recognition.stop();
        }catch(e){}

        return;
    }

    continuousVoice = false;

    try{
        recognition.start();
    }catch(e){}

}


/* ==========================================================
   CONTINUOUS VOICE
========================================================== */

function startContinuousVoice(){

    continuousVoice = true;

    if(!recognition){
        recognition = setupRecognition();
    }

    if(!recognition){
        continuousVoice = false;
        return;
    }

    try{
        recognition.start();
    }catch(e){}

    showToast(
        "Continuous voice فعال شو."
    );
}


/* ==========================================================
   TEXT TO SPEECH
========================================================== */

function speakText(text){

    if(!("speechSynthesis" in window)){

        showToast(
            "ستاسو browser text-to-speech نه ملاتړ کوي."
        );

        return;
    }

    window.speechSynthesis.cancel();

    const utterance =
        new SpeechSynthesisUtterance(text);

    utterance.lang = "ps-AF";
    utterance.rate = 0.9;

    window.speechSynthesis.speak(
        utterance
    );
}


/* ==========================================================
   MODAL
========================================================== */

function openModal(title, body){

    document.getElementById("modalTitle").textContent =
        title;

    document.getElementById("modalBody").innerHTML =
        body;

    document.getElementById("modal").classList.add("show");
}


function closeModal(){

    document.getElementById("modal").classList.remove("show");
}


document.getElementById("modal").addEventListener(
    "click",
    function(event){

        if(event.target === this){
            closeModal();
        }

    }
);


/* ==========================================================
   NEW CHAT
========================================================== */

function newChat(show=true){

    messages = [];

    chat.innerHTML =
        `
        <div class="empty" id="emptyState">
            👋 سلام! زه MedAI یم.<br>
            خپله طبي پوښتنه ولیکئ یا له tools څخه یو انتخاب کړئ.
        </div>
        `;

    if(show){
        showToast("نوی chat جوړ شو.");
    }

}


/* ==========================================================
   HTML ESCAPE
========================================================== */

function escapeHtml(value){

    return String(value)
        .replace(/&/g,"&amp;")
        .replace(/</g,"&lt;")
        .replace(/>/g,"&gt;")
        .replace(/"/g,"&quot;")
        .replace(/'/g,"&#039;");

}


/* ==========================================================
   EXTRA KEYBOARD SHORTCUT
========================================================== */

document.addEventListener(
    "keydown",
    function(event){

        if(
            (event.ctrlKey || event.metaKey) &&
            event.key.toLowerCase() === "k"
        ){

            event.preventDefault();

            messageBox.focus();

        }

        if(event.key === "Escape"){

            closeModal();
            closeSidebar();

        }

    }
);


/* ==========================================================
   PROFILE / LOCAL DATA INFO
========================================================== */

function openLocalProfile(){

    openModal(
        "Local Profile",
        `
        <div class="form">

            <input
                id="profileName"
                placeholder="ستاسو نوم"
                value="${escapeHtml(
                    localStorage.getItem("medai_profile_name") || ""
                )}"
            >

            <button class="primary-btn"
                onclick="saveLocalProfile()">
                Save
            </button>

        </div>

        <br>

        <small style="color:var(--muted)">
            دا local profile یوازې په همدې browser کې ساتل کېږي.
            دا cloud login یا secure medical account نه دی.
        </small>
        `
    );
}


function saveLocalProfile(){

    const name =
        document.getElementById("profileName").value.trim();

    localStorage.setItem(
        "medai_profile_name",
        name
    );

    closeModal();

    showToast("Profile خوندي شو.");
}


/* ==========================================================
   INITIAL TOOL
========================================================== */

selectTool(
    "AI Medical Chat",
    ""
);

</script>

</body>
</html>
"""


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )

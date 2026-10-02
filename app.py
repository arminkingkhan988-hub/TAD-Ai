from flask import Flask, request, jsonify, render_template_string
import os
import requests

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

HTML = """<!doctype html>
<html lang="ps" dir="rtl">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>MedAI</title>
    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f4f7fb;
            color: #172033;
        }

        header {
            background: #0b6bcb;
            color: white;
            padding: 18px;
            text-align: center;
        }

        main {
            max-width: 900px;
            margin: auto;
            padding: 16px;
        }

        .card {
            background: white;
            border-radius: 16px;
            padding: 16px;
            margin: 12px 0;
            box-shadow: 0 3px 14px #0001;
        }

        textarea,
        input,
        button {
            font: inherit;
        }

        textarea,
        input {
            width: 100%;
            box-sizing: border-box;
            padding: 12px;
            border: 1px solid #ccd5e0;
            border-radius: 10px;
            margin: 6px 0;
        }

        button {
            border: 0;
            border-radius: 10px;
            padding: 11px 15px;
            background: #0b6bcb;
            color: white;
            cursor: pointer;
            margin: 4px;
        }

        button:hover {
            opacity: 0.9;
        }

        #answer {
            white-space: pre-wrap;
            line-height: 1.8;
        }

        .small {
            color: #667085;
            font-size: 13px;
        }
    </style>
</head>

<body>

<header>
    <h1>MedAI 🩺</h1>
    <div>ستاسو طبي AI مرستیال</div>
</header>

<main>

    <div class="card">
        <h2>AI Chat</h2>

        <textarea
            id="q"
            rows="5"
            placeholder="خپله طبي پوښتنه ولیکئ..."
        ></textarea>

        <button onclick="chat()">پوښتنه واستوئ</button>
        <button onclick="speak()">🔊 ځواب واورئ</button>

        <div id="status" class="small"></div>
    </div>

    <div class="card">
        <h2>ځواب</h2>
        <div id="answer">دلته به ځواب ښکاره شي.</div>
    </div>

    <div class="card">
        <h2>د نښو معلومات</h2>

        <input
            id="sym"
            placeholder="مثلاً: تبه، ټوخی، د سینې درد"
        >

        <button onclick="tool('symptoms', document.getElementById('sym').value)">
            تحلیل
        </button>
    </div>

    <div class="card">
        <h2>بیړنی حالت</h2>

        <input
            id="em"
            placeholder="خپل حالت ولیکئ"
        >

        <button onclick="tool('emergency', document.getElementById('em').value)">
            بیړنی ارزونه
        </button>

        <p class="small">
            دا وسیله تشخیص نه کوي.
            د سخت یا ناڅاپي حالت پر مهال بیړنۍ طبي مرسته وغواړئ.
        </p>
    </div>

</main>

<script>
async function chat() {
    const q = document.getElementById("q").value.trim();

    if (!q) {
        return;
    }

    document.getElementById("status").textContent = "AI کار کوي...";

    try {
        const r = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: q
            })
        });

        const d = await r.json();

        document.getElementById("answer").textContent =
            d.answer || d.error || "خطا";

    } catch (error) {
        document.getElementById("answer").textContent =
            "د سرور سره د اړیکې خطا.";
    }

    document.getElementById("status").textContent = "";
}

async function tool(type, value) {
    if (!value.trim()) {
        return;
    }

    try {
        const r = await fetch("/tool", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                type: type,
                text: value
            })
        });

        const d = await r.json();

        document.getElementById("answer").textContent =
            d.answer || d.error || "خطا";

    } catch (error) {
        document.getElementById("answer").textContent =
            "د سرور سره د اړیکې خطا.";
    }
}

function speak() {
    const text = document.getElementById("answer").textContent;

    if ("speechSynthesis" in window) {
        speechSynthesis.cancel();

        const utterance =
            new SpeechSynthesisUtterance(text);

        utterance.lang = "ps-AF";

        speechSynthesis.speak(utterance);
    }
}
</script>

</body>
</html>
"""


SYSTEM = """ته MedAI طبي معلوماتي مرستیال یې.
په ساده پښتو ځواب ورکړه.

تشخیص په قطعي ډول مه کوه.
د خطرناکو نښو په صورت کې بیړنۍ طبي مرسته سپارښتنه کړه.

د درملو دوز مه ټاکه مګر که کاروونکي مشخص درمل او د معتبرې طبي سرچینې معلومات وغواړي؛
تل د ډاکټر یا فارماسسټ مشوره مهمه وښیه.

ځواب منظم، لنډ او واضح وساته.
"""


def ask_gemini(prompt):
    if not GEMINI_API_KEY:
        return (
            "GEMINI_API_KEY په Vercel Environment Variables "
            "کې نه دی ټاکل شوی."
        )

    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/{GEMINI_MODEL}:generateContent"
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": SYSTEM + "\n\n" + prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1200
        }
    }

    try:
        response = requests.post(
            url,
            params={"key": GEMINI_API_KEY},
            json=payload,
            timeout=30
        )

        data = response.json()

        if response.status_code != 200:
            error = data.get("error", {})
            message = error.get(
                "message",
                response.text
            )

            return f"Gemini خطا: {message}"

        candidates = data.get("candidates", [])

        if not candidates:
            return "Gemini هېڅ ځواب رانه کړ."

        parts = (
            candidates[0]
            .get("content", {})
            .get("parts", [])
        )

        if not parts:
            return "د Gemini ځواب تش دی."

        return parts[0].get(
            "text",
            "د Gemini ځواب ترلاسه نه شو."
        )

    except requests.RequestException as error:
        return f"د AI سره د اړیکې خطا: {error}"

    except Exception as error:
        return f"ناڅرګنده خطا: {error}"


@app.get("/")
def index():
    return render_template_string(HTML)


@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "service": "MedAI"
    })


@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}

    message = str(
        data.get("message", "")
    ).strip()

    if not message:
        return jsonify({
            "error": "پوښتنه تشه ده."
        }), 400

    answer = ask_gemini(message)

    return jsonify({
        "answer": answer
    })


@app.post("/tool")
def tool():
    data = request.get_json(silent=True) or {}

    kind = str(
        data.get("type", "")
    ).strip()

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return jsonify({
            "error": "معلومات داخل کړئ."
        }), 400

    prompts = {
        "symptoms": (
            "د لاندې نښو په اړه تعلیمي معلومات ورکړه. "
            "ممکن عام علتونه، خطرناکې نښې، "
            "او کله ډاکټر ته تګ مهم دی واضح کړه:\n\n"
            f"{text}"
        ),

        "emergency": (
            "دا حالت د بیړني خطر له نظره تشریح کړه. "
            "که کومه نښه سمدستي بیړنۍ مرستې ته اړتیا لري، "
            "واضح یې ووایه:\n\n"
            f"{text}"
        )
    }

    prompt = prompts.get(
        kind,
        text
    )

    answer = ask_gemini(prompt)

    return jsonify({
        "answer": answer
    })


if __name__ == "__main__":
    port = int(
        os.environ.get(
            "PORT",
            "5000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )

from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/gemini-3.5-flash-lite:generateContent"
)

WIKIMEDIA_URL = "https://commons.wikimedia.org/w/api.php"


# =========================================================
# GEMINI
# =========================================================

def ask_gemini(prompt):
    if not GEMINI_API_KEY:
        return "GEMINI_API_KEY نه دی تنظیم شوی."

    try:
        response = requests.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ]
            },
            timeout=60
        )

        if response.status_code != 200:
            return "د AI سره د اړیکې پر مهال ستونزه رامنځته شوه."

        data = response.json()
        candidates = data.get("candidates", [])

        if not candidates:
            return "AI ځواب ورنه کړ."

        parts = candidates[0].get("content", {}).get("parts", [])

        for part in parts:
            if part.get("text"):
                return part["text"]

        return "AI ځواب خالي دی."

    except requests.exceptions.Timeout:
        return "د AI ځواب ډېر وخت ونیو. بیا هڅه وکړئ."

    except Exception as error:
        return "د AI سره د اړیکې پر مهال ستونزه رامنځته شوه."


def build_prompt(instruction, user_text):
    return f"""
You are MedAI, an educational medical information assistant.

RULES:
- Answer in the SAME LANGUAGE as the user's question.
- Use simple language.
- Provide educational information only.
- Do not diagnose from symptoms alone.
- Do not claim to examine the patient.
- Do not invent facts.
- Do not provide personalized prescription or medication dosing.
- Do not tell users to start, stop, or change prescription medicines.
- If emergency warning signs are present, advise urgent professional medical care.
- Do not replace a doctor or other qualified healthcare professional.

TASK:
{instruction}

USER INFORMATION:
{user_text}
"""


# =========================================================
# WIKIMEDIA IMAGES
# =========================================================

def get_medical_images(query):
    try:
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query + " medical",
            "gsrnamespace": 6,
            "gsrlimit": 8,
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": 600
        }

        headers = {
            "User-Agent": "MedAI/1.0"
        }

        response = requests.get(
            WIKIMEDIA_URL,
            params=params,
            headers=headers,
            timeout=20
        )

        if response.status_code != 200:
            return []

        data = response.json()
        pages = data.get("query", {}).get("pages", {})

        images = []

        for page in pages.values():
            info = page.get("imageinfo", [])

            if not info:
                continue

            image_url = info[0].get("thumburl") or info[0].get("url")

            if image_url:
                images.append({
                    "url": image_url,
                    "title": page.get("title", "Medical Image")
                })

        return images

    except Exception:
        return []


# =========================================================
# HTML
# =========================================================

HTML = r"""
<!DOCTYPE html>
<html lang="ps" dir="rtl">

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
    font-family: Arial, Tahoma, sans-serif;
    background: #f3f6fa;
    color: #172033;
    transition: .3s;
}

body.dark {
    background: #0f172a;
    color: #f8fafc;
}

header {
    background: linear-gradient(135deg,#087f8c,#0b5ed7);
    color: white;
    text-align: center;
    padding: 25px 15px;
}

header h1 {
    margin: 0;
    font-size: 34px;
}

header p {
    margin: 8px 0 15px;
}

.container {
    max-width: 1100px;
    margin: auto;
    padding: 20px;
}

.card {
    background: white;
    padding: 20px;
    margin-bottom: 20px;
    border-radius: 18px;
    box-shadow: 0 5px 20px rgba(0,0,0,.08);
}

.dark .card {
    background: #1e293b;
}

.card h2 {
    margin-top: 0;
    color: #075985;
}

.dark .card h2 {
    color: #67e8f9;
}

textarea,
input,
select {
    width: 100%;
    padding: 13px;
    border: 1px solid #cbd5e1;
    border-radius: 11px;
    font-size: 16px;
    margin: 7px 0 12px;
}

.dark textarea,
.dark input,
.dark select {
    background: #0f172a;
    color: white;
    border-color: #475569;
}

button {
    width: 100%;
    border: 0;
    border-radius: 11px;
    padding: 13px;
    margin: 5px 0;
    background: #087f8c;
    color: white;
    font-size: 16px;
    cursor: pointer;
}

button:hover {
    opacity: .9;
}

.secondary {
    background: #64748b;
}

.danger {
    background: #b91c1c;
}

.success {
    background: #15803d;
}

.warning {
    background: #b45309;
}

.top-buttons {
    display: flex;
    justify-content: center;
    gap: 8px;
    flex-wrap: wrap;
}

.top-buttons button {
    width: auto;
    padding: 10px 15px;
    background: white;
    color: #075985;
}

.topics {
    display: grid;
    grid-template-columns: repeat(4,1fr);
    gap: 8px;
}

.result {
    margin-top: 12px;
    padding: 15px;
    background: #f8fafc;
    border-radius: 12px;
    line-height: 1.9;
    white-space: pre-wrap;
}

.dark .result {
    background: #0f172a;
}

.loading {
    display: none;
    text-align: center;
    padding: 10px;
    color: #087f8c;
    font-weight: bold;
}

.images {
    display: grid;
    grid-template-columns: repeat(4,1fr);
    gap: 12px;
}

.images img {
    width: 100%;
    height: 180px;
    object-fit: cover;
    border-radius: 12px;
}

.history-item,
.favorite-item,
.tracker-item,
.reminder-item {
    padding: 12px;
    margin: 8px 0;
    border-radius: 10px;
    background: #eef2f7;
}

.dark .history-item,
.dark .favorite-item,
.dark .tracker-item,
.dark .reminder-item {
    background: #0f172a;
}

.small {
    color: #64748b;
    font-size: 13px;
}

.dark .small {
    color: #94a3b8;
}

footer {
    text-align: center;
    padding: 30px;
    color: #64748b;
}

@media(max-width:800px) {
    .topics,
    .images {
        grid-template-columns: repeat(2,1fr);
    }
}

@media(max-width:500px) {
    .container {
        padding: 10px;
    }

    .card {
        padding: 15px;
    }

    .topics,
    .images {
        grid-template-columns: 1fr;
    }

    header h1 {
        font-size: 28px;
    }
}

</style>

</head>

<body>

<header>

<h1>🩺 MedAI</h1>

<p>ستاسو هوښیار طبي معلوماتي مرستیال</p>

<div class="top-buttons">

<button onclick="toggleDark()">🌙 Dark Mode</button>

<button onclick="startVoice()">🎤 Voice</button>

<button onclick="stopVoice()">⏹️ Stop</button>

</div>

</header>


<div class="container">


<!-- MAIN AI -->

<div class="card">

<h2>🤖 Medical AI Chat</h2>

<textarea id="question"
rows="5"
placeholder="خپله طبي پوښتنه ولیکئ..."></textarea>

<button onclick="askAI()">🤖 له MedAI څخه پوښتنه</button>

<button class="secondary" onclick="speakAnswer()">🔊 ځواب واورئ</button>

<div id="mainLoading" class="loading">AI کار کوي...</div>

<div id="answer" class="result"></div>

</div>


<!-- TOPICS -->

<div class="card">

<h2>🩺 Medical Topics</h2>

<div class="topics">

<button onclick="setTopic('Diabetes')">🩸 Diabetes</button>
<button onclick="setTopic('Hypertension')">❤️ فشار</button>
<button onclick="setTopic('Heart Disease')">❤️ زړه</button>
<button onclick="setTopic('Asthma')">🫁 Asthma</button>
<button onclick="setTopic('Cancer')">🧬 Cancer</button>
<button onclick="setTopic('Kidney Disease')">🫘 Kidney</button>
<button onclick="setTopic('Liver Disease')">🧫 Liver</button>
<button onclick="setTopic('Infection')">🦠 Infection</button>

</div>

</div>


<!-- SYMPTOMS -->

<div class="card">

<h2>🧠 Symptom Education</h2>

<textarea id="symptomsInput"
rows="4"
placeholder="مثلاً: تبه، ټوخی، ستونی درد..."></textarea>

<button onclick="special('/symptoms','symptomsInput','symptomsResult','symptomsLoading')">
🧠 نښې تشریح کړه
</button>

<div id="symptomsLoading" class="loading">AI کار کوي...</div>
<div id="symptomsResult" class="result"></div>

</div>


<!-- VITALS -->

<div class="card">

<h2>❤️ Vital Signs Guide</h2>

<textarea id="vitalsInput"
rows="4"
placeholder="مثلاً Blood Pressure 140/90, pulse 85..."></textarea>

<button onclick="special('/vitals','vitalsInput','vitalsResult','vitalsLoading')">
❤️ حیاتي نښې تشریح کړه
</button>

<div id="vitalsLoading" class="loading">AI کار کوي...</div>
<div id="vitalsResult" class="result"></div>

</div>


<!-- COMPARISON -->

<div class="card">

<h2>⚖️ Disease Comparison</h2>

<input id="disease1" placeholder="لومړۍ ناروغي">
<input id="disease2" placeholder="دوهمه ناروغي">

<button onclick="compare()">⚖️ پرتله یې کړه</button>

<div id="compareLoading" class="loading">AI کار کوي...</div>
<div id="compareResult" class="result"></div>

</div>


<!-- DOCTOR -->

<div class="card">

<h2>👨‍⚕️ Doctor Visit Assistant</h2>

<textarea id="doctorInput"
rows="6"
placeholder="خپلې نښې، د پیل وخت، درمل او ټیسټونه ولیکئ..."></textarea>

<button onclick="special('/doctor','doctorInput','doctorResult','doctorLoading')">
👨‍⚕️ معلومات منظم کړه
</button>

<div id="doctorLoading" class="loading">AI کار کوي...</div>
<div id="doctorResult" class="result"></div>

</div>


<!-- LAB -->

<div class="card">

<h2>🧪 Lab Report Explainer</h2>

<textarea id="labInput"
rows="6"
placeholder="د لابراتوار راپور یا ټیسټ ولیکئ..."></textarea>

<button onclick="special('/lab','labInput','labResult','labLoading')">
🧪 راپور تشریح کړه
</button>

<div id="labLoading" class="loading">AI کار کوي...</div>
<div id="labResult" class="result"></div>

</div>


<!-- MEDICINE -->

<div class="card">

<h2>💊 Medicine Information</h2>

<textarea id="medicineInput"
rows="4"
placeholder="د درملو نوم ولیکئ..."></textarea>

<button onclick="special('/medicine','medicineInput','medicineResult','medicineLoading')">
💊 معلومات
</button>

<div id="medicineLoading" class="loading">AI کار کوي...</div>
<div id="medicineResult" class="result"></div>

</div>


<!-- DICTIONARY -->

<div class="card">

<h2>📖 Medical Dictionary</h2>

<input id="dictionaryInput"
placeholder="مثلاً Hypertension">

<button onclick="special('/dictionary','dictionaryInput','dictionaryResult','dictionaryLoading')">
📖 تشریح
</button>

<div id="dictionaryLoading" class="loading">AI کار کوي...</div>
<div id="dictionaryResult" class="result"></div>

</div>


<!-- EMERGENCY -->

<div class="card">

<h2>🚨 Emergency Checker</h2>

<textarea id="emergencyInput"
rows="4"
placeholder="عمومي نښې ولیکئ..."></textarea>

<button class="danger"
onclick="special('/emergency','emergencyInput','emergencyResult','emergencyLoading')">
🚨 بیړنۍ نښې وګوره
</button>

<div id="emergencyLoading" class="loading">AI کار کوي...</div>
<div id="emergencyResult" class="result"></div>

</div>


<!-- MEDICAL SEARCH -->

<div class="card">

<h2>🔎 Medical Search</h2>

<input id="searchInput"
placeholder="طبي موضوع ولټوئ...">

<button onclick="medicalSearch()">🔎 Search</button>

<div id="searchResult" class="result"></div>

</div>


<!-- IMAGES -->

<div class="card">

<h2>🖼️ Medical Images</h2>

<input id="imageInput"
placeholder="مثلاً human heart">

<button onclick="loadImages()">🖼️ انځورونه</button>

<div id="imageLoading" class="loading">انځورونه لټول کېږي...</div>

<div id="images" class="images"></div>

</div>


<!-- INTERACTION -->

<div class="card">

<h2>💊 Medicine Interaction Checker</h2>

<textarea id="interactionInput"
rows="4"
placeholder="د دوو یا څو درملو نومونه ولیکئ..."></textarea>

<button onclick="special('/interaction','interactionInput','interactionResult','interactionLoading')">
💊 تداخل وګوره
</button>

<div id="interactionLoading" class="loading">AI کار کوي...</div>
<div id="interactionResult" class="result"></div>

</div>


<!-- REPORT -->

<div class="card">

<h2>📄 Medical Report Explainer</h2>

<textarea id="reportInput"
rows="7"
placeholder="د طبي راپور متن ولیکئ..."></textarea>

<button onclick="special('/report','reportInput','reportResult','reportLoading')">
📄 راپور تشریح کړه
</button>

<div id="reportLoading" class="loading">AI کار کوي...</div>
<div id="reportResult" class="result"></div>

</div>


<!-- FIRST AID -->

<div class="card">

<h2>🩹 First Aid Guide</h2>

<input id="firstAidInput"
placeholder="مثلاً minor burn, cut, nosebleed">

<button onclick="special('/firstaid','firstAidInput','firstAidResult','firstAidLoading')">
🩹 لومړنۍ مرسته
</button>

<div id="firstAidLoading" class="loading">AI کار کوي...</div>
<div id="firstAidResult" class="result"></div>

</div>


<!-- GLOSSARY -->

<div class="card">

<h2>🧬 Medical Glossary</h2>

<textarea id="glossaryInput"
rows="4"
placeholder="یو یا څو طبي اصطلاحات..."></textarea>

<button onclick="special('/glossary','glossaryInput','glossaryResult','glossaryLoading')">
🧬 ساده تشریح
</button>

<div id="glossaryLoading" class="loading">AI کار کوي...</div>
<div id="glossaryResult" class="result"></div>

</div>


<!-- QUIZ -->

<div class="card">

<h2>🧠 Medical Quiz</h2>

<button onclick="quiz()">🧠 Quiz جوړ کړه</button>

<div id="quizLoading" class="loading">AI کار کوي...</div>
<div id="quizResult" class="result"></div>

</div>


<!-- =====================================================
     NEW FEATURE 1
===================================================== -->

<div class="card">

<h2>🧠 Medical Risk Assessment</h2>

<textarea id="riskInput"
rows="6"
placeholder="خپلې نښې، عمر، د ستونزې موده او نور اړوند معلومات ولیکئ..."></textarea>

<button class="warning"
onclick="special('/risk','riskInput','riskResult','riskLoading')">
🧠 د خطر نښې وڅېړه
</button>

<div id="riskLoading" class="loading">AI کار کوي...</div>
<div id="riskResult" class="result"></div>

</div>


<!-- =====================================================
     NEW FEATURE 2
===================================================== -->

<div class="card">

<h2>⏰ Medication Reminder</h2>

<input id="reminderMedicine"
placeholder="د درملو نوم">

<input id="reminderTime"
type="time">

<input id="reminderNote"
placeholder="یادونه، مثلاً: سهار">

<button onclick="addReminder()">
⏰ Reminder اضافه کړه
</button>

<div id="reminders"></div>

</div>


<!-- =====================================================
     NEW FEATURE 3
===================================================== -->

<div class="card">

<h2>🩸 Health Tracker</h2>

<select id="trackerType">

<option value="Blood Pressure">Blood Pressure</option>
<option value="Pulse">Pulse</option>
<option value="Temperature">Temperature</option>
<option value="Weight">Weight</option>
<option value="Blood Sugar">Blood Sugar</option>
<option value="Oxygen">Oxygen</option>

</select>

<input id="trackerValue"
placeholder="Value، مثلاً 120/80">

<input id="trackerNote"
placeholder="یادونه">

<button onclick="addTracker()">
🩸 معلومات ثبت کړه
</button>

<div id="trackerList"></div>

<button class="danger" onclick="clearTracker()">
ټول Tracker پاک کړه
</button>

</div>


<!-- =====================================================
     NEW FEATURE 4
===================================================== -->

<div class="card">

<h2>📊 Health Report Generator</h2>

<textarea id="healthReportInput"
rows="7"
placeholder="خپل Health Tracker معلومات، نښې او نور معلومات ولیکئ..."></textarea>

<button onclick="generateHealthReport()">
📊 روغتیايي راپور جوړ کړه
</button>

<div id="healthReportLoading" class="loading">
AI کار کوي...
</div>

<div id="healthReportResult" class="result"></div>

</div>


<!-- HISTORY -->

<div class="card">

<h2>🕘 History</h2>

<div id="history"></div>

<button class="danger" onclick="clearHistory()">
History پاک کړه
</button>

</div>


<!-- FAVORITES -->

<div class="card">

<h2>⭐ Favorites</h2>

<div id="favorites"></div>

<button class="danger" onclick="clearFavorites()">
Favorites پاک کړه
</button>

</div>


</div>


<footer>
MedAI — Educational Medical AI
</footer>


<script>

let currentAnswer = "";
let recognition = null;


/* =====================================================
   HELPERS
===================================================== */

function loading(id, show) {

    const el = document.getElementById(id);

    if (el) {
        el.style.display = show ? "block" : "none";
    }

}


function escapeHTML(text) {

    const div = document.createElement("div");

    div.textContent = text;

    return div.innerHTML;

}


/* =====================================================
   MAIN AI
===================================================== */

async function askAI() {

    const question =
        document.getElementById("question").value.trim();

    const answer =
        document.getElementById("answer");

    if (!question) {

        answer.textContent =
            "مهرباني وکړئ پوښتنه ولیکئ.";

        return;
    }

    loading("mainLoading", true);

    answer.textContent = "";

    try {

        const response = await fetch("/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                question: question
            })

        });

        const data = await response.json();

        currentAnswer =
            data.answer || data.error || "";

        answer.textContent =
            currentAnswer;

        saveHistory(
            question,
            currentAnswer
        );

    } catch (error) {

        answer.textContent =
            "د سرور سره د اړیکې ستونزه.";

    } finally {

        loading("mainLoading", false);

    }

}


/* =====================================================
   SPECIAL REQUEST
===================================================== */

async function special(
    endpoint,
    inputId,
    resultId,
    loadingId
) {

    const input =
        document.getElementById(inputId);

    const result =
        document.getElementById(resultId);

    const text =
        input.value.trim();

    if (!text) {

        result.textContent =
            "مهرباني وکړئ معلومات ولیکئ.";

        return;
    }

    loading(loadingId, true);

    result.textContent = "";

    try {

        const response = await fetch(
            endpoint,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    text: text
                })
            }
        );

        const data =
            await response.json();

        result.textContent =
            data.answer ||
            data.error ||
            "ځواب ترلاسه نه شو.";

    } catch (error) {

        result.textContent =
            "د سرور سره د اړیکې ستونزه.";

    } finally {

        loading(loadingId, false);

    }

}


/* =====================================================
   COMPARISON
===================================================== */

async function compare() {

    const disease1 =
        document.getElementById("disease1")
        .value.trim();

    const disease2 =
        document.getElementById("disease2")
        .value.trim();

    const result =
        document.getElementById("compareResult");

    if (!disease1 || !disease2) {

        result.textContent =
            "دواړه ناروغۍ ولیکئ.";

        return;
    }

    loading("compareLoading", true);

    try {

        const response =
            await fetch("/compare", {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    disease1: disease1,
                    disease2: disease2
                })

            });

        const data =
            await response.json();

        result.textContent =
            data.answer ||
            data.error ||
            "ځواب ترلاسه نه شو.";

    } catch (error) {

        result.textContent =
            "د سرور ستونزه.";

    } finally {

        loading("compareLoading", false);

    }

}


/* =====================================================
   SEARCH
===================================================== */

async function medicalSearch() {

    const query =
        document.getElementById("searchInput")
        .value.trim();

    const result =
        document.getElementById("searchResult");

    if (!query) {

        result.textContent =
            "موضوع ولیکئ.";

        return;
    }

    result.textContent =
        "لټون کېږي...";

    try {

        const response =
            await fetch("/chat", {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    question:
                        "Give educational medical information about "
                        + query
                })

            });

        const data =
            await response.json();

        result.textContent =
            data.answer ||
            data.error ||
            "نتیجه پیدا نه شوه.";

    } catch (error) {

        result.textContent =
            "د لټون ستونزه.";

    }

}


/* =====================================================
   IMAGES
===================================================== */

async function loadImages() {

    const query =
        document.getElementById("imageInput")
        .value.trim();

    const container =
        document.getElementById("images");

    if (!query) {

        container.innerHTML =
            "<p>موضوع ولیکئ.</p>";

        return;
    }

    loading("imageLoading", true);

    container.innerHTML = "";

    try {

        const response =
            await fetch(
                "/images?q=" +
                encodeURIComponent(query)
            );

        const data =
            await response.json();

        if (!data.images ||
            data.images.length === 0) {

            container.innerHTML =
                "<p>انځورونه پیدا نه شول.</p>";

            return;
        }

        data.images.forEach(function(item) {

            const div =
                document.createElement("div");

            const img =
                document.createElement("img");

            img.src = item.url;

            img.alt = item.title;

            img.loading = "lazy";

            const title =
                document.createElement("div");

            title.className =
                "small";

            title.textContent =
                item.title;

            div.appendChild(img);

            div.appendChild(title);

            container.appendChild(div);

        });

    } catch (error) {

        container.innerHTML =
            "<p>د انځورونو ستونزه.</p>";

    } finally {

        loading("imageLoading", false);

    }

}


/* =====================================================
   QUIZ
===================================================== */

async function quiz() {

    const result =
        document.getElementById("quizResult");

    loading("quizLoading", true);

    try {

        const response =
            await fetch("/chat", {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    question:
                        "Create a 5-question educational medical quiz. "
                        + "Give four choices for each question and "
                        + "show the correct answer. "
                        + "Answer in the same language as the user."

                })

            });

        const data =
            await response.json();

        result.textContent =
            data.answer ||
            data.error ||
            "Quiz جوړ نه شو.";

    } catch (error) {

        result.textContent =
            "د Quiz ستونزه.";

    } finally {

        loading("quizLoading", false);

    }

}


/* =====================================================
   VOICE
===================================================== */

function startVoice() {

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if (!SpeechRecognition) {

        alert(
            "ستاسو browser Voice ملاتړ نه کوي."
        );

        return;
    }

    recognition =
        new SpeechRecognition();

    recognition.lang = "ps-AF";

    recognition.interimResults = false;

    recognition.continuous = false;

    recognition.onresult =
        function(event) {

            document.getElementById(
                "question"
            ).value =
                event.results[0][0]
                .transcript;

        };

    recognition.onerror =
        function() {

            alert(
                "Voice کې ستونزه رامنځته شوه."
            );

        };

    recognition.start();

}


function stopVoice() {

    if (recognition) {

        recognition.stop();

        recognition = null;

    }

    if ("speechSynthesis" in window) {

        speechSynthesis.cancel();

    }

}


function speakAnswer() {

    const text =
        currentAnswer ||
        document.getElementById(
            "answer"
        ).textContent;

    if (!text) {

        alert(
            "لومړی AI ځواب ترلاسه کړئ."
        );

        return;
    }

    if (!("speechSynthesis" in window)) {

        alert(
            "ستاسو browser Voice Output نه لري."
        );

        return;
    }

    speechSynthesis.cancel();

    const utterance =
        new SpeechSynthesisUtterance(text);

    utterance.lang = "ps-AF";

    utterance.rate = 0.9;

    speechSynthesis.speak(
        utterance
    );

}


/* =====================================================
   DARK MODE
===================================================== */

function toggleDark() {

    document.body.classList.toggle("dark");

    localStorage.setItem(
        "medai_dark",
        document.body.classList.contains("dark")
    );

}

if (
    localStorage.getItem("medai_dark")
    === "true"
) {
    document.body.classList.add("dark");
}


/* =====================================================
   TOPICS
===================================================== */

function setTopic(topic) {

    document.getElementById(
        "question"
    ).value =
        "د " +
        topic +
        " په اړه طبي معلومات راکړه.";

    document.getElementById(
        "question"
    ).focus();

}


/* =====================================================
   HISTORY
===================================================== */

function saveHistory(question, answer) {

    let items =
        JSON.parse(
            localStorage.getItem(
                "medai_history"
            ) || "[]"
        );

    items.unshift({

        question: question,

        answer: answer,

        time: new Date()
            .toLocaleString()

    });

    items =
        items.slice(0,30);

    localStorage.setItem(
        "medai_history",
        JSON.stringify(items)
    );

    loadHistory();

}


function loadHistory() {

    const container =
        document.getElementById(
            "history"
        );

    let items =
        JSON.parse(
            localStorage.getItem(
                "medai_history"
            ) || "[]"
        );

    if (!items.length) {

        container.innerHTML =
            "<p class='small'>History خالي دی.</p>";

        return;
    }

    container.innerHTML = "";

    items.forEach(function(item,index) {

        const div =
            document.createElement("div");

        div.className =
            "history-item";

        div.innerHTML =
            "<strong>" +
            escapeHTML(item.question) +
            "</strong>" +

            "<div class='small'>" +
            escapeHTML(item.time) +
            "</div>" +

            "<p>" +
            escapeHTML(item.answer) +
            "</p>" +

            "<button onclick='favorite(" +
            index +
            ")'>⭐ Favorite</button>";

        container.appendChild(div);

    });

}


function clearHistory() {

    localStorage.removeItem(
        "medai_history"
    );

    loadHistory();

}


/* =====================================================
   FAVORITES
===================================================== */

function favorite(index) {

    let history =
        JSON.parse(
            localStorage.getItem(
                "medai_history"
            ) || "[]"
        );

    if (!history[index]) return;

    let favorites =
        JSON.parse(
            localStorage.getItem(
                "medai_favorites"
            ) || "[]"
        );

    favorites.unshift(
        history[index]
    );

    favorites =
        favorites.slice(0,30);

    localStorage.setItem(
        "medai_favorites",
        JSON.stringify(favorites)
    );

    loadFavorites();

}


function loadFavorites() {

    const container =
        document.getElementById(
            "favorites"
        );

    let items =
        JSON.parse(
            localStorage.getItem(
                "medai_favorites"
            ) || "[]"
        );

    if (!items.length) {

        container.innerHTML =
            "<p class='small'>Favorites خالي دي.</p>";

        return;
    }

    container.innerHTML = "";

    items.forEach(function(item) {

        const div =
            document.createElement("div");

        div.className =
            "favorite-item";

        div.innerHTML =
            "<strong>" +
            escapeHTML(item.question) +
            "</strong>" +

            "<div class='small'>" +
            escapeHTML(item.time) +
            "</div>" +

            "<p>" +
            escapeHTML(item.answer) +
            "</p>";

        container.appendChild(div);

    });

}


function clearFavorites() {

    localStorage.removeItem(
        "medai_favorites"
    );

    loadFavorites();

}


/* =====================================================
   MEDICATION REMINDER
===================================================== */

function addReminder() {

    const medicine =
        document.getElementById(
            "reminderMedicine"
        ).value.trim();

    const time =
        document.getElementById(
            "reminderTime"
        ).value;

    const note =
        document.getElementById(
            "reminderNote"
        ).value.trim();

    if (!medicine || !time) {

        alert(
            "د درملو نوم او وخت ولیکئ."
        );

        return;
    }

    let reminders =
        JSON.parse(
            localStorage.getItem(
                "medai_reminders"
            ) || "[]"
        );

    reminders.push({

        medicine: medicine,

        time: time,

        note: note

    });

    localStorage.setItem(
        "medai_reminders",
        JSON.stringify(reminders)
    );

    document.getElementById(
        "reminderMedicine"
    ).value = "";

    document.getElementById(
        "reminderTime"
    ).value = "";

    document.getElementById(
        "reminderNote"
    ).value = "";

    loadReminders();

}


function loadReminders() {

    const container =
        document.getElementById(
            "reminders"
        );

    let reminders =
        JSON.parse(
            localStorage.getItem(
                "medai_reminders"
            ) || "[]"
        );

    container.innerHTML = "";

    reminders.forEach(function(item,index) {

        const div =
            document.createElement("div");

        div.className =
            "reminder-item";

        div.innerHTML =
            "<strong>💊 " +
            escapeHTML(item.medicine) +
            "</strong>" +

            "<p>⏰ " +
            escapeHTML(item.time) +
            "</p>" +

            "<p>" +
            escapeHTML(item.note || "") +
            "</p>" +

            "<button class='danger' " +
            "onclick='deleteReminder(" +
            index +
            ")'>حذف</button>";

        container.appendChild(div);

    });

}


function deleteReminder(index) {

    let reminders =
        JSON.parse(
            localStorage.getItem(
                "medai_reminders"
            ) || "[]"
        );

    reminders.splice(index,1);

    localStorage.setItem(
        "medai_reminders",
        JSON.stringify(reminders)
    );

    loadReminders();

}


/* =====================================================
   HEALTH TRACKER
===================================================== */

function addTracker() {

    const type =
        document.getElementById(
            "trackerType"
        ).value;

    const value =
        document.getElementById(
            "trackerValue"
        ).value.trim();

    const note =
        document.getElementById(
            "trackerNote"
        ).value.trim();

    if (!value) {

        alert(
            "Value ولیکئ."
        );

        return;
    }

    let records =
        JSON.parse(
            localStorage.getItem(
                "medai_tracker"
            ) || "[]"
        );

    records.unshift({

        type: type,

        value: value,

        note: note,

        time: new Date()
            .toLocaleString()

    });

    records =
        records.slice(0,100);

    localStorage.setItem(
        "medai_tracker",
        JSON.stringify(records)
    );

    document.getElementById(
        "trackerValue"
    ).value = "";

    document.getElementById(
        "trackerNote"
    ).value = "";

    loadTracker();

}


function loadTracker() {

    const container =
        document.getElementById(
            "trackerList"
        );

    let records =
        JSON.parse(
            localStorage.getItem(
                "medai_tracker"
            ) || "[]"
        );

    container.innerHTML = "";

    if (!records.length) {

        container.innerHTML =
            "<p class='small'>تر اوسه معلومات نشته.</p>";

        return;
    }

    records.forEach(function(item,index) {

        const div =
            document.createElement("div");

        div.className =
            "tracker-item";

        div.innerHTML =
            "<strong>" +
            escapeHTML(item.type) +
            "</strong>" +

            "<p>Value: " +
            escapeHTML(item.value) +
            "</p>" +

            "<p>" +
            escapeHTML(item.note || "") +
            "</p>" +

            "<div class='small'>" +
            escapeHTML(item.time) +
            "</div>" +

            "<button class='danger' " +
            "onclick='deleteTracker(" +
            index +
            ")'>حذف</button>";

        container.appendChild(div);

    });

}


function deleteTracker(index) {

    let records =
        JSON.parse(
            localStorage.getItem(
                "medai_tracker"
            ) || "[]"
        );

    records.splice(index,1);

    localStorage.setItem(
        "medai_tracker",
        JSON.stringify(records)
    );

    loadTracker();

}


function clearTracker() {

    localStorage.removeItem(
        "medai_tracker"
    );

    loadTracker();

}


/* =====================================================
   HEALTH REPORT
===================================================== */

async function generateHealthReport() {

    const manual =
        document.getElementById(
            "healthReportInput"
        ).value.trim();

    let tracker =
        JSON.parse(
            localStorage.getItem(
                "medai_tracker"
            ) || "[]"
        );

    const result =
        document.getElementById(
            "healthReportResult"
        );

    const combined =
        "User notes:\n" +
        manual +
        "\n\nHealth Tracker records:\n" +
        JSON.stringify(tracker);

    if (!manual && !tracker.length) {

        result.textContent =
            "لومړی Health Tracker کې معلومات ثبت کړئ یا خپل معلومات ولیکئ.";

        return;
    }

    loading(
        "healthReportLoading",
        true
    );

    try {

        const response =
            await fetch(
                "/health-report",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        text: combined
                    })

                }
            );

        const data =
            await response.json();

        result.textContent =
            data.answer ||
            data.error ||
            "راپور جوړ نه شو.";

    } catch (error) {

        result.textContent =
            "د راپور جوړولو ستونزه.";

    } finally {

        loading(
            "healthReportLoading",
            false
        );

    }

}


/* =====================================================
   LOAD LOCAL DATA
===================================================== */

loadHistory();
loadFavorites();
loadReminders();
loadTracker();

</script>

</body>
</html>
"""


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return HTML


# =========================================================
# MAIN CHAT
# =========================================================

@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json(silent=True) or {}

    question = str(
        data.get("question", "")
    ).strip()

    if not question:
        return jsonify({
            "error": "پوښتنه خالي ده."
        }), 400

    prompt = build_prompt(
        """
Give a structured medical educational answer.

Use these sections when appropriate:
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
""",
        question
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


# =========================================================
# SYMPTOMS
# =========================================================

@app.route("/symptoms", methods=["POST"])
def symptoms():

    data = request.get_json(silent=True) or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return jsonify({
            "error": "نښې ولیکئ."
        }), 400

    prompt = build_prompt(
        """
Explain the symptoms educationally.

Include:
- What the symptoms can generally mean
- Possible body systems involved
- Common conditions that can sometimes cause them
- Warning signs
- When professional evaluation may be appropriate

Do not diagnose the user.
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


# =========================================================
# VITALS
# =========================================================

@app.route("/vitals", methods=["POST"])
def vitals():

    data = request.get_json(silent=True) or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return jsonify({
            "error": "Vital signs معلومات ولیکئ."
        }), 400

    prompt = build_prompt(
        """
Explain the provided vital signs.

Explain:
- What each measurement means
- General reference concepts
- Factors that can affect readings
- Why repeated measurements can matter
- When professional evaluation may be appropriate

Do not diagnose.
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


# =========================================================
# COMPARISON
# =========================================================

@app.route("/compare", methods=["POST"])
def compare_route():

    data = request.get_json(silent=True) or {}

    disease1 = str(
        data.get("disease1", "")
    ).strip()

    disease2 = str(
        data.get("disease2", "")
    ).strip()

    if not disease1 or not disease2:
        return jsonify({
            "error": "دواړه ناروغۍ ولیکئ."
        }), 400

    text = (
        "Disease 1: " + disease1 +
        "\nDisease 2: " + disease2
    )

    prompt = build_prompt(
        """
Compare the two conditions.

Include:
- Definition
- Causes
- Risk factors
- Symptoms
- Diagnosis
- Treatment approaches
- Differences
- Similarities
- Warning signs

Do not diagnose the user.
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


# =========================================================
# DOCTOR
# =========================================================

@app.route("/doctor", methods=["POST"])
def doctor():

    data = request.get_json(silent=True) or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return jsonify({
            "error": "معلومات ولیکئ."
        }), 400

    prompt = build_prompt(
        """
Organize the user's notes for a doctor visit.

Create:
- Main concern
- Symptoms
- Onset
- Changes
- Medicines mentioned
- Tests or measurements
- Questions to ask the doctor

Do not add information not provided by the user.
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


# =========================================================
# LAB
# =========================================================

@app.route("/lab", methods=["POST"])
def lab():

    data = request.get_json(silent=True) or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return jsonify({
            "error": "Lab معلومات ولیکئ."
        }), 400

    prompt = build_prompt(
        """
Explain the laboratory test or results.

Include:
- What the test measures
- Why it may be used
- What high or low values can sometimes be associated with
- Factors affecting results
- Why reference ranges differ between laboratories

Do not diagnose from laboratory results alone.
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


# =========================================================
# MEDICINE
# =========================================================

@app.route("/medicine", methods=["POST"])
def medicine():

    data = request.get_json(silent=True) or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return jsonify({
            "error": "د درملو نوم ولیکئ."
        }), 400

    prompt = build_prompt(
        """
Provide general information about the medicine.

Include:
- What it is
- Common uses
- General mechanism
- Common side effects
- Precautions
- General interaction categories
- When professional advice is important

Do not give personalized dosage instructions.
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


# =========================================================
# DICTIONARY
# =========================================================

@app.route("/dictionary", methods=["POST"])
def dictionary():

    data = request.get_json(silent=True) or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return jsonify({
            "error": "اصطلاح ولیکئ."
        }), 400

    prompt = build_prompt(
        """
Explain the medical term in simple language.

Include:
- Simple definition
- Why it matters
- Short example
- Related terms if useful
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


# =========================================================
# EMERGENCY
# =========================================================

@app.route("/emergency", methods=["POST"])
def emergency():

    data = request.get_json(silent=True) or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return jsonify({
            "error": "نښې ولیکئ."
        }), 400

    prompt = build_prompt(
        """
Look only for general emergency warning signs.

Separate:
- Emergency warning signs
- Other information
- What action is generally appropriate

If serious warning signs are present, advise urgent professional medical care.

Do not diagnose.
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


# =========================================================
# MEDICINE INTERACTION
# =========================================================

@app.route("/interaction", methods=["POST"])
def interaction():

    data = request.get_json(silent=True) or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return jsonify({
            "error": "د درملو نومونه ولیکئ."
        }), 400

    prompt = build_prompt(
        """
Review the listed medicines for known or potentially important interactions.

Explain:
- Medicines involved
- Type of possible interaction
- Why it may matter
- Important possible effects
- Why a pharmacist or doctor may need to review it

Interaction risk can depend on dose, age, kidney/liver function,
other medicines, supplements and medical conditions.

Do not tell the user to stop or change medicines.
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


# =========================================================
# MEDICAL REPORT
# =========================================================

@app.route("/report", methods=["POST"])
def report():

    data = request.get_json(silent=True) or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return jsonify({
            "error": "طبي راپور ولیکئ."
        }), 400

    prompt = build_prompt(
        """
Explain the medical report in simple language.

Organize:
1. What the report is about
2. Important findings
3. Medical terms
4. Tests and measurements
5. What findings can generally be associated with
6. Questions for the doctor
7. Important limitations

Do not diagnose.
Do not invent missing information.
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


# =========================================================
# FIRST AID
# =========================================================

@app.route("/firstaid", methods=["POST"])
def firstaid():

    data = request.get_json(silent=True) or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return jsonify({
            "error": "حالت ولیکئ."
        }), 400

    prompt = build_prompt(
        """
Provide a general first-aid educational guide.

Structure:
1. Immediate priorities
2. Basic first-aid steps
3. What NOT to do
4. Emergency warning signs
5. When professional evaluation is needed

Keep instructions simple and safety-focused.
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


# =========================================================
# GLOSSARY
# =========================================================

@app.route("/glossary", methods=["POST"])
def glossary():

    data = request.get_json(silent=True) or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return jsonify({
            "error": "اصطلاحات ولیکئ."
        }), 400

    prompt = build_prompt(
        """
Explain each medical term in very simple language.

For each:
- Term
- Simple meaning
- Why it is used in medicine
- Short example
- Related term if useful
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


# =========================================================
# NEW: RISK ASSESSMENT
# =========================================================

@app.route("/risk", methods=["POST"])
def risk():

    data = request.get_json(silent=True) or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return jsonify({
            "error": "معلومات ولیکئ."
        }), 400

    prompt = build_prompt(
        """
Review the information for GENERAL medical risk indicators.

Do not calculate a fake medical score.

Organize:
- Important reported factors
- Potential warning signs
- Factors that may increase concern
- Information that is missing
- When urgent care may be appropriate
- When routine professional evaluation may be appropriate

Do not diagnose the person.
Do not predict their outcome.
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


# =========================================================
# NEW: HEALTH REPORT
# =========================================================

@app.route("/health-report", methods=["POST"])
def health_report():

    data = request.get_json(silent=True) or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return jsonify({
            "error": "د روغتیا معلومات ولیکئ."
        }), 400

    prompt = build_prompt(
        """
Create a clear educational health summary from the information provided.

Use:
- Summary
- Recorded measurements
- Symptoms or concerns mentioned
- Trends that can be directly observed from the provided data
- Questions to discuss with a healthcare professional
- Important limitations

Do not diagnose.
Do not invent missing information.
Do not give personalized prescriptions.
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


# =========================================================
# IMAGES
# =========================================================

@app.route("/images", methods=["GET"])
def images():

    query = request.args.get(
        "q",
        ""
    ).strip()

    if not query:
        return jsonify({
            "images": []
        })

    return jsonify({
        "images":
            get_medical_images(query)
    })


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )

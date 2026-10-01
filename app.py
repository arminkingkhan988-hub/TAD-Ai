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
# GEMINI AI
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
                            {
                                "text": prompt
                            }
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

    except Exception:
        return "د AI سره د اړیکې پر مهال تېروتنه رامنځته شوه."


# =========================================================
# MEDICAL PROMPT
# =========================================================

def build_prompt(instruction, user_text):
    return f"""
You are MedAI, an educational medical information assistant.

IMPORTANT RULES:
- Answer in the SAME LANGUAGE as the user's question.
- Use simple and understandable language.
- Give educational medical information only.
- Do not diagnose a person from symptoms alone.
- Do not claim that you examined the patient.
- Do not invent medical facts.
- Do not provide personalized prescription or medication dosing instructions.
- Do not tell a person to start, stop, or change prescription medicine based only on this answer.
- If the situation may be an emergency, clearly advise seeking urgent professional medical care.
- Mention that laboratory reference ranges can differ between laboratories when discussing lab results.
- Distinguish general information from personal medical advice.
- Be medically responsible and concise but useful.

REQUEST:
{instruction}

USER QUESTION / INFORMATION:
{user_text}
"""


# =========================================================
# WIKIMEDIA MEDICAL IMAGES
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
            imageinfo = page.get("imageinfo", [])

            if not imageinfo:
                continue

            info = imageinfo[0]

            image_url = info.get("thumburl") or info.get("url")

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

<title>MedAI - Medical AI</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, Tahoma, sans-serif;
    background: #f4f7fb;
    color: #172033;
    transition: 0.3s;
}

body.dark {
    background: #101522;
    color: #f1f5f9;
}

header {
    background: linear-gradient(135deg, #087f8c, #0b5ed7);
    color: white;
    padding: 25px 15px;
    text-align: center;
}

header h1 {
    margin: 0;
    font-size: 34px;
}

header p {
    margin: 10px 0 0;
    font-size: 16px;
}

.top-buttons {
    display: flex;
    justify-content: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 18px;
}

.top-buttons button {
    width: auto;
    padding: 10px 16px;
    margin: 0;
    background: white;
    color: #075985;
}

.container {
    max-width: 1100px;
    margin: auto;
    padding: 20px;
}

.card {
    background: white;
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 5px 22px rgba(0,0,0,0.08);
}

.dark .card {
    background: #182131;
    box-shadow: 0 5px 22px rgba(0,0,0,0.25);
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
    padding: 14px;
    border: 1px solid #ccd5e0;
    border-radius: 12px;
    font-size: 16px;
    margin: 8px 0 12px;
    background: white;
    color: #111827;
}

.dark textarea,
.dark input,
.dark select {
    background: #0f172a;
    color: white;
    border-color: #334155;
}

button {
    width: 100%;
    border: none;
    padding: 13px 16px;
    margin: 5px 0;
    border-radius: 12px;
    background: #0b78a8;
    color: white;
    font-size: 16px;
    cursor: pointer;
}

button:hover {
    opacity: 0.9;
}

button.secondary {
    background: #64748b;
}

button.success {
    background: #16803c;
}

button.warning {
    background: #b45309;
}

button.danger {
    background: #b91c1c;
}

.result {
    background: #f8fafc;
    border-radius: 12px;
    padding: 16px;
    margin-top: 12px;
    line-height: 1.9;
    white-space: pre-wrap;
}

.dark .result {
    background: #0f172a;
}

.loading {
    display: none;
    text-align: center;
    padding: 12px;
    color: #0b78a8;
    font-weight: bold;
}

.topic-buttons {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
}

.topic-buttons button {
    font-size: 14px;
}

.images {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
}

.images img {
    width: 100%;
    height: 180px;
    object-fit: cover;
    border-radius: 12px;
}

.image-title {
    font-size: 12px;
    margin-top: 4px;
}

.history-item,
.favorite-item {
    background: #f1f5f9;
    padding: 12px;
    margin: 8px 0;
    border-radius: 10px;
}

.dark .history-item,
.dark .favorite-item {
    background: #0f172a;
}

.small {
    font-size: 13px;
    color: #64748b;
}

.dark .small {
    color: #94a3b8;
}

footer {
    text-align: center;
    padding: 30px 15px;
    color: #64748b;
}

@media (max-width: 800px) {

    .topic-buttons {
        grid-template-columns: repeat(2, 1fr);
    }

    .images {
        grid-template-columns: repeat(2, 1fr);
    }

}

@media (max-width: 500px) {

    header h1 {
        font-size: 27px;
    }

    .container {
        padding: 10px;
    }

    .card {
        padding: 15px;
        border-radius: 14px;
    }

    .topic-buttons,
    .images {
        grid-template-columns: 1fr;
    }

    .images img {
        height: 220px;
    }

}

</style>

</head>

<body>

<header>

<h1>🩺 MedAI</h1>

<p>ستاسو هوښیار طبي معلوماتي مرستیال</p>

<div class="top-buttons">

<button onclick="toggleDarkMode()">
🌙 Dark Mode
</button>

<button onclick="startVoice()">
🎤 Voice Question
</button>

<button onclick="stopVoice()">
⏹️ Stop Voice
</button>

</div>

</header>


<div class="container">


<!-- MAIN AI -->

<div class="card">

<h2>🤖 Medical AI Chat</h2>

<textarea
id="question"
rows="5"
placeholder="خپله طبي پوښتنه دلته ولیکئ..."
></textarea>

<button onclick="askAI()">
🤖 له MedAI څخه پوښتنه وکړئ
</button>

<button class="secondary" onclick="speakCurrentAnswer()">
🔊 ځواب واورئ
</button>

<div id="mainLoading" class="loading">
AI کار کوي...
</div>

<div id="answer" class="result">
دلته به ستاسو ځواب ښکاره شي.
</div>

</div>


<!-- TOPICS -->

<div class="card">

<h2>🩺 Medical Topics</h2>

<div class="topic-buttons">

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

<textarea
id="symptomsInput"
rows="4"
placeholder="مثلاً: تبه، ټوخی او ستونی درد..."
></textarea>

<button onclick="explainSymptoms()">
🧠 نښې تشریح کړه
</button>

<div id="symptomsLoading" class="loading">
AI کار کوي...
</div>

<div id="symptomsResult" class="result"></div>

</div>


<!-- VITALS -->

<div class="card">

<h2>❤️ Vital Signs Guide</h2>

<textarea
id="vitalsInput"
rows="4"
placeholder="مثلاً: Blood Pressure 140/90, pulse 85..."
></textarea>

<button onclick="explainVitals()">
❤️ حیاتي نښې تشریح کړه
</button>

<div id="vitalsLoading" class="loading">
AI کار کوي...
</div>

<div id="vitalsResult" class="result"></div>

</div>


<!-- DISEASE COMPARISON -->

<div class="card">

<h2>⚖️ Disease Comparison</h2>

<input
id="disease1"
placeholder="لومړۍ ناروغي"
/>

<input
id="disease2"
placeholder="دوهمه ناروغي"
/>

<button onclick="compareDiseases()">
⚖️ پرتله یې کړه
</button>

<div id="compareLoading" class="loading">
AI کار کوي...
</div>

<div id="compareResult" class="result"></div>

</div>


<!-- DOCTOR ASSISTANT -->

<div class="card">

<h2>👨‍⚕️ Doctor Visit Assistant</h2>

<textarea
id="doctorInput"
rows="6"
placeholder="خپلې نښې، د پیل وخت، درمل، ټیسټونه او نور معلومات ولیکئ..."
></textarea>

<button onclick="prepareDoctorVisit()">
👨‍⚕️ معلومات منظم کړه
</button>

<div id="doctorLoading" class="loading">
AI کار کوي...
</div>

<div id="doctorResult" class="result"></div>

</div>


<!-- LAB -->

<div class="card">

<h2>🧪 Lab Report Explainer</h2>

<textarea
id="labInput"
rows="6"
placeholder="د لابراتوار راپور یا د ټیسټ نوم او نتیجه ولیکئ..."
></textarea>

<button onclick="explainLab()">
🧪 راپور تشریح کړه
</button>

<div id="labLoading" class="loading">
AI کار کوي...
</div>

<div id="labResult" class="result"></div>

</div>


<!-- MEDICINE -->

<div class="card">

<h2>💊 Medicine Information</h2>

<textarea
id="medicineInput"
rows="4"
placeholder="د درملو نوم ولیکئ..."
></textarea>

<button onclick="explainMedicine()">
💊 د درملو معلومات
</button>

<div id="medicineLoading" class="loading">
AI کار کوي...
</div>

<div id="medicineResult" class="result"></div>

</div>


<!-- MEDICAL DICTIONARY -->

<div class="card">

<h2>📖 Medical Dictionary</h2>

<input
id="dictionaryInput"
placeholder="طبي اصطلاح ولیکئ، مثلاً: Hypertension"
/>

<button onclick="explainDictionary()">
📖 اصطلاح تشریح کړه
</button>

<div id="dictionaryLoading" class="loading">
AI کار کوي...
</div>

<div id="dictionaryResult" class="result"></div>

</div>


<!-- EMERGENCY -->

<div class="card">

<h2>🚨 Emergency Checker</h2>

<textarea
id="emergencyInput"
rows="4"
placeholder="عمومي نښې ولیکئ..."
></textarea>

<button class="danger" onclick="checkEmergency()">
🚨 بیړنۍ نښې وګوره
</button>

<div id="emergencyLoading" class="loading">
AI کار کوي...
</div>

<div id="emergencyResult" class="result"></div>

</div>


<!-- SEARCH -->

<div class="card">

<h2>🔎 Medical Search</h2>

<input
id="searchInput"
placeholder="طبي موضوع ولټوئ..."
/>

<button onclick="searchMedical()">
🔎 Search
</button>

<div id="searchResult" class="result"></div>

</div>


<!-- IMAGES -->

<div class="card">

<h2>🖼️ Medical Images</h2>

<input
id="imageInput"
placeholder="مثلاً: human heart"
/>

<button onclick="displayImages()">
🖼️ انځورونه راوړه
</button>

<div id="imageLoading" class="loading">
انځورونه لټول کېږي...
</div>

<div id="images" class="images"></div>

</div>


<!-- MEDICINE INTERACTION -->

<div class="card">

<h2>💊 Medicine Interaction Checker</h2>

<textarea
id="interactionInput"
rows="4"
placeholder="مثلاً: Drug A + Drug B یا د څو درملو نومونه..."
></textarea>

<button onclick="checkInteraction()">
💊 احتمالي تداخل تشریح کړه
</button>

<div id="interactionLoading" class="loading">
AI کار کوي...
</div>

<div id="interactionResult" class="result"></div>

</div>


<!-- MEDICAL REPORT -->

<div class="card">

<h2>📄 Medical Report Explainer</h2>

<textarea
id="reportInput"
rows="7"
placeholder="خپل طبي راپور یا د راپور متن دلته ولیکئ..."
></textarea>

<button onclick="explainMedicalReport()">
📄 راپور تشریح کړه
</button>

<div id="reportLoading" class="loading">
AI کار کوي...
</div>

<div id="reportResult" class="result"></div>

</div>


<!-- FIRST AID -->

<div class="card">

<h2>🩹 First Aid Guide</h2>

<input
id="firstAidInput"
placeholder="مثلاً: minor burn, nosebleed, cut..."
/>

<button onclick="firstAidGuide()">
🩹 د لومړنۍ مرستې لارښود
</button>

<div id="firstAidLoading" class="loading">
AI کار کوي...
</div>

<div id="firstAidResult" class="result"></div>

</div>


<!-- GLOSSARY -->

<div class="card">

<h2>🧬 Medical Glossary</h2>

<textarea
id="glossaryInput"
rows="4"
placeholder="یوه یا څو طبي اصطلاحات ولیکئ..."
></textarea>

<button onclick="explainGlossary()">
🧬 اصطلاحات ساده کړه
</button>

<div id="glossaryLoading" class="loading">
AI کار کوي...
</div>

<div id="glossaryResult" class="result"></div>

</div>


<!-- QUIZ -->

<div class="card">

<h2>🧠 Medical Quiz</h2>

<p>
د پوښتنې لپاره لاندې تڼۍ کېکاږئ.
</p>

<button onclick="generateQuiz()">
🧠 Quiz جوړ کړه
</button>

<div id="quizLoading" class="loading">
AI کار کوي...
</div>

<div id="quizResult" class="result"></div>

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


/* =====================================================
   GENERAL HELPERS
===================================================== */

function showLoading(id, show) {
    const el = document.getElementById(id);

    if (!el) return;

    el.style.display = show ? "block" : "none";
}


function escapeHTML(text) {

    const div = document.createElement("div");

    div.textContent = text;

    return div.innerHTML;
}


async function sendSpecialRequest(
    endpoint,
    inputId,
    resultId,
    loadingId
) {

    const input = document.getElementById(inputId);
    const result = document.getElementById(resultId);

    if (!input || !result) return;

    const text = input.value.trim();

    if (!text) {
        result.textContent = "مهرباني وکړئ معلومات ولیکئ.";
        return;
    }

    showLoading(loadingId, true);

    result.textContent = "";

    try {

        const response = await fetch(endpoint, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                text: text
            })

        });

        const data = await response.json();

        result.textContent =
            data.answer || data.error || "ځواب ترلاسه نه شو.";

    } catch (error) {

        result.textContent =
            "د سرور سره د اړیکې ستونزه رامنځته شوه.";

    } finally {

        showLoading(loadingId, false);

    }
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
            "مهرباني وکړئ خپله پوښتنه ولیکئ.";

        return;
    }

    showLoading("mainLoading", true);

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

        answer.textContent = currentAnswer;

        saveHistory(question, currentAnswer);

    } catch (error) {

        answer.textContent =
            "د سرور سره د اړیکې ستونزه رامنځته شوه.";

    } finally {

        showLoading("mainLoading", false);

    }
}


/* =====================================================
   SYMPTOMS
===================================================== */

function explainSymptoms() {

    sendSpecialRequest(
        "/symptoms",
        "symptomsInput",
        "symptomsResult",
        "symptomsLoading"
    );

}


/* =====================================================
   VITALS
===================================================== */

function explainVitals() {

    sendSpecialRequest(
        "/vitals",
        "vitalsInput",
        "vitalsResult",
        "vitalsLoading"
    );

}


/* =====================================================
   LAB
===================================================== */

function explainLab() {

    sendSpecialRequest(
        "/lab",
        "labInput",
        "labResult",
        "labLoading"
    );

}


/* =====================================================
   MEDICINE
===================================================== */

function explainMedicine() {

    sendSpecialRequest(
        "/medicine",
        "medicineInput",
        "medicineResult",
        "medicineLoading"
    );

}


/* =====================================================
   DICTIONARY
===================================================== */

function explainDictionary() {

    sendSpecialRequest(
        "/dictionary",
        "dictionaryInput",
        "dictionaryResult",
        "dictionaryLoading"
    );

}


/* =====================================================
   EMERGENCY
===================================================== */

function checkEmergency() {

    sendSpecialRequest(
        "/emergency",
        "emergencyInput",
        "emergencyResult",
        "emergencyLoading"
    );

}


/* =====================================================
   DISEASE COMPARISON
===================================================== */

async function compareDiseases() {

    const disease1 =
        document.getElementById("disease1").value.trim();

    const disease2 =
        document.getElementById("disease2").value.trim();

    const result =
        document.getElementById("compareResult");

    if (!disease1 || !disease2) {

        result.textContent =
            "مهرباني وکړئ دواړه ناروغۍ ولیکئ.";

        return;
    }

    showLoading("compareLoading", true);

    result.textContent = "";

    try {

        const response = await fetch("/compare", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                disease1: disease1,
                disease2: disease2
            })

        });

        const data = await response.json();

        result.textContent =
            data.answer || data.error || "ځواب ترلاسه نه شو.";

    } catch (error) {

        result.textContent =
            "د سرور سره د اړیکې ستونزه.";

    } finally {

        showLoading("compareLoading", false);

    }

}


/* =====================================================
   DOCTOR VISIT
===================================================== */

function prepareDoctorVisit() {

    sendSpecialRequest(
        "/doctor",
        "doctorInput",
        "doctorResult",
        "doctorLoading"
    );

}


/* =====================================================
   MEDICINE INTERACTION
===================================================== */

function checkInteraction() {

    sendSpecialRequest(
        "/interaction",
        "interactionInput",
        "interactionResult",
        "interactionLoading"
    );

}


/* =====================================================
   MEDICAL REPORT
===================================================== */

function explainMedicalReport() {

    sendSpecialRequest(
        "/report",
        "reportInput",
        "reportResult",
        "reportLoading"
    );

}


/* =====================================================
   FIRST AID
===================================================== */

function firstAidGuide() {

    sendSpecialRequest(
        "/firstaid",
        "firstAidInput",
        "firstAidResult",
        "firstAidLoading"
    );

}


/* =====================================================
   GLOSSARY
===================================================== */

function explainGlossary() {

    sendSpecialRequest(
        "/glossary",
        "glossaryInput",
        "glossaryResult",
        "glossaryLoading"
    );

}


/* =====================================================
   SEARCH
===================================================== */

async function searchMedical() {

    const query =
        document.getElementById("searchInput").value.trim();

    const result =
        document.getElementById("searchResult");

    if (!query) {

        result.textContent =
            "مهرباني وکړئ د لټون موضوع ولیکئ.";

        return;
    }

    result.textContent =
        "لټون کېږي...";

    try {

        const response = await fetch("/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                question:
                    "Provide educational medical information about: "
                    + query
            })

        });

        const data = await response.json();

        result.textContent =
            data.answer || data.error || "نتیجه ونه موندل شوه.";

    } catch (error) {

        result.textContent =
            "د لټون ستونزه رامنځته شوه.";

    }

}


/* =====================================================
   IMAGES
===================================================== */

async function displayImages() {

    const query =
        document.getElementById("imageInput").value.trim();

    const container =
        document.getElementById("images");

    if (!query) {

        container.innerHTML =
            "<p>مهرباني وکړئ موضوع ولیکئ.</p>";

        return;
    }

    showLoading("imageLoading", true);

    container.innerHTML = "";

    try {

        const response = await fetch(
            "/images?q=" + encodeURIComponent(query)
        );

        const data = await response.json();

        if (!data.images || data.images.length === 0) {

            container.innerHTML =
                "<p>انځورونه پیدا نه شول.</p>";

            return;
        }

        data.images.forEach(function(image) {

            const wrapper =
                document.createElement("div");

            const img =
                document.createElement("img");

            img.src = image.url;

            img.alt = image.title;

            img.loading = "lazy";

            const title =
                document.createElement("div");

            title.className = "image-title";

            title.textContent = image.title;

            wrapper.appendChild(img);

            wrapper.appendChild(title);

            container.appendChild(wrapper);

        });

    } catch (error) {

        container.innerHTML =
            "<p>د انځورونو په راوړلو کې ستونزه.</p>";

    } finally {

        showLoading("imageLoading", false);

    }

}


/* =====================================================
   QUIZ
===================================================== */

async function generateQuiz() {

    const result =
        document.getElementById("quizResult");

    showLoading("quizLoading", true);

    result.textContent = "";

    try {

        const response = await fetch("/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                question:
                    "Create a short educational medical quiz with 5 multiple-choice questions. "
                    + "Give four options for each question and provide the correct answer after each question. "
                    + "Use the same language as this request."

            })

        });

        const data = await response.json();

        result.textContent =
            data.answer || data.error || "Quiz جوړ نه شو.";

    } catch (error) {

        result.textContent =
            "د Quiz جوړولو ستونزه.";

    } finally {

        showLoading("quizLoading", false);

    }

}


/* =====================================================
   VOICE QUESTION
===================================================== */

let recognition = null;

function startVoice() {

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if (!SpeechRecognition) {

        alert(
            "ستاسو browser د Voice Question ملاتړ نه کوي."
        );

        return;
    }

    recognition =
        new SpeechRecognition();

    recognition.lang = "ps-AF";

    recognition.interimResults = false;

    recognition.continuous = false;

    recognition.onresult = function(event) {

        const text =
            event.results[0][0].transcript;

        document.getElementById("question").value =
            text;

    };

    recognition.onerror = function() {

        alert("Voice Question کې ستونزه رامنځته شوه.");

    };

    recognition.start();

}


function stopVoice() {

    if (recognition) {

        recognition.stop();

        recognition = null;

    }

    if ("speechSynthesis" in window) {

        window.speechSynthesis.cancel();

    }

}


/* =====================================================
   VOICE OUTPUT
===================================================== */

function speakCurrentAnswer() {

    if (!currentAnswer) {

        currentAnswer =
            document.getElementById("answer").textContent;

    }

    if (!currentAnswer) {

        alert("لومړی یو AI ځواب ترلاسه کړئ.");

        return;
    }

    if (!("speechSynthesis" in window)) {

        alert(
            "ستاسو browser د Voice Output ملاتړ نه کوي."
        );

        return;
    }

    window.speechSynthesis.cancel();

    const utterance =
        new SpeechSynthesisUtterance(currentAnswer);

    utterance.lang = "ps-AF";

    utterance.rate = 0.9;

    window.speechSynthesis.speak(
        utterance
    );

}


/* =====================================================
   DARK MODE
===================================================== */

function toggleDarkMode() {

    document.body.classList.toggle("dark");

    localStorage.setItem(
        "medai_dark",
        document.body.classList.contains("dark")
    );

}


if (localStorage.getItem("medai_dark") === "true") {

    document.body.classList.add("dark");

}


/* =====================================================
   TOPICS
===================================================== */

function setTopic(topic) {

    document.getElementById("question").value =
        "د " + topic + " په اړه طبي معلومات راکړه.";

    document.getElementById("question").focus();

}


/* =====================================================
   HISTORY
===================================================== */

function saveHistory(question, answer) {

    let history =
        JSON.parse(
            localStorage.getItem("medai_history") || "[]"
        );

    history.unshift({

        question: question,

        answer: answer,

        time: new Date().toLocaleString()

    });

    history =
        history.slice(0, 30);

    localStorage.setItem(
        "medai_history",
        JSON.stringify(history)
    );

    loadHistory();

}


function loadHistory() {

    const container =
        document.getElementById("history");

    let history =
        JSON.parse(
            localStorage.getItem("medai_history") || "[]"
        );

    if (!history.length) {

        container.innerHTML =
            "<p class='small'>History خالي دی.</p>";

        return;
    }

    container.innerHTML = "";

    history.forEach(function(item, index) {

        const div =
            document.createElement("div");

        div.className =
            "history-item";

        div.innerHTML = `
            <strong>${escapeHTML(item.question)}</strong>
            <div class="small">${escapeHTML(item.time)}</div>
            <p>${escapeHTML(item.answer)}</p>
            <button onclick="saveFavorite(${index})">
                ⭐ Favorite
            </button>
        `;

        container.appendChild(div);

    });

}


function clearHistory() {

    localStorage.removeItem(
        "medai_history"
    );

    loadHistory();

}


loadHistory();


/* =====================================================
   FAVORITES
===================================================== */

function saveFavorite(index) {

    let history =
        JSON.parse(
            localStorage.getItem("medai_history") || "[]"
        );

    if (!history[index]) return;

    let favorites =
        JSON.parse(
            localStorage.getItem("medai_favorites") || "[]"
        );

    favorites.unshift(
        history[index]
    );

    favorites =
        favorites.slice(0, 30);

    localStorage.setItem(
        "medai_favorites",
        JSON.stringify(favorites)
    );

    loadFavorites();

}


function loadFavorites() {

    const container =
        document.getElementById("favorites");

    let favorites =
        JSON.parse(
            localStorage.getItem("medai_favorites") || "[]"
        );

    if (!favorites.length) {

        container.innerHTML =
            "<p class='small'>Favorites خالي دي.</p>";

        return;
    }

    container.innerHTML = "";

    favorites.forEach(function(item) {

        const div =
            document.createElement("div");

        div.className =
            "favorite-item";

        div.innerHTML = `
            <strong>${escapeHTML(item.question)}</strong>
            <div class="small">${escapeHTML(item.time)}</div>
            <p>${escapeHTML(item.answer)}</p>
        `;

        container.appendChild(div);

    });

}


function clearFavorites() {

    localStorage.removeItem(
        "medai_favorites"
    );

    loadFavorites();

}


loadFavorites();

</script>

</body>
</html>
"""


# =========================================================
# ROUTES
# =========================================================

@app.route("/")
def home():
    return HTML


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

Use these sections when relevant:
1. Definition
2. Causes
3. Types
4. Risk Factors
5. Signs and Symptoms
6. Diagnosis
7. Treatment
8. Prevention
9. Complications
10. Important Points
""",
        question
    )

    answer = ask_gemini(prompt)

    return jsonify({
        "answer": answer
    })


@app.route("/symptoms", methods=["POST"])
def symptoms():

    data = request.get_json(silent=True) or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return jsonify({
            "error": "نښې خالي دي."
        }), 400

    prompt = build_prompt(
        """
Explain the reported symptoms educationally.

Include:
- What the symptoms can generally mean
- Body systems that may be associated
- Common conditions that can sometimes cause them
- Warning signs requiring urgent medical attention
- When professional medical evaluation may be appropriate

Do not diagnose the user.
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


@app.route("/vitals", methods=["POST"])
def vitals():

    data = request.get_json(silent=True) or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return jsonify({
            "error": "Vital signs معلومات خالي دي."
        }), 400

    prompt = build_prompt(
        """
Explain the provided vital signs educationally.

Discuss:
- What each measurement means
- General adult reference concepts where appropriate
- Factors that can affect readings
- Why repeated measurements may matter
- When a reading may need professional attention

Do not diagnose the person.
Do not provide personalized treatment or medication instructions.
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


@app.route("/compare", methods=["POST"])
def compare():

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

    text = f"""
Disease 1: {disease1}
Disease 2: {disease2}
"""

    prompt = build_prompt(
        """
Compare the two medical conditions.

Use:
- Definition
- Causes
- Risk factors
- Symptoms
- Diagnosis
- Treatment approaches
- Main differences
- Similarities
- Warning signs

Keep the comparison educational and do not diagnose the user.
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


@app.route("/doctor", methods=["POST"])
def doctor():

    data = request.get_json(silent=True) or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return jsonify({
            "error": "معلومات خالي دي."
        }), 400

    prompt = build_prompt(
        """
Organize the user's notes so they can be easier to discuss with a doctor.

Create:
- Main concern
- Symptoms
- When symptoms started
- How symptoms changed
- Current medicines mentioned by the user
- Measurements or tests mentioned
- Important questions to ask the doctor

Do not add facts that the user did not provide.
Do not diagnose.
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


@app.route("/lab", methods=["POST"])
def lab():

    data = request.get_json(silent=True) or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return jsonify({
            "error": "Lab معلومات خالي دي."
        }), 400

    prompt = build_prompt(
        """
Explain the laboratory test or results educationally.

For each test where possible:
- What the test measures
- Why it may be ordered
- What higher or lower results can sometimes be associated with
- Factors that can affect results
- Why reference ranges differ between laboratories
- When discussing abnormal results, explain that interpretation depends on clinical context

Do not diagnose from laboratory results alone.
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


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
Provide general educational information about the medicine.

Include:
- What it is
- Common uses
- General mechanism if useful
- Common side effects
- Important precautions
- General interaction categories
- Situations where professional advice is important

Do not provide personalized dosage instructions.
Do not tell the user to start, stop, or change prescription medicine.
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


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
- Why it matters medically
- A short example if helpful
- Related terms if useful
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


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
Assess only for general emergency warning signs.

Clearly separate:
- Emergency warning signs
- Other information
- What action is generally appropriate if an emergency sign is present

If serious warning signs are present, advise urgent professional medical care.

Do not diagnose.
The absence of a warning sign does not guarantee that the person is safe.
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


# =========================================================
# NEW FEATURE 1
# MEDICINE INTERACTION CHECKER
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
Review the listed medicines for known or potentially important interaction
categories using general medical information.

For each possible interaction, explain:
- Which medicines are involved
- What type of interaction may occur
- Why it may matter
- What symptoms or effects may be important
- Whether a pharmacist or doctor should review the combination

Important:
- Do not assume the exact dose or patient history.
- Do not tell the user to stop or change medicines.
- Mention that interaction risk can depend on dose, age, kidney/liver function,
  other medicines, supplements, and medical conditions.
- If the medicine names are unclear, say so.
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


# =========================================================
# NEW FEATURE 2
# MEDICAL REPORT EXPLAINER
# =========================================================

@app.route("/report", methods=["POST"])
def report():

    data = request.get_json(silent=True) or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return jsonify({
            "error": "د طبي راپور معلومات ولیکئ."
        }), 400

    prompt = build_prompt(
        """
Explain the medical report in simple language.

Organize the explanation into:
1. What the report is about
2. Important findings
3. Meaning of medical terms
4. Tests or measurements mentioned
5. What findings can generally be associated with
6. Questions the patient could ask their doctor
7. Important limitations

Do not diagnose from the report alone.
Do not invent missing information.
If the report contains a reference range, explain that ranges can vary
between laboratories or institutions.
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


# =========================================================
# NEW FEATURE 3
# FIRST AID GUIDE
# =========================================================

@app.route("/firstaid", methods=["POST"])
def firstaid():

    data = request.get_json(silent=True) or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return jsonify({
            "error": "د حالت نوم ولیکئ."
        }), 400

    prompt = build_prompt(
        """
Provide a general first-aid educational guide for the described situation.

Structure it as:
1. Immediate priorities
2. Basic first-aid steps
3. What NOT to do
4. When emergency services or urgent medical care are needed
5. When professional evaluation is appropriate

Keep instructions simple and safety-focused.
Do not diagnose.
Do not give dangerous or invasive instructions.
If the situation could be life-threatening, emphasize emergency medical care.
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


# =========================================================
# NEW FEATURE 4
# MEDICAL GLOSSARY
# =========================================================

@app.route("/glossary", methods=["POST"])
def glossary():

    data = request.get_json(silent=True) or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return jsonify({
            "error": "طبي اصطلاحات ولیکئ."
        }), 400

    prompt = build_prompt(
        """
Explain the listed medical terms in very simple language.

For each term provide:
- Term
- Simple meaning
- Why it is used in medicine
- Short example when helpful
- Related term when useful

Keep every explanation understandable to a general audience.
""",
        text
    )

    return jsonify({
        "answer": ask_gemini(prompt)
    })


# =========================================================
# MEDICAL IMAGES ROUTE
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
        "images": get_medical_images(query)
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

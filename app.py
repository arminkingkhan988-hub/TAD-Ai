from flask import Flask, request, jsonify, render_template_string
import os
import json
import urllib.request
import urllib.error

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite"
)

GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/"
    f"models/{GEMINI_MODEL}:generateContent"
)

SYSTEM_PROMPT = """
You are MedAI, an educational medical information assistant.
Developer: Toyebullah Dawoodzay. Created in 2026.

Answer in the SAME LANGUAGE as the user's question.
Use simple, clear language.
Provide educational information only.

Do not diagnose from symptoms alone.
Do not claim to examine the patient.
Do not invent facts.
Do not provide personalized prescription or medication dosing.
Do not tell users to start, stop, or change prescription medicines.

If emergency warning signs are present, advise urgent professional medical care.
Do not replace a qualified healthcare professional.

If asked who created you, say:
"زه MedAI یم، د Toyebullah Dawoodzay لخوا په ۲۰۲۶ کال کې جوړ شوی یم."
"""

HTML = r"""
<!doctype html>
<html lang="ps" dir="rtl">

<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#1677ff">

<title>MedAI — Medical AI</title>

<style>
*{box-sizing:border-box}

:root{
--bg:#f4f8fc;
--card:#fff;
--text:#102a43;
--muted:#627d98;
--blue:#1677ff;
--blue2:#0d5ed7;
--soft:#eaf3ff;
--border:#d8e5f0;
--danger:#d93025;
--ok:#12805c
}

body.dark{
--bg:#0b1520;
--card:#132231;
--text:#eef6ff;
--muted:#a9bac8;
--soft:#17344f;
--border:#294355
}

body{
margin:0;
background:var(--bg);
color:var(--text);
font-family:Arial,sans-serif;
transition:.2s
}

button,input,textarea,select{
font:inherit
}

button{
border:0;
border-radius:13px;
padding:11px 15px;
background:var(--blue);
color:#fff;
cursor:pointer
}

button:hover{
background:var(--blue2)
}

button:disabled{
opacity:.55;
cursor:not-allowed
}

button.secondary{
background:var(--soft);
color:var(--text)
}

button.danger{
background:#feeceb;
color:var(--danger)
}

.wrap{
max-width:1100px;
margin:auto;
padding:12px
}

header{
background:var(--card);
border:1px solid var(--border);
border-radius:23px;
padding:15px;
display:flex;
align-items:center;
justify-content:space-between;
gap:12px;
box-shadow:0 8px 30px #0000000a
}

.brand{
display:flex;
align-items:center;
gap:10px
}

.logo{
font-size:38px
}

.brand h1{
margin:0;
color:var(--blue)
}

.brand p{
margin:4px 0 0;
color:var(--muted);
font-size:13px
}

.actions{
display:flex;
gap:7px;
flex-wrap:wrap
}

.hero{
margin-top:14px;
padding:24px;
border-radius:25px;
background:linear-gradient(135deg,#1677ff,#5bb0ff);
color:#fff;
box-shadow:0 12px 35px #1677ff30
}

.hero h2{
margin:0 0 8px;
font-size:28px
}

.hero p{
margin:0;
line-height:1.8
}

.card{
background:var(--card);
border:1px solid var(--border);
border-radius:20px;
padding:17px;
margin-top:14px;
box-shadow:0 7px 24px #00000008
}

h3{
margin-top:0
}

textarea,input,select{
width:100%;
padding:13px;
border:1px solid var(--border);
border-radius:13px;
background:var(--bg);
color:var(--text);
outline:none
}

textarea{
min-height:105px;
resize:vertical
}

.row{
display:flex;
gap:8px;
flex-wrap:wrap;
margin-top:10px
}

.row>*{
flex:1;
min-width:120px
}

.grid{
display:grid;
grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
gap:9px
}

.tile{
padding:15px;
border:1px solid var(--border);
border-radius:16px;
background:var(--card);
color:var(--text);
text-align:center;
cursor:pointer;
transition:.15s
}

.tile:hover{
border-color:var(--blue);
transform:translateY(-1px)
}

.tile b{
display:block;
margin-top:6px
}

.result{
white-space:pre-wrap;
line-height:1.85;
background:var(--soft);
border-radius:15px;
padding:15px;
margin-top:12px;
min-height:55px
}

.status{
color:var(--muted);
font-size:13px;
margin-top:8px
}

.chatbox{
max-height:430px;
overflow:auto;
padding:4px
}

.msg{
padding:12px 14px;
border-radius:14px;
margin:8px 0;
line-height:1.75;
white-space:pre-wrap
}

.msg.user{
background:var(--soft);
margin-left:15%
}

.msg.ai{
background:var(--bg);
margin-right:8%
}

.modal{
display:none;
position:fixed;
inset:0;
background:#0008;
z-index:10;
padding:18px;
overflow:auto
}

.modal.show{
display:block
}

.modalbox{
max-width:700px;
margin:40px auto;
background:var(--card);
color:var(--text);
border-radius:20px;
padding:18px
}

.small{
font-size:12px;
color:var(--muted)
}

.pill{
display:inline-block;
padding:6px 9px;
border-radius:20px;
background:var(--soft);
margin:3px
}

footer{
text-align:center;
color:var(--muted);
padding:25px 5px
}

.danger-text{
color:var(--danger)
}

.loading{
animation:pulse 1s infinite
}

@keyframes pulse{
50%{opacity:.5}
}

@media(max-width:600px){

.wrap{
padding:8px
}

.hero h2{
font-size:23px
}

.grid{
grid-template-columns:repeat(2,1fr)
}

.brand p{
font-size:11px
}

.brand h1{
font-size:23px
}

.msg.user{
margin-left:5%
}

.msg.ai{
margin-right:5%
}

}
</style>
</head>

<body>

<div class="wrap">

<header>

<div class="brand">
<div class="logo">🩺</div>

<div>
<h1>MedAI</h1>
<p>ستاسو هوښیار طبي معلوماتي مرستیال</p>
</div>
</div>

<div class="actions">
<button class="secondary" onclick="toggleDark()">🌙</button>
<button class="secondary" onclick="openModal('account')">👤 حساب</button>
<button class="secondary" onclick="openModal('language')">🌐 ژبه</button>
</div>

</header>


<section class="hero">

<h2>ښه راغلاست 👋</h2>

<p>
خپله طبي پوښتنه ولیکئ.
MedAI د تعلیمي طبي معلوماتو لپاره جوړ شوی او د ډاکټر بدیل نه دی.
</p>

</section>


<section class="card">

<h3>🤖 MedAI Chat</h3>

<div class="chatbox" id="chatbox">

<div class="msg ai">
سلام! زه MedAI یم.
خپله طبي پوښتنه ولیکئ.
</div>

</div>

<textarea
id="question"
placeholder="خپله پوښتنه دلته ولیکئ..."
></textarea>

<div class="row">

<button id="askBtn" onclick="askAI()">
🤖 پوښتنه
</button>

<button class="secondary" onclick="startVoice()">
🎤 Voice
</button>

<button class="secondary" onclick="speakAnswer()">
🔊 واورئ
</button>

<button class="secondary" onclick="stopVoice()">
⏹️ Stop
</button>

<button class="secondary" onclick="saveFavorite()">
⭐ خوندي
</button>

</div>

<div id="status" class="status"></div>

<div id="answer" class="result">
ځواب به دلته ښکاره شي.
</div>

</section>


<section class="card">

<h3>⚕️ طبي موضوعات</h3>

<div class="grid">

<div class="tile" onclick="askPreset('د شکر یا Diabetes په اړه مهم معلومات')">
🩸<b>شکر</b>
</div>

<div class="tile" onclick="askPreset('د وینې د لوړ فشار په اړه معلومات')">
❤️<b>فشار</b>
</div>

<div class="tile" onclick="askPreset('د زړه ناروغیو په اړه معلومات')">
🫀<b>زړه</b>
</div>

<div class="tile" onclick="askPreset('د Asthma په اړه معلومات')">
🫁<b>سالنډۍ</b>
</div>

<div class="tile" onclick="askPreset('د سرطان په اړه عمومي معلومات')">
🎗️<b>سرطان</b>
</div>

<div class="tile" onclick="askPreset('د پښتورګو ناروغیو په اړه معلومات')">
🫘<b>پښتورګي</b>
</div>

<div class="tile" onclick="askPreset('د ځیګر ناروغیو په اړه معلومات')">
🧡<b>ځیګر</b>
</div>

<div class="tile" onclick="askPreset('د انتانونو په اړه معلومات')">
🦠<b>انتان</b>
</div>

</div>
</section>


<section class="card">

<h3>🛠️ طبي وسایل</h3>

<div class="grid">

<div class="tile"
onclick="askPreset('د دې نښو په اړه معلومات: ')">
🩺<b>Symptoms</b>
</div>

<div class="tile"
onclick="askPreset('Vital signs څه دي او د هر یوه اهمیت څه دی؟')">
❤️<b>Vitals</b>
</div>

<div class="tile"
onclick="askPreset('د دوو ناروغیو مقایسه وکړئ: ')">
⚖️<b>Compare</b>
</div>

<div class="tile"
onclick="askPreset('د Doctor Assistant په توګه دا طبي معلومات تشریح کړه: ')">
👨‍⚕️<b>Doctor Assistant</b>
</div>

<div class="tile"
onclick="askPreset('دا Lab Report په ساده ژبه تشریح کړه: ')">
🧪<b>Lab Report</b>
</div>

<div class="tile"
onclick="askPreset('د دې Medicine په اړه عمومي معلومات راکړه: ')">
💊<b>Medicine</b>
</div>

<div class="tile"
onclick="askPreset('د دې طبي اصطلاح تعریف کړه: ')">
📖<b>Dictionary</b>
</div>

<div class="tile"
onclick="askPreset('د Emergency warning signs په اړه معلومات راکړه.')">
🚨<b>Emergency</b>
</div>

<div class="tile"
onclick="askPreset('د درملو Drug Interaction په اړه معلومات: ')">
💊<b>Interaction</b>
</div>

<div class="tile"
onclick="askPreset('د First Aid مهم اصول راکړه.')">
🩹<b>First Aid</b>
</div>

<div class="tile"
onclick="askPreset('Medical Glossary راکړه.')">
📚<b>Glossary</b>
</div>

<div class="tile"
onclick="askPreset('Health Risk Assessment لپاره تعلیمي پوښتنې راکړه.')">
📋<b>Risk</b>
</div>

</div>
</section>


<section class="card">

<h3>📊 روغتیا او نور</h3>

<div class="grid">

<div class="tile" onclick="openModal('tracker')">
📊<b>Health Tracker</b>
</div>

<div class="tile" onclick="openModal('reminder')">
⏰<b>Medication Reminder</b>
</div>

<div class="tile" onclick="openModal('report')">
📝<b>Health Report</b>
</div>

<div class="tile" onclick="makeQuiz()">
🧠<b>Medical Quiz</b>
</div>

<div class="tile" onclick="showHistory()">
🕘<b>History</b>
</div>

<div class="tile" onclick="showFavorites()">
⭐<b>Favorites</b>
</div>

<div class="tile" onclick="openMap()">
🗺️<b>Healthcare Map</b>
</div>

<div class="tile" onclick="openModal('about')">
ℹ️<b>About MedAI</b>
</div>

</div>
</section>


<footer>
MedAI — Educational Medical AI · Toyebullah Dawoodzay · 2026
</footer>

</div>


<div class="modal" id="modal">

<div class="modalbox" id="modalbox"></div>

</div>


<script>

let lastAnswer="";

let historyList=
JSON.parse(
localStorage.getItem("medai_history")||"[]"
);

let favorites=
JSON.parse(
localStorage.getItem("medai_favorites")||"[]"
);

let reminders=
JSON.parse(
localStorage.getItem("medai_reminders")||"[]"
);

let tracker=
JSON.parse(
localStorage.getItem("medai_tracker")||"[]"
);


function openModal(type){

const modal=document.getElementById("modal");
const box=document.getElementById("modalbox");

let html="";


if(type==="account"){

const account=
JSON.parse(
localStorage.getItem("medai_account")||"{}"
);

html=`

<h3>👤 Login / Signup</h3>

<p class="small">
دا د محلي demo حساب دی.
ریښتینی آنلاین حساب د Database/Auth خدمت ته اړتیا لري.
</p>

<input
id="email"
placeholder="Email"
value="${escapeHtml(account.email||"")}"
>

<br><br>

<input
id="name"
placeholder="نوم"
value="${escapeHtml(account.name||"")}"
>

<div class="row">

<button onclick="localAccount()">
Save Account
</button>

<button
class="secondary"
onclick="closeModal()">
Close
</button>

</div>

<div id="accountStatus" class="status"></div>
`;

}


if(type==="language"){

html=`

<h3>🌐 Language</h3>

<select id="lang">

<option>پښتو</option>
<option>دري</option>
<option>English</option>
<option>العربية</option>
<option>اردو</option>
<option>বাংলা</option>
<option>Türkçe</option>

</select>

<p class="small">
AI د پوښتنې په ژبه ځواب ورکوي.
</p>

<button onclick="closeModal()">
Done
</button>
`;

}


if(type==="tracker"){

html=`

<h3>📊 Health Tracker</h3>

<input
id="metric"
placeholder="مثلاً وزن 70kg"
>

<div class="row">

<button onclick="saveTracker()">
Save
</button>

<button
class="secondary"
onclick="closeModal()">
Close
</button>

</div>

<div>

${tracker.map(
x=>"<span class='pill'>"+
escapeHtml(x)+
"</span>"
).join("")}

</div>
`;

}


if(type==="reminder"){

html=`

<h3>⏰ Medication Reminder</h3>

<input
id="reminderText"
placeholder="د یادونې متن"
>

<br><br>

<input
id="reminderTime"
type="time"
>

<div class="row">

<button onclick="saveReminder()">
Save
</button>

<button
class="secondary"
onclick="closeModal()">
Close
</button>

</div>

<div>

${reminders.map(
x=>"<span class='pill'>"+
escapeHtml(x.text)+
" — "+escapeHtml(x.time)+
"</span>"
).join("")}

</div>
`;

}


if(type==="report"){

html=`

<h3>📝 Health Report</h3>

<textarea
id="reportText"
placeholder="خپل روغتیايي معلومات ولیکئ..."
></textarea>

<button onclick="generateReport()">
Generate
</button>

<div
id="reportOut"
class="result">
</div>
`;

}


if(type==="history"){

html=`

<h3>🕘 History</h3>

<div>

${
historyList.length
?
historyList.map(
x=>`

<div class="msg ai">

<b>${escapeHtml(x.t)}</b>

<br>

<strong>پوښتنه:</strong>
${escapeHtml(x.q)}

<br><br>

<strong>ځواب:</strong>
${escapeHtml(x.a)}

</div>
`
).join("")
:
"<p>تر اوسه History نشته.</p>"
}

</div>

<div class="row">

<button
class="danger"
onclick="clearHistory()">
Clear History
</button>

<button
class="secondary"
onclick="closeModal()">
Close
</button>

</div>
`;

}


if(type==="favorites"){

html=`

<h3>⭐ Favorites</h3>

<div>

${
favorites.length
?
favorites.map(
x=>`

<div class="msg ai">
${escapeHtml(x)}
</div>
`
).join("")
:
"<p>تر اوسه Favorite نشته.</p>"
}

</div>

<div class="row">

<button
class="danger"
onclick="clearFavorites()">
Clear Favorites
</button>

<button
class="secondary"
onclick="closeModal()">
Close
</button>

</div>
`;

}


if(type==="about"){

html=`

<h3>ℹ️ About MedAI</h3>

<p>
MedAI یو تعلیمي طبي معلوماتي AI دی.
</p>

<p>
<b>Developer:</b>
Toyebullah Dawoodzay
</p>

<p>
<b>Created:</b>
2026
</p>

<p class="small">
MedAI د ډاکټر بدیل نه دی.
د بیړني حالت پر مهال مسلکي طبي مرسته وغواړئ.
</p>

<button onclick="closeModal()">
Close
</button>
`;

}


modal.classList.add("show");
box.innerHTML=html;

}


function closeModal(){

document
.getElementById("modal")
.classList
.remove("show");

}


function escapeHtml(s){

return String(s).replace(
/[&<>"']/g,
c=>({
"&":"&amp;",
"<":"&lt;",
">":"&gt;",
'"':"&quot;",
"'":"&#39;"
}[c])
);

}


function localAccount(){

const name=
document.getElementById("name").value.trim();

const email=
document.getElementById("email").value.trim();

localStorage.setItem(
"medai_account",
JSON.stringify({
name,
email
})
);

document.getElementById(
"accountStatus"
).textContent=
"حساب په دې وسیله خوندي شو.";

}


function saveTracker(){

const value=
document
.getElementById("metric")
.value
.trim();

if(!value)return;

tracker.unshift(
new Date().toLocaleDateString()
+" — "+value
);

localStorage.setItem(
"medai_tracker",
JSON.stringify(tracker)
);

openModal("tracker");

}


function saveReminder(){

const text=
document
.getElementById("reminderText")
.value
.trim();

const time=
document
.getElementById("reminderTime")
.value;

if(!text||!time)return;

reminders.unshift({
text,
time
});

localStorage.setItem(
"medai_reminders",
JSON.stringify(reminders)
);

alert("یادونه خوندي شوه.");

openModal("reminder");

}


function addHistory(q,a){

historyList.unshift({
q,
a,
t:new Date().toLocaleString()
});

historyList=
historyList.slice(0,50);

localStorage.setItem(
"medai_history",
JSON.stringify(historyList)
);

}


function showHistory(){
openModal("history");
}


function showFavorites(){
openModal("favorites");
}


function makeQuiz(){

askPreset(
"د طب په اړه 5 تعلیمي پوښتنې جوړې کړه او هرې پوښتنې ته لنډ سم ځواب هم ورکړه."
);

}


function askPreset(text){

document.getElementById(
"question"
).value=text;

askAI();

}


function saveFavorite(){

if(!lastAnswer){
alert("لومړی یو ځواب ترلاسه کړئ.");
return;
}

favorites.unshift(lastAnswer);

favorites=
favorites.slice(0,30);

localStorage.setItem(
"medai_favorites",
JSON.stringify(favorites)
);

alert("⭐ ځواب خوندي شو.");

}


function clearHistory(){

historyList=[];

localStorage.setItem(
"medai_history",
"[]"
);

openModal("history");

}


function clearFavorites(){

favorites=[];

localStorage.setItem(
"medai_favorites",
"[]"
);

openModal("favorites");

}


function toggleDark(){

document.body.classList.toggle("dark");

localStorage.setItem(
"medai_dark",
document.body.classList.contains("dark")
?"1"
:"0"
);

}


if(
localStorage.getItem("medai_dark")==="1"
){

document.body.classList.add("dark");

}


async function askAI(){

const input=
document.getElementById("question");

const button=
document.getElementById("askBtn");

const status=
document.getElementById("status");

const output=
document.getElementById("answer");

const chat=
document.getElementById("chatbox");

const message=
input.value.trim();

if(!message)return;


chat.innerHTML+=`

<div class="msg user">
${escapeHtml(message)}
</div>

`;

input.value="";

button.disabled=true;

status.innerHTML=
'<span class="loading">MedAI فکر کوي...</span>';

output.textContent=
"لږ صبر وکړئ...";


try{

const response=
await fetch(
"/api/chat",
{
method:"POST",
headers:{
"Content-Type":
"application/json"
},
body:JSON.stringify({
message
})
}
);


const data=
await response.json();


if(!response.ok){

let errorMessage=
data.error||
"API request failed";

if(data.details){

errorMessage+=
" — "+
data.details;

}

throw new Error(
errorMessage
);

}


lastAnswer=
data.reply||
"ځواب ترلاسه نه شو.";

output.textContent=
lastAnswer;

chat.innerHTML+=`

<div class="msg ai">
${escapeHtml(lastAnswer)}
</div>

`;

addHistory(
message,
lastAnswer
);

status.textContent=
"چمتو دی";

chat.scrollTop=
chat.scrollHeight;


}catch(error){

output.textContent=
"ستونزه: "+
error.message;

status.textContent=
"API Error";

}finally{

button.disabled=false;

}

}


function speakAnswer(){

if(
lastAnswer &&
"speechSynthesis" in window
){

speechSynthesis.cancel();

const speech=
new SpeechSynthesisUtterance(
lastAnswer
);

speech.lang="ps-AF";

speechSynthesis.speak(
speech
);

}

}


function stopVoice(){

if(
"speechSynthesis" in window
){

speechSynthesis.cancel();

}

}


function startVoice(){

const Recognition=
window.SpeechRecognition||
window.webkitSpeechRecognition;

if(!Recognition){

alert(
"ستاسې براوزر Voice Input نه ملاتړ کوي."
);

return;

}

const recognition=
new Recognition();

recognition.lang="ps-AF";

recognition.interimResults=false;

recognition.onresult=function(event){

document.getElementById(
"question"
).value=
event.results[0][0].transcript;

};

recognition.onerror=function(){

alert("Voice Input کې ستونزه راغله.");

};

recognition.start();

}


function generateReport(){

const text=
document.getElementById(
"reportText"
).value.trim();

if(!text)return;

document.getElementById(
"reportOut"
).textContent=
"راپور د AI لپاره چمتو شو. که غواړئ، دا معلومات د MedAI Chat ته ولیږئ او د تعلیمي تشریح غوښتنه وکړئ.";

}


function openMap(){

window.open(
"https://www.google.com/maps/search/healthcare+hospital+near+me",
"_blank"
);

}


document
.getElementById("modal")
.addEventListener(
"click",
function(event){

if(
event.target.id==="modal"
){

closeModal();

}

}
);


document
.getElementById("question")
.addEventListener(
"keydown",
function(event){

if(
event.key==="Enter" &&
(event.ctrlKey||event.metaKey)
){

askAI();

}

}
);

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
        "status": "ok",
        "model": GEMINI_MODEL,
        "api_key_configured": bool(GEMINI_API_KEY)
    })


@app.route("/api/chat", methods=["POST"])
def chat():

    if not GEMINI_API_KEY:
        return jsonify({
            "error":
            "GEMINI_API_KEY is not configured in Vercel."
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
                        "text":
                        SYSTEM_PROMPT
                        + "\n\nUSER QUESTION:\n"
                        + message
                    }
                ]
            }
        ]
    }

    req = urllib.request.Request(
        GEMINI_URL,
        data=json.dumps(payload).encode("utf-8"),
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
                response
                .read()
                .decode("utf-8")
            )

        candidates = result.get(
            "candidates",
            []
        )

        if not candidates:

            return jsonify({
                "error":
                "Gemini returned no candidates.",
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
                "error":
                "Gemini returned an empty response.",
                "details": result
            }), 502

        return jsonify({
            "reply": text
        })

    except urllib.error.HTTPError as error:

        detail = error.read().decode(
            "utf-8",
            errors="ignore"
        )

        return jsonify({
            "error":
            f"Gemini API error: HTTP {error.code}",
            "details": detail
        }), 502

    except urllib.error.URLError as error:

        return jsonify({
            "error":
            "Could not connect to Gemini.",
            "details": str(error)
        }), 502

    except Exception as error:

        return jsonify({
            "error":
            "Server error.",
            "details": str(error)
        }), 500


@app.route("/chat", methods=["POST"])
def chat_alias():
    return chat()


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

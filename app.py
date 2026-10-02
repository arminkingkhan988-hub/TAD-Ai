from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/gemini-3.5-flash-lite:generateContent"
)

WIKIMEDIA_URL = "https://commons.wikimedia.org/w/api.php"


def ask_gemini(prompt):
    if not GEMINI_API_KEY:
        return "GEMINI_API_KEY نه دی تنظیم شوی."

    try:
        response = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ]
            },
            timeout=45
        )

        data = response.json()

        if response.status_code != 200:
            return "د AI خدمت سره ستونزه پیدا شوه."

        candidates = data.get("candidates", [])

        if not candidates:
            return "AI ځواب ورنه کړ."

        parts = candidates[0].get("content", {}).get("parts", [])

        answer = "\n".join(
            part.get("text", "")
            for part in parts
            if isinstance(part, dict)
        ).strip()

        return answer or "تش ځواب ترلاسه شو."

    except Exception:
        return "د AI سره د اړیکې ستونزه پیدا شوه."


def medical_prompt(task, text):
    return f"""
You are MedAI, an educational medical AI assistant.

Developer: Toyebullah Dawoodzay, 2026.

Rules:
- Answer in the same language as the user.
- If the user uses Pashto, answer in Pashto.
- Use simple, clear language.
- Provide educational information only.
- Do not claim to physically examine the user.
- Do not diagnose from symptoms alone.
- Do not invent medical facts.
- Do not provide personalized prescription dosing.
- Do not tell users to start, stop, or change prescription medicines.
- For emergency warning signs, recommend urgent professional medical care.
- Do not pretend to be a doctor.
- Clearly state uncertainty when information is uncertain.

TASK:
{task}

USER INPUT:
{text}
"""


def get_images(query):
    if not query:
        return []

    try:
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,
            "gsrlimit": 8,
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": 500,
            "format": "json"
        }

        response = requests.get(
            WIKIMEDIA_URL,
            params=params,
            timeout=20
        )

        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        images = []

        for page in pages.values():
            info = page.get("imageinfo", [])

            if not info:
                continue

            image = info[0]

            images.append({
                "title": page.get("title", ""),
                "url": image.get("url", ""),
                "thumbnail": image.get(
                    "thumburl",
                    image.get("url", "")
                )
            })

        return images

    except Exception:
        return []


HTML = r"""
<!DOCTYPE html>
<html lang="ps" dir="rtl">
<head>

<meta charset="UTF-8">

<meta
name="viewport"
content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"
>

<title>MedAI</title>

<style>

*{
box-sizing:border-box;
margin:0;
padding:0;
}

:root{
--bg:#f7f7f8;
--card:#ffffff;
--text:#171717;
--muted:#737373;
--border:#e5e5e5;
--green:#10a37f;
--danger:#dc2626;
}

body.dark{
--bg:#212121;
--card:#2f2f2f;
--text:#f5f5f5;
--muted:#b8b8b8;
--border:#444;
}

body{
font-family:system-ui,-apple-system,"Segoe UI",sans-serif;
background:var(--bg);
color:var(--text);
min-height:100vh;
}

button,
input,
textarea,
select{
font:inherit;
}

button{
cursor:pointer;
}

.header{
height:64px;
position:sticky;
top:0;
z-index:100;
background:var(--card);
border-bottom:1px solid var(--border);
display:flex;
align-items:center;
justify-content:space-between;
padding:0 15px;
}

.brand{
display:flex;
align-items:center;
gap:9px;
font-size:20px;
font-weight:800;
}

.logo{
width:39px;
height:39px;
border-radius:12px;
background:var(--green);
color:white;
display:flex;
align-items:center;
justify-content:center;
font-weight:900;
}

.header-buttons{
display:flex;
gap:7px;
}

.icon{
width:40px;
height:40px;
border:1px solid var(--border);
background:var(--card);
color:var(--text);
border-radius:10px;
}

.main{
max-width:900px;
margin:auto;
padding:20px 14px 120px;
}

.welcome{
text-align:center;
padding:45px 10px 25px;
}

.big-logo{
width:70px;
height:70px;
margin:auto auto 16px;
border-radius:20px;
background:var(--green);
color:#fff;
font-size:35px;
font-weight:900;
display:flex;
align-items:center;
justify-content:center;
}

.welcome h1{
font-size:30px;
margin-bottom:8px;
}

.welcome p{
color:var(--muted);
line-height:1.8;
}

.messages{
display:flex;
flex-direction:column;
gap:14px;
}

.message{
display:flex;
width:100%;
}

.message.user{
justify-content:flex-start;
}

.message.ai{
justify-content:flex-end;
}

.bubble{
max-width:90%;
padding:12px 15px;
border-radius:17px;
line-height:1.9;
white-space:pre-wrap;
}

.user .bubble{
background:var(--green);
color:white;
border-bottom-left-radius:5px;
}

.ai .bubble{
background:var(--card);
border:1px solid var(--border);
border-bottom-right-radius:5px;
}

.quick{
margin-top:25px;
}

.quick h3{
margin-bottom:12px;
}

.quick-grid{
display:grid;
grid-template-columns:repeat(4,1fr);
gap:8px;
}

.quick-btn{
background:var(--card);
color:var(--text);
border:1px solid var(--border);
border-radius:12px;
padding:12px 6px;
min-height:70px;
}

.quick-btn:hover{
border-color:var(--green);
}

.composer-wrap{
position:fixed;
left:0;
right:0;
bottom:0;
z-index:90;
padding:22px 12px 12px;
background:linear-gradient(transparent,var(--bg) 30%);
}

.composer{
max-width:900px;
margin:auto;
display:flex;
align-items:flex-end;
gap:5px;
padding:7px;
background:var(--card);
border:1px solid var(--border);
border-radius:18px;
box-shadow:0 4px 25px rgba(0,0,0,.12);
}

.composer textarea{
flex:1;
border:0;
outline:0;
resize:none;
background:transparent;
color:var(--text);
padding:10px;
min-height:45px;
max-height:130px;
}

.send,
.voice{
width:43px;
height:43px;
border-radius:12px;
border:0;
display:flex;
align-items:center;
justify-content:center;
}

.send{
background:var(--green);
color:white;
}

.voice{
background:transparent;
color:var(--text);
}

.overlay{
display:none;
position:fixed;
inset:0;
background:rgba(0,0,0,.45);
z-index:200;
}

.overlay.open{
display:block;
}

.menu{
position:fixed;
top:0;
right:-340px;
width:320px;
max-width:90vw;
height:100vh;
background:var(--card);
z-index:210;
overflow-y:auto;
transition:.25s;
box-shadow:-10px 0 30px rgba(0,0,0,.2);
}

.menu.open{
right:0;
}

.menu-head{
padding:16px;
display:flex;
align-items:center;
justify-content:space-between;
border-bottom:1px solid var(--border);
}

.menu-title{
font-size:19px;
font-weight:800;
}

.menu-section{
padding:10px;
}

.menu-label{
font-size:12px;
color:var(--muted);
padding:8px;
}

.menu-item{
width:100%;
border:0;
background:transparent;
color:var(--text);
padding:12px;
border-radius:10px;
text-align:right;
display:flex;
align-items:center;
gap:10px;
}

.menu-item:hover{
background:var(--bg);
}

.tool{
display:none;
}

.tool.active{
display:block;
}

.tool-head{
display:flex;
align-items:center;
gap:10px;
margin-bottom:15px;
}

.back{
width:40px;
height:40px;
border:1px solid var(--border);
border-radius:10px;
background:var(--card);
color:var(--text);
}

.card{
background:var(--card);
border:1px solid var(--border);
border-radius:16px;
padding:16px;
margin-bottom:14px;
}

.card h3{
margin-bottom:12px;
}

.field{
margin-bottom:12px;
}

.field label{
display:block;
margin-bottom:6px;
font-size:14px;
}

.input{
width:100%;
border:1px solid var(--border);
border-radius:10px;
background:var(--bg);
color:var(--text);
padding:12px;
outline:none;
}

.input:focus{
border-color:var(--green);
}

.primary{
width:100%;
border:0;
border-radius:10px;
background:var(--green);
color:white;
padding:12px;
font-weight:700;
}

.result{
margin-top:14px;
background:var(--bg);
border-radius:12px;
padding:13px;
line-height:1.9;
white-space:pre-wrap;
}

.image-grid{
display:grid;
grid-template-columns:repeat(2,1fr);
gap:10px;
margin-top:14px;
}

.image-card{
border:1px solid var(--border);
border-radius:12px;
overflow:hidden;
background:var(--card);
}

.image-card img{
width:100%;
height:160px;
object-fit:cover;
display:block;
}

.image-card p{
padding:8px;
font-size:12px;
}

.history{
padding:12px;
border-bottom:1px solid var(--border);
cursor:pointer;
}

.history small{
color:var(--muted);
}

@media(max-width:700px){

.quick-grid{
grid-template-columns:repeat(2,1fr);
}

.bubble{
max-width:95%;
}

.image-grid{
grid-template-columns:1fr;
}

.welcome{
padding-top:30px;
}

.welcome h1{
font-size:26px;
}

}

</style>

</head>

<body>

<header class="header">

<div class="brand">
<div class="logo">M</div>
<span>MedAI</span>
</div>

<div class="header-buttons">

<button class="icon" onclick="toggleDark()">🌙</button>

<button class="icon" onclick="openMenu()">☰</button>

</div>

</header>


<main class="main">

<section id="home">

<div class="welcome">

<div class="big-logo">M</div>

<h1>MedAI</h1>

<p>
ستا د طبي معلوماتو هوښیار AI مرستیال
</p>

</div>

<div id="messages" class="messages"></div>


<div class="quick">

<h3>چټک طبي موضوعات</h3>

<div class="quick-grid">

<button class="quick-btn" onclick="quick('د شکر ناروغۍ په اړه معلومات راکړه')">
🩸<br>شکر
</button>

<button class="quick-btn" onclick="quick('د لوړ فشار په اړه معلومات راکړه')">
❤️<br>فشار
</button>

<button class="quick-btn" onclick="quick('د زړه ناروغۍ په اړه معلومات راکړه')">
❤️<br>زړه
</button>

<button class="quick-btn" onclick="quick('د سالنډۍ په اړه معلومات راکړه')">
🫁<br>سالنډي
</button>

<button class="quick-btn" onclick="quick('د سرطان په اړه عمومي معلومات راکړه')">
🧬<br>سرطان
</button>

<button class="quick-btn" onclick="quick('د پښتورګو ناروغۍ په اړه معلومات راکړه')">
🫘<br>پښتورګي
</button>

<button class="quick-btn" onclick="quick('د ځیګر ناروغۍ په اړه معلومات راکړه')">
🫀<br>ځیګر
</button>

<button class="quick-btn" onclick="quick('د انتان په اړه معلومات راکړه')">
🦠<br>انتان
</button>

</div>

</div>

</section>


<section id="tool" class="tool">

<div class="tool-head">

<button class="back" onclick="backHome()">→</button>

<h2 id="toolTitle">MedAI</h2>

</div>

<div id="toolContent"></div>

</section>

</main>


<div class="composer-wrap">

<div class="composer">

<button class="voice" onclick="voice()">🎤</button>

<textarea
id="input"
rows="1"
placeholder="خپله طبي پوښتنه ولیکئ..."
></textarea>

<button class="send" onclick="send()">➤</button>

</div>

</div>


<div id="overlay" class="overlay" onclick="closeMenu()"></div>


<aside id="menu" class="menu">

<div class="menu-head">

<div class="menu-title">MedAI Menu</div>

<button class="icon" onclick="closeMenu()">✕</button>

</div>


<div class="menu-section">

<div class="menu-label">طبي AI وسایل</div>

<button class="menu-item" onclick="tool('symptoms')">
🩺 د نښو معلومات
</button>

<button class="menu-item" onclick="tool('vitals')">
❤️ Vital Signs
</button>

<button class="menu-item" onclick="tool('compare')">
⚖️ د ناروغیو پرتله
</button>

<button class="menu-item" onclick="tool('doctor')">
👨‍⚕️ Doctor Assistant
</button>

<button class="menu-item" onclick="tool('lab')">
🧪 Lab Report
</button>

<button class="menu-item" onclick="tool('medicine')">
💊 Medicine Info
</button>

<button class="menu-item" onclick="tool('dictionary')">
📖 Medical Dictionary
</button>

<button class="menu-item" onclick="tool('emergency')">
🚨 Emergency Checker
</button>

<button class="menu-item" onclick="tool('interaction')">
💊 Drug Interaction
</button>

<button class="menu-item" onclick="tool('report')">
📄 Medical Report
</button>

<button class="menu-item" onclick="tool('firstaid')">
🩹 First Aid
</button>

<button class="menu-item" onclick="tool('glossary')">
📚 Medical Glossary
</button>

<button class="menu-item" onclick="tool('risk')">
📊 Risk Assessment
</button>

<button class="menu-item" onclick="tool('health')">
📋 Health Report
</button>

<button class="menu-item" onclick="tool('images')">
🖼️ Medical Images
</button>

<button class="menu-item" onclick="tool('quiz')">
🧠 Medical Quiz
</button>

</div>


<div class="menu-section">

<div class="menu-label">Health</div>

<button class="menu-item" onclick="tracker()">
📈 Health Tracker
</button>

<button class="menu-item" onclick="reminders()">
⏰ Medicine Reminder
</button>

</div>


<div class="menu-section">

<div class="menu-label">نور</div>

<button class="menu-item" onclick="historyPage()">
🕘 History
</button>

<button class="menu-item" onclick="favorites()">
⭐ Favorites
</button>

<button class="menu-item" onclick="about()">
ℹ️ About MedAI
</button>

</div>

</aside>


<script>

const $ = id => document.getElementById(id);

let historyData =
JSON.parse(localStorage.getItem("medai_history") || "[]");

let favoritesData =
JSON.parse(localStorage.getItem("medai_favorites") || "[]");

let remindersData =
JSON.parse(localStorage.getItem("medai_reminders") || "[]");

let trackerData =
JSON.parse(localStorage.getItem("medai_tracker") || "[]");


function openMenu(){

$("menu").classList.add("open");
$("overlay").classList.add("open");

}


function closeMenu(){

$("menu").classList.remove("open");
$("overlay").classList.remove("open");

}


function toggleDark(){

document.body.classList.toggle("dark");

localStorage.setItem(
"medai_dark",
document.body.classList.contains("dark")
);

}


if(localStorage.getItem("medai_dark")==="true"){
document.body.classList.add("dark");
}


function addMessage(role,text){

const wrap=document.createElement("div");

wrap.className="message "+role;

const bubble=document.createElement("div");

bubble.className="bubble";

bubble.textContent=text;

wrap.appendChild(bubble);

$("messages").appendChild(wrap);

window.scrollTo({
top:document.body.scrollHeight,
behavior:"smooth"
});

return wrap;

}


async function send(){

const input=$("input");

const text=input.value.trim();

if(!text)return;

addMessage("user",text);

input.value="";

const loading=addMessage(
"ai",
"AI ځواب جوړوي..."
);

try{

const response=await fetch("/chat",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({
message:text
})

});

const data=await response.json();

loading.remove();

const answer=data.answer||data.error||"ځواب ترلاسه نه شو.";

addMessage("ai",answer);

saveHistory(text,answer);

speak(answer);

}catch(error){

loading.remove();

addMessage(
"ai",
"د سرور سره اړیکه ناکامه شوه."
);

}

}


function quick(text){

$("input").value=text;

send();

}


$("input").addEventListener(
"keydown",
function(e){

if(e.key==="Enter"&&!e.shiftKey){

e.preventDefault();

send();

}

});


function voice(){

const Recognition=
window.SpeechRecognition||
window.webkitSpeechRecognition;

if(!Recognition){

alert("ستاسې براوزر Voice Recognition نه ملاتړ کوي.");

return;

}

const recognition=new Recognition();

recognition.lang="ps-AF";

recognition.interimResults=false;

recognition.onresult=function(e){

$("input").value=
e.results[0][0].transcript;

};

recognition.start();

}


function speak(text){

if(!window.speechSynthesis)return;

const utterance=
new SpeechSynthesisUtterance(text);

utterance.lang="ps-AF";

speechSynthesis.cancel();

speechSynthesis.speak(utterance);

}


function backHome(){

$("tool").classList.remove("active");

$("home").style.display="block";

}


function showTool(title,html){

closeMenu();

$("home").style.display="none";

$("tool").classList.add("active");

$("toolTitle").textContent=title;

$("toolContent").innerHTML=html;

}


function tool(name){

if(name==="symptoms"){

showTool(
"د نښو معلومات",
`
<div class="card">

<h3>🩺 د نښو معلومات</h3>

<div class="field">

<label>نښې ولیکئ</label>

<textarea
id="x"
class="input"
rows="6"
placeholder="مثلاً تبه، ټوخی، سر درد..."
></textarea>

</div>

<button
class="primary"
onclick="run('/symptoms',{symptoms:$('x').value},'r')"
>
تحلیل
</button>

<div id="r" class="result"></div>

</div>
`
);

}


else if(name==="vitals"){

showTool(
"Vital Signs",
`
<div class="card">

<h3>❤️ Vital Signs</h3>

<div class="field">
<label>Blood Pressure</label>
<input id="a" class="input" placeholder="120/80">
</div>

<div class="field">
<label>Pulse</label>
<input id="b" class="input" placeholder="72">
</div>

<div class="field">
<label>Temperature</label>
<input id="c" class="input" placeholder="37">
</div>

<div class="field">
<label>Oxygen</label>
<input id="d" class="input" placeholder="98%">
</div>

<button class="primary"
onclick="run('/vitals',{
bp:$('a').value,
pulse:$('b').value,
temperature:$('c').value,
oxygen:$('d').value
},'r')"
>
ارزونه
</button>

<div id="r" class="result"></div>

</div>
`
);

}


else if(name==="compare"){

showTool(
"د ناروغیو پرتله",
`
<div class="card">

<h3>⚖️ Compare</h3>

<input id="a" class="input" placeholder="لومړۍ ناروغي">

<br><br>

<input id="b" class="input" placeholder="دوهمه ناروغي">

<br><br>

<button class="primary"
onclick="run('/compare',{
disease1:$('a').value,
disease2:$('b').value
},'r')"
>
پرتله
</button>

<div id="r" class="result"></div>

</div>
`
);

}


else if(name==="doctor"){

showTool(
"Doctor Assistant",
`
<div class="card">

<h3>👨‍⚕️ Doctor Assistant</h3>

<textarea
id="x"
class="input"
rows="8"
placeholder="د ناروغ معلومات..."
></textarea>

<br><br>

<button class="primary"
onclick="run('/doctor',{text:$('x').value},'r')"
>
تحلیل
</button>

<div id="r" class="result"></div>

</div>
`
);

}


else if(name==="lab"){

showTool(
"Lab Report",
`
<div class="card">

<h3>🧪 Lab Report</h3>

<textarea
id="x"
class="input"
rows="9"
placeholder="د لابراتوار پایلې..."
></textarea>

<br><br>

<button class="primary"
onclick="run('/lab',{text:$('x').value},'r')"
>
تشریح
</button>

<div id="r" class="result"></div>

</div>
`
);

}


else if(name==="medicine"){

showTool(
"Medicine Info",
`
<div class="card">

<h3>💊 Medicine Info</h3>

<input
id="x"
class="input"
placeholder="د دوا نوم"
>

<br><br>

<button class="primary"
onclick="run('/medicine',{medicine:$('x').value},'r')"
>
معلومات
</button>

<div id="r" class="result"></div>

</div>
`
);

}


else if(name==="dictionary"){

showTool(
"Medical Dictionary",
`
<div class="card">

<h3>📖 Medical Dictionary</h3>

<input
id="x"
class="input"
placeholder="Medical term"
>

<br><br>

<button class="primary"
onclick="run('/dictionary',{term:$('x').value},'r')"
>
تشریح
</button>

<div id="r" class="result"></div>

</div>
`
);

}


else if(name==="emergency"){

showTool(
"Emergency Checker",
`
<div class="card">

<h3>🚨 Emergency Checker</h3>

<textarea
id="x"
class="input"
rows="7"
placeholder="د حالت معلومات..."
></textarea>

<br><br>

<button class="primary"
onclick="run('/emergency',{text:$('x').value},'r')"
>
ارزونه
</button>

<div id="r" class="result"></div>

</div>
`
);

}


else if(name==="interaction"){

showTool(
"Drug Interaction",
`
<div class="card">

<h3>💊 Drug Interaction</h3>

<input id="a" class="input" placeholder="لومړۍ دوا">

<br><br>

<input id="b" class="input" placeholder="دوهمه دوا">

<br><br>

<button class="primary"
onclick="run('/interaction',{
drug1:$('a').value,
drug2:$('b').value
},'r')"
>
بررسی
</button>

<div id="r" class="result"></div>

</div>
`
);

}


else if(name==="report"){

showTool(
"Medical Report",
`
<div class="card">

<h3>📄 Medical Report</h3>

<textarea
id="x"
class="input"
rows="9"
placeholder="طبي معلومات..."
></textarea>

<br><br>

<button class="primary"
onclick="run('/report',{text:$('x').value},'r')"
>
راپور جوړول
</button>

<div id="r" class="result"></div>

</div>
`
);

}


else if(name==="firstaid"){

showTool(
"First Aid",
`
<div class="card">

<h3>🩹 First Aid</h3>

<input
id="x"
class="input"
placeholder="مثلاً سوځېدنه"
>

<br><br>

<button class="primary"
onclick="run('/firstaid',{text:$('x').value},'r')"
>
لارښوونې
</button>

<div id="r" class="result"></div>

</div>
`
);

}


else if(name==="glossary"){

showTool(
"Medical Glossary",
`
<div class="card">

<h3>📚 Medical Glossary</h3>

<input
id="x"
class="input"
placeholder="طبي اصطلاح"
>

<br><br>

<button class="primary"
onclick="run('/glossary',{term:$('x').value},'r')"
>
تشریح
</button>

<div id="r" class="result"></div>

</div>
`
);

}


else if(name==="risk"){

showTool(
"Risk Assessment",
`
<div class="card">

<h3>📊 Risk Assessment</h3>

<textarea
id="x"
class="input"
rows="8"
placeholder="عمومي روغتیايي معلومات..."
></textarea>

<br><br>

<button class="primary"
onclick="run('/risk',{text:$('x').value},'r')"
>
ارزونه
</button>

<div id="r" class="result"></div>

</div>
`
);

}


else if(name==="health"){

showTool(
"Health Report",
`
<div class="card">

<h3>📋 Health Report</h3>

<button class="primary"
onclick="run('/health-report',{
tracker:${JSON.stringify(trackerData)}
},'r')"
>
راپور جوړول
</button>

<div id="r" class="result"></div>

</div>
`
);

}


else if(name==="images"){

showTool(
"Medical Images",
`
<div class="card">

<h3>🖼️ Medical Images</h3>

<input
id="x"
class="input"
placeholder="مثلاً human heart anatomy"
>

<br><br>

<button class="primary"
onclick="imagesSearch()"
>
انځورونه پیدا کړه
</button>

<div id="r" class="image-grid"></div>

</div>
`
);

}


else if(name==="quiz"){

showTool(
"Medical Quiz",
`
<div class="card">

<h3>🧠 Medical Quiz</h3>

<input
id="x"
class="input"
placeholder="مثلاً Anatomy"
>

<br><br>

<button class="primary"
onclick="run('/chat',{
message:'د دې طبي موضوع په اړه 5 تعلیمي multiple-choice quiz پوښتنې جوړې کړه: '+$('x').value
},'r')"
>
Quiz جوړ کړه
</button>

<div id="r" class="result"></div>

</div>
`
);

}

}


async function run(endpoint,payload,resultId){

const result=$(resultId);

result.textContent="لطفاً انتظار وکړئ...";

try{

const response=await fetch(endpoint,{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify(payload)

});

const data=await response.json();

result.textContent=
data.answer||
data.error||
"ځواب ترلاسه نه شو.";

}catch(e){

result.textContent=
"د سرور سره اړیکه ناکامه شوه.";

}

}


async function imagesSearch(){

const query=$("x").value.trim();

if(!query)return;

const result=$("r");

result.innerHTML="لټون...";

try{

const response=await fetch(
"/images?q="+encodeURIComponent(query)
);

const data=await response.json();

result.innerHTML="";

if(!data.images.length){

result.innerHTML="انځور ونه موندل شو.";

return;

}

data.images.forEach(item=>{

const div=document.createElement("div");

div.className="image-card";

const img=document.createElement("img");

img.src=item.thumbnail||item.url;

img.alt=item.title||"Medical image";

const p=document.createElement("p");

p.textContent=item.title||"";

div.appendChild(img);
div.appendChild(p);

result.appendChild(div);

});

}catch(e){

result.innerHTML="د انځورونو لټون ناکام شو.";

}

}


function tracker(){

closeMenu();

showTool(
"Health Tracker",
`
<div class="card">

<h3>📈 Health Tracker</h3>

<div class="field">
<label>وینې فشار</label>
<input id="bp" class="input" placeholder="120/80">
</div>

<div class="field">
<label>نبض</label>
<input id="pulse" class="input" placeholder="72">
</div>

<div class="field">
<label>تودوخه</label>
<input id="temp" class="input" placeholder="37">
</div>

<div class="field">
<label>وزن</label>
<input id="weight" class="input" placeholder="kg">
</div>

<div class="field">
<label>د وینې شکر</label>
<input id="sugar" class="input" placeholder="mg/dL">
</div>

<div class="field">
<label>اکسیجن</label>
<input id="oxygen" class="input" placeholder="%">
</div>

<button class="primary" onclick="saveTracker()">
ثبتول
</button>

</div>

<div class="card">

<h3>ثبت شوي معلومات</h3>

<div id="trackerList"></div>

</div>
`
);

renderTracker();

}


function saveTracker(){

trackerData.unshift({

date:new Date().toLocaleString(),

bp:$("bp").value,

pulse:$("pulse").value,

temp:$("temp").value,

weight:$("weight").value,

sugar:$("sugar").value,

oxygen:$("oxygen").value

});

trackerData=trackerData.slice(0,100);

localStorage.setItem(
"medai_tracker",
JSON.stringify(trackerData)
);

renderTracker();

}


function renderTracker(){

const list=$("trackerList");

if(!list)return;

if(!trackerData.length){

list.innerHTML="تر اوسه معلومات نشته.";

return;

}

list.innerHTML=trackerData.map(x=>`

<div class="history">

<strong>${safe(x.date)}</strong><br>

فشار: ${safe(x.bp||"-")}
<br>

نبض: ${safe(x.pulse||"-")}
<br>

تودوخه: ${safe(x.temp||"-")}
<br>

وزن: ${safe(x.weight||"-")}
<br>

شکر: ${safe(x.sugar||"-")}
<br>

اکسیجن: ${safe(x.oxygen||"-")}

</div>

`).join("");

}


function reminders(){

closeMenu();

showTool(
"Medicine Reminder",
`
<div class="card">

<h3>⏰ Medicine Reminder</h3>

<div class="field">
<label>دوا</label>
<input id="med" class="input" placeholder="دوا نوم">
</div>

<div class="field">
<label>وخت</label>
<input id="time" type="time" class="input">
</div>

<button class="primary" onclick="saveReminder()">
ثبتول
</button>

</div>

<div class="card">

<h3>Reminders</h3>

<div id="reminderList"></div>

</div>
`
);

renderReminders();

}


function saveReminder(){

const medicine=$("med").value.trim();

const time=$("time").value;

if(!medicine||!time){

alert("دوا او وخت ولیکئ.");

return;

}

remindersData.push({
medicine,
time
});

localStorage.setItem(
"medai_reminders",
JSON.stringify(remindersData)
);

renderReminders();

}


function renderReminders(){

const list=$("reminderList");

if(!list)return;

if(!remindersData.length){

list.innerHTML="Reminder نشته.";

return;

}

list.innerHTML=remindersData.map(
(x,i)=>`

<div class="history">

💊 ${safe(x.medicine)}

—

⏰ ${safe(x.time)}

<button
onclick="deleteReminder(${i})"
style="float:left;border:0;background:transparent;"
>
🗑️
</button>

</div>

`
).join("");

}


function deleteReminder(i){

remindersData.splice(i,1);

localStorage.setItem(
"medai_reminders",
JSON.stringify(remindersData)
);

renderReminders();

}


function saveHistory(question,answer){

historyData.unshift({
question,
answer,
date:new Date().toLocaleString()
});

historyData=historyData.slice(0,100);

localStorage.setItem(
"medai_history",
JSON.stringify(historyData)
);

}


function historyPage(){

closeMenu();

showTool(
"History",
`
<div class="card">

<h3>🕘 History</h3>

<div id="historyList"></div>

</div>
`
);

renderHistory();

}


function renderHistory(){

const list=$("historyList");

if(!list)return;

if(!historyData.length){

list.innerHTML="History تش دی.";

return;

}

list.innerHTML=historyData.map(
(x,i)=>`

<div class="history"
onclick="showHistory(${i})">

<strong>${safe(x.question)}</strong>

<br>

<small>${safe(x.date)}</small>

</div>

`
).join("");

}


function showHistory(i){

const x=historyData[i];

backHome();

addMessage("user",x.question);

addMessage("ai",x.answer);

}


function favorites(){

closeMenu();

showTool(
"Favorites",
`
<div class="card">

<h3>⭐ Favorites</h3>

<p>
Favorite معلومات دلته ساتل کېدای شي.
</p>

</div>
`
);

}


function about(){

closeMenu();

showTool(
"About MedAI",
`
<div class="card">

<h3>MedAI</h3>

<p style="line-height:2;">

MedAI د طبي معلوماتو لپاره
AI-powered educational assistant دی.

<br><br>

جوړونکی:
<strong>Toyebullah Dawoodzay</strong>

<br>

کال:
<strong>2026</strong>

<br><br>

MedAI د ډاکټر بدیل نه دی.

</p>

</div>
`
);

}


function safe(value){

return String(value||"")
.replace(/&/g,"&amp;")
.replace(/</g,"&lt;")
.replace(/>/g,"&gt;")
.replace(/"/g,"&quot;")
.replace(/'/g,"&#039;");

}

</script>

</body>
</html>
"""


@app.get("/")
def index():
    return HTML


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "app": "MedAI",
        "year": 2026
    })


@app.post("/chat")
def chat():

    data=request.get_json(silent=True) or {}

    message=str(
        data.get("message","")
    ).strip()

    if not message:
        return jsonify({
            "error":"پوښتنه ولیکئ."
        }),400

    prompt=medical_prompt(
        """
Answer the medical question clearly.
Give educational information.
Do not diagnose.
Mention emergency care when appropriate.
""",
        message
    )

    return jsonify({
        "answer":ask_gemini(prompt)
    })


@app.post("/symptoms")
def symptoms():

    data=request.get_json(silent=True) or {}

    text=str(
        data.get("symptoms","")
    ).strip()

    if not text:
        return jsonify({
            "error":"نښې ولیکئ."
        }),400

    prompt=medical_prompt(
        """
Explain possible general causes and significance
of these symptoms.
Do not diagnose.
Explain warning signs and when medical evaluation
may be appropriate.
""",
        text
    )

    return jsonify({
        "answer":ask_gemini(prompt)
    })


@app.post("/vitals")
def vitals():

    data=request.get_json(silent=True) or {}

    text=f"""
Blood pressure: {data.get("bp","")}
Pulse: {data.get("pulse","")}
Temperature: {data.get("temperature","")}
Oxygen saturation: {data.get("oxygen","")}
"""

    prompt=medical_prompt(
        """
Explain these vital signs educationally.
Interpretation depends on age, context and measurement.
Do not diagnose.
Mention urgent care for potentially dangerous findings.
""",
        text
    )

    return jsonify({
        "answer":ask_gemini(prompt)
    })


@app.post("/compare")
def compare():

    data=request.get_json(silent=True) or {}

    disease1=str(
        data.get("disease1","")
    ).strip()

    disease2=str(
        data.get("disease2","")
    ).strip()

    if not disease1 or not disease2:
        return jsonify({
            "error":"دواړه ناروغۍ ولیکئ."
        }),400

    prompt=medical_prompt(
        """
Compare these two conditions educationally.
Discuss definitions, common symptoms,
causes/risk factors, diagnosis and general management.
Do not diagnose the user.
""",
        f"""
{disease1}
{disease2}
"""
    )

    return jsonify({
        "answer":ask_gemini(prompt)
    })


@app.post("/doctor")
def doctor():

    data=request.get_json(silent=True) or {}

    text=str(
        data.get("text","")
    ).strip()

    if not text:
        return jsonify({
            "error":"معلومات ولیکئ."
        }),400

    prompt=medical_prompt(
        """
Organize the information into key facts,
possible considerations, important questions,
red flags and general educational next steps.
Do not prescribe medication.
""",
        text
    )

    return jsonify({
        "answer":ask_gemini(prompt)
    })


@app.post("/lab")
def lab():

    data=request.get_json(silent=True) or {}

    text=str(
        data.get("text","")
    ).strip()

    if not text:
        return jsonify({
            "error":"د لابراتوار نتیجه ولیکئ."
        }),400

    prompt=medical_prompt(
        """
Explain the provided laboratory results in simple language.
Explain what each test generally measures and why reference
ranges differ. Do not diagnose.
""",
        text
    )

    return jsonify({
        "answer":ask_gemini(prompt)
    })


@app.post("/medicine")
def medicine():

    data=request.get_json(silent=True) or {}

    name=str(
        data.get("medicine","")
    ).strip()

    if not name:
        return jsonify({
            "error":"د دوا نوم ولیکئ."
        }),400

    prompt=medical_prompt(
        """
Give general information about this medicine including
common uses, common side effects, warnings and general
interaction considerations.
Do not provide personalized dosing.
Do not tell the user to start or stop prescription medicine.
""",
        name
    )

    return jsonify({
        "answer":ask_gemini(prompt)
    })


@app.post("/dictionary")
def dictionary():

    data=request.get_json(silent=True) or {}

    term=str(
        data.get("term","")
    ).strip()

    if not term:
        return jsonify({
            "error":"طبي اصطلاح ولیکئ."
        }),400

    prompt=medical_prompt(
        """
Define the medical term in simple language.
Give a short definition and clinical context.
""",
        term
    )

    return jsonify({
        "answer":ask_gemini(prompt)
    })


@app.post("/emergency")
def emergency():

    data=request.get_json(silent=True) or {}

    text=str(
        data.get("text","")
    ).strip()

    if not text:
        return jsonify({
            "error":"د حالت معلومات ولیکئ."
        }),400

    prompt=medical_prompt(
        """
Look for possible emergency warning signs.
If such signs may be present, clearly recommend
urgent professional/emergency medical care.
Do not claim certainty from text alone.
""",
        text
    )

    return jsonify({
        "answer":ask_gemini(prompt)
    })


@app.post("/interaction")
def interaction():

    data=request.get_json(silent=True) or {}

    drug1=str(
        data.get("drug1","")
    ).strip()

    drug2=str(
        data.get("drug2","")
    ).strip()

    if not drug1 or not drug2:
        return jsonify({
            "error":"دواړه د دوا نومونه ولیکئ."
        }),400

    prompt=medical_prompt(
        """
Explain general known interaction concerns between
these medicines. Be careful about brand names and uncertainty.
Do not give personalized prescribing instructions.
""",
        f"""
Medicine 1: {drug1}
Medicine 2: {drug2}
"""
    )

    return jsonify({
        "answer":ask_gemini(prompt)
    })


@app.post("/report")
def report():

    data=request.get_json(silent=True) or {}

    text=str(
        data.get("text","")
    ).strip()

    if not text:
        return jsonify({
            "error":"معلومات ولیکئ."
        }),400

    prompt=medical_prompt(
        """
Create a clear educational medical summary.
Do not invent missing information.
""",
        text
    )

    return jsonify({
        "answer":ask_gemini(prompt)
    })


@app.post("/firstaid")
def firstaid():

    data=request.get_json(silent=True) or {}

    text=str(
        data.get("text","")
    ).strip()

    if not text:
        return jsonify({
            "error":"د حالت نوم ولیکئ."
        }),400

    prompt=medical_prompt(
        """
Provide general first-aid educational guidance.
Clearly identify situations requiring emergency care.
Do not provide unsafe specialized procedures.
""",
        text
    )

    return jsonify({
        "answer":ask_gemini(prompt)
    })


@app.post("/glossary")
def glossary():

    data=request.get_json(silent=True) or {}

    term=str(
        data.get("term","")
    ).strip()

    if not term:
        return jsonify({
            "error":"اصطلاح ولیکئ."
        }),400

    prompt=medical_prompt(
        """
Explain this medical terminology term for a beginner.
""",
        term
    )

    return jsonify({
        "answer":ask_gemini(prompt)
    })


@app.post("/risk")
def risk():

    data=request.get_json(silent=True) or {}

    text=str(
        data.get("text","")
    ).strip()

    if not text:
        return jsonify({
            "error":"معلومات ولیکئ."
        }),400

    prompt=medical_prompt(
        """
Discuss general health risk factors present in the
provided information. Do not diagnose and do not claim
to calculate a validated risk score.
""",
        text
    )

    return jsonify({
        "answer":ask_gemini(prompt)
    })


@app.post("/health-report")
def health_report():

    data=request.get_json(silent=True) or {}

    tracker=data.get("tracker",[])

    prompt=medical_prompt(
        """
Create an educational health-tracker summary.
Describe only trends supported by the supplied data.
Do not diagnose.
""",
        str(tracker)
    )

    return jsonify({
        "answer":ask_gemini(prompt)
    })


@app.get("/images")
def images():

    query=request.args.get("q","").strip()

    return jsonify({
        "images":get_images(query)
    })


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT",5000)),
        debug=False
    )

from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent"
WIKIMEDIA_URL = "https://commons.wikimedia.org/w/api.php"


def ask_gemini(prompt):
    if not GEMINI_API_KEY:
        return "GEMINI_API_KEY نه دی تنظیم شوی."
    try:
        r = requests.post(
            GEMINI_URL, params={"key": GEMINI_API_KEY},
            json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60
        )
        if r.status_code != 200:
            return "د AI سره د اړیکې پر مهال ستونزه رامنځته شوه."
        data = r.json()
        for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
            if part.get("text"):
                return part["text"]
        return "AI ځواب ورنه کړ."
    except requests.exceptions.Timeout:
        return "د AI ځواب ډېر وخت ونیو. بیا هڅه وکړئ."
    except Exception:
        return "د AI سره د اړیکې پر مهال ستونزه رامنځته شوه."


def build_prompt(instruction, user_text):
    return f"""
You are MedAI, an educational medical information assistant.
Developer: Toyebullah Dawoodzay. Created in 2026.

RULES:
- Answer in the SAME LANGUAGE as the user's question.
- Use simple, clear language.
- Provide educational information only.
- Do not diagnose from symptoms alone.
- Do not claim to examine the patient.
- Do not invent facts.
- Do not provide personalized prescription or medication dosing.
- Do not tell users to start, stop, or change prescription medicines.
- If emergency warning signs are present, advise urgent professional medical care.
- Do not replace a qualified healthcare professional.
- If asked who created you, say: "زه MedAI یم، د Toyebullah Dawoodzay لخوا په ۲۰۲۶ کال کې جوړ شوی یم."

TASK:
{instruction}

USER INFORMATION:
{user_text}
"""


def get_medical_images(query):
    try:
        params = {
            "action": "query", "format": "json", "generator": "search",
            "gsrsearch": query + " medical", "gsrnamespace": 6,
            "gsrlimit": 8, "prop": "imageinfo",
            "iiprop": "url", "iiurlwidth": 600
        }
        r = requests.get(
            WIKIMEDIA_URL, params=params,
            headers={"User-Agent": "MedAI/1.0"}, timeout=20
        )
        if r.status_code != 200:
            return []
        pages = r.json().get("query", {}).get("pages", {})
        out = []
        for page in pages.values():
            info = page.get("imageinfo", [])
            if info:
                url = info[0].get("thumburl") or info[0].get("url")
                if url:
                    out.append({"url": url, "title": page.get("title", "Medical Image")})
        return out
    except Exception:
        return []


HTML = r"""<!DOCTYPE html>
<html lang="ps" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="theme-color" content="#0b7fab">
<title>MedAI — Medical AI</title>
<style>
:root{--blue:#087fba;--cyan:#11b5c9;--navy:#082f49;--bg:#eef7fb;--card:#fff;--text:#102a43;--muted:#64748b;--line:#dbe8ef;--danger:#dc2626;--green:#0f9d6e}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;font-family:Arial,Tahoma,sans-serif;background:var(--bg);color:var(--text);transition:.25s}
body.dark{--bg:#071827;--card:#10283a;--text:#f1f8fc;--muted:#9fb4c3;--line:#23465c}
header{background:linear-gradient(135deg,#075985,#0b9fba);color:#fff;padding:18px 18px 26px;position:sticky;top:0;z-index:10;box-shadow:0 5px 20px #07598535}
.head{max-width:1120px;margin:auto;display:flex;align-items:center;justify-content:space-between;gap:14px}
.brand{display:flex;align-items:center;gap:12px}.logo{width:52px;height:52px;border-radius:16px;background:#fff;color:#087fba;display:grid;place-items:center;font-size:28px;box-shadow:0 6px 18px #003b5028}
h1{font-size:25px;margin:0}.sub{margin:3px 0 0;opacity:.88;font-size:13px}
.actions{display:flex;gap:7px;flex-wrap:wrap}.actions button{width:auto;margin:0;background:#ffffff18;border:1px solid #ffffff45;color:#fff}
.container{max-width:1120px;margin:auto;padding:20px 14px 50px}
.hero{background:linear-gradient(135deg,#e7f8fc,#fff);border:1px solid #ccebf2;border-radius:24px;padding:20px;margin-bottom:18px;box-shadow:0 10px 35px #07598512}
.dark .hero{background:linear-gradient(135deg,#10384a,#10283a);border-color:#24576e}
.hero h2{margin:0 0 7px;color:#075985}.dark .hero h2{color:#70e0ef}
.hero p{color:var(--muted);margin:0 0 15px}
.searchbar{display:flex;gap:8px}.searchbar textarea{min-height:74px;flex:1}
.card{background:var(--card);border:1px solid var(--line);padding:18px;border-radius:20px;margin-bottom:16px;box-shadow:0 7px 25px #0b486612}
.card h2{margin:0 0 13px;font-size:19px;color:#075985}.dark .card h2{color:#71d8e8}
textarea,input,select{width:100%;padding:12px;border:1px solid var(--line);border-radius:12px;background:var(--card);color:var(--text);font-size:15px;margin:5px 0 10px;outline:none}
textarea:focus,input:focus,select:focus{border-color:var(--cyan);box-shadow:0 0 0 3px #11b5c91c}
button{width:100%;border:0;border-radius:12px;padding:12px;margin:4px 0;background:var(--blue);color:#fff;font-size:15px;font-weight:bold;cursor:pointer;transition:.18s}
button:hover{transform:translateY(-1px);filter:brightness(1.04)}
.secondary{background:#64748b}.danger{background:var(--danger)}.success{background:var(--green)}.warning{background:#c27605}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:9px}.grid button{margin:0;background:#edf9fc;color:#075985;border:1px solid #ccebf2}.dark .grid button{background:#12384a;color:#bceef5;border-color:#24576e}
.tools{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.tool{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:15px}.tool h3{margin:0 0 6px;font-size:16px}.tool p{margin:0 0 8px;color:var(--muted);font-size:13px}
.result{margin-top:10px;padding:14px;background:#f4f9fc;border-radius:13px;line-height:1.9;white-space:pre-wrap;min-height:20px}.dark .result{background:#081c2b}
.loading{display:none;text-align:center;color:var(--blue);font-weight:bold;padding:8px}.images{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.images img{width:100%;height:160px;object-fit:cover;border-radius:13px}
.item{padding:12px;margin:7px 0;background:#f1f6f9;border-radius:12px}.dark .item{background:#081c2b}.small{color:var(--muted);font-size:12px}
footer{text-align:center;padding:28px;color:var(--muted)}
@media(max-width:850px){.tools{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:repeat(2,1fr)}.images{grid-template-columns:repeat(2,1fr)}.head{align-items:flex-start}}
@media(max-width:560px){header{padding:13px}.head{display:block}.actions{margin-top:12px}.actions button{width:auto}.container{padding:12px 10px}.hero,.card{border-radius:17px;padding:14px}.tools{grid-template-columns:1fr}.searchbar{display:block}.images{grid-template-columns:1fr}.images img{height:210px}h1{font-size:22px}}
</style>
</head>
<body>
<header><div class="head">
<div class="brand"><div class="logo">🩺</div><div><h1>MedAI</h1><div class="sub">ستاسو هوښیار طبي معلوماتي مرستیال</div></div></div>
<div class="actions"><button onclick="toggleDark()">🌙</button><button onclick="startVoice()">🎤 Voice</button><button onclick="stopVoice()">⏹️</button></div>
</div></header>

<main class="container">
<section class="hero">
<h2>سلام! MedAI ته ښه راغلاست 👋</h2>
<p>طبي پوښتنې، نښې، راپورونه او روغتیايي معلومات په ساده ژبه وڅېړئ.</p>
<div class="searchbar"><textarea id="question" rows="2" placeholder="خپله طبي پوښتنه ولیکئ..."></textarea><button onclick="askAI()">🤖 پوښتنه</button></div>
<div id="mainLoading" class="loading">AI کار کوي...</div><div id="answer" class="result"></div>
<button class="secondary" onclick="speakAnswer()">🔊 ځواب واورئ</button>
</section>

<div class="card"><h2>🩺 چټک طبي موضوعات</h2><div class="grid">
<button onclick="setTopic('Diabetes')">🩸 شکر</button><button onclick="setTopic('Hypertension')">❤️ فشار</button><button onclick="setTopic('Heart Disease')">❤️ زړه</button><button onclick="setTopic('Asthma')">🫁 ساه</button>
<button onclick="setTopic('Cancer')">🧬 سرطان</button><button onclick="setTopic('Kidney Disease')">🫘 پښتورګي</button><button onclick="setTopic('Liver Disease')">🧫 ځیګر</button><button onclick="setTopic('Infection')">🦠 انتان</button>
</div></div>

<div class="tools">
<div class="tool"><h3>🧠 نښې</h3><p>نښې په تعلیمي ډول تشریح کړئ.</p><textarea id="symptomsInput" rows="3" placeholder="تبه، ټوخی..."></textarea><button onclick="special('/symptoms','symptomsInput','symptomsResult','symptomsLoading')">تشریح</button><div id="symptomsLoading" class="loading">...</div><div id="symptomsResult" class="result"></div></div>
<div class="tool"><h3>❤️ حیاتي نښې</h3><p>فشار، نبض او نور معلومات.</p><textarea id="vitalsInput" rows="3" placeholder="140/90, pulse 85..."></textarea><button onclick="special('/vitals','vitalsInput','vitalsResult','vitalsLoading')">تشریح</button><div id="vitalsLoading" class="loading">...</div><div id="vitalsResult" class="result"></div></div>
<div class="tool"><h3>⚖️ پرتله</h3><input id="disease1" placeholder="لومړۍ ناروغي"><input id="disease2" placeholder="دوهمه ناروغي"><button onclick="compare()">پرتله</button><div id="compareLoading" class="loading">...</div><div id="compareResult" class="result"></div></div>
</div>

<div class="card"><h2>🧰 طبي وسایل</h2><div class="tools">
<div class="tool"><h3>👨‍⚕️ Doctor Assistant</h3><textarea id="doctorInput" rows="3" placeholder="خپلې نښې او معلومات..."></textarea><button onclick="special('/doctor','doctorInput','doctorResult','doctorLoading')">معلومات منظم کړه</button><div id="doctorLoading" class="loading">...</div><div id="doctorResult" class="result"></div></div>
<div class="tool"><h3>🧪 Lab Report</h3><textarea id="labInput" rows="3" placeholder="د لابراتوار راپور..."></textarea><button onclick="special('/lab','labInput','labResult','labLoading')">تشریح</button><div id="labLoading" class="loading">...</div><div id="labResult" class="result"></div></div>
<div class="tool"><h3>💊 Medicine</h3><input id="medicineInput" placeholder="د درملو نوم"><button onclick="special('/medicine','medicineInput','medicineResult','medicineLoading')">معلومات</button><div id="medicineLoading" class="loading">...</div><div id="medicineResult" class="result"></div></div>
<div class="tool"><h3>📖 Dictionary</h3><input id="dictionaryInput" placeholder="Hypertension"><button onclick="special('/dictionary','dictionaryInput','dictionaryResult','dictionaryLoading')">تشریح</button><div id="dictionaryLoading" class="loading">...</div><div id="dictionaryResult" class="result"></div></div>
<div class="tool"><h3>🚨 Emergency</h3><textarea id="emergencyInput" rows="3" placeholder="نښې ولیکئ..."></textarea><button class="danger" onclick="special('/emergency','emergencyInput','emergencyResult','emergencyLoading')">بیړنۍ نښې وګوره</button><div id="emergencyLoading" class="loading">...</div><div id="emergencyResult" class="result"></div></div>
<div class="tool"><h3>💊 Interaction</h3><textarea id="interactionInput" rows="3" placeholder="د درملو نومونه..."></textarea><button onclick="special('/interaction','interactionInput','interactionResult','interactionLoading')">تداخل وګوره</button><div id="interactionLoading" class="loading">...</div><div id="interactionResult" class="result"></div></div>
<div class="tool"><h3>📄 Report</h3><textarea id="reportInput" rows="3" placeholder="طبي راپور..."></textarea><button onclick="special('/report','reportInput','reportResult','reportLoading')">تشریح</button><div id="reportLoading" class="loading">...</div><div id="reportResult" class="result"></div></div>
<div class="tool"><h3>🩹 First Aid</h3><input id="firstAidInput" placeholder="burn, cut, nosebleed"><button onclick="special('/firstaid','firstAidInput','firstAidResult','firstAidLoading')">لومړنۍ مرسته</button><div id="firstAidLoading" class="loading">...</div><div id="firstAidResult" class="result"></div></div>
<div class="tool"><h3>🧬 Glossary</h3><textarea id="glossaryInput" rows="3" placeholder="طبي اصطلاحات..."></textarea><button onclick="special('/glossary','glossaryInput','glossaryResult','glossaryLoading')">ساده تشریح</button><div id="glossaryLoading" class="loading">...</div><div id="glossaryResult" class="result"></div></div>
</div></div>

<div class="card"><h2>🖼️ طبي انځورونه</h2><input id="imageInput" placeholder="human heart"><button onclick="loadImages()">🖼️ انځورونه ولټوه</button><div id="imageLoading" class="loading">لټول کېږي...</div><div id="images" class="images"></div></div>

<div class="card"><h2>🧠 Risk Assessment</h2><textarea id="riskInput" rows="4" placeholder="نښې، عمر، موده او اړوند معلومات..."></textarea><button class="warning" onclick="special('/risk','riskInput','riskResult','riskLoading')">د خطر نښې وڅېړه</button><div id="riskLoading" class="loading">AI کار کوي...</div><div id="riskResult" class="result"></div></div>

<div class="card"><h2>⏰ Medication Reminder</h2><input id="reminderMedicine" placeholder="د درملو نوم"><input id="reminderTime" type="time"><input id="reminderNote" placeholder="یادونه"><button onclick="addReminder()">Reminder اضافه کړه</button><div id="reminders"></div></div>

<div class="card"><h2>🩸 Health Tracker</h2><select id="trackerType"><option>Blood Pressure</option><option>Pulse</option><option>Temperature</option><option>Weight</option><option>Blood Sugar</option><option>Oxygen</option></select><input id="trackerValue" placeholder="Value"><input id="trackerNote" placeholder="یادونه"><button onclick="addTracker()">معلومات ثبت کړه</button><div id="trackerList"></div><button class="danger" onclick="clearTracker()">ټول پاک کړه</button></div>

<div class="card"><h2>📊 Health Report</h2><textarea id="healthReportInput" rows="5" placeholder="خپل روغتیايي معلومات..."></textarea><button onclick="generateHealthReport()">راپور جوړ کړه</button><div id="healthReportLoading" class="loading">AI کار کوي...</div><div id="healthReportResult" class="result"></div></div>

<div class="card"><h2>🧠 Medical Quiz</h2><button onclick="quiz()">Quiz جوړ کړه</button><div id="quizLoading" class="loading">AI کار کوي...</div><div id="quizResult" class="result"></div></div>

<div class="card"><h2>🕘 History</h2><div id="history"></div><button class="danger" onclick="clearHistory()">History پاک کړه</button></div>
<div class="card"><h2>⭐ Favorites</h2><div id="favorites"></div><button class="danger" onclick="clearFavorites()">Favorites پاک کړه</button></div>

<div class="card"><h2>👨‍💻 About MedAI</h2><p><b>Developer:</b> Toyebullah Dawoodzay</p><p><b>Created:</b> 2026</p><p class="small">MedAI د تعلیمي طبي معلوماتو لپاره جوړ شوی او د ډاکټر بدیل نه دی.</p></div>
</main>
<footer>🩺 MedAI — Educational Medical AI · Toyebullah Dawoodzay · 2026</footer>

<script>
let currentAnswer="",recognition=null;
const $=id=>document.getElementById(id);
function loading(id,show){if($(id))$(id).style.display=show?"block":"none"}
function esc(t){const d=document.createElement("div");d.textContent=t;return d.innerHTML}

async function askAI(){
 const q=$("question").value.trim(),a=$("answer"); if(!q){a.textContent="مهرباني وکړئ پوښتنه ولیکئ.";return}
 loading("mainLoading",true);a.textContent="";
 try{const r=await fetch("/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({question:q})});const d=await r.json();currentAnswer=d.answer||d.error||"";a.textContent=currentAnswer;saveHistory(q,currentAnswer)}
 catch(e){a.textContent="د سرور سره د اړیکې ستونزه."}finally{loading("mainLoading",false)}
}
async function special(endpoint,input,result,load){
 const text=$(input).value.trim();if(!text){$(result).textContent="مهرباني وکړئ معلومات ولیکئ.";return}
 loading(load,true);$(result).textContent="";
 try{const r=await fetch(endpoint,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text})});const d=await r.json();$(result).textContent=d.answer||d.error||"ځواب ترلاسه نه شو."}
 catch(e){$(result).textContent="د سرور سره د اړیکې ستونزه."}finally{loading(load,false)}
}
async function compare(){
 const a=$("disease1").value.trim(),b=$("disease2").value.trim();if(!a||!b){$("compareResult").textContent="دواړه ناروغۍ ولیکئ.";return}
 loading("compareLoading",true);try{const r=await fetch("/compare",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({disease1:a,disease2:b})});const d=await r.json();$("compareResult").textContent=d.answer||d.error||"ځواب ترلاسه نه شو."}catch(e){$("compareResult").textContent="د سرور ستونزه."}finally{loading("compareLoading",false)}
}
async function loadImages(){
 const q=$("imageInput").value.trim(),box=$("images");if(!q){box.innerHTML="<p>موضوع ولیکئ.</p>";return}
 loading("imageLoading",true);box.innerHTML="";
 try{const r=await fetch("/images?q="+encodeURIComponent(q)),d=await r.json();if(!d.images?.length){box.innerHTML="<p>انځورونه پیدا نه شول.</p>";return}
 d.images.forEach(x=>{const div=document.createElement("div"),img=document.createElement("img"),p=document.createElement("div");img.src=x.url;img.alt=x.title;img.loading="lazy";p.className="small";p.textContent=x.title;div.append(img,p);box.appendChild(div)})}
 catch(e){box.innerHTML="<p>د انځورونو ستونزه.</p>"}finally{loading("imageLoading",false)}
}
async function quiz(){loading("quizLoading",true);try{const r=await fetch("/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({question:"Create a 5-question educational medical quiz with four choices and correct answers. Answer in the same language as the user."})});const d=await r.json();$("quizResult").textContent=d.answer||d.error||"Quiz جوړ نه شو."}catch(e){$("quizResult").textContent="د Quiz ستونزه."}finally{loading("quizLoading",false)}}
function startVoice(){
 const SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR){alert("ستاسو browser Voice ملاتړ نه کوي.");return}
 recognition=new SR();recognition.lang="ps-AF";recognition.interimResults=false;recognition.continuous=false;
 recognition.onresult=e=>$("question").value=e.results[0][0].transcript;recognition.onerror=()=>alert("Voice کې ستونزه رامنځته شوه.");recognition.start()
}
function stopVoice(){if(recognition){recognition.stop();recognition=null}if("speechSynthesis"in window)speechSynthesis.cancel()}
function speakAnswer(){const t=currentAnswer||$("answer").textContent;if(!t){alert("لومړی AI ځواب ترلاسه کړئ.");return}if(!("speechSynthesis"in window)){alert("Voice Output نه شته.");return}speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(t);u.lang="ps-AF";u.rate=.9;speechSynthesis.speak(u)}
function toggleDark(){document.body.classList.toggle("dark");localStorage.setItem("medai_dark",document.body.classList.contains("dark"))}
if(localStorage.getItem("medai_dark")==="true")document.body.classList.add("dark")
function setTopic(t){$("question").value="د "+t+" په اړه طبي معلومات راکړه.";$("question").focus()}
function saveHistory(q,a){let x=JSON.parse(localStorage.getItem("medai_history")||"[]");x.unshift({question:q,answer:a,time:new Date().toLocaleString()});localStorage.setItem("medai_history",JSON.stringify(x.slice(0,30)));loadHistory()}
function loadHistory(){const c=$("history"),x=JSON.parse(localStorage.getItem("medai_history")||"[]");c.innerHTML=x.length?x.map((i,n)=>`<div class="item"><b>${esc(i.question)}</b><div class="small">${esc(i.time)}</div><p>${esc(i.answer)}</p><button onclick="favorite(${n})">⭐ Favorite</button></div>`).join(""):"<p class='small'>History خالي دی.</p>"}
function clearHistory(){localStorage.removeItem("medai_history");loadHistory()}
function favorite(n){let h=JSON.parse(localStorage.getItem("medai_history")||"[]"),f=JSON.parse(localStorage.getItem("medai_favorites")||"[]");if(h[n])f.unshift(h[n]);localStorage.setItem("medai_favorites",JSON.stringify(f.slice(0,30)));loadFavorites()}
function loadFavorites(){const c=$("favorites"),x=JSON.parse(localStorage.getItem("medai_favorites")||"[]");c.innerHTML=x.length?x.map(i=>`<div class="item"><b>${esc(i.question)}</b><div class="small">${esc(i.time)}</div><p>${esc(i.answer)}</p></div>`).join(""):"<p class='small'>Favorites خالي دي.</p>"}
function clearFavorites(){localStorage.removeItem("medai_favorites");loadFavorites()}
function addReminder(){let m=$("reminderMedicine").value.trim(),t=$("reminderTime").value,n=$("reminderNote").value.trim();if(!m||!t){alert("د درملو نوم او وخت ولیکئ.");return}let x=JSON.parse(localStorage.getItem("medai_reminders")||"[]");x.push({medicine:m,time:t,note:n});localStorage.setItem("medai_reminders",JSON.stringify(x));$("reminderMedicine").value="";$("reminderTime").value="";$("reminderNote").value="";loadReminders()}
function loadReminders(){let x=JSON.parse(localStorage.getItem("medai_reminders")||"[]");$("reminders").innerHTML=x.map((i,n)=>`<div class="item"><b>💊 ${esc(i.medicine)}</b><p>⏰ ${esc(i.time)}</p><p>${esc(i.note||"")}</p><button class="danger" onclick="deleteReminder(${n})">حذف</button></div>`).join("")}
function deleteReminder(n){let x=JSON.parse(localStorage.getItem("medai_reminders")||"[]");x.splice(n,1);localStorage.setItem("medai_reminders",JSON.stringify(x));loadReminders()}
function addTracker(){let type=$("trackerType").value,v=$("trackerValue").value.trim(),n=$("trackerNote").value.trim();if(!v){alert("Value ولیکئ.");return}let x=JSON.parse(localStorage.getItem("medai_tracker")||"[]");x.unshift({type,value:v,note:n,time:new Date().toLocaleString()});localStorage.setItem("medai_tracker",JSON.stringify(x.slice(0,100)));$("trackerValue").value="";$("trackerNote").value="";loadTracker()}
function loadTracker(){let x=JSON.parse(localStorage.getItem("medai_tracker")||"[]");$("trackerList").innerHTML=x.length?x.map((i,n)=>`<div class="item"><b>${esc(i.type)}</b><p>Value: ${esc(i.value)}</p><p>${esc(i.note||"")}</p><div class="small">${esc(i.time)}</div><button class="danger" onclick="deleteTracker(${n})">حذف</button></div>`).join(""):"<p class='small'>تر اوسه معلومات نشته.</p>"}
function deleteTracker(n){let x=JSON.parse(localStorage.getItem("medai_tracker")||"[]");x.splice(n,1);localStorage.setItem("medai_tracker",JSON.stringify(x));loadTracker()}
function clearTracker(){localStorage.removeItem("medai_tracker");loadTracker()}
async function generateHealthReport(){
 let manual=$("healthReportInput").value.trim(),tr=JSON.parse(localStorage.getItem("medai_tracker")||"[]");if(!manual&&!tr.length){$("healthReportResult").textContent="لومړی معلومات ولیکئ یا Tracker وکاروئ.";return}
 loading("healthReportLoading",true);try{const r=await fetch("/health-report",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:"User notes:\n"+manual+"\n\nHealth Tracker:\n"+JSON.stringify(tr)})});const d=await r.json();$("healthReportResult").textContent=d.answer||d.error||"راپور جوړ نه شو."}catch(e){$("healthReportResult").textContent="د راپور ستونزه."}finally{loading("healthReportLoading",false)}
}
loadHistory();loadFavorites();loadReminders();loadTracker();
</script>
</body></html>"""


@app.route("/")
def home():
    return HTML


@app.route("/chat", methods=["POST"])
def chat():
    q = str((request.get_json(silent=True) or {}).get("question", "")).strip()
    if not q:
        return jsonify({"error": "پوښتنه خالي ده."}), 400
    return jsonify({"answer": ask_gemini(build_prompt("""
Give a structured medical educational answer.
Use sections when appropriate: Definition, Causes, Types, Risk Factors,
Signs and Symptoms, Diagnosis, Treatment, Prevention, Complications,
Important Points.
""", q))})


def simple_route(name, instruction, empty):
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    if not text:
        return jsonify({"error": empty}), 400
    return jsonify({"answer": ask_gemini(build_prompt(instruction, text))})


@app.route("/symptoms", methods=["POST"])
def symptoms():
    return simple_route("symptoms", "Explain symptoms educationally, possible systems/conditions, warning signs and when professional evaluation may be appropriate. Do not diagnose.", "نښې ولیکئ.")


@app.route("/vitals", methods=["POST"])
def vitals():
    return simple_route("vitals", "Explain what the provided vital signs mean, general reference concepts, factors affecting readings and when professional evaluation may be appropriate. Do not diagnose.", "Vital signs معلومات ولیکئ.")


@app.route("/doctor", methods=["POST"])
def doctor():
    return simple_route("doctor", "Organize the notes into main concern, symptoms, onset, changes, medicines mentioned, tests/measurements and questions for a doctor. Do not add information.", "معلومات ولیکئ.")


@app.route("/lab", methods=["POST"])
def lab():
    return simple_route("lab", "Explain what the test measures, why it is used, what high/low values can sometimes be associated with, factors affecting results and why reference ranges differ. Do not diagnose.", "Lab معلومات ولیکئ.")


@app.route("/medicine", methods=["POST"])
def medicine():
    return simple_route("medicine", "Give general medicine information: what it is, common uses, general mechanism, common side effects, precautions and interaction categories. No personalized dosing.", "د درملو نوم ولیکئ.")


@app.route("/dictionary", methods=["POST"])
def dictionary():
    return simple_route("dictionary", "Explain the medical term simply with definition, why it matters and a short example.", "اصطلاح ولیکئ.")


@app.route("/emergency", methods=["POST"])
def emergency():
    return simple_route("emergency", "Look only for general emergency warning signs. Separate warning signs, other information and appropriate action. If serious warning signs exist, advise urgent professional medical care. Do not diagnose.", "نښې ولیکئ.")


@app.route("/interaction", methods=["POST"])
def interaction():
    return simple_route("interaction", "Review listed medicines for known or potentially important interactions. Explain medicines involved, possible interaction, why it matters and why pharmacist/doctor review may be needed. Do not tell user to stop/change medicines.", "د درملو نومونه ولیکئ.")


@app.route("/report", methods=["POST"])
def report():
    return simple_route("report", "Explain the medical report simply: subject, important findings, terms, tests, what findings can generally be associated with, questions for a doctor and limitations. Do not diagnose or invent missing information.", "طبي راپور ولیکئ.")


@app.route("/firstaid", methods=["POST"])
def firstaid():
    return simple_route("firstaid", "Give a general first-aid guide: immediate priorities, basic steps, what not to do, emergency warning signs and when professional evaluation is needed.", "حالت ولیکئ.")


@app.route("/glossary", methods=["POST"])
def glossary():
    return simple_route("glossary", "Explain each medical term in very simple language with meaning, medical use and short example.", "اصطلاحات ولیکئ.")


@app.route("/risk", methods=["POST"])
def risk():
    return simple_route("risk", "Review information for general medical risk indicators. Do not calculate a fake score. Identify reported factors, warning signs, missing information and when urgent/routine professional evaluation may be appropriate. Do not diagnose or predict outcome.", "معلومات ولیکئ.")


@app.route("/health-report", methods=["POST"])
def health_report():
    return simple_route("health-report", "Create an educational health summary: summary, recorded measurements, symptoms/concerns, directly observable trends, questions for a healthcare professional and limitations. Do not diagnose or invent information.", "د روغتیا معلومات ولیکئ.")


@app.route("/compare", methods=["POST"])
def compare_route():
    data = request.get_json(silent=True) or {}
    a, b = str(data.get("disease1", "")).strip(), str(data.get("disease2", "")).strip()
    if not a or not b:
        return jsonify({"error": "دواړه ناروغۍ ولیکئ."}), 400
    text = f"Disease 1: {a}\nDisease 2: {b}"
    return jsonify({"answer": ask_gemini(build_prompt("Compare definition, causes, risk factors, symptoms, diagnosis, treatment approaches, differences, similarities and warning signs. Do not diagnose.", text))})


@app.route("/images")
def images():
    q = request.args.get("q", "").strip()
    return jsonify({"images": get_medical_images(q) if q else []})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)

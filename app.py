import os, json, urllib.request, urllib.error
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
MAX_HISTORY = 20
MAX_MESSAGE = 12000

SYSTEM_PROMPT = """You are MedAI, a cautious medical information assistant.
Give clear, evidence-aware educational information. Do not claim certainty or diagnose from limited information.
For emergencies, advise immediate local emergency care. Ask useful follow-up questions when needed.
Explain symptoms, medicines, labs, first aid, prevention and general health.
Mention important contraindications/interactions when relevant. Never tell users to stop or change prescribed treatment without a clinician.
Respond in the user's language. This app is educational and does not replace a qualified clinician."""

def gemini(message, history):
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured on the server.")
    contents = []
    for item in (history or [])[-MAX_HISTORY:]:
        if not isinstance(item, dict):
            continue
        role = "model" if item.get("role") == "model" else "user"
        text = str(item.get("text", "")).strip()
        if text:
            contents.append({"role": role, "parts": [{"text": text[:MAX_MESSAGE]}]})
    if not contents or contents[-1]["parts"][0]["text"] != message:
        contents.append({"role": "user", "parts": [{"text": message}]})

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.35, "maxOutputTokens": 1800}
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type":"application/json","x-goog-api-key":GEMINI_API_KEY},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8")
        except Exception:
            detail = ""
        raise RuntimeError(f"Gemini API error ({e.code}). {detail[:500]}")
    except Exception as e:
        raise RuntimeError(f"AI connection error: {e}")

    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError("The AI returned no answer.")
    parts = (candidates[0].get("content") or {}).get("parts") or []
    answer = "".join(p.get("text","") for p in parts if isinstance(p, dict)).strip()
    return answer or "No answer was returned."

@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), geolocation=(), payment=()"
    return response

PAGE = '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<title>MedAI - Medical AI Assistant</title>\n<style>\n*{box-sizing:border-box}body{margin:0;font-family:Inter,system-ui,-apple-system,Segoe UI,sans-serif;background:#fff;color:#172033}\nbutton,input,textarea,select{font:inherit}button{cursor:pointer}.app{display:flex;height:100vh;overflow:hidden}\n.side{width:280px;background:#f7f8fa;border-right:1px solid #e5e7eb;padding:14px;display:flex;flex-direction:column;gap:10px}\n.brand{font-size:21px;font-weight:800;padding:10px 8px}.new{width:100%;padding:11px;border:1px solid #d8dde5;border-radius:10px;background:#fff;font-weight:700}\n.tools{display:grid;grid-template-columns:1fr 1fr;gap:7px;overflow:auto;padding-right:2px}.tool{border:1px solid #e1e5ea;background:#fff;border-radius:9px;padding:9px 6px;font-size:12px;text-align:left}\n.recent-title{font-size:11px;color:#697386;margin-top:5px}.recent{overflow:auto}.recent div{padding:8px;border-radius:8px;cursor:pointer;font-size:12px}.recent div:hover{background:#e9edf2}\n.main{flex:1;display:flex;flex-direction:column;min-width:0}.top{height:58px;border-bottom:1px solid #e5e7eb;display:flex;align-items:center;padding:0 18px;gap:10px}.menu{display:none;border:0;background:none;font-size:22px}.title{font-weight:750}.grow{flex:1}.icon{border:0;background:transparent;font-size:18px;padding:7px;border-radius:8px}.chat{flex:1;overflow:auto;padding:25px 18px}.wrap{max-width:900px;margin:auto}\n.welcome{text-align:center;padding:8vh 10px 30px}.logo{font-size:45px}.welcome h1{margin:10px 0 6px}.welcome p{color:#687385}.cards{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-top:25px}.card{border:1px solid #e1e5ea;background:#fff;border-radius:12px;padding:14px;text-align:left}.card b{display:block;margin-bottom:4px}.card span{font-size:13px;color:#6b7280}\n.msg{display:flex;gap:12px;margin:20px 0}.avatar{width:32px;height:32px;border-radius:50%;display:grid;place-items:center;background:#eef2f7;flex:none}.bubble{white-space:pre-wrap;line-height:1.6;max-width:800px}.user .bubble{background:#f1f3f5;padding:11px 14px;border-radius:14px}.actions{margin-top:5px}.actions button{border:0;background:none;color:#697386;font-size:12px;margin-right:7px}\n.composer{padding:12px 18px 18px}.box{max-width:900px;margin:auto;border:1px solid #cfd5dd;border-radius:15px;padding:10px;background:#fff;box-shadow:0 2px 12px #0000000b}.box textarea{width:100%;border:0;outline:0;resize:none;min-height:48px;max-height:160px}.bar{display:flex;align-items:center;gap:8px}.send{margin-left:auto;border:0;background:#111827;color:white;border-radius:9px;padding:9px 15px}.hint{text-align:center;font-size:11px;color:#8a93a1}\n.modal{position:fixed;inset:0;background:#0007;display:none;align-items:center;justify-content:center;padding:15px;z-index:20}.modal.show{display:flex}.panel{width:min(650px,100%);max-height:90vh;overflow:auto;background:#fff;border-radius:16px;padding:20px}.panel h2{margin-top:0}.close{float:right;border:0;background:none;font-size:22px}.form{display:grid;gap:10px}.form input,.form textarea,.form select{width:100%;padding:10px;border:1px solid #d1d5db;border-radius:9px}.primary{border:0;background:#111827;color:#fff;padding:10px 14px;border-radius:9px}.list{display:grid;gap:8px}.item{border:1px solid #e1e5ea;padding:10px;border-radius:9px}\n.dark{background:#111827;color:#e5e7eb}.dark .side,.dark .top{background:#151b26;border-color:#2b3442}.dark .new,.dark .tool,.dark .card,.dark .box,.dark .panel,.dark .item{background:#151b26;color:#e5e7eb;border-color:#303947}.dark .user .bubble{background:#273141}.dark .bubble{color:#e5e7eb}.dark .hint,.dark .welcome p,.dark .card span{color:#9aa5b5}\n@media(max-width:760px){.side{position:fixed;z-index:25;left:-295px;top:0;bottom:0;transition:.2s}.side.open{left:0}.menu{display:block}.cards{grid-template-columns:1fr}.chat{padding:15px 10px}.composer{padding:8px 10px 12px}}\n</style>\n</head>\n<body>\n<div class="app">\n<aside class="side" id="side">\n<div class="brand">🩺 MedAI</div>\n<button class="new" onclick="newChat()">＋ New Chat</button>\n<div class="tools" id="tools"></div>\n<div class="recent-title">RECENT CHATS</div>\n<div class="recent" id="recent"></div>\n</aside>\n<main class="main">\n<header class="top">\n<button class="menu" onclick="toggleSide()">☰</button>\n<div class="title">MedAI</div><div class="grow"></div>\n<button class="icon" onclick="openModal(\'trackerModal\')">❤️</button>\n<button class="icon" onclick="openModal(\'reminderModal\')">⏰</button>\n<button class="icon" onclick="toggleTheme()">🌙</button>\n</header>\n<section class="chat" id="chat"><div class="wrap" id="messages"></div></section>\n<div class="composer"><div class="box">\n<textarea id="input" placeholder="Describe your symptoms or ask a medical question..." rows="2"></textarea>\n<div class="bar">\n<button class="icon" onclick="voiceInput()">🎙️</button>\n<button class="icon" onclick="readLast()">🔊</button>\n<span class="hint">Educational medical information - not a diagnosis</span>\n<button class="send" onclick="send()">Send</button>\n</div></div></div>\n</main></div>\n\n<div class="modal" id="featureModal"><div class="panel">\n<button class="close" onclick="closeModal(\'featureModal\')">×</button>\n<h2 id="featureTitle"></h2><p id="featureDesc"></p>\n<div class="form"><textarea id="featureInput" rows="7"></textarea><button class="primary" onclick="runFeature()">Ask MedAI</button></div>\n</div></div>\n\n<div class="modal" id="trackerModal"><div class="panel">\n<button class="close" onclick="closeModal(\'trackerModal\')">×</button><h2>❤️ Health Tracker</h2>\n<div class="form"><input id="trackNote" placeholder="e.g. BP 120/80, weight 70 kg, symptoms..."><button class="primary" onclick="saveTracker()">Save</button></div>\n<div class="list" id="trackerList" style="margin-top:12px"></div>\n</div></div>\n\n<div class="modal" id="reminderModal"><div class="panel">\n<button class="close" onclick="closeModal(\'reminderModal\')">×</button><h2>⏰ Medicine Reminders</h2>\n<div class="form"><input id="reminderText" placeholder="Medicine / reminder"><input id="reminderTime" type="datetime-local"><button class="primary" onclick="saveReminder()">Save Reminder</button></div>\n<div class="list" id="reminderList" style="margin-top:12px"></div>\n</div></div>\n\n<script>\nconst features=[\n["🩺","Symptoms Checker","Describe symptoms, duration, age, sex, and important medical history. I will provide possible causes and warning signs."],\n["❤️","Vital Signs","Enter blood pressure, pulse, temperature, oxygen saturation, age, and symptoms for general interpretation."],\n["⚖️","Disease Compare","Name two conditions and ask for a structured comparison of symptoms, tests, treatment approaches, and red flags."],\n["👨\u200d⚕️","Doctor Assistant","Prepare a concise history, medication list, questions, and appointment summary for a clinician."],\n["🧪","Lab Report","Paste lab results with units and reference ranges. I can explain what they generally mean and what may need clinician review."],\n["💊","Medicine Info","Enter a medicine name. Ask about common uses, side effects, precautions, and questions to discuss with a pharmacist or clinician."],\n["📖","Medical Dictionary","Enter a medical term and receive a simple explanation."],\n["🚨","Emergency Checker","Describe urgent symptoms. I will highlight emergency warning signs and advise when immediate care is appropriate."],\n["💊","Drug Interaction","Enter medicines/supplements together. I can discuss possible interactions, but a pharmacist should verify the final list."],\n["🩹","First Aid","Describe a first-aid situation and I will provide general immediate-care steps and escalation signs."],\n["📊","Risk Assessment","Describe risk factors such as age, smoking, family history, symptoms, and measurements for general risk discussion."],\n["📋","Health Report","Provide your health information and I can organize it into a clinician-friendly summary."],\n["🧠","Medical Quiz","Ask for a medical quiz by topic and difficulty."],\n["📚","Medical Glossary","Ask for a list of medical terms with simple definitions."],\n["🖼️","Medical Images","Describe an image or ask what information should be collected. Direct image/vision upload is not enabled in this version."],\n["🎤","Voice Input","Use your browser microphone to dictate a medical question."],\n["🔊","Voice Output","Read the latest AI answer aloud."],\n["⏰","Medicine Reminders","Save medicine reminders locally in this browser and check them from this panel."],\n["❤️\u200d🩹","Health Tracker","Save simple health notes locally on this device."],\n["⭐","Favorites","Save useful AI answers locally."]\n];\n\nlet history=[], lastAnswer="", activeFeature=null;\nconst $=id=>document.getElementById(id);\n\nfunction escapeHtml(s){return String(s).replace(/[&<>"\']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",\'"\':"&quot;","\'":"&#39;"}[c]))}\n\nfunction renderTools(){\n $("tools").innerHTML=features.map((f,i)=>`<button class="tool" onclick="openFeature(${i})">${f[0]} ${f[1]}</button>`).join("");\n}\nfunction renderWelcome(){\n $("messages").innerHTML=`<div class="welcome"><div class="logo">🩺</div><h1>How can I help?</h1><p>AI medical information assistant</p><div class="cards">${features.slice(0,10).map((f,i)=>`<button class="card" onclick="openFeature(${i})"><b>${f[0]} ${f[1]}</b><span>${f[2]}</span></button>`).join("")}</div></div>`;\n}\nfunction renderRecent(){\n const a=JSON.parse(localStorage.getItem("medai_chats")||"[]");\n $("recent").innerHTML=a.slice(-12).reverse().map((x,i)=>`<div onclick=\'loadChat(${JSON.stringify(x).replace(/</g,"\\\\u003c")})\'>${escapeHtml(x.title||"Medical chat")}</div>`).join("");\n}\nfunction add(role,text){\n if(document.querySelector(".welcome")) $("messages").innerHTML="";\n const d=document.createElement("div"); d.className="msg "+role;\n d.innerHTML=`<div class="avatar">${role==="user"?"👤":"🩺"}</div><div><div class="bubble">${escapeHtml(text)}</div>${role==="model"?\'<div class="actions"><button onclick="copyAnswer(this)">Copy</button><button onclick="speakAnswer(this)">Read</button><button onclick="favoriteAnswer(this)">☆ Favorite</button></div>\':""}</div>`;\n $("messages").appendChild(d); $("chat").scrollTop=$("chat").scrollHeight;\n}\nfunction openFeature(i){\n activeFeature=i;$("featureTitle").textContent=features[i][0]+" "+features[i][1];\n $("featureDesc").textContent=features[i][2];$("featureInput").value="";\n openModal("featureModal");setTimeout(()=>$("featureInput").focus(),100);\n}\nfunction runFeature(){\n const text=$("featureInput").value.trim();\n if(!text){alert("Please enter information first.");return}\n closeModal("featureModal");$("input").value=features[activeFeature][1]+": "+text;send();\n}\nfunction openModal(id){$(id).classList.add("show");if(id==="trackerModal")renderTracker();if(id==="reminderModal")renderReminders()}\nfunction closeModal(id){$(id).classList.remove("show")}\nfunction toggleSide(){$("side").classList.toggle("open")}\nfunction toggleTheme(){document.body.classList.toggle("dark");localStorage.setItem("medai_dark",document.body.classList.contains("dark"))}\nfunction newChat(){history=[];lastAnswer="";renderWelcome();$("input").focus()}\nfunction saveChat(){\n if(!history.length)return;\n let a=JSON.parse(localStorage.getItem("medai_chats")||"[]"),first=history.find(x=>x.role==="user");\n a.push({title:(first?.text||"Medical chat").slice(0,55),history});\n localStorage.setItem("medai_chats",JSON.stringify(a.slice(-40)));renderRecent();\n}\nfunction loadChat(x){history=x.history||[];$("messages").innerHTML="";history.forEach(m=>add(m.role,m.text));}\nasync function send(){\n const text=$("input").value.trim();if(!text)return;\n if(text.length>12000){alert("Message is too long.");return}\n add("user",text);$("input").value="";\n const old=history.slice(-20), d=document.createElement("div");d.className="msg model";\n d.innerHTML=\'<div class="avatar">🩺</div><div class="bubble">Thinking...</div>\';$("messages").appendChild(d);\n $("chat").scrollTop=$("chat").scrollHeight;\n try{\n  const r=await fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:text,history:old})});\n  const data=await r.json();d.remove();if(!r.ok)throw new Error(data.error||"Request failed");\n  add("model",data.answer);lastAnswer=data.answer;\n  history.push({role:"user",text:text},{role:"model",text:data.answer});saveChat();\n }catch(e){d.remove();add("model","Sorry: "+e.message)}\n}\nfunction copyAnswer(b){const t=b.parentElement.previousElementSibling.innerText;navigator.clipboard?.writeText(t);b.innerText="Copied";setTimeout(()=>b.innerText="Copy",1000)}\nfunction speakAnswer(b){speechSynthesis.cancel();speechSynthesis.speak(new SpeechSynthesisUtterance(b.parentElement.previousElementSibling.innerText))}\nfunction readLast(){if(lastAnswer)speechSynthesis.speak(new SpeechSynthesisUtterance(lastAnswer))}\nfunction favoriteAnswer(b){\n const t=b.parentElement.previousElementSibling.innerText,a=JSON.parse(localStorage.getItem("medai_favorites")||"[]");\n if(!a.includes(t))a.push(t);localStorage.setItem("medai_favorites",JSON.stringify(a));b.innerText="★ Saved";\n}\nfunction voiceInput(){\n const SR=window.SpeechRecognition||window.webkitSpeechRecognition;\n if(!SR){alert("Voice input is not supported by this browser.");return}\n const r=new SR();r.lang=navigator.language||"en-US";r.onresult=e=>$("input").value=e.results[0][0].transcript;r.start();\n}\nfunction saveTracker(){\n const v=$("trackNote").value.trim();if(!v)return;\n const a=JSON.parse(localStorage.getItem("medai_tracker")||"[]");a.push({text:v,time:new Date().toLocaleString()});\n localStorage.setItem("medai_tracker",JSON.stringify(a.slice(-100)));$("trackNote").value="";renderTracker();\n}\nfunction renderTracker(){\n const a=JSON.parse(localStorage.getItem("medai_tracker")||"[]");\n $("trackerList").innerHTML=a.length?a.slice().reverse().map((x,i)=>`<div class="item"><b>${escapeHtml(x.time)}</b><br>${escapeHtml(x.text)}</div>`).join(""):"<div class=\'item\'>No health notes saved.</div>";\n}\nfunction saveReminder(){\n const text=$("reminderText").value.trim(),time=$("reminderTime").value;if(!text||!time)return;\n const a=JSON.parse(localStorage.getItem("medai_reminders")||"[]");a.push({text,time});localStorage.setItem("medai_reminders",JSON.stringify(a));$("reminderText").value="";renderReminders();\n if("Notification" in window&&Notification.permission==="default")Notification.requestPermission();\n}\nfunction renderReminders(){\n const a=JSON.parse(localStorage.getItem("medai_reminders")||"[]");\n $("reminderList").innerHTML=a.length?a.slice().sort((x,y)=>x.time.localeCompare(y.time)).map(x=>`<div class="item"><b>${escapeHtml(x.text)}</b><br>${escapeHtml(x.time)}</div>`).join(""):"<div class=\'item\'>No reminders saved.</div>";\n}\n$("input").addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send()}});\nif(localStorage.getItem("medai_dark")==="true")document.body.classList.add("dark");\nrenderTools();renderWelcome();renderRecent();\n</script>\n</body></html>'

@app.get("/")
def index():
    return render_template_string(PAGE)

@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "MedAI", "gemini_configured": bool(GEMINI_API_KEY)})

@app.post("/api/chat")
def api_chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message","")).strip()
    history = data.get("history", [])
    if not message:
        return jsonify({"error":"Message is required."}), 400
    if len(message) > MAX_MESSAGE:
        return jsonify({"error":"Message is too long."}), 413
    if not isinstance(history, list):
        history = []
    try:
        return jsonify({"answer": gemini(message, history)})
    except Exception as e:
        return jsonify({"error": str(e)}), 502

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error":"Not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT","5000")))

import os, json, urllib.request, urllib.error
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
MAX_HISTORY = 20
MAX_MESSAGE = 12000

SYSTEM_PROMPT = "You are MedAI, a cautious medical information assistant.\nGive clear, evidence-aware educational information. Do not claim certainty or diagnose from limited information.\nFor emergencies, tell the user to contact local emergency services or go to the nearest emergency department.\nAsk useful follow-up questions when needed. Explain medicines, symptoms, labs, first aid, prevention and general health.\nMention important contraindications/interactions when relevant. Never tell users to stop or change prescribed treatment without a clinician.\nRespond in the user's language. This app is educational and does not replace a qualified clinician."

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
    payload = {"systemInstruction":{"parts":[{"text":SYSTEM_PROMPT}]},"contents":contents,
               "generationConfig":{"temperature":0.35,"maxOutputTokens":1800}}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
        headers={"Content-Type":"application/json","x-goog-api-key":GEMINI_API_KEY}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            data=json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try: detail=e.read().decode()
        except Exception: detail=""
        raise RuntimeError(f"Gemini API error ({e.code}). {detail[:500]}")
    except Exception as e:
        raise RuntimeError(f"AI connection error: {e}")
    candidates=data.get("candidates") or []
    if not candidates: raise RuntimeError("The AI returned no answer.")
    parts=(candidates[0].get("content") or {}).get("parts") or []
    answer="".join(p.get("text","") for p in parts if isinstance(p,dict)).strip()
    return answer or "No answer was returned."

@app.after_request
def headers(response):
    response.headers["X-Content-Type-Options"]="nosniff"
    response.headers["X-Frame-Options"]="SAMEORIGIN"
    response.headers["Referrer-Policy"]="strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"]="camera=(), geolocation=(), payment=()"
    return response

PAGE = r'<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n<title>MedAI - Medical AI Assistant</title>\n<style>\n*{box-sizing:border-box}body{margin:0;font-family:Inter,system-ui,-apple-system,Segoe UI,sans-serif;background:#fff;color:#172033}\nbutton,input,textarea{font:inherit}button{cursor:pointer}.app{display:flex;height:100vh;overflow:hidden}\n.side{width:270px;background:#f7f8fa;border-right:1px solid #e5e7eb;padding:14px;display:flex;flex-direction:column;gap:12px}\n.brand{font-size:21px;font-weight:800;padding:10px 8px}.new{width:100%;padding:12px;border:1px solid #d8dde5;border-radius:10px;background:#fff;font-weight:700}\n.tools{display:grid;grid-template-columns:1fr 1fr;gap:7px;overflow:auto}.tool{border:1px solid #e1e5ea;background:#fff;border-radius:9px;padding:9px 6px;font-size:12px;text-align:left}\n.recent{margin-top:5px;font-size:12px;color:#697386}.recent div{padding:8px;border-radius:8px;cursor:pointer}.recent div:hover{background:#e9edf2}\n.main{flex:1;display:flex;flex-direction:column;min-width:0}.top{height:58px;border-bottom:1px solid #e5e7eb;display:flex;align-items:center;padding:0 18px;gap:10px}.menu{display:none;border:0;background:none;font-size:22px}.title{font-weight:750}.grow{flex:1}.icon{border:0;background:transparent;font-size:18px;padding:7px;border-radius:8px}.chat{flex:1;overflow:auto;padding:28px 18px}.wrap{max-width:850px;margin:auto}.welcome{text-align:center;padding:10vh 10px 30px}.logo{font-size:45px}.welcome h1{margin:10px 0 6px}.welcome p{color:#687385}.cards{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-top:25px}.card{border:1px solid #e1e5ea;background:#fff;border-radius:12px;padding:14px;text-align:left}.card b{display:block;margin-bottom:4px}.card span{font-size:13px;color:#6b7280}.msg{display:flex;gap:12px;margin:20px 0}.avatar{width:32px;height:32px;border-radius:50%;display:grid;place-items:center;background:#eef2f7;flex:none}.bubble{white-space:pre-wrap;line-height:1.6;max-width:780px}.user .bubble{background:#f1f3f5;padding:11px 14px;border-radius:14px}.actions{margin-top:5px}.actions button{border:0;background:none;color:#697386;font-size:12px;margin-right:7px}.composer{padding:12px 18px 18px}.box{max-width:850px;margin:auto;border:1px solid #cfd5dd;border-radius:15px;padding:10px;background:#fff;box-shadow:0 2px 12px #0000000b}.box textarea{width:100%;border:0;outline:0;resize:none;min-height:48px;max-height:160px}.bar{display:flex;align-items:center;gap:8px}.send{margin-left:auto;border:0;background:#111827;color:white;border-radius:9px;padding:9px 15px}.hint{text-align:center;font-size:11px;color:#8a93a1;margin-top:7px}.dark{background:#111827;color:#e5e7eb}.dark .side,.dark .top{background:#151b26;border-color:#2b3442}.dark .new,.dark .tool,.dark .card,.dark .box{background:#151b26;color:#e5e7eb;border-color:#303947}.dark .user .bubble{background:#273141}.dark .bubble{color:#e5e7eb}.dark .hint,.dark .welcome p,.dark .card span{color:#9aa5b5}\n@media(max-width:760px){.side{position:fixed;z-index:5;left:-290px;top:0;bottom:0;transition:.2s}.side.open{left:0}.menu{display:block}.cards{grid-template-columns:1fr}.chat{padding:18px 10px}.composer{padding:8px 10px 12px}}\n</style></head>\n<body><div class="app" id="app"><aside class="side" id="side"><div class="brand">🩺 MedAI</div><button class="new" onclick="newChat()">＋ New chat</button><div class="tools" id="tools"></div><div class="recent">RECENT CHATS</div><div id="recent"></div></aside>\n<main class="main"><header class="top"><button class="menu" onclick="toggleSide()">☰</button><div class="title">MedAI</div><div class="grow"></div><button class="icon" onclick="toggleTheme()">🌙</button><button class="icon" onclick="newChat()">＋</button></header>\n<section class="chat" id="chat"><div class="wrap" id="messages"></div></section>\n<div class="composer"><div class="box"><textarea id="input" placeholder="Describe your symptoms or ask a medical question..." rows="2"></textarea><div class="bar"><button class="icon" onclick="voice()">🎙️</button><button class="icon" onclick="readLast()">🔊</button><span class="hint">Medical information only - not a diagnosis</span><button class="send" onclick="send()">Send</button></div></div></div></main></div>\n<script>\nconst tools=[["🩺","Symptoms Checker","Check symptoms and possible causes."],["❤️","Vital Signs","Understand blood pressure, pulse, temperature and SpO₂."],["⚖️","Disease Compare","Compare conditions and typical differences."],["👨\u200d⚕️","Doctor Assistant","Prepare questions for a clinician."],["🧪","Lab Report","Explain lab values and reference ranges."],["💊","Medicine Info","Uses, precautions and common side effects."],["📖","Medical Dictionary","Explain medical terms simply."],["🚨","Emergency Checker","Check warning signs requiring urgent care."],["💊","Drug Interaction","Discuss possible medication interactions."],["🩹","First Aid","Get general first-aid guidance."],["📊","Risk Assessment","Discuss general health risk factors."],["📋","Health Report","Create a structured health summary."],["🧠","Medical Quiz","Practice medical knowledge."],["📚","Medical Glossary","Learn medical vocabulary."],["🖼️","Medical Images","Ask about medical images; vision upload is not enabled here."],["🎤","Voice Input","Use browser speech recognition when supported."],["🔊","Voice Output","Read the latest answer aloud."],["⏰","Medicine Reminders","Save reminder notes in this browser."],["❤️\u200d🩹","Health Tracker","Save simple health notes locally."],["⭐","Favorites","Save useful answers locally."]];\nlet history=[],lastAnswer="";\nconst $=id=>document.getElementById(id);\nfunction renderTools(){$("tools").innerHTML=tools.map((t,i)=>`<button class="tool" onclick="useTool(${i})">${t[0]} ${t[1]}</button>`).join("")}\nfunction renderWelcome(){$("messages").innerHTML=`<div class="welcome"><div class="logo">🩺</div><h1>How can I help?</h1><p>Your AI medical information assistant</p><div class="cards">${tools.slice(0,8).map((t,i)=>`<button class="card" onclick="useTool(${i})"><b>${t[0]} ${t[1]}</b><span>${t[2]}</span></button>`).join("")}</div></div>`}\nfunction renderRecent(){let a=JSON.parse(localStorage.getItem("medai_chats")||"[]");$("recent").innerHTML=a.slice(-8).reverse().map(x=>`<div onclick=\'loadChat(${JSON.stringify(x).replace(/</g,"\\u003c")})\'>${escapeHtml(x.title||"Medical chat")}</div>`).join("")}\nfunction escapeHtml(s){return String(s).replace(/[&<>"\']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",\'"\':"&quot;","\'":"&#39;"}[c]))}\nfunction add(role,text){if(document.querySelector(".welcome"))$("messages").innerHTML="";let d=document.createElement("div");d.className="msg "+role;d.innerHTML=`<div class="avatar">${role==="user"?"👤":"🩺"}</div><div><div class="bubble">${escapeHtml(text)}</div>${role==="model"?\'<div class="actions"><button onclick="copyText(this)">Copy</button><button onclick="speak(this)">Read</button><button onclick="favorite(this)">☆ Favorite</button></div>\':""}</div>`;$("messages").appendChild(d);$("chat").scrollTop=$("chat").scrollHeight}\nfunction useTool(i){$("input").value=tools[i][2]+" Please give me a clear, safe medical explanation.";send()}\nasync function send(){let text=$("input").value.trim();if(!text)return;if(text.length>12000){alert("Message is too long.");return}add("user",text);$("input").value="";let old=history.slice(-20),d=document.createElement("div");d.className="msg model";d.innerHTML=\'<div class="avatar">🩺</div><div class="bubble">Thinking...</div>\';$("messages").appendChild(d);$("chat").scrollTop=$("chat").scrollHeight;try{let r=await fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:text,history:old})}),data=await r.json();d.remove();if(!r.ok)throw new Error(data.error||"Request failed");add("model",data.answer);lastAnswer=data.answer;history.push({role:"user",text:text},{role:"model",text:data.answer});saveChat()}catch(e){d.remove();add("model","Sorry: "+e.message)}}\nfunction saveChat(){if(!history.length)return;let a=JSON.parse(localStorage.getItem("medai_chats")||"[]"),f=history.find(x=>x.role==="user");a.push({title:(f?.text||"Medical chat").slice(0,45),history});localStorage.setItem("medai_chats",JSON.stringify(a.slice(-30)));renderRecent()}\nfunction loadChat(x){history=x.history||[];$("messages").innerHTML="";history.forEach(m=>add(m.role,m.text))}\nfunction newChat(){history=[];lastAnswer="";renderWelcome();$("input").focus()}\nfunction toggleSide(){$("side").classList.toggle("open")}\nfunction toggleTheme(){document.body.classList.toggle("dark");localStorage.setItem("medai_dark",document.body.classList.contains("dark"))}\nfunction copyText(b){let t=b.parentElement.previousElementSibling.innerText;navigator.clipboard?.writeText(t);b.innerText="Copied";setTimeout(()=>b.innerText="Copy",900)}\nfunction speak(b){speechSynthesis.cancel();speechSynthesis.speak(new SpeechSynthesisUtterance(b.parentElement.previousElementSibling.innerText))}\nfunction readLast(){if(lastAnswer)speechSynthesis.speak(new SpeechSynthesisUtterance(lastAnswer))}\nfunction favorite(b){let t=b.parentElement.previousElementSibling.innerText,a=JSON.parse(localStorage.getItem("medai_favorites")||"[]");if(!a.includes(t))a.push(t);localStorage.setItem("medai_favorites",JSON.stringify(a));b.innerText="★ Saved"}\nfunction voice(){let SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR){alert("Voice input is not supported by this browser.");return}let r=new SR();r.lang=navigator.language||"en-US";r.onresult=e=>$("input").value=e.results[0][0].transcript;r.start()}\n$("input").addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send()}});\nif(localStorage.getItem("medai_dark")==="true")document.body.classList.add("dark");renderTools();renderWelcome();renderRecent();\n</script></body></html>'

@app.get("/")
def index():
    return render_template_string(PAGE)

@app.get("/health")
def health():
    return jsonify({"ok":True,"service":"MedAI","gemini_configured":bool(GEMINI_API_KEY)})

@app.post("/api/chat")
def api_chat():
    data=request.get_json(silent=True) or {}
    message=str(data.get("message","")).strip()
    history=data.get("history",[])
    if not message:return jsonify({"error":"Message is required."}),400
    if len(message)>MAX_MESSAGE:return jsonify({"error":"Message is too long."}),413
    if not isinstance(history,list):history=[]
    try:return jsonify({"answer":gemini(message,history)})
    except Exception as e:return jsonify({"error":str(e)}),502

@app.errorhandler(404)
def not_found(e): return jsonify({"error":"Not found"}),404

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT","5000")))

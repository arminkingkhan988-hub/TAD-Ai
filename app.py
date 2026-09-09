from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os, requests, json
load_dotenv()
app = Flask(__name__)
@app.route("/")
def home():
    return "<h1>🤖 پښتو AI</h1><style>body{font-family:Arial;max-width:700px;margin:50px auto;padding:20px;background:#f5f5f5}input{width:70%;padding:14px;border:1px solid #ccc;border-radius:10px;font-size:16px}button{padding:14px 22px;border:0;border-radius:10px;cursor:pointer}#answer{background:white;padding:18px;border-radius:12px;margin-top:20px;min-height:40px}</style><input id=\"msg\" placeholder=\"خپل پیغام ولیکئ...\"><button onclick=\"send()\">Send</button><p id=\"answer\"></p><script>async function send(){let msg=document.getElementById(\"msg\").value;let r=await fetch(\"/chat\",{method:\"POST\",headers:{\"Content-Type\":\"application/json\"},body:JSON.stringify({message:msg})});let d=await r.json();document.getElementById(\"answer\").innerText=d.answer||d.error;}</script>"
@app.route("/chat", methods=["POST"])
def chat():
    history=[{"role":"system","content":"ستاسو نوم TAD AI دی. که څوک ستا د نوم پوښتنه وکړي، ووایه چې زما نوم TAD AI دی او زه د آرمان لخوا جوړ شوی یم."}]+json.load(open("chat_history.json")); history.append({"role":"user","content":request.json["message"]}); r=requests.post("https://api.openai.com/v1/responses",headers={"Authorization":"Bearer "+os.getenv("OPENAI_API_KEY"),"Content-Type":"application/json"},json={"model":"gpt-5.6-luna","input":history})
    d=r.json()
    answer="".join(c.get("text","") for o in d.get("output",[]) for c in o.get("content",[]) if c.get("type")=="output_text") or str(d); history.append({"role":"assistant","content":answer}); json.dump(history,open("chat_history.json","w")); return jsonify({"answer":answer})
app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))

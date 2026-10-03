from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return "MedAI is running successfully!"


@app.route("/health")
def health():
    return jsonify({
        "service": "MedAI",
        "status": "ok"
    })

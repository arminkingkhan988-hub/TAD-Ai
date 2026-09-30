from flask import Flask, request, jsonify
import os
import requests
import urllib.parse

app = Flask(__name__)

@app.route("/")
def home():
    return "MedAI is working"

@app.route("/chat", methods=["POST"])
def chat():
    return jsonify({"answer": "MedAI AI is working"})

if __name__ == "__main__":
    app.run()

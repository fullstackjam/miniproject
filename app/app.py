from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route("/")
def index():
    version = os.getenv("VERSION", "unknown")
    return jsonify({"service": "demo", "version": version})

@app.route("/healthz")
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

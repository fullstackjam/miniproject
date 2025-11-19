from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route("/")
def index():
    version = os.getenv("VERSION", "unknown")
    experiment = os.getenv("EXPERIMENT", "default")
    return jsonify({
        "service": "demo",
        "version": version,
        "experiment": experiment,
        "message": f"A/B/N Testing - Experiment {experiment}",
        "deployment": "multi-variant",
        "status": "healthy"
    })

@app.route("/healthz")
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

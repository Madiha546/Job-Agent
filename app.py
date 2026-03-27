"""
Flask API — serves job data and handles send/reject actions for the dashboard.
Run: python agent/app.py
"""

import json
import sys
import os
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASHBOARD_DIR = os.path.join(BASE_DIR, 'dashboard')

app = Flask(__name__, static_folder=DASHBOARD_DIR)
CORS(app)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gmail_sender import get_all_jobs, send_email, reject_job

CONFIG_PATH = Path(BASE_DIR) / "config.json"

@app.route("/")
def home():
    return send_from_directory(DASHBOARD_DIR, "index.html")

@app.route("/api/jobs", methods=["GET"])
def list_jobs():
    return jsonify(get_all_jobs())

@app.route("/api/jobs/<int:job_id>/send", methods=["POST"])
def send_job(job_id):
    body = request.json or {}
    config = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
    sender_name = config.get("sender_name", "Candidate")
    success = send_email(
        job_id,
        edited_subject=body.get("subject", ""),
        edited_body=body.get("body", ""),
        sender_name=sender_name,
    )
    return jsonify({"ok": success})

@app.route("/api/jobs/<int:job_id>/reject", methods=["POST"])
def reject(job_id):
    reject_job(job_id)
    return jsonify({"ok": True})

@app.route("/api/config", methods=["GET"])
def get_config():
    if CONFIG_PATH.exists():
        cfg = json.loads(CONFIG_PATH.read_text())
        return jsonify({"sender_name": cfg.get("sender_name", ""), "telegram_group": cfg.get("telegram_group", "")})
    return jsonify({})

if __name__ == "__main__":
    app.run(port=5050, debug=True)

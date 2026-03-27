"""
Job Application Agent - Telegram Monitor
Watches a Telegram group, extracts job postings, drafts personalized emails.
Uses Groq API (LLaMA 3.1) - Free tier
"""

import asyncio
import json
import os
import sqlite3
from pathlib import Path

from groq import Groq
from telethon import TelegramClient, events
from telethon.tl.types import Message
import docx2txt

# ─── CONFIG ────────────────────────────────────────────────────────────────────
CONFIG_PATH = Path(__file__).parent.parent / "config.json"
DB_PATH     = Path(__file__).parent.parent / "jobs.db"
RESUME_PATH = Path(__file__).parent.parent / "resume.docx"

# ─── DB SETUP ──────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_msg_id TEXT UNIQUE,
            raw_message     TEXT,
            company         TEXT,
            role            TEXT,
            hr_email        TEXT,
            job_desc        TEXT,
            draft_subject   TEXT,
            draft_body      TEXT,
            status          TEXT DEFAULT 'pending',
            created_at      TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def is_already_saved(msg_id: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT id FROM jobs WHERE telegram_msg_id=?", (msg_id,)).fetchone()
    conn.close()
    return row is not None

def save_job(data: dict) -> int:
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute("""
            INSERT INTO jobs (telegram_msg_id, raw_message, company, role, hr_email, job_desc, draft_subject, draft_body)
            VALUES (:telegram_msg_id, :raw_message, :company, :role, :hr_email, :job_desc, :draft_subject, :draft_body)
        """, data)
        job_id = cur.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        job_id = -1
    conn.close()
    return job_id

# ─── RESUME READER ─────────────────────────────────────────────────────────────
def read_resume() -> str:
    if not RESUME_PATH.exists():
        raise FileNotFoundError(f"Resume not found at {RESUME_PATH}. Place your resume.docx in the job-agent folder.")
    return docx2txt.process(str(RESUME_PATH))

# ─── AI PROCESSING WITH GROQ ───────────────────────────────────────────────────
def parse_and_draft(message_text: str, resume_text: str) -> dict | None:
    """Use Groq LLaMA to extract job info and draft a personalized email."""

    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    prompt = f"""Analyze the Telegram message and extract job details. Use the resume to draft a professional email.

TELEGRAM MESSAGE: {message_text}
RESUME: {resume_text}

Return ONLY a JSON object:
{{
  "company": "Company Name",
  "role": "Job Title",
  "hr_email": "email@example.com",
  "job_desc": "Requirements summary",
  "draft_subject": "Email subject line",
  "draft_body": "Full professional email body. Sign off with [YOUR_NAME]"
}}
If no email is found, return {{"hr_email": null}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return data if data.get("hr_email") else None
    except Exception as e:
        print(f"[ERROR] Groq failed: {e}")
        return None

def process_message(text: str, msg_id: str, resume_text: str) -> bool:
    if len(text) < 30 or is_already_saved(msg_id):
        return False
    result = parse_and_draft(text, resume_text)
    if result:
        job_id = save_job({
            "telegram_msg_id": msg_id,
            "raw_message":     text,
            "company":         result.get("company", "Unknown"),
            "role":            result.get("role", "Unknown"),
            "hr_email":        result["hr_email"],
            "job_desc":        result.get("job_desc", ""),
            "draft_subject":   result.get("draft_subject", ""),
            "draft_body":      result.get("draft_body", ""),
        })
        if job_id > 0:
            print(f"✅ Job #{job_id} saved | {result.get('role')} @ {result.get('company')}")
            return True
    return False

# ─── MAIN RUNNER ──────────────────────────────────────────────────────────────
async def run_agent():
    config = json.loads(CONFIG_PATH.read_text())
    init_db()
    resume_text = read_resume()
    print(f"✅ Resume loaded ({len(resume_text)} chars)")

    client = TelegramClient("job_agent_session", config["telegram_api_id"], config["telegram_api_hash"])
    await client.start()

    target = await client.get_entity(config["telegram_group"])
    print(f"✅ Monitoring: {target.title}")

    print("\n🔍 Scanning last 70 messages... 🌸")
    found = 0
    async for msg in client.iter_messages(target, limit=70):
        if process_message(msg.text or "", str(msg.id), resume_text):
            found += 1
        await asyncio.sleep(1)

    print(f"\n✅ Scan complete! Found {found} job(s)! Check your dashboard! 🎀")

    @client.on(events.NewMessage(chats=target))
    async def handle_message(event):
        msg = event.message
        print(f"📨 New message! (ID: {msg.id})")
        process_message(msg.text or "", str(msg.id), resume_text)

    print("🚀 Agent LIVE — listening for new posts. Ctrl+C to stop.\n")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(run_agent())

"""
Gmail Sender — sends approved job application emails via Gmail API.
"""

import base64
import os
import sqlite3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

DB_PATH     = Path(__file__).parent.parent / "jobs.db"
RESUME_PATH = Path(__file__).parent.parent / "resume.docx"
TOKEN_PATH  = Path(__file__).parent.parent / "gmail_token.json"
CREDS_PATH  = Path(__file__).parent.parent / "gmail_credentials.json"
SCOPES      = ["https://www.googleapis.com/auth/gmail.send"]

def get_gmail_service():
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def send_email(job_id: int, edited_subject: str, edited_body: str, sender_name: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT hr_email, role, company FROM jobs WHERE id=?", (job_id,)).fetchone()
    conn.close()

    if not row:
        print(f"[ERROR] Job #{job_id} not found")
        return False

    hr_email, role, company = row

    msg = MIMEMultipart()
    msg["To"]      = hr_email
    msg["Subject"] = edited_subject
    body_with_name = edited_body.replace("[YOUR_NAME]", sender_name)
    msg.attach(MIMEText(body_with_name, "plain"))

    if RESUME_PATH.exists():
        with open(RESUME_PATH, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="Resume_{sender_name.replace(" ", "_")}.docx"')
        msg.attach(part)

    service = get_gmail_service()
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE jobs SET status='sent' WHERE id=?", (job_id,))
    conn.commit()
    conn.close()

    print(f"✅ Email sent to {hr_email} for {role} @ {company}")
    return True

def reject_job(job_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE jobs SET status='rejected' WHERE id=?", (job_id,))
    conn.commit()
    conn.close()

def get_pending_jobs() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM jobs WHERE status='pending' ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_jobs() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

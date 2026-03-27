# 🤖 AI Job Application Agent

An end-to-end automated job application pipeline that monitors a Telegram job group, extracts HR contact details, generates personalized cold emails using LLaMA 3.1 via Groq API, and dispatches them via Gmail — all reviewed through a custom pastel dashboard.

---

## 🏗️ System Architecture

```
Telegram Group (MTProto API via Telethon)
        ↓
  Message Parser
  (extracts HR email + JD)
        ↓
  Groq API — LLaMA 3.1
  (generates personalized email from resume)
        ↓
  SQLite Database
  (stores jobs + draft emails)
        ↓
  Flask REST API
        ↓
  Review Dashboard (HTML/CSS/JS)
  ← Human-in-the-loop review
        ↓
  Gmail API (OAuth 2.0)
  (sends email + resume attachment)
```

---

## ✨ Features

- 🔍 **Real-time Telegram monitoring** via Telethon MTProto API
- 🧠 **AI-powered email generation** using Groq + LLaMA 3.1-8b-instant
- 📄 **Resume-aware personalization** — cross-references your resume with job requirements
- 💌 **Gmail API integration** with OAuth 2.0 for secure email dispatch
- 🗄️ **SQLite persistence** with duplicate detection
- 🎀 **Custom review dashboard** — human-in-the-loop before sending
- ⚡ **Scans last 70 messages** on startup + listens for new ones

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Telegram Client | Telethon (MTProto) |
| AI Model | LLaMA 3.1-8b-instant via Groq API |
| Email Dispatch | Gmail API + OAuth 2.0 |
| Backend API | Flask + Flask-CORS |
| Database | SQLite |
| Frontend | Vanilla HTML/CSS/JS |
| Resume Parsing | docx2txt |

---

## ⚙️ Setup

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/job-agent.git
cd job-agent
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure credentials
Fill in `config.json`:
```json
{
  "telegram_api_id": "YOUR_TELEGRAM_API_ID",
  "telegram_api_hash": "YOUR_TELEGRAM_API_HASH",
  "telegram_group": "YOUR_GROUP_NAME_OR_ID",
  "sender_name": "Your Full Name"
}
```

### 4. Set environment variables
```bash
# Windows
set GROQ_API_KEY=your_groq_api_key

# Mac/Linux
export GROQ_API_KEY=your_groq_api_key
```

### 5. Add your files
- Place `resume.docx` in the root folder
- Place `gmail_credentials.json` in the root folder (from Google Cloud Console)

### 6. Get API credentials
- **Telegram API** → https://my.telegram.org/auth
- **Groq API** → https://console.groq.com
- **Gmail API** → https://console.cloud.google.com

---

## 🚀 Running

```bash
# Terminal 1 — Telegram Agent
python agent/telegram_agent.py

# Terminal 2 — Dashboard API
python agent/app.py
```

Open `dashboard/index.html` in your browser → review drafts → click Send! 💌

---

## 📁 Folder Structure

```
job-agent/
├── config.json              ← Your credentials (fill this in)
├── resume.docx              ← Your resume (not committed)
├── gmail_credentials.json   ← Gmail OAuth (not committed)
├── requirements.txt
├── agent/
│   ├── telegram_agent.py    ← Monitors Telegram + AI drafting
│   ├── gmail_sender.py      ← Gmail API integration
│   └── app.py               ← Flask REST API
└── dashboard/
    └── index.html           ← Review dashboard
```

---

## 🔒 Security

Sensitive files are excluded via `.gitignore`:
- `config.json` — Telegram credentials
- `gmail_credentials.json` — Gmail OAuth secrets
- `gmail_token.json` — Gmail access token
- `*.session` — Telegram session files
- `jobs.db` — Local database

---

## 👩‍💻 Built By

**Madiha Maheen** — Final Year CS Student & Data Engineer Intern  
[LinkedIn](https://www.linkedin.com/in/madiha-maheen8086/) • [GitHub](https://github.com/Madiha546)

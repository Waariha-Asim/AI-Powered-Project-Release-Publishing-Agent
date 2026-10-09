# 🚀 AI-Powered Project Release & Publishing Agent

> An end-to-end n8n automation that takes raw project files, scans and sanitizes secrets, generates documentation, and publishes the project to GitHub and LinkedIn — fully autonomously.

![Screenshot](https://raw.githubusercontent.com/Waariha-Asim/AI-Powered-Project-Release-Publishing-Agent/main/Screenshot%202026-10-09%20224619.png)

---

## 📖 Overview

This project is an **n8n workflow** that automates the entire release pipeline for a software project — from raw file upload to a published GitHub repository and a LinkedIn announcement post. It detects the project type, scans for leaked secrets using regex + AI verification, sanitizes them into environment variables, generates a README and workflow diagram, and pushes everything live after human approval.

---

## ✨ Features

| Feature | Description | Status |
|---|---|---|
| 📁 Multi-File Intake | Accepts individual files or a ZIP upload via a form trigger | ✅ |
| 🔎 Project Type Detection | Detects Streamlit, FastAPI, Flask, Gradio, Django, static web, or n8n workflow projects | ✅ |
| 🔐 Two-Pass Secret Scanning | Regex-based detection (Pass 1) + AI-verified confirmation, then a final regex re-scan (Pass 2) | ✅ |
| 🧹 Secret Sanitization | Replaces real secrets with env-var placeholders and auto-generates `.env.example` | ✅ |
| 🛑 Security Gate | Blocks publishing and alerts via email if any secret survives sanitization | ✅ |
| 🧩 n8n Workflow Sanitization | Deep-cleans `workflow.json` credentials and credential-like parameters | ✅ |
| 🖼️ Visual Generation | Takes a Selenium screenshot of runnable apps, or auto-generates an SVG workflow diagram for n8n projects | ✅ |
| 📝 AI README Generation | Produces a structured, emoji-rich README from actual code content | ✅ |
| 💼 LinkedIn Post Drafting | Generates a structured announcement post and GitHub metadata (description, topics) | ✅ |
| ✅ Human-in-the-Loop Approval | Emails a review link before anything is posted to LinkedIn | ✅ |
| 🐙 GitHub Publishing | Creates the repository and pushes all files, README, and visuals | ✅ |
| 📊 Release Logging | Logs every release (and rejection) to Google Sheets | ✅ |

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| n8n | Workflow orchestration engine |
| Groq (OpenAI GPT-OSS-20B) | AI-based secret verification & project analysis |
| OpenRouter (Nemotron) | README and LinkedIn/GitHub metadata generation |
| Flask + Selenium | External screenshot microservice (`screenshot.py`) for app previews |
| GitHub REST API | Repository creation & file publishing |
| LinkedIn REST API | Image upload & post publishing |
| Gmail API | Approval emails & release summaries |
| Google Sheets API | Release tracking log |

---

## 📁 Project Structure

```
.
├── workflow.json        # Main n8n automation (this file)
├── screenshot.py         # Flask microservice: launches Streamlit apps
│                          # headlessly and captures a Selenium screenshot
└── assets/
    ├── screenshot.png     # Captured app screenshot (generated per run)
    └── workflow-diagram.svg  # Auto-generated n8n node diagram
```

---

## 🚀 Getting Started

### Prerequisites
- A running **n8n instance** (self-hosted or cloud)
- **Python 3.9+** with `Flask`, `selenium`, `webdriver-manager`, `Pillow` installed for the screenshot service
- API credentials: Groq, OpenRouter, GitHub, LinkedIn, Gmail (OAuth2), Google Sheets (OAuth2)

### Installation
1. Import `workflow.json` into your n8n instance.
2. Configure credentials for Gmail, Google Sheets, GitHub, and LinkedIn in n8n.
3. Install and run the screenshot microservice:
   ```bash
   pip install flask selenium webdriver-manager pillow
   python screenshot.py
   ```

### Environment Variables

| Variable | Description | Required |
|---|---|---|
| `GITHUB_TOKEN` | Personal access token with repo scope | ✅ |
| `GROQ_API_KEY` | Groq API key for security review | ✅ |
| `OPENROUTER_API_KEY` | OpenRouter API key for content generation | ✅ |
| `LINKEDIN_ACCESS_TOKEN` | LinkedIn REST API token | ✅ |
| `GMAIL_CREDENTIAL` | Gmail OAuth2 credential (configured in n8n) | ✅ |
| `GOOGLE_SHEETS_CREDENTIAL` | Google Sheets OAuth2 credential (configured in n8n) | ✅ |

### Running
- Trigger the workflow via the **n8n Form Trigger** (project name, files/ZIP, visibility, tone, email).
- The screenshot service listens on:
  ```bash
  python screenshot.py   # runs on http://0.0.0.0:9000
  ```

---

## ⚙️ How It Works

1. **Intake** – Form Trigger collects project files and metadata.
2. **Detection** – Identifies the framework/runtime (Streamlit, FastAPI, Flask, Gradio, Django, static HTML, or n8n workflow).
3. **Pass 1 Scan** – Regex scan flags potential secrets across all text files.
4. **AI Review** – Groq confirms which flagged items are real secrets and proposes env-var names.
5. **Sanitization** – Real secrets are replaced with placeholders; a `.env.example` is generated.
6. **Pass 2 Scan** – A strict regex re-scan verifies nothing was missed.
7. **Security Gate** – If anything remains, publishing is blocked and an alert email is sent.
8. **Visual Capture** – A Selenium screenshot (web apps) or an auto-generated SVG diagram (n8n workflows) is produced.
9. **Documentation** – An AI-generated README and GitHub/LinkedIn metadata are created from the actual code.
10. **Approval** – A review email with the GitHub link and draft LinkedIn post is sent for human approval.
11. **Publishing** – On approval, the repo is created, files are pushed, and the LinkedIn post goes live.
12. **Logging** – The outcome (published or rejected) is logged to Google Sheets, and a summary email is sent.

---

## 🔒 Security

- All detected secrets are replaced with environment-variable placeholders — no credentials are ever published.
- A `.env.example` file is generated to document required variables without exposing real values.
- A dedicated two-pass scan plus a hard security gate prevents publishing if any secret is still present.

---

## 📄 License

This project is licensed under the MIT License.

---

## 👤 Author

- **Name:** Waariha Asim
- **GitHub:** [@Waariha-Asim](https://github.com/Waariha-Asim)

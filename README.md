# Toluwalemi — AI Digital Twin 🤖

An AI-powered digital twin that answers questions about my professional career, skills, projects, and interests in a natural, first-person voice.

**Live at:** `[]`

## Architecture

```
GitHub Actions
  ├── deploy-app.yml   → Docker build → Artifact Registry → Cloud Run (auto on push)
  └── infra-apply.yml  → Terraform plan/apply                          (manual)

Cloud Run (FastAPI container)
  ├── /api/chat        → streams from OpenRouter
  ├── /api/health
  └── /*               → static frontend (HTML + JS)
        │
        ├── OpenRouter API      (google/gemini-2.5-flash-lite)
        ├── Secret Manager      (OPENROUTER_API_KEY)
        └── GCS bucket          (conversation memory, 7-day TTL)
```

## Tech Stack

| Layer          | Technology                                        |
|----------------|---------------------------------------------------|
| Backend        | Python 3.12, FastAPI, httpx                       |
| Frontend       | HTML, CSS, JavaScript (vanilla)                   |
| LLM Provider   | OpenRouter (`google/gemini-2.5-flash-lite`)       |
| Memory         | Google Cloud Storage (JSON per session)           |
| Secrets        | Google Secret Manager                             |
| Infrastructure | Terraform (GCP)                                   |
| Hosting        | Google Cloud Run                                  |

## Local Development

```bash
# 1. Clone.
git clone https://github.com/Toluwalemi/tolu-ai-digital-twin.git
cd tolu-ai-digital-twin

# 2. Virtual env + deps.
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 3. Create backend/.env (loaded regardless of cwd).
cat > backend/.env << 'EOF'
OPENROUTER_API_KEY=sk-or-v1-your-key-here
GCS_BUCKET_NAME=
CHAT_MODEL=google/gemini-2.5-flash-lite
EOF

# 4. Run the server.
cd backend
uvicorn app.main:app --reload --port 8000

# 5. Open http://localhost:8000
```


## Knowledge Base

The twin's knowledge is stored as Markdown files in `backend/knowledge/`:

- `bio.md` — Background, personality, interests
- `skills.md` — Technical skills and certifications
- `experience.md` — Work history
- `availability.md` — Job search status and preferences
- `education.md` — Education and certifications
- `projects.md` — Personal and professional projects

To update the twin's knowledge, edit these files and push to `main` — `deploy-app.yml` will rebuild and redeploy.

## License

MIT

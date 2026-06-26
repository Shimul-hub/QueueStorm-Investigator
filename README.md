# QueueStorm Investigator

**SUST CSE Carnival 2026 · Codex Community Hackathon · Online Preliminary Round**

Hybrid AI/API support copilot: **rules decide evidence and routing**; **OpenRouter (meta-llama/llama-3.1-8b-instruct)** assists multilingual understanding and safe text drafting.

| Resource | URL |
|----------|-----|
| **Live Demo API** | `https://queuestorm-investigator-5btq.onrender.com` |
| **Swagger UI** | `https://queuestorm-investigator-5btq.onrender.com/docs` |
| **Health Check** | `https://queuestorm-investigator-5btq.onrender.com/health` |
| **GitHub** | https://github.com/Shimul-hub/QueueStorm-Investigator |

---

## Docker Fallback

```bash
git clone https://github.com/Shimul-hub/QueueStorm-Investigator.git
cd QueueStorm-Investigator
docker build -t queuestorm-team .
docker run -p 8000:8000 --env-file .env.example queuestorm-team
curl http://localhost:8000/health
```

Judges can also run: `docker run -p 8000:8000 --env-file judging.env queuestorm-team`

Image target: under 500MB · binds `0.0.0.0` · no GPU · no secrets baked in.

---

## Quick Start (Local)

```bash
git clone https://github.com/Shimul-hub/QueueStorm-Investigator.git
cd QueueStorm-Investigator
python -m venv .venv
```

**Windows (PowerShell):**
```powershell
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env — set OPENROUTER_API_KEY (never commit .env)
python scripts/check_openrouter.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Linux / macOS:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — set OPENROUTER_API_KEY
python scripts/check_openrouter.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**One-command start (Windows):** `.\run_local.ps1`

Verify:
```bash
curl http://localhost:8000/health
pytest tests/ -v
python scripts/run_samples.py --base-url http://localhost:8000
python scripts/validate_samples.py
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Returns `{"status":"ok"}` within 60s of startup |
| POST | `/analyze-ticket` | Analyze one support ticket (JSON in/out) |

### Swagger / Manual Testing

- Local: http://localhost:8000/docs
- Live: `https://queuestorm-mock.onrender.com/docs`

Use sample inputs from [`SUST_Preli_Sample_Cases.json`](SUST_Preli_Sample_Cases.json).

### Example request

```bash
curl -X POST https://queuestorm-mock.onrender.com/analyze-ticket \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TKT-001",
    "complaint": "I sent 5000 taka to a wrong number around 2pm today.",
    "language": "en",
    "transaction_history": [{
      "transaction_id": "TXN-9101",
      "timestamp": "2026-04-14T14:08:22Z",
      "type": "transfer",
      "amount": 5000,
      "counterparty": "+8801719876543",
      "status": "completed"
    }]
  }'
```

Sample response: [`samples/sample_output.json`](samples/sample_output.json)

---

## Architecture

```
Request → Validation → Language Normalization → NLU (rules + optional LLM)
       → Transaction Matching → Evidence Engine → Classifier/Router
       → Text Drafting (templates + optional LLM) → Safety Sanitizer → JSON Response
```

- **Rules (source of truth):** transaction ID, evidence verdict, case type, department, severity, human review
- **LLM (assistant only):** drafting when confidence < threshold; never overrides evidence
- **Safety:** post-LLM sanitizer blocks credential requests and unauthorized refund promises

---

## MODELS

| Model | Provider | Role |
|-------|----------|------|
| `meta-llama/llama-3.1-8b-instruct` | OpenRouter (primary) | NLU assist + text drafting |
| `google/gemini-2.0-flash-001` | OpenRouter (fallback) | Bangla-heavy fallback |

Set `LLM_ENABLED=false` for fully rule-based mode (passes all 10 public samples without API key).

---

## Environment Variables

Copy [`.env.example`](.env.example) to `.env`. **Never commit `.env` or real API keys.**

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Server port (Render sets this automatically) |
| `LOG_LEVEL` | `info` | Logging level |
| `OPENROUTER_API_KEY` | — | OpenRouter API key (**Render dashboard only**) |
| `OPENROUTER_MODEL` | `meta-llama/llama-3.1-8b-instruct` | Primary model |
| `OPENROUTER_FALLBACK_MODEL` | `google/gemini-2.0-flash-001` | Fallback model |
| `OPENROUTER_APP_NAME` | `QueueStorm Investigator` | OpenRouter X-Title header |
| `OPENROUTER_APP_URL` | your public URL | OpenRouter HTTP-Referer header |
| `LLM_ENABLED` | `true` | Enable LLM assist |
| `LLM_CONFIDENCE_THRESHOLD` | `0.7` | LLM triggers below this |
| `LLM_TIMEOUT_SECONDS` | `12` | LLM call timeout |

---

## Render Deployment

1. Push this repo to GitHub.
2. [Render Dashboard](https://dashboard.render.com) → **New +** → **Web Service**.
3. Connect **Shimul-hub/QueueStorm-Investigator**.
4. Settings:
   - **Environment:** Docker
   - **Dockerfile path:** `./Dockerfile`
   - **Health Check Path:** `/health`
5. Add environment variables in Render (not in GitHub):
   - `OPENROUTER_API_KEY` = your key
   - `OPENROUTER_MODEL` = `meta-llama/llama-3.1-8b-instruct`
   - `LLM_ENABLED` = `true`
   - `OPENROUTER_APP_URL` = your Render URL (e.g. `https://your-app.onrender.com`)
6. Deploy → copy public URL → update this README demo links.
7. Verify:
   - `GET https://your-app.onrender.com/health`
   - `POST https://your-app.onrender.com/analyze-ticket` with SAMPLE-01

Optional: use [`render.yaml`](render.yaml) blueprint for one-click deploy.

---

## Testing

All **10 public sample cases** pass (hard fields: transaction, verdict, case type, department, human review):

```bash
pytest tests/ -v
python scripts/run_samples.py --base-url http://localhost:8000
python scripts/validate_samples.py
```

Covers: public samples, Banglish, malformed input, safety adversarial cases, hidden-style edge cases.

---

## Submission Checklist (Judges)

- [ ] Public endpoint: `GET /health` and `POST /analyze-ticket`
- [ ] GitHub repo accessible (add organizer `bipulhf` if private)
- [ ] README with setup, AI usage, safety logic, limitations
- [ ] `.env.example` present — no real secrets in repo
- [ ] `samples/sample_output.json` included
- [ ] Docker fallback documented

---

## Safety Logic

- Never asks for PIN, OTP, password, CVV, or card number
- Never promises refund/reversal/unblock without authority
- Uses: *"any eligible amount will be returned through official channels"*
- Ignores prompt-injection in complaint text
- Escalates phishing, fraud, and ambiguous high-risk cases

---

## Known Limitations

- Cannot match transactions absent from provided history
- Ambiguous same-amount transfers return `null` + clarification request (by design)
- OpenRouter outage → rule templates (same verdicts, simpler text)
- Informal Banglish slang may reduce NLU confidence → safe `insufficient_data` fallback

---

## Tech Stack

Python 3.12 · FastAPI · Pydantic v2 · httpx · OpenRouter · Render · Docker

**Author:** [Shimul-hub](https://github.com/Shimul-hub)

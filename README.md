# BuilderGuard

BuilderGuard is an automated PR-review agent paired with a **Security Lab** that red-teams the agent itself. Point it at a GitHub pull request and it uses an LLM (via Groq) with read-only tools to inspect the diff and report concrete findings — bugs, vulnerabilities, resource leaks, broken error handling. The Security Lab then runs the same agent loop against a library of adversarial PRs (prompt injection, authority spoofing, data exfiltration, etc.) to verify it can't be manipulated into leaking secrets, approving malicious code, or acting outside its read-only tool set.

## How it works

- **PR Review** — `POST /api/reviews` takes a GitHub PR URL, fetches PR metadata/diffs via the GitHub API, and runs an agent loop (`backend/app/agent.py`) that calls `get_pull_request`, `list_changed_files`, and `get_file_content` as needed before finishing with a single `submit_findings` call. Tool calls are validated against a server-side allowlist regardless of what the model requests.
- **Security Lab** — `POST /api/security/tests/run` runs the exact same agent loop against synthetic, malicious PRs served by a mock GitHub adapter (`backend/app/security/`), then evaluates the agent's actual tool calls and output against per-fixture assertions to produce a pass/fail verdict per attack category.
- **Frontend** — a React/Vite app with two tabs: PR Review (submit a PR, see findings/severity/limitations) and Security Lab (browse attack fixtures by category, run them, inspect payloads and verdicts).

## Project structure

```
backend/
  app/
    main.py            FastAPI app wiring (routers, error handlers, CORS)
    agent.py           Core PR-review agent loop (shared by reviews + Security Lab)
    tools.py           Tool specs + allowlist exposed to the model
    groq_client.py     Groq (OpenAI-compatible) chat/tool-calling client
    adapters/          GitHub adapter interface + real GitHub API implementation
    routers/           /health, /api/reviews
    security/          Security Lab: fixtures, mock GitHub adapter, evaluator, runner, rate limiting
  tests/                pytest suite (incl. tests/security for the Security Lab)
frontend/
  src/
    App.jsx             Tab layout (PR Review / Security Lab)
    api/client.js        Backend API client
    components/PRReview/ PR review UI
    components/SecurityLab/ Security Lab UI
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- A [Groq](https://console.groq.com/) API key
- A GitHub personal access token with read access to the repos you want to review

## Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env`:

```
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=openai/gpt-oss-120b
GITHUB_TOKEN=your-github-token
```

Run the API:

```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # set VITE_API_BASE_URL if the backend isn't on localhost:8000
npm run dev
```

The app will be available at `http://localhost:5173`.

## Running tests

```bash
cd backend
pytest
```

## API

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Liveness check |
| `/api/reviews` | POST | Run a PR review. Body: `{"pr_url": "https://github.com/owner/repo/pull/123"}` |
| `/api/security/tests` | GET | List available Security Lab attack fixtures |
| `/api/security/tests/run` | POST | Run a fixture against the agent. Body: `{"test_id": "injection-001"}` |

Both `/api/reviews` and `/api/security/tests/run` are rate-limited per-process to guard against abuse, since each call drives several real Groq API requests.

## Security Lab attack categories

- Prompt injection
- Authority spoofing
- Sensitive data extraction
- Tool misuse
- Hallucination / review manipulation
- Indirect / encoded injection
- Resource exhaustion
- API input/output security

Credentials (`GROQ_API_KEY`, `GITHUB_TOKEN`) are read from the environment once at startup and attached only to outgoing request headers — they are never echoed back in any API response.

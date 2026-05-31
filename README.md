# Plum AI Engineer Assignment - Claims Processing System

Submission-ready FastAPI + LangGraph + SQLite backend with a Next.js + TypeScript + Tailwind demo UI.

## What Is Included

- Claim submission UI with demo scenarios
- Document verification, extraction, policy, fraud, decision, and trace agents
- Dynamic policy evaluation from `policy_terms.json`
- Graceful degradation path for component failure
- Eval runner for all 12 supplied cases
- Architecture and component contract documents
- Railway backend and Vercel frontend deployment config

## Backend

```bash
cd backend
py -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. Set `NEXT_PUBLIC_API_BASE_URL` if the backend is not on `http://localhost:8000`.

## Evaluation

```bash
py eval/run_eval.py
```

The latest run passed all supplied cases and writes the complete report to `eval/eval_report.json`.

## Documents

- `docs/architecture.md`
- `docs/component_contracts.md`
- `docs/demo_script.md`

## Deployment

Backend on Railway:

- Use `Dockerfile.backend` and `railway.json`
- Set `PLUM_POLICY_TERMS_PATH=/app/policy_terms.json`
- Optional Gemini vars: `PLUM_ENABLE_GEMINI=true`, `PLUM_GEMINI_API_KEY=...`

Frontend on Vercel:

- Root directory: `frontend`
- Set `NEXT_PUBLIC_API_BASE_URL` to the Railway backend URL

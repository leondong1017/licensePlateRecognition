# License Plate Recognition

A full-stack license plate recognition app:

- `frontend`: Vue 3 + Vite + TDesign
- `backend`: FastAPI + HyperLPR3 + Real-ESRGAN + SQLite

## Quick Start (Docker)

### 1) Prerequisites

- Docker Desktop 4.0+
- Docker Compose v2 (`docker compose version`)

### 2) Start services

```bash
docker compose up -d --build
```

### 3) Open app

- Frontend: <http://localhost:5173>
- Backend API docs: <http://localhost:8000/docs>

### 4) Stop services

```bash
docker compose down
```

## Data Persistence

Docker mode persists runtime data in:

- `backend/data/lpr.db`
- `backend/data/images/`

These paths are bind-mounted to container `/data` and used through env vars:

- `DB_PATH=/data/lpr.db`
- `IMAGES_DIR=/data/images`

> Do not commit runtime data files to Git.

## Local Dev (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## GitHub Publishing Checklist

Before pushing:

1. Ensure secrets are not in repo (`.env`, private keys, tokens).
2. Ensure runtime data is excluded:
   - `backend/lpr.db`
   - `backend/images/`
   - `backend/data/`
3. Validate Docker startup:
   - `docker compose up -d --build`
   - `docker compose ps`
4. Run basic smoke tests:
   - Open frontend at `http://localhost:5173`
   - Upload one image and verify recognition
   - Open history page and verify records load
5. Stop services: `docker compose down`

## Push to GitHub

```bash
git add .
git commit -m "Add Docker deployment and GitHub publish docs"
git remote add origin <your-repo-url>
git push -u origin main
```

If `origin` already exists, skip `git remote add`.

## Recommended Next Step (Optional)

This repository already includes `.github/workflows/docker-build.yml`:

- builds backend image from `backend/`
- builds frontend image from `frontend/`
- runs on push to `main` and pull requests

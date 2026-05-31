# Flow

A self-hosted AI agent platform.

## Quick start

```bash
docker compose up --build
```

This starts three services:

- **PostgreSQL** — database on port 5432
- **Backend** — FastAPI server on port 8000
- **Frontend** — React + Vite SPA on port 5173

Open [http://localhost:5173](http://localhost:5173) in your browser.

## Architecture

Flow is a full-stack application with a Python/FastAPI backend and a TypeScript/React frontend built with Vite. The backend handles authentication, agent orchestration, and data persistence via SQLAlchemy + asyncpg against PostgreSQL. The frontend communicates with the backend through a REST API. Both services run in Docker containers orchestrated by docker compose, and the database uses a named volume for persistent storage.

## Plan docs

- [Governance review](./governance-review.md)

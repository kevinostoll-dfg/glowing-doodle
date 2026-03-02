# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Call Intelligence Platform for auto repair shops. Handles phone calls via Twilio, routes to human or AI agent based on business hours, transcribes via Deepgram, scores calls against playbook rubrics using Claude API, and provides a React analytics dashboard. Deploys on DigitalOcean Kubernetes via Helm.

## Architecture

- **shared/** — shared Python library (config, database, models, schemas, auth, storage) imported by all services
- **services/api-gateway/** — FastAPI REST API (port 8000) for dashboard and Twilio webhooks
- **services/call-handler/** — FastAPI service (port 8001) for Twilio call routing and TwiML generation
- **services/voice-agent/** — FastAPI WebSocket service (port 8002) bridging Twilio media streams to OpenAI Realtime API
- **services/workers/** — Celery workers for transcription (Deepgram), analysis (Claude), and notifications
- **services/dashboard/** — React/TypeScript SPA with Vite, TanStack Query, Recharts, Tailwind CSS
- **alembic/** — database migrations
- **scripts/** — init_db, seed_shops, twilio_setup
- **argo/** — Argo CronWorkflows and batch job scripts
- **helm/call-intelligence/** — Kubernetes Helm chart with Bitnami PostgreSQL/Redis dependencies

## Language & Tooling

- Python 3.11+ for backend (FastAPI, SQLAlchemy, Celery, Pydantic)
- TypeScript 5 + React 18 for dashboard (Vite, TanStack Query, Recharts, Tailwind)
- Ruff for linting/formatting (line-length=100)
- mypy in strict mode
- pytest with pytest-asyncio

## Key Dev Commands

```bash
make dev        # docker-compose up --build
make test       # pytest
make lint       # ruff check + mypy
make format     # ruff format + fix
make migrate    # alembic upgrade head
make seed       # python -m scripts.seed_shops
make build      # docker-compose build
```

## Key Patterns

- **Shared imports**: All services import from `shared.config`, `shared.database`, `shared.models`, `shared.schemas`
- **Auth**: API key in `X-API-Key` header, hashed with SHA-256, validated via `get_current_user` dependency
- **Webhooks**: Twilio webhooks use `validate_twilio_signature` dependency (no API key), return TwiML XML
- **Celery chains**: recording callback enqueues `transcribe_call` which chains to `analyze_call` which triggers `notify_low_score` if score < 60
- **TwiML generation**: `twiml_builder.py` in call-handler creates Dial, Connect/Stream, Record, Say responses
- **Voice agent**: WebSocket bridges Twilio mulaw audio to OpenAI Realtime API bidirectionally
- **Scoring**: Claude scores transcripts against playbook rubric (6 categories, weighted 0-100), returns JSON
- **Database**: SQLAlchemy with PostgreSQL, JSONB for business_hours/key_points/criteria/utterances
- **Storage**: S3-compatible (DigitalOcean Spaces) via boto3 for call recordings

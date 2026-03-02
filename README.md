# Call Intelligence Platform

AI-powered call analytics platform for auto repair shops. Handles inbound/outbound phone calls via Twilio, routes to human agents or AI voice assistant based on business hours, transcribes calls with Deepgram, scores service advisor performance using Claude, and provides a React analytics dashboard.

## Architecture

```
                    ┌─────────────┐
                    │   Twilio    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌───▼────┐ ┌─────▼─────┐
        │   Call     │ │  API   │ │   Voice   │
        │  Handler   │ │Gateway │ │   Agent   │
        │  :8001     │ │ :8000  │ │  :8002    │
        └─────┬──────┘ └───┬────┘ └───────────┘
              │            │          (WebSocket)
              └────────┬───┘
                       │
              ┌────────▼────────┐
              │    PostgreSQL   │
              │    + Redis      │
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │  Celery Workers │
              │  - Transcribe   │
              │  - Analyze      │
              │  - Notify       │
              └─────────────────┘

        ┌────────────────────────┐
        │   React Dashboard      │
        │   :3000                │
        └────────────────────────┘
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| API Gateway | 8000 | REST API for dashboard, webhooks |
| Call Handler | 8001 | Twilio call routing and TwiML |
| Voice Agent | 8002 | AI voice assistant (OpenAI Realtime) |
| Workers | - | Celery: transcription, scoring, notifications |
| Dashboard | 3000 | React analytics UI |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Twilio account
- API keys: OpenAI, Deepgram, Anthropic

### Setup

1. Clone and configure:
```bash
cp .env.example .env
# Edit .env with your API keys
```

2. Start all services:
```bash
docker-compose up --build
```

3. Initialize database:
```bash
docker-compose exec api-gateway python -m scripts.init_db
docker-compose exec api-gateway python -m scripts.seed_shops
```

4. Configure Twilio webhooks:
```bash
docker-compose exec api-gateway python -m scripts.twilio_setup \
  --all --base-url https://your-domain.com
```

5. Access the dashboard at http://localhost:3000

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `TWILIO_ACCOUNT_SID` | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `OPENAI_API_KEY` | OpenAI API key (Realtime API) |
| `DEEPGRAM_API_KEY` | Deepgram API key (transcription) |
| `ANTHROPIC_API_KEY` | Anthropic API key (call scoring) |
| `S3_ENDPOINT` | S3-compatible storage endpoint |
| `S3_BUCKET` | Storage bucket name |
| `S3_ACCESS_KEY` | Storage access key |
| `S3_SECRET_KEY` | Storage secret key |
| `CORS_ORIGINS` | Allowed CORS origins |
| `LOG_LEVEL` | Logging level (INFO, DEBUG, etc.) |

## Development

```bash
# Run tests
make test

# Lint and type check
make lint

# Format code
make format

# Run database migrations
make migrate

# Seed sample data
make seed
```

## Project Structure

```
├── shared/                  # Shared Python library
│   ├── config.py           # Pydantic settings
│   ├── database.py         # SQLAlchemy engine/session
│   ├── models/             # SQLAlchemy models
│   └── schemas/            # Pydantic schemas
├── services/
│   ├── api-gateway/        # FastAPI REST API
│   ├── call-handler/       # Twilio call routing
│   ├── voice-agent/        # AI voice WebSocket
│   ├── workers/            # Celery background tasks
│   └── dashboard/          # React/TypeScript UI
├── alembic/                # Database migrations
├── scripts/                # Setup and seed scripts
├── argo/                   # Argo workflow definitions
│   ├── workflows/          # CronWorkflows and templates
│   └── jobs/               # Python job scripts
├── helm/                   # Kubernetes Helm charts
│   └── call-intelligence/
├── docker-compose.yml      # Local development
└── docker-compose.prod.yml # Production overrides
```

## Deployment

### DigitalOcean Kubernetes

```bash
# Install with Helm
helm install call-iq helm/call-intelligence \
  -f helm/call-intelligence/values-prod.yaml \
  --set secrets.twilioAccountSid=AC... \
  --set secrets.anthropicApiKey=sk-ant-...

# Upgrade
helm upgrade call-iq helm/call-intelligence \
  -f helm/call-intelligence/values-prod.yaml
```

### Argo Workflows

- **Daily Analytics**: Runs at 6 AM ET, scores unscored calls and generates daily digest
- **Weekly Report**: Runs Monday 8 AM ET, generates weekly summary per shop
- **Batch Scoring**: Manual workflow for scoring calls in a date range

## License

Apache License 2.0

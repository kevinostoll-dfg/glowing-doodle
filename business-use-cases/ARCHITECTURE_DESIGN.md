# Call Intelligence Platform - Architecture Design Document

## Executive Summary

The Call Intelligence Platform is a cloud-native, AI-powered call management and analysis system designed specifically for auto repair shops. It combines real-time call handling with post-call AI analysis to provide actionable insights for improving customer service quality and conversion rates.

**Key Architectural Principles:**
- **Microservices-based**: Independent, scalable services for different functions
- **Event-driven**: Asynchronous processing of recordings and analysis
- **Real-time capable**: Live call routing and agent capabilities
- **Cost-optimized**: Serverless components where appropriate
- **Enterprise-ready**: Multi-tenancy, RBAC, audit logging

---

## System Architecture Overview

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interfaces                           │
├─────────────────────────────────────────────────────────────┤
│ • Dashboard (React SPA)  • Mobile App  • API Clients        │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────────────┐
│              API Gateway (FastAPI)                           │
├──────────────────────────────────────────────────────────────┤
│ • Request validation     • Authentication/Authorization      │
│ • Rate limiting          • Request routing                   │
│ • Webhook handlers       • Response aggregation              │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┼──────────┬──────────┐
        │          │          │          │
        ▼          ▼          ▼          ▼
    ┌────┐    ┌────┐    ┌────┐    ┌────────┐
    │Call│    │STT │    │LLM │    │Webhook │
    │Hdlr│    │Wrk │    │Wrk │    │Handler │
    └────┘    └────┘    └────┘    └────────┘
        │          │          │          │
        └──────────┼──────────┴──────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
    ┌─────────┐          ┌──────────┐
    │PostgreSQL           │  Redis   │
    │(Primary DB)         │ (Cache)  │
    └─────────┘          └──────────┘
```

---

## Component Architecture

### 1. API Gateway Service

**Purpose**: Single entry point for all client requests, providing authentication, authorization, and routing.

**Technology**: FastAPI (Python)

**Responsibilities**:
- API versioning and stability
- API key management and validation
- OAuth2/JWT token management
- Rate limiting per API key
- Request/response logging
- CORS handling
- Webhook receipt and processing

**Deployment**: Kubernetes Deployment (2-3 replicas)

**Scaling**: Horizontal - stateless design allows easy scaling

### 2. Call Handler Service

**Purpose**: Manages real-time call lifecycle with Twilio integration.

**Technology**: FastAPI + Twilio SDK

**Key Functions**:
- Inbound call reception and routing
- Business hours detection
- Call forwarding to human agents
- Call recording initiation
- Call status tracking (queued, ringing, in-progress, completed)
- Call event webhooks (call initiated, completed, failed, recording available)

**Deployment**: Kubernetes Deployment (2-3 replicas)

**Database**: PostgreSQL (calls table, phone_numbers table)

**External Integration**: Twilio Voice API

### 3. Voice Agent Service

**Purpose**: AI-powered voice agent for after-hours and overflow calls.

**Technology**: Python + OpenAI Realtime API + WebSocket

**Capabilities**:
- Real-time bidirectional audio streaming
- Multi-language support (English/Spanish)
- Business context awareness (shop hours, services, pricing)
- Function calling (save customer messages, get hours)
- Conversation history tracking
- Call transcription capture

**Deployment**: Kubernetes Deployment (3+ replicas for resilience)

**Communication**: WebSocket connections from Twilio via Media Streams

**Stateless Design**: Each call instance is independent; no persistent state on service

### 4. Worker Services (Celery)

**Purpose**: Asynchronous task processing for I/O-bound operations.

**Technology**: Celery + Redis + Python

**Task Queues**:

#### 4.1 Transcription Worker
- Downloads recording from Twilio
- Sends audio to Deepgram for speech-to-text
- Handles speaker diarization (identifies who spoke)
- Extracts sentiment per utterance
- Stores transcript and speaker data

#### 4.2 Analysis Worker
- Uses Claude API to score calls against playbook criteria
- Extracts caller intent, key points, coaching notes
- Generates red flags and highlights
- Caches results in Redis for dashboard

#### 4.3 Notification Worker
- Sends email alerts for important events
- Generates SMS summaries
- Creates daily/weekly reports
- Handles asynchronous webhooks to external systems

**Deployment**: Kubernetes Deployment with 3+ replicas
**Retry Logic**: Exponential backoff with max retries
**Dead Letter Queue**: Failed tasks logged to database for manual review

### 5. Dashboard Service

**Purpose**: Web-based analytics and call management interface.

**Technology**: React SPA + TypeScript + TailwindCSS

**Features**:
- Real-time call list with search/filter
- Call detail view with transcript playback
- AI-generated coaching notes
- Historical analytics (daily/weekly/monthly)
- Shop management
- User management and permissions
- API key management

**Deployment**: Nginx reverse proxy + React build artifacts on CDN

**State Management**: React Context API + React Query for server state

---

## Data Flow Diagrams

### Inbound Call Flow (Business Hours)

```
1. Customer calls shop number
   ↓
2. Twilio receives call → POST /webhooks/inbound
   ↓
3. API Gateway verifies Twilio signature, creates Call record
   ↓
4. Call Handler checks business hours
   ↓
5a. Business Hours → Forward to human (SIP/PSTN)
   ↓
6. Call recorded by Twilio
   ↓
7. Call completes → POST /webhooks/call-completed
   ↓
8. Recording becomes available → POST /webhooks/recording-available
   ↓
9. Transcription task queued to Celery
   ↓
10. Analysis task queued after transcription completes
   ↓
11. Results cached in Redis, visible in dashboard
```

### After-Hours AI Agent Call Flow

```
1. Customer calls shop number (after hours)
   ↓
2. Twilio receives call → POST /webhooks/inbound
   ↓
3. Call Handler detects after-hours
   ↓
4. Initiates Media Streams WebSocket to Voice Agent service
   ↓
5. Voice Agent connects to OpenAI Realtime API
   ↓
6. Two-way audio streaming:
   - Twilio → Voice Agent → OpenAI (transcription)
   - OpenAI → Voice Agent → Twilio (response audio)
   ↓
7. Agent can invoke functions:
   - save_customer_message()
   - get_business_hours()
   ↓
8. Call ends, conversation history stored
   ↓
9. Transcription + analysis queued (same as business hours)
```

### Batch Analytics Flow

```
2 AM Daily (Argo CronWorkflow)
↓
Aggregate previous day's calls from PostgreSQL
↓
Calculate metrics:
  - Total calls, inbound/outbound, missed
  - AI-handled vs human
  - Average duration, quality score
  - Sentiment distribution
  - Lead source breakdown
↓
Insert/update call_metrics table
↓
Cache summaries in Redis
↓
Available in Dashboard → Analytics view
```

---

## Database Design

### Core Tables

**shops**: Multi-tenant organization records
- id, name, shop_code, phone_number, timezone, business_hours, address

**users**: Dashboard access control
- id, email, api_key, role (admin/manager/viewer), shop_id

**calls**: Primary call records
- id, shop_id, twilio_call_sid, direction, from_number, to_number
- status, start_time, end_time, duration_seconds
- recording_url, transcript, sentiment, ai_score
- handled_by (human/ai_agent), analysis_status

**call_participants**: Speaker diarization
- id, call_id, speaker_label, role (employee/customer/ai_agent)
- utterances (JSON array), total_talk_time_seconds

**phone_numbers**: Number attribution and lead source tracking
- id, shop_id, phone_number, number_type (primary/tracking)
- lead_source, is_active

**call_metrics**: Aggregated daily statistics
- id, shop_id, date
- total_calls, inbound, outbound, missed, ai_handled
- avg_duration, avg_ai_score, new_customers
- sentiment distribution, lead_source_breakdown

**playbooks**: Call scoring rubrics
- id, name, version, criteria (JSON), script_template, is_active

### Indexing Strategy

```sql
-- Frequently queried
CREATE INDEX idx_calls_shop_id ON calls(shop_id);
CREATE INDEX idx_calls_start_time ON calls(start_time);
CREATE INDEX idx_calls_status ON calls(status);

-- Analytics queries
CREATE INDEX idx_call_metrics_shop_date ON call_metrics(shop_id, date);

-- Filtering
CREATE INDEX idx_calls_direction ON calls(direction);
CREATE INDEX idx_calls_handled_by ON calls(handled_by);
```

---

## Deployment Architecture

### Development Environment

- **Docker Compose**: All services + PostgreSQL + Redis locally
- **Hot reload**: Code changes reflected immediately
- **Test database**: Isolated from production

### Staging Environment

- **Kubernetes cluster** (single node or small cluster)
- **Real external services**: Twilio test account, Deepgram sandbox
- **Persistent data**: Separate database, not production data

### Production Environment

- **DigitalOcean Kubernetes Service (DOKS)**
- **Auto-scaling**: Services scale based on CPU/memory metrics
- **Node pool**: Different node types for compute-heavy (workers) vs light (API)
- **Managed PostgreSQL**: HA setup with automated backups
- **Managed Redis**: Master-replica for cache layer
- **Object storage**: DigitalOcean Spaces for call recordings
- **CDN**: Cloudflare for dashboard static assets

### Kubernetes Resources

```yaml
# Example: API Gateway Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: registry.example.com/api-gateway:v1.0
        ports:
        - containerPort: 8000
        resources:
          requests:
            cpu: 200m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
```

---

## Security Architecture

### Authentication & Authorization

**API Key Authentication**:
- Clients receive unique API key from dashboard
- Requests include key in `Authorization: Bearer <api_key>` header
- API Gateway validates key existence and shop association

**Multi-tenancy Isolation**:
- Row-level security: Each query filters by `shop_id`
- Users can only access their assigned shop(s)
- Role-based access control: admin/manager/viewer

**Twilio Webhook Validation**:
- All Twilio webhooks validated against Auth Token signature
- Prevents spoofed webhook calls

### Data Encryption

**In Transit**:
- All external services use HTTPS/TLS
- Internal Kubernetes services use mTLS (Istio)
- Database connections encrypted

**At Rest**:
- PostgreSQL encryption at storage level
- Sensitive fields (API keys, tokens) encrypted in database
- Call recordings stored in S3 with AES-256 encryption

### Network Security

**Network Policies**:
```yaml
# Only allow calls from API Gateway to PostgreSQL
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: postgres-access
spec:
  podSelector:
    matchLabels:
      app: postgres
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api-gateway
    ports:
    - protocol: TCP
      port: 5432
```

**Secrets Management**:
- Sensitive values (API keys, DB credentials) stored in Kubernetes Secrets
- Environment-specific values in ConfigMaps
- No secrets in container images

### Audit Logging

- All API calls logged with user, action, timestamp, IP
- Database query logging for compliance
- Webhook receipt/processing logged
- Failed authentication attempts tracked

---

## Scaling Considerations

### Horizontal Scaling

**Services that scale well**:
- API Gateway (stateless)
- Call Handler (stateless)
- Voice Agent (connection-based, scales with concurrent calls)
- Workers (task-based, scales with queue depth)

**Kubernetes HPA Configuration**:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-gateway-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-gateway
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Database Scaling

**PostgreSQL Approach**:
- Read replicas for analytics queries
- Connection pooling (PgBouncer) to limit connections
- Partition calls table by date for large datasets
- Archive old records to separate cold storage

**Redis Scaling**:
- Cluster mode for distributed caching
- Automatic failover with Redis Sentinel
- Cache expiration policies for memory management

### Concurrency Limits

**Twilio Concurrent Calls**:
- Voice API limits based on account tier
- Queue overflow calls to AI agent

**OpenAI Realtime Connections**:
- Max concurrent connections per API key
- Graceful degradation if limit reached

**Deepgram Transcriptions**:
- Concurrent processing limit
- Queue backlog if exceeded

---

## Monitoring & Observability

### Key Metrics

**System Health**:
- Service availability (uptime %)
- Response time (API latency p50, p95, p99)
- Error rate (5xx responses)
- Queue depth (Celery tasks pending)

**Business Metrics**:
- Calls processed (daily/monthly)
- AI agent adoption rate
- Transcription success rate
- Analysis completion time

**Resource Utilization**:
- CPU/memory usage per service
- Database connection count
- Redis memory usage
- Network I/O

### Logging Stack

```
Services → Fluent Bit → Elasticsearch → Kibana
                ↓
           CloudWatch (AWS) or
           DigitalOcean Logs
```

**Log Aggregation**:
- Structured JSON logging from all services
- Log level filtering (ERROR, WARN, INFO)
- 30-day retention policy

### Alerting

**Critical Alerts**:
- Database down or unresponsive
- Celery queue growing unbounded
- API error rate > 5%
- Service pod crashes repeatedly

**Warning Alerts**:
- High memory usage (>80%)
- Slow transcription processing
- Redis evictions occurring

---

## Cost Optimization

### Compute

| Component | Sizing | Cost Estimate |
|-----------|--------|---|
| Kubernetes Cluster (3×4GB nodes) | 12GB total | $120/month |
| Auto-scaling up to 5 nodes | Peak capacity | Scales with demand |

### Storage

| Component | Size | Cost Estimate |
|-----------|------|---|
| PostgreSQL (managed, 2GB) | - | $15/month |
| Call recordings (DigitalOcean Spaces) | ~500GB/month | $5/month |
| Database backups | 7-day retention | Included |

### External Services

| Service | Usage | Cost |
|---------|-------|------|
| Twilio | 5,000 calls × 4 min | $250/month |
| Deepgram | 5,000 transcriptions | $90/month |
| OpenAI Realtime | 500 after-hours calls | $100/month |
| Anthropic Claude | 5,000 analyses | $150/month |
| **Total** | | **$730/month** |

### Cost Reduction Strategies

1. **Batch Processing**: Analyze calls off-peak hours
2. **Caching**: Cache analysis results to avoid re-processing
3. **Model Selection**: Use Claude 3 Haiku for simpler analyses
4. **Reserved Instances**: K8s reserved capacity discounts
5. **Spot Instances**: For non-critical batch jobs

---

## Disaster Recovery

### RTO & RPO Targets

| Component | RTO | RPO |
|-----------|-----|-----|
| API Services | 5 minutes | 0 (stateless) |
| Database | 1 hour | 5 minutes |
| Call Recordings | 24 hours | 24 hours |

### Backup Strategy

**PostgreSQL**:
- Automated daily backups
- Point-in-time recovery (7-day window)
- Cross-region backup replication

**Call Recordings**:
- S3 replication across availability zones
- Lifecycle policy: Archive to Glacier after 90 days

**Configuration**:
- Infrastructure as Code (Terraform/Helm) stored in Git
- Database schemas in version control (Alembic)

### Failover Procedures

**Database Failover**:
1. Managed PostgreSQL automatic failover to replica
2. Applications reconnect using connection pooling
3. Manual verification and promotion of replica

**Service Failover**:
1. Kubernetes automatically restarts failed pods
2. Load balancer removes unhealthy endpoints
3. Horizontal pod autoscaler spins up replacements

---

## Future Enhancements

### Planned Features

1. **Video Call Support**: Handle video consultations
2. **Chat Integration**: WhatsApp/SMS agent support
3. **Advanced Analytics**: Predictive modeling for conversion
4. **Custom Playbooks**: Shop-specific scoring rules
5. **Integration Marketplace**: Zapier, Make.com connectors
6. **Offline Mode**: Web app caching for network resilience
7. **Mobile App**: Native iOS/Android apps

### Scalability Roadmap

**Phase 1 (Current)**: 10-50 shops, 5,000-25,000 calls/month
**Phase 2**: 100 shops, 50,000+ calls/month (distributed database)
**Phase 3**: 500+ shops (multi-region deployment, data residency)

---

## Appendix: Technology Justifications

### Why FastAPI?
- Type hints enable auto-documentation (OpenAPI/Swagger)
- Async/await for efficient I/O handling
- Built-in validation with Pydantic
- Growing ecosystem of extensions

### Why Celery?
- Distributed task queue widely proven at scale
- Flexible scheduling (cron jobs, delayed tasks)
- Integration with Kubernetes via CronJobs
- Easy retry and failure handling

### Why PostgreSQL?
- ACID transactions for data consistency
- Excellent JSON support for semi-structured data
- Full-text search for transcripts
- Row-level security for multi-tenancy

### Why OpenAI Realtime?
- Low-latency bidirectional audio streaming
- Function calling for agentic behavior
- Built-in speech recognition and generation
- Superior voice quality over alternatives

### Why Claude API for Analysis?
- Superior reasoning for quality scoring
- Consistent formatting (JSON) for parsing
- Cost-effective for batch analysis
- Customizable prompts for shop-specific criteria

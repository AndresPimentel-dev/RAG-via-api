# RAG Provider via API

A production-oriented Retrieval-Augmented Generation (RAG) API for uploading PDF documents, converting them into 3072-dimensional vector embeddings, and answering questions grounded in the user's own documents.

The project combines FastAPI, PostgreSQL with pgvector, Redis/Celery, Google Gemini, Caddy, Prometheus, Loki, Alloy, and Grafana. It follows a modular layered architecture with domain entities and interfaces, application use cases, and infrastructure adapters.

## Features

- JWT-based user registration and login
- PDF upload with MIME-type validation
- Asynchronous document processing with Celery
- Text extraction and overlapping text chunking
- Vector embeddings through Google Gemini
- Semantic search with PostgreSQL/pgvector
- User-scoped and optional document-scoped queries
- File and vector metadata persisted in PostgreSQL
- Docker Compose deployment with an HTTPS-ready Caddy reverse proxy
- Health, metrics, and request-observability endpoints
- Prometheus metrics plus Loki/Grafana log collection
- Database migrations managed by Alembic
- Unit and integration test suites

## How It Works

1. A user registers or logs in.
2. The API returns a bearer access token.
3. The authenticated user uploads a PDF.
4. The API stores the original file and creates a document record with `pending` status.
5. Celery receives an asynchronous processing task.
6. The worker extracts text, splits it into 500-character chunks with 50-character overlap, creates Gemini embeddings, and stores chunk vectors in pgvector.
7. The document status becomes `processed`. Processing failures become `failed`.
8. A query generates an embedding, retrieves relevant chunks for the user (and optionally for one document), and sends that context to the Gemini text model.
9. The model returns an answer constrained to the supplied context.

## Architecture

```text
src/
├── domain/                 # Entities, enums, interfaces, and domain exceptions
├── use_cases/              # Authentication, storage, querying, and processing workflows
└── infrastructure/
    ├── api/                # FastAPI app, routes, schemas, dependencies, middleware
    ├── celery/             # Celery app and PDF-processing task trigger/worker
    ├── database/           # SQLAlchemy models, connection, and repositories
    ├── model/              # Google Gemini integration
    ├── pdfprocessor/       # PDF text extraction and chunking
    ├── security/           # Password hashing and JWT handling
    ├── storage/            # Local PDF storage adapter
    ├── logging/            # Application logging
    └── metrics/            # Instrumented repositories and Prometheus metrics
```

### Document Statuses

| Status | Meaning |
|---|---|
| `pending` | Stored and waiting for worker processing |
| `processing` | Reserved status in the domain model; the current worker updates it only on success/failure |
| `processed` | Text and vectors were generated successfully |
| `failed` | Processing failed; the worker records the error and marks the document failed |

## Technology Stack

| Area | Technology |
|---|---|
| API | FastAPI, Uvicorn |
| Database | PostgreSQL 15 with pgvector |
| ORM/migrations | SQLAlchemy, Alembic |
| Authentication | OAuth2 password flow, JWT, pwdlib/Argon2 |
| AI | Google Gemini Embeddings and Gemini text generation |
| Async processing | Redis 7, Celery |
| PDF processing | pypdf |
| Reverse proxy | Caddy 2 |
| Metrics | Prometheus, prometheus-client |
| Logging | Loki, Grafana Alloy |
| Dashboards | Grafana |
| Packaging | Docker, Docker Compose |

## API Reference

The interactive documentation is available at:

- Swagger UI: `http://localhost/docs`
- OpenAPI JSON: `http://localhost/openapi.json`

All application endpoints other than `/health` and `/metrics` are under `/api/v1`.

### Health and Metrics

| Method | Endpoint | Authentication | Description |
|---|---|---:|---|
| `GET` | `/health` | No | Basic health response |
| `GET` | `/metrics` | No | Prometheus metrics |

### Authentication

| Method | Endpoint | Authentication | Description |
|---|---|---:|---|
| `POST` | `/api/v1/register` | No | Create a user and return a bearer token |
| `POST` | `/api/v1/login` | No | Login with form fields `username` and `password` |

Registration request:

```json
{
  "username": "jane",
  "email": "jane@example.com",
  "password": "a-strong-password"
}
```

Login uses OAuth2 form encoding, not JSON:

```bash
curl -X POST "http://localhost/api/v1/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=jane&password=a-strong-password"
```

The response is:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

### Storage

| Method | Endpoint | Authentication | Description |
|---|---|---:|---|
| `POST` | `/api/v1/storage` | Bearer | Upload a PDF and enqueue processing |
| `GET` | `/api/v1/get` | Bearer | List the current user's documents |
| `DELETE` | `/api/v1/delete/{document_id}` | Bearer | Delete a document owned by the user |

Upload a PDF:

```bash
curl -X POST "http://localhost/api/v1/storage" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf;type=application/pdf"
```

Document response:

```json
{
  "id": 1,
  "filename": "document.pdf",
  "file_path": "users/1/<uuid>_document.pdf",
  "status": "pending",
  "created_at": "2026-11-24T14:38:35Z"
}
```

Only the user's own documents are returned or deleted. The upload endpoint rejects files whose reported content type is not `application/pdf`.

### Query

| Method | Endpoint | Authentication | Description |
|---|---|---:|---|
| `POST` | `/api/v1/query` | Bearer | Ask a question against all or one of the user's documents |

```json
{
  "request": "What are the payment terms?",
  "file_id": 1
}
```

`file_id` is optional. If omitted, the API searches vectors from every processed document owned by the user.

```bash
curl -X POST "http://localhost/api/v1/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"request":"What are the payment terms?","file_id":1}'
```

Example response:

```json
{
  "answer": "The context indicates that payment is due within 30 days."
}
```

## Environment Variables

Copy the example environment file before starting Compose:

```bash
cp .env.example .env
```

| Variable | Required | Purpose |
|---|---:|---|
| `POSTGRES_USER` | Yes | PostgreSQL administrator role |
| `POSTGRES_PASSWORD` | Yes | PostgreSQL administrator password |
| `SECRET_KEY` | Yes | Secret used to sign and validate JWT access tokens |
| `API_KEY` | Yes | Google Gemini API key used for embeddings and answers |
| `BASE_PATH` | Yes | Mounted directory for uploaded files |
| `GF_SECURITY_ADMIN_USER` | Yes | Grafana administrator username |
| `GF_SECURITY_ADMIN_PASSWORD` | Yes | Grafana administrator password |
| `ALGORITHM` | No | JWT algorithm; defaults to `HS256` |
| `EXPIRE_TOKEN_TIME` | No | JWT lifetime in minutes; defaults to `30` |
| `DATABASE_URL` | Production Compose sets this | SQLAlchemy PostgreSQL connection URL |
| `REDIS_URL` | Production Compose sets this | Redis URL used for Celery |

Generate a strong secret locally, for example:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Keep `.env`, API keys, database credentials, and JWT secrets out of source control.

## Docker Deployment

Requirements:

- Docker Engine or Docker Desktop
- Docker Compose v2
- A Google Gemini API key
- At least 3072-dimensional embedding support in the configured Gemini model

Start the full stack:

```bash
docker compose up --build -d
```

The Compose stack provides:

- PostgreSQL with pgvector on an internal Docker network
- Redis with append-only persistence
- Alembic database migrations
- FastAPI API
- Celery worker
- Caddy reverse proxy
- Prometheus
- Loki
- Grafana Alloy
- Grafana

Public ports:

| Service | URL or port |
|---|---|
| API through Caddy | `http://localhost` and `https://localhost` when certificates are available |
| Grafana | `http://localhost:3000` |
| Prometheus | Internal `prometheus:9090` |

Caddy is configured with `localhost`, so its public configuration is intended primarily for local development. For a public domain, replace `localhost` in `caddyfile` with the domain and ensure DNS and inbound ports 80/443 are configured.

Useful commands:

```bash
# Follow all service logs
docker compose logs -f

# Follow API or worker logs
docker compose logs -f api worker

# Show running services
docker compose ps

# Apply migrations
docker compose run --rm migrations alembic upgrade head

# Stop the stack and preserve volumes
docker compose down

# Remove the stack and its persisted data
docker compose down -v
```

## Local Development

Use Python 3.11 or newer in a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create a PostgreSQL database with pgvector enabled and set the required variables:

```bash
export DATABASE_URL="postgresql+psycopg2://postgresuser:password@localhost:5432/rag_production_db"
export SECRET_KEY="replace-this-with-a-random-secret"
export API_KEY="your-google-gemini-api-key"
export REDIS_URL="redis://localhost:6379"
export BASE_PATH="./data"
```

Run migrations:

```bash
alembic upgrade head
```

Start Redis and the API in separate terminals:

```bash
redis-server
uvicorn src.infrastructure.api.main:app --reload --host 0.0.0.0 --port 8000
celery -A src.infrastructure.celery.celery_app.celery_app worker --loglevel=info
```

The API will then be available at `http://localhost:8000`.

## Tests

The test configuration requires `DATABASE_URL` to contain `test` or `prueba`, preventing accidental execution against a production database. Run unit and integration tests with:

```bash
export DATABASE_URL="postgresql+psycopg2://tests_database_user:tests_database_password@localhost:5432/tests_database"
export SECRET_KEY="test-secret"
export API_KEY="test-key"
export REDIS_URL="memory://"
export BASE_PATH="./data"

pytest
ruff check
ruff format --check
```

Alternatively, the test database and test container are included in Docker Compose:

```bash
docker compose up --build --abort-on-container-exit tests_database tests_container
```

The test container's command runs pytest, Ruff linting, and Ruff formatting checks.

## Database and Vector Search

Alembic migrations create and evolve the application tables. One migration updates document vectors to the 3072-column pgvector representation used by the embedding model.

Key relationships:

- A user owns documents and vectors.
- A document belongs to a user and owns its vectors.
- Deleting a user cascades to documents and vectors.
- Deleting a document cascades to its vectors.

Vector search is performed through pgvector against all of a user's vectors or against a specific document, depending on whether `file_id` is supplied.

## Storage Behavior

Uploaded PDFs are written to local storage under:

```text
users/<user_id>/<uuid>_<original_filename>
```

Docker mounts `uploads_data` to `BASE_PATH`, but the included adapter is local filesystem storage. A shared object store or distributed filesystem is required for horizontally scaled API/worker deployments.

## Observability

- `/health` provides a basic API status response.
- `/metrics` exposes Prometheus metrics.
- FastAPI request middleware records observability data.
- The Celery worker emits task latency, operation, and error counters.
- Prometheus scrapes the API at 15-second intervals.
- Grafana is available on port 3000.
- Alloy forwards container logs to Loki, based on `alloy/config.alloy`.

Prometheus data, Grafana data, Redis data, PostgreSQL data, Caddy certificates, and uploaded files are persisted in Docker named volumes.

## Operational Limitations

This repository is a functional RAG system rather than a guarantee of production readiness. Before a public production deployment, review these areas:

- Add a robust PDF page-limit and file-size policy.
- Replace local filesystem storage with durable object storage for multiple replicas.
- Add document processing status updates when work starts, not only on completion/failure.
- Add retry policies and dead-letter handling for Celery tasks.
- Add refresh tokens, logout/revocation, password policies, and stricter account validation.
- Restrict CORS and add an explicit HTTP security policy.
- Add readiness/liveness checks and backup/restore procedures.
- Add file type verification by content, not only by upload MIME metadata.
- Add rate limiting and query/document quotas.
- Configure TLS for PostgreSQL and Redis where required.
- Validate and pin third-party/model versions for reproducible deployments.

## Project Structure

```text
.
├── src/                         # Application source code
├── test/unit/                   # Unit tests
├── test/integration/            # API and database integration tests
├── alembic/versions/            # Database migrations
├── grafana/provisioning/        # Grafana datasource configuration
├── loki/                        # Loki configuration
├── alloy/                       # Grafana Alloy configuration
├── Dockerfile
├── docker-compose.yml
├── prometheus.yml
├── caddyfile
├── requirements.txt
├── .env.example
└── pyproject.toml
```

## License

LICENSE by MIT LICENSES
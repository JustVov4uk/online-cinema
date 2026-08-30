# Online Cinema API

[![CI](https://github.com/JustVov4uk/online-cinema/actions/workflows/main.yml/badge.svg)](https://github.com/JustVov4uk/online-cinema/actions/workflows/main.yml)

Online Cinema API is a FastAPI backend project for a movie streaming platform.
It covers the main backend flows of a real product: authentication, movie catalog,
shopping cart, orders, payments, purchased movies, background jobs, file storage,
Docker infrastructure, API documentation, and automated tests.

The project is built as a portfolio-ready backend application with a clear
layered structure and production-like tooling.

## Tech Stack

| Area | Technology |
| --- | --- |
| API framework | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.0 async |
| Migrations | Alembic |
| Validation | Pydantic |
| Auth | JWT, Argon2 password hashing |
| Background jobs | Celery, Celery Beat |
| Broker / result backend | Redis |
| Email testing | MailHog |
| Object storage | MinIO / S3-compatible storage |
| Dependency management | Poetry |
| Code quality | Ruff |
| Tests | Pytest, FastAPI TestClient |
| Containerization | Docker, Docker Compose |
| CI | GitHub Actions |

## Implemented Features

### Authentication and Accounts

- User registration with email activation.
- Account activation token flow.
- Resend activation email.
- JWT login with access and refresh tokens.
- Refresh access token.
- Logout by deleting refresh token from the database.
- Current user endpoint.
- Password reset request and confirmation.
- Authenticated password change.
- User groups: user, moderator, admin.
- User profile with avatar upload.

### Movies

- Movie catalog.
- Movie details.
- Create, update, and delete movie records.
- Genres, stars, directors, certifications, and related movie metadata.
- Pagination with `skip` and `limit`.

### Shopping Cart

- One cart per user.
- Add movie to cart.
- Remove one movie from cart.
- Clear cart.
- Unique cart item rule: one movie can appear only once in a user's cart.

### Orders

- Create order from cart items.
- View authenticated user's orders.
- View order details.
- Cancel order.
- Admin order listing.

### Payments

- Create payment for an order.
- Store payment records.
- Payment webhook endpoint.
- View user's payments.
- View payment details.
- Admin payment listing.
- Mock payment URL support for local development.

### Purchased Movies

- Store movies purchased by a user.
- Prevent duplicate purchased movie records for the same user and movie.
- Purchased movies are created after successful payment flow.

### Infrastructure

- PostgreSQL, Redis, MailHog, MinIO, API, Celery worker, and Celery Beat run with Docker Compose.
- Alembic migrations run in a dedicated `migrator` container.
- Celery Beat schedules cleanup of expired activation and password reset tokens.
- GitHub Actions runs Ruff, migrations, tests, and Docker image build.
- Swagger/OpenAPI documentation is available for all endpoints.

## API Documentation

After starting the project, open:

```text
http://localhost:8000/docs
```

Alternative ReDoc documentation:

```text
http://localhost:8000/redoc
```

OpenAPI schema:

```text
http://localhost:8000/openapi.json
```

## Main API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v1/health/` | Health check |
| `POST` | `/api/v1/auth/register` | Register user |
| `POST` | `/api/v1/auth/activate` | Activate account |
| `POST` | `/api/v1/auth/login` | Login and receive tokens |
| `POST` | `/api/v1/auth/refresh` | Refresh access token |
| `POST` | `/api/v1/auth/logout` | Logout user |
| `POST` | `/api/v1/auth/password-reset/request` | Request password reset |
| `POST` | `/api/v1/auth/password-reset/confirm` | Confirm password reset |
| `GET` | `/api/v1/auth/me` | Get current user |
| `POST` | `/api/v1/auth/password-change` | Change password |
| `POST` | `/api/v1/auth/activation/resend` | Resend activation email |
| `GET` | `/api/v1/movies/` | List movies |
| `POST` | `/api/v1/movies/` | Create movie |
| `GET` | `/api/v1/movies/{movie_id}` | Get movie details |
| `PATCH` | `/api/v1/movies/{movie_id}` | Update movie |
| `DELETE` | `/api/v1/movies/{movie_id}` | Delete movie |
| `GET` | `/api/v1/cart/` | Get current user's cart |
| `POST` | `/api/v1/cart/items/` | Add movie to cart |
| `DELETE` | `/api/v1/cart/items/{movie_id}` | Remove movie from cart |
| `DELETE` | `/api/v1/cart/items` | Clear cart |
| `POST` | `/api/v1/orders/` | Create order |
| `GET` | `/api/v1/orders/` | List user's orders |
| `GET` | `/api/v1/orders/{order_id}` | Get order details |
| `POST` | `/api/v1/orders/{order_id}/cancel` | Cancel order |
| `GET` | `/api/v1/admin/orders/` | Admin order listing |
| `POST` | `/api/v1/payments/` | Create payment |
| `GET` | `/api/v1/payments/` | List user's payments |
| `GET` | `/api/v1/payments/{payment_id}` | Get payment details |
| `POST` | `/api/v1/payments/webhook` | Payment webhook |
| `GET` | `/api/v1/admin/payments/` | Admin payment listing |
| `POST` | `/api/v1/profile/avatar` | Upload user avatar |

## Project Structure

```text
src/
  api/
    dependencies/      Shared FastAPI dependencies
    v1/                API route handlers
  core/                App settings, security, Celery configuration
  database/
    models/            SQLAlchemy models
    session.py         Async database session
  repositories/        Database query layer
  schemas/             Pydantic request and response schemas
  services/            External services: email, storage
  tasks/               Celery background tasks
  main.py              FastAPI application entrypoint

migrations/            Alembic migrations
tests/                 Automated tests
docker-compose.yml     Local infrastructure
Dockerfile             API image definition
```

## Architecture Overview

The project uses a layered backend structure:

- `api/v1` receives HTTP requests and returns HTTP responses.
- `schemas` define request and response data shapes.
- `repositories` contain database operations.
- `database/models` define database tables and relationships.
- `services` isolate external systems such as email and S3-compatible storage.
- `tasks` run background jobs through Celery.
- `core` keeps configuration, security helpers, and app-level setup.

This keeps route handlers focused on application flow while database logic,
validation, security, and external integrations stay in separate modules.

## Running with Docker

### 1. Clone the repository

```bash
git clone https://github.com/JustVov4uk/online-cinema.git
cd online-cinema
```

### 2. Create environment file

Linux / macOS:

```bash
cp .env.example .env
```

Windows Command Prompt:

```cmd
copy .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

### 3. Start the full stack

```bash
docker compose up -d --build
```

This starts:

- FastAPI app
- PostgreSQL
- Redis
- Celery worker
- Celery Beat
- MailHog
- MinIO
- Alembic migrator

### 4. Check running containers

```bash
docker compose ps
```

### 5. Check the API

```bash
curl http://localhost:8000/api/v1/health/
```

Expected response:

```json
{"status":"ok"}
```

## Local Service URLs

| Service | URL |
| --- | --- |
| FastAPI | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |
| MailHog UI | `http://localhost:8025` |
| MinIO Console | `http://localhost:9001` |
| MinIO public bucket | `http://localhost:9000/online-cinema-media` |

Default MinIO credentials are defined in `.env.example`.

## Running Locally with Poetry

Docker is still recommended for PostgreSQL, Redis, MailHog, and MinIO.

### 1. Install dependencies

```bash
poetry install
```

### 2. Start infrastructure services

```bash
docker compose up -d db redis mailhog minio minio_setup
```

### 3. Run migrations

```bash
poetry run alembic upgrade head
```

### 4. Start FastAPI development server

```bash
poetry run uvicorn src.main:app --reload
```

## Tests and Quality Checks

Run Ruff:

```bash
poetry run ruff check .
```

Run tests:

```bash
poetry run pytest
```

Run migrations:

```bash
poetry run alembic upgrade head
```

Build Docker image:

```bash
docker build -t online-cinema-api:ci .
```

Current test suite covers:

- authentication
- activation tokens
- refresh tokens
- password reset
- password change
- current user endpoint
- movies
- cart
- orders
- payments
- purchased movies
- avatar upload
- token cleanup tasks
- OpenAPI schema

## Environment Variables

The project uses `.env` for local configuration.

`.env.example` is committed to the repository as a safe template.
`.env` should stay local and must not be committed.

Main configuration groups:

- project settings
- PostgreSQL connection
- Redis and Celery
- MailHog SMTP
- MinIO / S3-compatible storage
- JWT settings
- mock payment base URL

## Database Migrations

Alembic is used for database schema changes.

Create a new migration:

```bash
poetry run alembic revision --autogenerate -m "migration message"
```

Apply migrations:

```bash
poetry run alembic upgrade head
```

Show current migration:

```bash
poetry run alembic current
```

## CI Pipeline

GitHub Actions runs on every push and pull request.

The CI pipeline:

1. Starts PostgreSQL and Redis services.
2. Installs Python 3.12 and Poetry.
3. Installs project dependencies.
4. Runs Ruff.
5. Applies Alembic migrations.
6. Runs Pytest.
7. Builds the Docker image.

## Project Status

Implemented:

- Authentication and authorization flows
- Movie catalog
- Shopping cart
- Orders
- Payments
- Purchased movies
- Avatar upload with MinIO
- Email testing with MailHog
- Background cleanup jobs with Celery Beat
- Docker Compose local infrastructure
- GitHub Actions CI
- Swagger/OpenAPI documentation
- Automated tests

Planned:

- Production deployment
- Final deployment documentation

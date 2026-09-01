# Online Cinema API

[![CI](https://github.com/JustVov4uk/online-cinema/actions/workflows/main.yml/badge.svg)](https://github.com/JustVov4uk/online-cinema/actions/workflows/main.yml)

Backend API for an online cinema platform built with FastAPI, async SQLAlchemy,
PostgreSQL, Docker, Celery, Redis, MinIO, and automated tests.

The project is designed as a portfolio backend application: it does not stop at
basic CRUD, but connects real backend concerns into one working system:
authentication, token lifecycle, catalog management, shopping cart, orders,
payments, purchased content, background jobs, object storage, CI, and deployment.

## Live Demo

| Resource | URL |
| --- | --- |
| Swagger UI | `http://18.196.243.210/docs` |
| ReDoc | `http://18.196.243.210/redoc` |
| Health check | `http://18.196.243.210/api/v1/health/` |

The demo is deployed on AWS EC2 and runs through Docker Compose.

## Why This Project Matters

This project demonstrates the kind of backend work that appears in real products:

- secure account flows with JWT, refresh tokens, activation, logout, and password reset;
- relational database design with SQLAlchemy models, constraints, and migrations;
- async database access with PostgreSQL and SQLAlchemy 2.0;
- API separation into routes, schemas, repositories, services, and background tasks;
- infrastructure with Docker Compose, PostgreSQL, Redis, Celery, MailHog, and MinIO;
- automated quality checks with Ruff, Pytest, Alembic, and GitHub Actions;
- live AWS deployment that can be opened and tested from a browser.

## Tech Stack

| Area | Technology |
| --- | --- |
| API framework | FastAPI |
| Language | Python 3.12 |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.0 async |
| Migrations | Alembic |
| Data validation | Pydantic |
| Authentication | JWT, Argon2 password hashing |
| Background jobs | Celery, Celery Beat |
| Message broker | Redis |
| Email testing | MailHog |
| Object storage | MinIO / S3-compatible storage |
| Dependency management | Poetry |
| Code quality | Ruff |
| Tests | Pytest, FastAPI TestClient |
| Containers | Docker, Docker Compose |
| CI | GitHub Actions |
| Deployment | AWS EC2 |

## Core Product Flow

```text
User registers
  -> receives activation email
  -> activates account
  -> logs in and receives JWT tokens
  -> browses movies
  -> adds movies to cart
  -> creates order
  -> creates payment
  -> successful payment unlocks purchased movies
```

## Implemented Features

### Authentication and Accounts

- User registration with email activation.
- Activation token confirmation.
- Resend activation email.
- JWT login with access and refresh tokens.
- Refresh access token.
- Logout by removing refresh token from the database.
- Current authenticated user endpoint.
- Password reset request and confirmation.
- Authenticated password change.
- User groups: user, moderator, admin.
- User profile with avatar upload.

### Movie Catalog

- Movie list endpoint.
- Movie detail endpoint.
- Movie create, update, and delete endpoints.
- Genres, stars, directors, certifications, and related movie metadata.
- Pagination with `skip` and `limit`.

### Shopping Cart

- One cart per user.
- Add movie to cart.
- Remove movie from cart.
- Clear cart.
- Unique constraint for `(cart_id, movie_id)`.

### Orders

- Create order from cart items.
- List authenticated user's orders.
- Get order details.
- Cancel order.
- Admin order listing.

### Payments

- Create payment for an order.
- Store payment records.
- Payment webhook endpoint.
- List authenticated user's payments.
- Get payment details.
- Admin payment listing.
- Mock payment URL support for local development and demo flow.

### Purchased Movies

- Store movies purchased by a user.
- Prevent duplicate purchased movie records for the same user and movie.
- Connect successful payment flow with access to purchased content.

### Infrastructure

- Docker Compose stack with API, PostgreSQL, Redis, Celery worker, Celery Beat,
  MailHog, MinIO, and Alembic migrator.
- Celery Beat scheduled job for expired activation/password reset token cleanup.
- MinIO bucket setup for avatar/media-like file storage.
- MailHog for local activation and password reset email testing.
- GitHub Actions for linting, migrations, tests, and Docker image build.
- Swagger/OpenAPI documentation for all endpoints.

## API Documentation

Swagger UI:

```text
http://localhost:8000/docs
```

ReDoc:

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

## Architecture

The application uses a layered backend structure:

```text
HTTP request
  -> FastAPI route
  -> Pydantic schema validation
  -> service/repository logic
  -> SQLAlchemy async session
  -> PostgreSQL
```

Project layout:

```text
src/
  api/
    dependencies/      Shared FastAPI dependencies
    v1/                Route handlers grouped by feature
  core/                Settings, security helpers, Celery app
  database/
    models/            SQLAlchemy models and relationships
    session.py         Async database engine and session factory
  repositories/        Database query layer
  schemas/             Pydantic request and response schemas
  services/            Email and S3-compatible storage services
  tasks/               Celery tasks
  main.py              FastAPI application entrypoint

migrations/            Alembic migration history
tests/                 Automated test suite
docker-compose.yml     Local Docker Compose stack
Dockerfile             Application image definition
```

## Running Locally with Docker

### 1. Clone repository

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

### 3. Start full stack

```bash
docker compose up -d --build
```

### 4. Check containers

```bash
docker compose ps
```

### 5. Check API

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

## Running Locally with Poetry

Docker is still recommended for PostgreSQL, Redis, MailHog, and MinIO.

Install dependencies:

```bash
poetry install
```

Start infrastructure services:

```bash
docker compose up -d db redis mailhog minio minio_setup
```

Run migrations:

```bash
poetry run alembic upgrade head
```

Start development server:

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

The current test suite contains 67 tests and covers:

- authentication and account activation;
- refresh tokens and logout;
- password reset and password change;
- current user endpoint;
- movie catalog;
- shopping cart;
- orders;
- payments;
- purchased movies;
- avatar upload;
- token cleanup task;
- OpenAPI schema.

## Environment Variables

The project uses `.env` for local and deployment configuration.

`.env.example` is committed as a safe template. `.env` must stay local and
must not be committed.

Main configuration groups:

- PostgreSQL connection;
- Redis and Celery;
- MailHog SMTP;
- MinIO / S3-compatible storage;
- JWT settings;
- mock payment base URL.

## Database Migrations

Create a migration:

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

GitHub Actions runs on push and pull request.

The pipeline:

1. Starts PostgreSQL and Redis.
2. Installs Python 3.12 and Poetry.
3. Installs dependencies.
4. Runs Ruff.
5. Applies Alembic migrations.
6. Runs Pytest.
7. Builds Docker image.

## Deployment Notes

The live demo is deployed on AWS EC2 with Docker Compose.

Deployment setup:

- Ubuntu 24.04 EC2 instance;
- Docker and Docker Compose v2;
- 2 GB swap file for stable work on a small instance;
- PostgreSQL, Redis, MinIO, MailHog, Celery worker, Celery Beat, and API in containers;
- HTTP traffic exposed on port `80`;
- SSH restricted by security group.

Current live Swagger:

```text
http://18.196.243.210/docs
```

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
- AWS EC2 deployment
- Automated tests

Possible future improvements:

- HTTPS and domain name
- Dedicated production object storage
- Managed PostgreSQL
- More advanced admin permissions
- API rate limiting

# Secure Authentication System

Full-stack authentication system built to explore a production-style login architecture: short-lived JWT access tokens, HTTPOnly refresh cookies, refresh token rotation, Google OAuth, and a small admin layer.

The problem is familiar in real applications: keep the frontend responsive without storing sensitive long-lived credentials in JavaScript-accessible storage, while still supporting local login, social login, session recovery, and privileged users.

## Executive Summary

I designed this project around a hybrid authentication model:

- The access token is short-lived and stored client-side for authenticated API requests.
- The refresh token is opaque, persisted server-side as a hash, and sent to the browser through an HTTPOnly cookie.
- Refresh token rotation invalidates the previous token on every renewal.
- Reuse of a revoked refresh token is treated as a security event and closes all sessions for that user.
- Google OAuth accounts are linked by e-mail when a local account already exists.

The result is a compact authentication system that demonstrates backend security decisions, frontend session management, and the operational details that usually make auth harder than it looks.

## Why These Technical Choices

### FastAPI

I chose FastAPI because authentication APIs benefit from explicit request/response contracts, dependency injection, and simple route composition. The project uses route modules for local auth and Google OAuth, while dependencies handle authenticated-user resolution.

### SQLAlchemy and SQLite

I used SQLAlchemy to keep the data model explicit and portable. SQLite keeps the project easy to run locally, but the ORM layer avoids tying the business logic directly to SQLite-specific code.

### JWT Access Tokens

JWTs work well for short-lived access tokens because the backend can validate requests without storing every active access token. I kept the access token lifetime short and delegated long-term session continuity to refresh tokens.

### Opaque Refresh Tokens

Refresh tokens are generated as random strings and stored in the database only as SHA-256 hashes. This mirrors how passwords are handled conceptually: a database leak should not expose usable refresh tokens.

### HTTPOnly Cookies

I used HTTPOnly cookies for refresh tokens to reduce exposure to XSS. The frontend never needs to read the refresh token directly; it only asks the backend to refresh the session, and the browser attaches the cookie.

### Next.js and React Context

Next.js provides a straightforward frontend structure for the auth screens and callback page. React Context centralizes session state so login, logout, route protection, and session restoration share the same source of truth.

### Axios Interceptors

Axios interceptors keep token attachment and refresh behavior out of individual pages. That lets the UI call the API normally while the HTTP client handles access-token injection and renewal.

## Features

- Local registration with hashed passwords.
- Local login with e-mail and password.
- JWT access token issuance.
- HTTPOnly refresh token cookie.
- Refresh token rotation.
- Replay detection for revoked refresh tokens.
- Google OAuth login.
- Account linking by e-mail for Google users.
- `/auth/me` session validation.
- Logout with refresh cookie cleanup.
- Development-only admin bootstrap.
- Admin-only diagnostic route in development.

## Architecture and Design

```text
.
|-- app/
|   |-- core/          # Settings, security helpers, admin guard
|   |-- db/            # SQLAlchemy engine and session setup
|   |-- deps/          # Authentication dependencies
|   |-- models/        # User and refresh token models
|   |-- routes/        # HTTP endpoints
|   |-- schemas/       # Pydantic request/response contracts
|   `-- services/      # Authentication and OAuth business logic
|-- frontend/
|   |-- components/    # Layout and protected route wrapper
|   |-- context/       # Auth context and session restoration
|   |-- pages/         # Next.js pages
|   |-- services/      # Axios API client
|   `-- styles/        # Global styles
|-- tests/             # Automated tests
|-- requirements.txt
`-- README.md
```

The backend separates routing from business logic. Routes handle HTTP concerns, services handle user creation, credential checks, token generation, token rotation, and OAuth persistence.

The frontend keeps session state in `AuthContext`. On startup, it first checks `/auth/me`; if the access token is missing or expired, it attempts `/auth/refresh` using the HTTPOnly cookie, then retries `/auth/me`.

## Authentication Flow

### Local Login

1. The user registers through `/auth/register`.
2. The user logs in through `/auth/login`.
3. The backend returns an access token in the response body.
4. The backend sets a refresh token in an HTTPOnly cookie.
5. The frontend stores the access token in `sessionStorage`.
6. Authenticated calls include `Authorization: Bearer <access_token>`.
7. `/auth/me` returns the current user when the token is valid.
8. `/auth/refresh` rotates the refresh token and returns a new access token.
9. `/auth/logout` clears the refresh cookie.

### Google OAuth

1. The frontend redirects to `/auth/google/login`.
2. The backend creates a `state` token and redirects to Google.
3. Google redirects back to `/auth/google/callback`.
4. The backend validates the `state` cookie, exchanges the code for Google tokens, and validates the ID token claims.
5. The backend finds or creates the local user.
6. The backend issues the local access and refresh tokens.
7. The frontend receives the access token on `/auth-callback`.

## The Battlefield: Challenges and Solutions

### 1. Refresh Token Rotation Without Breaking the User Session

The first architectural challenge was balancing security with usability. A simple refresh token would keep users logged in, but it would also remain valid if leaked. I opted for rotation: every refresh revokes the current token and creates a new one.

That decision introduced a second requirement: detect replay. If a revoked refresh token appears again, the backend treats it as suspicious and revokes every refresh token for that user. This adds defensive behavior without changing the normal login experience.

### 2. Cookies, CORS, and Local Development

Cross-origin authentication is easy to get almost right and still fail in the browser. The frontend runs on `localhost:3000`, while the API runs on `localhost:8000`. Cookies only work correctly when CORS allows credentials and the browser accepts the cookie attributes.

I made the backend set secure cookies only in production. In local development, forcing the `Secure` flag over plain HTTP would make the browser silently drop the refresh cookie, breaking session restoration and refresh.

### 3. Google OAuth State Validation

OAuth is more than redirecting to Google. The callback must prove it belongs to the same login attempt that started the flow. I added a generated `state` value stored in an HTTPOnly cookie and validated it during the callback. That keeps the flow simple while still addressing CSRF risk in the OAuth round trip.

## Development Admin Account

In development, the application guarantees a default admin account:

```text
Email: admin@example.com
Password: admin123
```

This account is for local testing only. It is not created in production and must not be used as a production credential. In production, use `ADMIN_EMAIL` to promote an existing user to administrator.

## Environment Variables

The backend reads `.env` from the project root:

```env
DATABASE_URL=sqlite:///./sql_app.db
SECRET_KEY=change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
ENVIRONMENT=development
ADMIN_EMAIL=admin@example.com
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
FRONTEND_URL=http://localhost:3000
```

The frontend can read `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Example files are included:

- `backend/.env.example`
- `frontend/.env.local.example`

Real `.env` files and local databases are intentionally ignored by Git.

## Quick Start

### Backend

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend URL:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/health
```

API docs:

```text
http://localhost:8000/docs
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL:

```text
http://localhost:3000
```

## Production Notes

Before deploying, I would change the operational setup:

- Use a managed database instead of SQLite.
- Move secrets to the hosting provider's secret manager.
- Use HTTPS and `ENVIRONMENT=production`.
- Configure real Google OAuth credentials.
- Replace development admin credentials with a production-safe admin creation process.
- Add migrations instead of lightweight startup schema adjustments.
- Add rate limiting to authentication endpoints.
- Add structured logging and audit trails for refresh-token replay events.

## Future Roadmap

If I continued this project, I would focus on operational maturity:

- Add Alembic migrations.
- Add password reset flow.
- Add e-mail verification.
- Add rate limiting and lockout policies.
- Add refresh-token session management in the UI.
- Add deployment configuration for a cloud provider.
- Expand tests around OAuth failure cases and cookie behavior.

## What This Project Demonstrates

This project is less about a login screen and more about the engineering decisions behind a reliable authentication flow. It shows how access tokens, refresh cookies, OAuth redirects, replay detection, admin rules, and frontend session restoration fit together in one working system.

# Prerequisites: Access Governance System (Semester V1 — Trimmed Scope)

**Project:** Access Governance System (V1)
**Purpose:** Semester project — development, testing, zero-cost MVP deployment
**Scope note:** This is a reduced scope compared to the original "Enterprise" prerequisites doc. MFA, CSRF, and threat monitoring are deferred to V2 (see Section 8). This scope is chosen to be realistically achievable within a semester timeline.

---

## 1. Development Environment

### 1.1 IDE
**Cursor** — Python support, Git integration, Markdown support, REST/API testing extensions recommended.

### 1.2 Backend Runtime
**Python 3.11 or 3.12** (not 3.13 — avoid dependency/wheel compatibility risk on a new interpreter version).

Stack:
* FastAPI
* Uvicorn
* Pydantic
* SQLAlchemy
* PostgreSQL driver (psycopg2 or asyncpg)
* Argon2id password hashing (`argon2-cffi`)

Verify: `python --version`

### 1.3 Python Package Management
**uv** — dependency and virtual-environment management.
Verify: `uv --version`
Use a dedicated virtual environment; never install project deps globally.

### 1.4 Version Control
**Git** + GitHub repository.

```text
GRC-Access-Governance/
├── backend/
├── frontend/
├── docs/
├── tests/
├── .env.example
├── .gitignore
└── README.md
```

---

## 2. Database & Cloud Services (Zero-Cost)

### 2.1 Database — Supabase (managed PostgreSQL)
Stores: Users, Departments, Roles, Permissions, Resources, Access Requests, User Resource Access, Audit Logs.
Frontend never connects directly to the database — backend only.

**Known limitation:** free Supabase projects pause after a period of inactivity. If demoing after a gap, ping the project awake beforehand.

### 2.2 Backend Deployment — Render
Exposes REST endpoints for: Authentication, RBAC, Access Governance, Audit Logging, Health Monitoring.

**Known limitation:** free Render services cold-start (spin down on inactivity, ~30–50s wake time). Acceptable for a semester project; mention it in your report rather than trying to "fix" it.

### 2.3 Frontend Deployment — Vercel
React + Tailwind CSS. Communicates with backend via REST over HTTPS. No secrets or DB credentials in frontend.

### 2.4 Availability Monitoring — UptimeRobot (optional)
Not required for local development. Optional post-deployment health check on `GET /health`.

---

## 3. Frontend & UI Requirements

* React + Tailwind CSS
* HTTPS REST communication with backend only
* Design: flat, clean spacing, minimal clutter, responsive, security-dashboard feel
* Palette: Background `#0A192F`, Accent `#64FFDA` (adjust shades for accessibility as needed)

---

## 4. Security Prerequisites (Trimmed)

### 4.1 Authentication
Email + Password. Passwords hashed with **Argon2id** — never stored in plaintext.

### 4.2 Session Handling — Simplified for V1
Use **JWT via `Authorization: Bearer <token>` header**, not cookies.

Rationale: this avoids the cross-domain cookie problem entirely (Vercel frontend + Render backend are different origins, and `SameSite=None` cookies are unreliable across browsers, especially Safari). Using a header instead of a cookie also removes the need for CSRF protection in V1, since CSRF only matters when the browser auto-attaches credentials (cookies).

* Frontend stores the token in memory (or localStorage if simplicity is prioritized over XSS hardening — acceptable trade-off for a semester project, document it as a known limitation).
* Backend validates the JWT signature + expiry on every protected request.
* Include a `token_version` field on the User table; increment it on role change or forced logout so old tokens can be invalidated without needing a full session store.
* **Important:** `token_version` only works as revocation if it is checked against the DB on every request (auth middleware fetches current `token_version` for the user and compares it to the value embedded in the JWT). This is a DB read on every request, not free session revocation — it's a deliberate, minimal trade-off for V1 instead of a full server-side session store. Document this explicitly in `ARCHITECTURE.md` so it isn't mistaken for real-time session invalidation without the check in place.
* **Token storage:** default to storing the JWT in memory (JS variable / React state), not `localStorage`. This means a page refresh logs the user out — acceptable for V1. If `localStorage` is used instead for convenience, this is a deviation from the default and must be explicitly documented in `SECURITY.md` as an accepted XSS risk, not left implicit.

### 4.3 Authorization (RBAC)
Enforced server-side only. Frontend hiding buttons is not a security control.

```text
Authenticated User
        ↓
Role
        ↓
Department Scope
        ↓
Permission / Resource Scope
```

---

## 5. Required Security Concepts (Trimmed)

* Authentication vs Authorization
* RBAC, Least Privilege
* Department-level authorization
* JWT structure and validation
* Password hashing (Argon2id)
* Audit logging
* Input validation
* SQL injection prevention
* CORS
* HTTPS/TLS

(MFA, CSRF, and threat-detection concepts are deferred — see Section 8 — but worth reading about for your final report's "future work" section.)

---

## 6. Access Governance Prerequisites

```text
REQUEST → PENDING → APPROVED / REJECTED → GRANTED → REVOKED
```

### 6.1 Departments
Every Employee and Manager belongs to one department (e.g. Sales, HR, Finance, IT). Managers can only act within their own department.

### 6.2 Roles
`Admin`, `Manager`, `Employee` — defined in `RBAC.md`.

### 6.3 Resources
Access requests target a defined resource from a catalog (e.g. VPN, CRM, Financial Dashboard, HR Portal). Actual external provisioning is out of scope — granting access means setting an internal state to `GRANTED`, not touching a real VPN/CRM.

---

## 7. Audit Logging Prerequisites

Append-only audit trail. Events to log:
* Successful/failed login
* Role changes
* Access requests, approvals, rejections
* Access grants, revocations

Fields: `Timestamp, User ID, Action, Target User, Resource, Status, Metadata`.

**"Append-only" must be enforced, not just stated:**
* No API endpoint exposes UPDATE or DELETE for audit records — this is an API design constraint, not just a rule written in docs.
* At the database level, the application's DB role should not have UPDATE/DELETE grants on the audit log table (only INSERT and SELECT). This is the actual enforcement mechanism; the API-level omission alone is not sufficient if someone gets direct DB access or a future endpoint is added carelessly.
* This constraint must be reflected in `DATABASE_SCHEMA.md` (table permissions) and `SECURITY.md` (why it matters), not only described here.

---

## 8. Deferred to V2 (Explicitly Out of Scope for This Semester)

These are removed from V1 on purpose — not oversights. List them in your final report as "future work":

* MFA / TOTP / recovery codes
* CSRF protection (not needed since V1 uses header-based JWT, not cookies)
* Brute-force detection / rolling window rate limiting
* Out-of-hours activity flagging
* Threat monitoring dashboard
* SSO / external identity providers

---

## 9. Environment Variables & Secrets

```text
DATABASE_URL
JWT_SECRET
CORS_ALLOWED_ORIGIN
```

Commit `.env.example` only. Real secrets live in `.env`, which must be in `.gitignore`.

---

## 10. Network Prerequisites

HTTPS everywhere in production. Backend enforces a strict CORS allow-list (only the deployed frontend origin).

---

## 11. Database Prerequisites

Define before building: primary/foreign keys, unique constraints, NOT NULL constraints, indexes, delete/update behavior, department isolation rules, audit-log integrity, transaction boundaries. Full schema in `docs/DATABASE_SCHEMA.md`.

---

## 12. Testing Prerequisites (Trimmed)

**Authentication:** valid login, invalid password, unknown email, expired token, tampered token.

**Authorization:** Admin access, Manager access, Employee access, cross-department access attempt, unauthorized API request.

**Access Governance:** create request, approve, reject, grant, revoke, invalid state transitions.

**Basic Security:** input validation, SQL injection attempt, auth bypass attempt, audit-log modification attempt (should fail).

---

## 13. Zero-Cost MVP Constraints

Accepted limitations of free-tier infra: cold-start latency (Render), inactivity pausing (Supabase), API/storage limits. These are fine for a semester project — document them, don't try to solve them.

---

## 14. Pre-Development Checklist

* [ ] Cursor installed
* [ ] Python 3.11/3.12 installed
* [ ] `uv` installed
* [ ] Git installed, GitHub repo created
* [ ] Supabase project created
* [ ] Render account available
* [ ] Vercel account available
* [ ] Auth model confirmed (header-based JWT, no cookies)
* [ ] RBAC model confirmed
* [ ] Access lifecycle confirmed
* [ ] Department isolation confirmed
* [ ] Audit logging model confirmed
* [ ] Environment-variable strategy confirmed
* [ ] Database schema drafted

---

## 15. Definition of Ready

```text
PREREQUISITES.md → REQUIREMENTS.md → ARCHITECTURE.md → DATABASE_SCHEMA.md → RBAC.md → SECURITY.md → Implementation
```

For a semester timeline, don't over-invest in exhaustive documentation before coding. Get ARCHITECTURE.md and DATABASE_SCHEMA.md solid enough to start; RBAC.md and SECURITY.md can be filled in more precisely as you implement, since some details will only become clear once you're building.
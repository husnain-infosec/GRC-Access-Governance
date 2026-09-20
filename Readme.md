## Project Constraints

### Scope

The V1 project focuses on access governance and security management at the application level, scoped for a semester-length academic project (see `PREREQUISITES.md` for the full trim rationale).

This project is modeled on the core capabilities of **SAP GRC Access Control** — specifically its **Access Request Management (ARM)** module (request → review → grant → revoke lifecycle) and **Business Role Management (BRM)** module (role-based governance) — as a conceptual reference for a semester-scope academic build, not a claim of feature parity with the commercial product.

**Included:**

* User authentication (email + password, Argon2id hashing)
* JWT session (header-based, with `token_version` revocation)
* RBAC (Admin / Manager / Employee)
* Department-level authorization
* Resource access requests
* Approval and rejection workflow
* Access granting and revocation
* Audit logging (application- and database-enforced append-only)
* REST API
* PostgreSQL database

**Excluded from V1 (deferred to V2 — see `PREREQUISITES.md` Section 8):**

* Admin MFA / TOTP / recovery codes
* CSRF protection (not applicable — no cookie-based session in V1)
* Basic threat detection (brute-force detection, out-of-hours flagging)
* Security dashboard
* External SSO
* External application provisioning
* SMS MFA
* Machine-learning anomaly detection
* Native mobile application
* Paid SIEM integrations

Detailed scope and requirements are defined in [`REQUIREMENTS.md`](docs/REQUIREMENTS.md).

---

### Quality

The system prioritizes:

* Secure backend-enforced authorization
* Least-privilege access
* Department isolation
* Secure authentication and session management (header-based JWT, `token_version` revocation)
* Input validation
* Database integrity, including DB-level permission grants enforcing audit-log append-only behavior
* Transaction-safe security operations
* Auditability
* Maintainable and modular code
* Clear documentation

The target is a professional, security-focused university MVP within a semester timeline — not a production enterprise platform. Scope was deliberately trimmed from an earlier, broader draft to keep it achievable; deferred items are documented rather than silently dropped.

Detailed quality and acceptance requirements are defined in [`REQUIREMENTS.md`](docs/REQUIREMENTS.md) and [`SECURITY.md`](docs/SECURITY.md).

---

### Cost

The project is designed as a **zero-cost MVP** using free-tier services where practical.

Planned infrastructure:

```text
Vercel       → Frontend
Render       → FastAPI Backend
Supabase     → PostgreSQL Database
UptimeRobot  → Monitoring (optional, post-deployment)
```

The project accepts free-tier limitations such as Render cold starts, Supabase inactivity pausing, and usage restrictions. No paid infrastructure is required for the V1 MVP.

---

### Time

The project is developed incrementally in phases:

```text
Planning & Documentation
        ↓
Database Setup
        ↓
Backend Foundation
        ↓
Authentication
        ↓
RBAC & Authorization
        ↓
Access Governance
        ↓
Audit Logging
        ↓
Frontend
        ↓
Testing
        ↓
Deployment
```

Development prioritizes core security and access-governance functionality first, followed by frontend integration, testing, and deployment. Threat detection and MFA are explicitly out of this timeline — if time remains after V1 is complete and tested, they may be added as stretch goals, but they are not on the critical path.

Detailed functional requirements and acceptance criteria are defined in [`REQUIREMENTS.md`](docs/REQUIREMENTS.md).
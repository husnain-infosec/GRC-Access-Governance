# Product Requirements Document (PRD)

## Project: Access Governance System (V1 — Semester Scope)

**Target Environment:** Zero-Cost MVP Infrastructure
**Deployment:** Vercel / Render / Supabase

**Scope note:** This document reflects the trimmed V1 scope in `PREREQUISITES.md`. MFA, CSRF, and threat detection (brute-force/out-of-hours) are deferred to V2 — see Section 16. Session auth uses header-based JWT with `token_version` revocation, not cookies.

---

# 1. Product Overview

The Access Governance System (V1) is a web-based application demonstrating core access governance, role-based access control, and audit capabilities within a semester-project scope.

The system provides controlled access to application resources through a structured request and approval workflow.

Primary goals:

* Centralized user and role management
* Department-based access isolation
* Controlled resource access requests
* Manager-based approval workflow
* Application-level access state management
* Audit logging

V1 is intentionally designed as a zero-cost MVP and does not provide real provisioning to external enterprise systems.

---

# 2. Core Access Management Workflow

```text
REQUEST → PENDING → APPROVED / REJECTED → GRANTED → REVOKED
```

### Workflow Rules

1. An Employee submits an access request for an available resource.
2. The request enters `PENDING` status.
3. An authorized Manager reviews the request.
4. A Manager may approve or reject requests within their permitted department scope.
5. An approved request results in application-level access being set to `GRANTED`.
6. Access may later be changed to `REVOKED`.
7. Security-sensitive workflow actions must be recorded in the audit log.

`GRANTED` represents authorization within this application only. V1 does **not** automatically provision accounts or permissions in external VPN, CRM, ERP, cloud, or other third-party systems.

---

# 3. User Roles and Isolation

### Admin
Global administrative access across the application. Capabilities: user management, role management, department management, resource management, global access governance, audit log access, force-invalidating a user's session via `token_version`.

### Manager
Department-scoped management access: viewing users within their department, reviewing/approving/rejecting department requests, managing permitted department-level access operations. A Manager must not access or modify another department's protected data.

### Employee
Self-service access: viewing own profile and resource access, creating access requests for themselves, viewing the status of their own requests. An Employee must not approve access requests or manage other users.

---

# 4. Functional Requirements

## FR-1 Authentication

The system shall provide:

* Email/password authentication
* Secure password hashing using Argon2id
* Header-based JWT session (`Authorization: Bearer <token>`)

### Authentication Requirements

Passwords must never be stored in plaintext; they shall be stored using Argon2id.

Authenticated sessions shall use a JWT delivered via the `Authorization` header — **not** a cookie. The frontend stores the token in memory by default (page refresh requires re-login); if `localStorage` is used instead, this must be documented in `SECURITY.md` as an accepted XSS-related trade-off.

Because there is no cookie-based session, CSRF protection does not apply to V1 (see Section 16).

Each user has a `token_version` field. Every protected request validates the JWT's embedded `token_version` against the current database value; a mismatch results in `401 Unauthorized` even for an otherwise-valid token. `token_version` is incremented on role change, deactivation, or forced logout.

---

# 5. FR-2 RBAC and Department Isolation

The backend shall enforce role-based authorization:

```text
User → Role → Permission → Department Scope → Requested Operation
```

The frontend shall not be considered a security boundary.

### Department Rules

* Admin has global access.
* Manager access is restricted to the Manager's department.
* Employee access is restricted to the Employee's own account and permitted resources.

Cross-department Manager access attempts shall be rejected with `HTTP 403 Forbidden`.

---

# 6. FR-3 Access Request and Approval

The system shall provide a resource catalog of application-controlled resources. Employees shall submit access requests for available resources.

Each request shall include at minimum: requester, resource, request status, creation timestamp, optional business reason.

Valid request states: `PENDING`, `APPROVED`, `REJECTED`.

### Approval Rules

A Manager may approve or reject a request only when:
1. The Manager is authorized to perform the operation.
2. The request is still pending.
3. The requested user belongs to the Manager's department.

Approval shall result in application-level access `GRANTED`. The actual current access state is maintained separately from the request status.

---

# 7. FR-4 Access Revocation

Authorized users shall be able to revoke application-level resource access according to their role permissions. The access state shall become `REVOKED`. Revocation must be recorded in the audit log. V1 does not perform external account/infrastructure provisioning or revocation.

---

# 8. FR-5 Audit Logging

The system shall maintain an application-level audit trail for security-sensitive and administrative actions.

Each audit event should contain, where applicable: timestamp, actor user ID, target user ID, department context, resource ID, action, status, client IP address, additional structured metadata.

Examples:

```text
LOGIN_SUCCESS
LOGIN_FAILURE
ACCESS_REQUEST_CREATED
ACCESS_REQUEST_APPROVED
ACCESS_REQUEST_REJECTED
ACCESS_GRANTED
ACCESS_REVOKED
USER_CREATED
USER_UPDATED
USER_DEACTIVATED
ROLE_CHANGED
```

**Audit records shall be append-only, enforced at two levels:**
1. The API exposes no update/delete functionality for audit records to normal application users.
2. The application's database role has only `INSERT`/`SELECT` grants on the `audit_logs` table — no `UPDATE`/`DELETE` (see `DATABASE_SCHEMA.md` Section 12.3). This is the actual enforcement mechanism, not just an API-level omission.

The V1 system does not claim protection against a compromised database superuser — only that the application itself cannot alter history.

---

# 9. FR-6 Client IP Handling

The backend shall record the client IP for relevant security events. Because the application is deployed behind trusted infrastructure/proxies, forwarded IP headers may be used only when the deployment's trusted proxy configuration explicitly permits it. The backend must not blindly trust an arbitrary `X-Forwarded-For` value supplied directly by an untrusted client. The resolved IP shall be stored in a PostgreSQL `INET` field where available.

---

# 10. FR-7 Admin Account Protection

The system shall always maintain at least one active Admin account. The final active Admin must not be deleted, deactivated, demoted, or removed from the Admin role. This protection must be transaction-safe and account for concurrent requests — a simple preflight Admin count is not sufficient.

---

# 11. Non-Functional Requirements

## NFR-1 Cost

The V1 system shall use a zero-cost development/deployment approach wherever practical: Vercel, Render, Supabase, and (optionally, post-deployment) UptimeRobot. The system shall not require paid infrastructure for core functionality.

## NFR-2 Performance

Target `< 800ms` for normal non-cold-start API operations under reasonable MVP load. Cold starts on free-tier infrastructure are accepted as an MVP constraint. Performance optimization shall not weaken security controls.

## NFR-3 Availability

The system shall be designed to tolerate normal free-tier infrastructure limitations (Render cold starts, Supabase inactivity pausing). External uptime monitoring may be used after deployment but is not a core application security control.

## NFR-4 User Interface

The interface shall provide a professional security-dashboard appearance: clean corporate layout, clear navigation, role-specific dashboards, accessible tables and status indicators, minimal visual clutter.

Initial design palette: Navy `#0A192F`, Cyan `#64FFDA`.

The UI must clearly distinguish: `PENDING`, `APPROVED`, `REJECTED`, `GRANTED`, `REVOKED`.

---

# 12. Security Requirements

## SR-1 Password Security
Passwords shall be hashed using Argon2id. Plaintext passwords must never be stored, logged, or returned through APIs.

## SR-2 Session Security
JWT authentication shall use the `Authorization: Bearer <token>` header. The frontend stores the token in memory by default. JWT secrets must be stored outside source code.

## SR-3 `token_version` Revocation
Every protected request shall validate the JWT's embedded `token_version` against the current database value for that user. A mismatch shall result in `401 Unauthorized`. `token_version` shall be incremented on role change, deactivation, or forced logout.

## SR-4 Backend Authorization
All authorization decisions shall be enforced server-side. The frontend may hide or display UI elements based on role, but this must never replace backend authorization.

## SR-5 Audit Integrity
Application users shall not be able to modify or delete audit events through normal application functionality, and the database role used by the application shall not hold `UPDATE`/`DELETE` grants on `audit_logs`. Security-sensitive actions shall generate audit records.

## SR-6 Secret Management
Secrets must not be committed to source control. Sensitive configuration shall be supplied through environment variables:

```text
DATABASE_URL
JWT_SECRET
CORS_ALLOWED_ORIGIN
```

---

# 13. Acceptance Criteria

## AC-1 Authentication
Given valid credentials: user submits login → credentials verified → JWT issued. Invalid credentials must not produce a valid JWT.

## AC-2 Access Request
Given an Employee requesting access: selects resource → submits request → request becomes `PENDING`. The Employee must not receive `GRANTED` access merely by submitting the request.

## AC-3 Manager Approval
Given a valid pending request belonging to the Manager's department: reviews request → approves → request becomes `APPROVED` → application access becomes `GRANTED`. The approval and access change must be auditable.

## AC-4 Cross-Department Protection
Given a Manager attempting to access or approve a request outside their department: operation attempted → backend checks department scope → request rejected with `HTTP 403 Forbidden`. No protected data or access state may be modified.

## AC-5 Last Admin Protection
Given only one active Admin exists: attempt to delete/deactivate/demote the final Admin → operation rejected. At least one active Admin must remain after the transaction completes.

## AC-6 Audit Logging
Given a security-sensitive operation: operation occurs → audit event created. The application must not provide normal users with an interface to modify or delete the resulting audit event, and a direct attempt to `UPDATE`/`DELETE` the row using the application's own DB credentials must fail at the database level.

## AC-7 Session Revocation
Given a user's role is changed or their session is force-logged-out by an Admin: `token_version` is incremented → any request using a JWT issued before the change is rejected with `401 Unauthorized` on its next call, even if the JWT signature and expiry are still valid.

---

# 14. Deferred to V2 (Explicitly Outside V1)

Consistent with `PREREQUISITES.md` Section 8 and `ARCHITECTURE.md` Section 15:

* Admin MFA / TOTP / recovery codes
* CSRF protection (not applicable — no cookie session in V1)
* Brute-force detection (rolling 5-minute failed-login analysis)
* Out-of-hours login flagging
* Security/threat monitoring dashboard
* External SSO / Google / Microsoft authentication
* External VPN/CRM/ERP/Cloud IAM provisioning
* Machine-learning anomaly detection
* Native mobile application
* Real-time database subscriptions
* Paid SIEM / paid alerting infrastructure
* Automatic IP blocking

These may be considered for future versions and should be listed as "future work" in the final report, but are not required for V1 and must not be reintroduced mid-implementation.

---

# 15. V1 Definition of Done

V1 is considered complete when:

* Authentication works securely (Argon2id + header-based JWT).
* `token_version` revocation works on role change / deactivation / forced logout.
* RBAC is enforced by the backend.
* Manager department isolation works.
* Employees can submit access requests.
* Managers can approve/reject authorized requests.
* Approved requests create application-level `GRANTED` access.
* Access can be revoked.
* Security-sensitive actions are audited, and audit append-only behavior is enforced at both the API and database-grant level.
* Last-active-Admin protection is transaction-safe.
* The frontend, backend, and database are deployed using the approved MVP architecture.
* No V1 feature depends on paid infrastructure.

---

# 16. Requirements Summary

```text
Authentication
      ↓
RBAC
      ↓
Department Isolation
      ↓
Access Request
      ↓
Manager Approval
      ↓
Application-Level Access
      ↓
Audit Logging
```

The system prioritizes: Least Privilege, Backend Authorization, Department Isolation, Auditability, Secure Authentication, Controlled Access, Zero-Cost MVP Scope.

V1 is intentionally limited to demonstrating these core governance capabilities within a semester timeline, without external provisioning, MFA, or threat-detection infrastructure that would extend the timeline beyond what's achievable.
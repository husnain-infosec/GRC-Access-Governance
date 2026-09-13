# Security & Controls Document

**Project:** Access Governance System (V1 — Semester Scope)
**Scope:** Application-Level Security, Cryptography, and Threat Mitigation

**Scope note:** This document reflects the trimmed V1 scope in `PREREQUISITES.md`. MFA, CSRF, cookie-based sessions, and brute-force/out-of-hours threat detection are deferred to V2 — see Section 12. Session auth uses header-based JWT with `token_version` revocation. API rate limiting is also deferred to V2 — see Section 4.1.

---

## 1. Cryptography & Password Management

All credentials and security-sensitive values must be protected before database storage. Plaintext passwords must never be stored.

### 1.1 Password Hashing

* **Algorithm:** `Argon2id`
* **Library:** Python `argon2-cffi`
* **MVP Baseline Parameters:** Time Cost `2`, Memory Cost `65536 KB (64 MB)`, Parallelism `2`
* **Salt:** Automatically generated and managed by `argon2-cffi`.
* **Storage:** Only the resulting Argon2id hash is stored in `users.password_hash`.

Password verification must use the Argon2id verification mechanism rather than comparing plaintext.

---

## 2. Session Management

The application uses a decoupled cross-domain architecture: Vercel (frontend), Render (backend), Supabase (database).

**V1 uses header-based JWT authentication, not cookies.** This is a deliberate choice given the cross-origin topology — see `ARCHITECTURE.md` Section 6 for the rationale (cross-site cookies are unreliable across browsers and would require CSRF protection; header-based tokens avoid both problems).

### 2.1 JWT Configuration

* **Algorithm:** `HS256` using a strong, cryptographically random `JWT_SECRET`.
* **Expiration:** `2 hours` for standard sessions.
* **Payload:** only non-sensitive identifiers required for authorization/session context: `user_id`, `role_id`, `department_id`, `token_version`, `exp`.
* Passwords or other sensitive information must never be included in the JWT.
* The backend returns the JWT in the JSON response body (`{"access_token": "..."}"`), since there is no cookie to set it into.
* The frontend sends the token via `Authorization: Bearer <token>` on every subsequent protected request.

The backend remains the authoritative source for authentication, authorization, role, and department-scope decisions.

### 2.2 Token Storage on the Frontend

* **Default:** store the JWT in memory (React state, not persisted). A page refresh requires re-login — this is the accepted V1 default.
* If `localStorage` is used instead for developer convenience, this is a documented deviation and must be flagged here explicitly: storing a JWT in `localStorage` makes it readable by any JavaScript running on the page, so a successful XSS attack anywhere on the frontend can exfiltrate the token. If this trade-off is taken, mitigate it by keeping the JWT expiration short (the 2-hour default already limits the exposure window) and by being disciplined about not introducing `dangerouslySetInnerHTML` or unsanitized third-party scripts on the frontend.

### 2.3 Session Revocation — `token_version`

Because JWTs are otherwise stateless, V1 implements revocation via a `token_version` integer column on `users` (see `DATABASE_SCHEMA.md` Section 6.1):

* The JWT payload embeds `token_version` at issue time.
* **Every protected request re-fetches the user's current `token_version` from the database and compares it to the JWT's value.** A mismatch → `401 Unauthorized`, regardless of otherwise-valid signature/expiry.
* Incremented on: role change, account deactivation, Admin-forced logout.

This costs one DB lookup per authenticated request. It is documented as such — it must not be described elsewhere as free or instantaneous revocation, since it depends on this check actually being implemented in the auth middleware.

### 2.4 CSRF — Not Applicable in V1

Because there is no cookie-based session (no ambient credential the browser auto-attaches), CSRF does not apply to this architecture. No CSRF token generation, storage, or validation logic is implemented in V1. See Section 12 for the full deferred list.

---

## 3. Multi-Factor Authentication — Deferred to V2

MFA (TOTP-based, for Admin accounts) is **not implemented in V1**. See Section 12. If implemented in a future version, it should follow RFC 6238 (HMAC-SHA1, 30-second time step, 6-digit codes), with the TOTP secret encrypted at rest and recovery codes stored as hashes — but none of this is built or tested against in V1, and no `TOTP_ENCRYPTION_KEY` or related secret exists in this scope.

---

## 4. Threat Detection — Deferred to V2

Brute-force detection (rolling 5-minute failed-login window) and out-of-hours login flagging are **not implemented in V1**. See Section 12.

### 4.1 API Rate Limiting

**Decision: Deferred to V2. V1 does not implement application-level API rate limiting.**

Rationale: V1's scope already excludes MFA, brute-force detection, and threat monitoring; rate limiting is consistent with that same boundary rather than an exception to it. It is useful but not a core requirement for the semester MVP, and adding it would introduce implementation and testing work outside the frozen scope. V1 relies on Render's and Supabase's platform-level limits alone. If added in a future version, a library-based limiter (e.g. `slowapi` for FastAPI) on `/api/auth/*` is the recommended low-effort approach.

---

## 5. Network & API Security

### 5.1 Trusted Proxy IP Extraction

Render operates behind reverse-proxy infrastructure. The backend must be configured so that forwarded client IP information is trusted only from configured/trusted proxy infrastructure. The application must not blindly trust an arbitrary client-supplied `X-Forwarded-For` header. When a trusted proxy is correctly configured, the backend may use the forwarded client IP for audit logging.

### 5.2 CORS

* `Access-Control-Allow-Origin` must contain only the exact production frontend origin (e.g. `https://my-grc-app.vercel.app`). Wildcard (`*`) origins are prohibited.
* Because V1 uses header-based auth rather than cookies, `Access-Control-Allow-Credentials` is **not required** — this is a direct simplification following from the Section 2 session design, not an oversight.
* Allowed methods: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS`. Only required methods/headers are exposed to the frontend.

### 5.3 Input Validation

All client-controlled input must be validated on the backend: email addresses, UUIDs, role/department/resource identifiers, request status values, textual fields, query/pagination parameters, security-sensitive request bodies. Frontend validation improves UX but is never a security control.

### 5.4 SQL Injection Prevention

The backend must use parameterized queries / ORM parameterization / validated query parameters. Raw SQL must never be built by concatenating untrusted input; user-controlled values must never be interpolated directly into SQL statements.

---

## 6. Authentication & Authorization Security

### 6.1 Backend Authorization Authority

The Python backend is the sole authority for authentication, authorization, RBAC, department isolation, access governance, and audit logging. Frontend route protection and UI visibility are not security boundaries. Every protected API request must be authorized server-side.

### 6.2 RBAC Enforcement

The backend must verify: the user is authenticated, the JWT's `token_version` matches the current DB value, the account is active, the user's role, the required permission, and the applicable scope.

Authorization must follow: **Authenticated + Valid token_version + Active Account + Required Permission + Valid Scope**

Unauthenticated requests → `401 Unauthorized`. Authenticated but unauthorized → `403 Forbidden`.

### 6.3 Department Isolation

Manager access is limited to the Manager's own department, derived from the authenticated user's server-side account information. Client-provided `department_id`, `user_id`, `request_id`, `resource_id` values must never be trusted to establish authorization scope. Cross-department attempts must return `403 Forbidden` without unauthorized data exposure or mutation.

### 6.4 Privilege Escalation Prevention

Users must not be able to modify their own `role_id`, `department_id`, permissions, or administrative privileges through normal API requests. Changes to privileged attributes require appropriate authorization, must be audited, and must increment the affected user's `token_version` so any existing session is invalidated on its next request rather than continuing under stale privileges.

---

## 7. Access Governance Transaction Security

### 7.1 Approval Transaction (atomic)

1. Lock the relevant pending access request.
2. Verify status is `PENDING`.
3. Verify reviewer authorization and department scope.
4. Verify the resource is active.
5. Change the request to `APPROVED`.
6. Create/update the `user_resource_access` record → `GRANTED`, set `granted_at`, record the approving user.
7. Create the audit event.
8. Commit.

If any step fails, roll back — this prevents an approved request without corresponding granted access.

### 7.2 Rejection Transaction

Lock the pending request → verify `PENDING` → verify authorization/scope → set `REJECTED` → set `reviewed_by`/`reviewed_at` → audit event → commit. A rejected request must not create granted access.

### 7.3 Access Revocation

`GRANTED → REVOKED`: set `revoked_at`, record `revoked_by`, preserve the historical record, create an audit event. Historical records are never physically deleted merely because access was revoked.

---

## 8. Audit & Database Integrity

### 8.1 Audit Log Protection

Audit logs are append-only. The API exposes no `UPDATE`/`DELETE` operations on `audit_logs`. Records contain: timestamp, acting user, department snapshot, action, target user, resource, IP address, status, metadata where appropriate. Audit logging must never store plaintext passwords or other authentication secrets.

### 8.2 Database-Level Controls — Actual Enforcement

Append-only is enforced structurally, not just by omitting endpoints:

```sql
REVOKE UPDATE, DELETE ON audit_logs FROM app_role;
GRANT INSERT, SELECT ON audit_logs TO app_role;
```

**This only works if the application connects using a restricted role, not the Supabase default connection.** Supabase's default connection string commonly uses a role with broad (often superuser-adjacent) privileges via the connection pooler. If the app connects with that default role, the `REVOKE` above is meaningless — the app can still bypass it. A dedicated, restricted database role must be created for the application's runtime connection, and `DATABASE_URL` must point to that role, not the default one. This must be explicitly verified during setup, not assumed.

This guarantees the *application* cannot alter audit history through its normal operation. It does not defend against a compromised database superuser or direct console access — that distinction must not be blurred into a claim of full immutability.

The Supabase service-role key (which bypasses RLS entirely) must never be exposed to the frontend, and should not be the credential the backend uses for routine audit writes either — use the restricted `app_role` for that.

---

## 9. Last Active Admin Safeguard

The system must never allow an administrative action to leave it without an active Admin. Applies to operations that would deactivate, demote, or otherwise remove the final active Admin's authority.

### 9.1 Transaction-Safe Enforcement

The check and modification must occur inside the same transaction, with the relevant Admin rows locked before the decision:

```sql
BEGIN;

SELECT id
FROM users
WHERE role_id = 1
  AND is_active = true
FOR UPDATE;

-- Application verifies at least one active Admin will remain
-- after the requested change, then performs it only if so.

COMMIT;
```

A non-transactional `COUNT(active_admins) = 1` check alone is insufficient — concurrent requests could bypass it.

### 9.2 User Deletion

V1 prefers account deactivation (`is_active = false`) over physical deletion, to preserve historical audit and access-governance context.

---

## 10. Secrets & Environment Configuration

Security-sensitive configuration must never be committed to source control. Required for V1:

```text
DATABASE_URL       (pointing to the restricted app_role, not the default Supabase role)
JWT_SECRET
CORS_ALLOWED_ORIGIN
```

The frontend must never receive backend-only secrets. The Supabase service-role key is strictly backend-only and, per Section 8.2, shouldn't be the routine connection credential either. A committed secret must be treated as compromised and rotated.

---

## 11. Security Headers, Error Handling, Dependencies, Deployment

### 11.1 Security Headers
Apply where supported: `Strict-Transport-Security` (HSTS) for HTTPS, `X-Content-Type-Options: nosniff`, `Content-Security-Policy` where compatible with the frontend, a restrictive `Referrer-Policy`, appropriate `Permissions-Policy`. Test against the actual Vercel/Render deployment to avoid breaking legitimate functionality.

### 11.2 Error Handling & Information Disclosure
Production error responses must not reveal: database credentials, environment variables, JWT secrets, password hashes, stack traces, internal SQL, filesystem paths, infrastructure credentials. Authentication errors should avoid unnecessarily revealing whether a specific account exists. Detailed diagnostics may be logged server-side while the client receives a safe error response.

### 11.3 Dependency Management
Keep Python/JavaScript dependencies reasonably current. Review security-sensitive libraries (`argon2-cffi`, JWT library, FastAPI dependencies, database drivers, frontend dependencies) for known vulnerabilities before deployment. Use trusted package sources only.

### 11.4 Platform Security
* **Vercel:** HTTPS, no exposed backend secrets, credentials sent only to the intended backend origin.
* **Render:** HTTPS, secrets in environment configuration, CORS restricted to the production frontend, correct trusted-proxy handling, debug mode disabled in production.
* **Supabase:** restricted `app_role` for the application connection (Section 8.2), protected credentials, service-role key backend-only and not used for routine operations.

---

## 12. Deferred to V2 (Explicitly Outside V1 Security Scope)

Consistent with `PREREQUISITES.md` Section 8, `ARCHITECTURE.md` Section 15, and `REQUIREMENTS.md` Section 14:

* MFA / TOTP / recovery codes and their associated encryption key management
* CSRF token generation, storage, and validation (not applicable — no cookie session)
* Brute-force detection (rolling-window failed-login analysis) and its dashboard
* Out-of-hours login flagging
* External SSO / Google / Microsoft authentication
* External VPN/CRM/ERP provisioning
* Machine-learning anomaly detection
* Native mobile application
* Real-time database subscriptions
* Paid SIEM / paid external alerting services
* Automatic IP blocking
* Fully immutable/tamper-proof audit infrastructure (Section 8.2's guarantee is deliberately narrower)
* Enterprise-grade centralized secrets management

These are scope decisions, not gaps to silently reintroduce during implementation.

---

## 13. Security Testing Checklist

### Authentication
- [ ] Passwords are stored only as Argon2id hashes.
- [ ] Incorrect passwords are rejected.
- [ ] Inactive users cannot authenticate.
- [ ] JWT is returned in the response body and used via `Authorization: Bearer`.
- [ ] JWT expiration is enforced.
- [ ] A JWT with a stale `token_version` (after role change/deactivation/forced logout) is rejected with `401`.

### Authorization
- [ ] Employee cannot access another employee's records.
- [ ] Manager cannot access another department.
- [ ] Manager cannot modify global roles.
- [ ] Employee cannot approve or revoke access.
- [ ] Frontend-only permission checks cannot bypass backend authorization.
- [ ] Privilege escalation attempts return `403`.

### Access Governance
- [ ] Only `PENDING` requests can be approved/rejected.
- [ ] Approval atomically creates `GRANTED` access.
- [ ] Rejection does not create granted access.
- [ ] Revocation changes access to `REVOKED`.
- [ ] Historical access records remain available.

### Audit
- [ ] Login successes/failures are audited.
- [ ] Access requests, approvals/rejections, grants/revocations are audited.
- [ ] Privileged user/role changes are audited.
- [ ] Audit logs cannot be modified through normal API endpoints.
- [ ] **A direct `UPDATE`/`DELETE` against `audit_logs` using the application's own DB credentials fails** — verifies Section 8.2's grant restriction actually works, not just that no endpoint exists for it.
- [ ] Sensitive authentication secrets are never written to audit metadata.

### Infrastructure
- [ ] CORS allows only the production frontend origin.
- [ ] Backend secrets are not exposed to the frontend.
- [ ] Production debug mode is disabled.
- [ ] HTTPS is enforced.
- [ ] Security headers are configured where appropriate.
- [ ] Database credentials are protected; the app connects via the restricted `app_role`, not the default/service-role credential.

### Last Admin Protection
- [ ] Final active Admin cannot be deactivated.
- [ ] Final active Admin cannot be demoted.
- [ ] The safeguard is transaction-safe; concurrent privileged requests cannot bypass it.

---

## 14. Final Security Principles

1. Never store authentication secrets in plaintext.
2. Use Argon2id for password hashing.
3. Use header-based JWT (`Authorization: Bearer`), not cookies — a deliberate architectural choice for this cross-origin topology, not a shortcut.
4. Enforce `token_version` revocation on every protected request; document it as a per-request DB check, never as free/instant revocation.
5. Enforce RBAC and department isolation entirely on the backend.
6. Treat frontend controls as usability features, not security boundaries.
7. Use parameterized database access to prevent SQL injection.
8. Restrict CORS to the trusted production frontend.
9. Trust forwarded IP information only from configured proxies.
10. Record security-relevant events through append-only audit logging, enforced at both the API and database-grant level — verify the app connects with a role that actually has the grants restricted.
11. Keep approval, granting, revocation, and admin safeguards transaction-safe.
12. Never allow the system to lose its final active Admin.
13. Keep backend secrets outside source control and frontend code.
14. Prefer realistic, zero-cost V1 security controls over unsupported enterprise claims — MFA, CSRF, and threat detection are explicitly deferred rather than implemented partially or claimed without being built.

### Security Model

**Authentication proves who the user is.**
**RBAC determines what the user is allowed to do.**
**Scope determines which records the user may access.**
**`token_version` ensures a revoked or changed session can't keep acting on stale privileges.**
**Audit logging records security-relevant actions, and the database itself — not just the API — refuses to let those records be altered.**
**The backend enforces all security decisions.**
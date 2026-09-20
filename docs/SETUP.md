# Setup Log — GRC Access Governance System

This file records all setup steps completed so far, so progress doesn't need to be re-explained later.

---

## ✅ Step 1: Project Folder

Location: `C:\GRC-SAP`

Reason: Kept outside OneDrive (to avoid sync conflicts), simple path (no special characters/spaces).

```bash
mkdir C:\GRC-SAP
cd C:\GRC-SAP
```

---

## ✅ Step 2: Virtual Environment

```bash
uv venv --python 3.12
.venv\Scripts\activate
```

Python version installed: `3.12.13`

Once activated, the prompt shows `(GRC-SAP) C:\GRC-SAP>` — this means the venv is active.

To reactivate later (when opening a new terminal):
```bash
cd C:\GRC-SAP
.venv\Scripts\activate
```

---

## ✅ Step 3: Project Folder Structure

```bash
mkdir backend
mkdir frontend
mkdir docs
mkdir tests
```

Result: `backend/`, `frontend/`, `docs/`, `tests/` folders created inside `C:\GRC-SAP`.

---

## ✅ Step 4: Backend Dependencies

```bash
cd backend
uv pip install fastapi uvicorn pydantic sqlalchemy psycopg2-binary argon2-cffi "python-jose[cryptography]" python-dotenv
```

Note: `"python-jose[cryptography]"` must be in quotes — safer with bracket syntax on Windows CMD/PowerShell.

Result: 27 packages installed successfully, no errors. Verified via `uv pip list` — all expected packages present: `fastapi==0.141.1`, `uvicorn==0.52.4`, `sqlalchemy==2.0.52`, `psycopg2-binary==2.9.13`, `argon2-cffi==25.1.0`, `python-jose==3.5.0` (with `cryptography==50.0.1`), `python-dotenv==1.2.3`.

---

## ✅ Step 5: Supabase Database Connected

* Supabase project created: `GRC-Access-Governance` (region: South Asia / Mumbai, `ap-south-1`)
* GitHub repo created: `husnain-infosec/GRC-Access-Governance` (Private, pushed successfully, `.env` confirmed NOT tracked)
* `.env` created at `C:\GRC-SAP\backend\.env` with `DATABASE_URL`, `JWT_SECRET` (cryptographically generated), `CORS_ALLOWED_ORIGIN` (left blank until frontend framework/port is chosen)
* `.gitignore` created at project root
* **Important fix:** Supabase's "Direct Connection" hostname (`db.xxx.supabase.co`) failed to resolve — likely IPv6-only, incompatible with the local network. Switched to **Session Pooler** connection string (`...pooler.supabase.com:5432`) — this worked.
* Backend structure created: `backend/app/{models,routes,core,schemas}/` with `__init__.py` in each
* `backend/app/core/config.py` — loads settings from `.env` using an absolute path (`Path(__file__).resolve().parent.parent.parent / ".env"`) so it doesn't depend on the terminal's working directory
* `backend/app/core/database.py` — SQLAlchemy engine + session setup
* **Verified:** `python -c "from app.core.database import engine; conn = engine.connect(); print('Connection successful'); conn.close()"` → "Connection successful"

---

## ✅ Step 6: SQLAlchemy Models & Tables Created

* All 9 models written in `backend/app/models/`: `role.py`, `department.py`, `permission.py`, `user.py`, `role_permission.py`, `resource.py`, `access_request.py`, `user_resource_access.py`, `audit_log.py` — all exactly matching `DATABASE_SCHEMA.md`.
* **Note:** in `audit_log.py`, the `metadata` column is named `metadata_json` on the Python side (SQLAlchemy's `Base` class already uses the `metadata` attribute internally), but `Column("metadata", JSONB, ...)` was used so the actual DB column name is still `metadata` — matching the schema doc.
* `models/__init__.py` imports all 9 models so `Base.metadata.create_all()` registers all of them.
* Command run:
  ```bash
  python -c "from app.models import *; from app.core.database import engine, Base; Base.metadata.create_all(bind=engine); print('Tables created successfully')"
  ```
* **Verified in the Supabase Table Editor** — all 9 tables created: `access_requests`, `audit_logs`, `departments`, `permissions`, `resources`, `role_permissions`, `roles`, `user_resource_access`, `users`.
* Tables show "UNRESTRICTED" (RLS off) — **this is expected**, since RLS was deliberately not used (`ARCHITECTURE.md`); the backend enforces authorization itself, and DB-level control is handled via table `GRANT`/`REVOKE` (next step).

---

## ✅ Step 7: Restricted DB Role (`app_role`) Created

* Created a role named `app_role` via SQL Editor, granted full SELECT/INSERT/UPDATE/DELETE on the normal tables (roles, departments, permissions, users, role_permissions, resources, access_requests, user_resource_access).
* **Granted only SELECT + INSERT on the `audit_logs` table, explicitly not UPDATE/DELETE** — per `SECURITY.md` Section 8.2, enforcing append-only behavior.
* Verified: `SELECT rolname FROM pg_roles WHERE rolname = 'app_role';` → row returned, role exists.
* **Switched `.env`'s `DATABASE_URL` to `app_role` credentials.**

### ⚠️ Important fixes encountered in this step (worth remembering, may recur):

1. **"Smart quotes" issue in SQL Editor** — copy-pasting sometimes converts straight quotes (`'`) into curly quotes (`‘’`), which causes a Postgres syntax error. Fix: type quotes manually with the keyboard instead of pasting.

2. **Session Pooler username format — the project-ref suffix is required even for `app_role`.** Using just `app_role` alone caused a "no tenant identifier provided" error. Correct format:
   ```
   postgresql://app_role.jneqodwuhlfscpbcsaja:PASSWORD@aws-0-ap-south-1.pooler.supabase.com:5432/postgres
   ```
   (`jneqodwuhlfscpbcsaja` is our Supabase project ref — same pattern as `postgres.PROJECT_REF`, just with `app_role` as the username)

3. If the old error (`user "postgres"`) still appears after updating `.env`, it means **the file wasn't saved or the wrong line was edited** — re-open `.env` to verify.

* **Final verified:** `python -c "from app.core.database import engine; conn = engine.connect(); print('Connection successful'); conn.close()"` → "Connection successful", now via `app_role`.

---

## ✅ Step 8: Foreign Key Rules & Unique Indexes

* Set `user_id` foreign keys in `access_request.py` and `user_resource_access.py` to `ondelete="RESTRICT"` — per `DATABASE_SCHEMA.md` Section 13, this preserves history by preventing hard-deletion of users with related records. **(This was missed the first time the models were written; going forward, code will be explicitly cross-checked against the docs before sharing.)**
* Created unique partial indexes via Supabase SQL Editor:
  ```sql
  CREATE UNIQUE INDEX idx_unique_pending_request
  ON access_requests (user_id, resource_id)
  WHERE status = 'PENDING';

  CREATE UNIQUE INDEX idx_unique_active_grant
  ON user_resource_access (user_id, resource_id)
  WHERE status = 'GRANTED';
  ```
* Verified via `SELECT indexname FROM pg_indexes WHERE tablename IN ('access_requests', 'user_resource_access') AND indexname LIKE 'idx_unique%';` — both indexes confirmed present.

---

## ✅ Step 9: Performance Indexes Created

* Created 14 performance indexes (per `DATABASE_SCHEMA.md` Section 14) on the users, access_requests, user_resource_access, and audit_logs tables.
* Verified via `SELECT indexname FROM pg_indexes WHERE indexname LIKE 'idx_%' ORDER BY indexname;` — all 16 of our own indexes (14 performance + 2 unique) confirmed present.
* Note: the query result also showed indexes from Supabase's own internal `auth.*`/`storage.*` schemas (`idx_auth_code`, `idx_objects_*`, etc.) — these are not ours, Supabase creates them for its own services, and can be ignored.

---

## ✅ Step 10: Password Hashing Utility (Argon2id)

* Created `backend/app/core/security.py` with `hash_password()` and `verify_password()` functions using `argon2-cffi`'s `PasswordHasher`.
* Parameters match `SECURITY.md` Section 1.1 exactly: Time Cost `2`, Memory Cost `65536 KB (64 MB)`, Parallelism `2`. Salt handled automatically by the library.
* **Verified with a test script:**
  ```bash
  python -c "from app.core.security import hash_password, verify_password; h = hash_password('TestPassword123'); print('Hash created:', h.startswith('$argon2id$')); print('Correct password verifies:', verify_password('TestPassword123', h)); print('Wrong password rejected:', not verify_password('WrongPassword', h))"
  ```
  Result: `Hash created: True`, `Correct password verifies: True`, `Wrong password rejected: True` — all checks passed.
* Reminder: if a `ModuleNotFoundError` shows up unexpectedly, check `where python` first — this project has repeatedly run into the venv not being active in a new terminal session.

---

## ✅ Step 11: JWT Utility

* Created `backend/app/core/jwt_utils.py` with `create_access_token()` and `decode_access_token()` using `python-jose`.
* Payload matches `SECURITY.md` Section 2.1 exactly: `user_id`, `role_id`, `department_id`, `token_version`, `exp`. Algorithm `HS256`, expiry 2 hours.
* **Important correction during this step:** an earlier draft mistakenly proposed switching to cookie-based sessions and dropping `token_version` from the payload, based on a misreading of an older conversation summary. This was caught and reversed — `SECURITY.md`, `ARCHITECTURE.md`, and `RBAC.md` (all previously finalized) clearly specify header-based JWT (`Authorization: Bearer`) with no cookies and no CSRF, plus `token_version` as the sole revocation mechanism. The original design was correctly restored and confirmed against the actual frozen documents.
* Verified: token created and decoded successfully, payload fields all correct.

## ✅ Step 12: Pydantic Schemas

* Installed `email-validator` (required for Pydantic's `EmailStr` type).
* Created `backend/app/schemas/user.py` with `UserRegister`, `UserLogin`, `UserResponse`, `TokenResponse`.
* Verified: valid email passes validation, invalid email correctly raises a `ValidationError`.

## ✅ Step 13: Auth Endpoints (Register & Login)

* Added `get_db()` dependency to `backend/app/core/database.py` for per-request DB sessions.
* Created `backend/app/routes/auth.py` with `POST /api/auth/register` and `POST /api/auth/login`.
* Created `backend/app/main.py` to wire up the FastAPI app and include the auth router.
* **Important security fix during this step:** the first draft of `/register` accepted `role_id` directly from the client, which would let anyone self-assign Admin. Caught before implementation — per `RBAC.md` Section 11.3, role assignment must never be self-service. Fixed by hardcoding public registration to always create an Employee (`role_id=3`), and removing `role_id` from the `UserRegister` schema entirely so it can't even be submitted.
* Login uses a generic error message ("Invalid email or password") for both wrong password and nonexistent email, per `SECURITY.md` Section 11.2. Inactive accounts are rejected at login, per `RBAC.md` Section 11.2.

## ✅ Step 14: Roles Table Seeded

* `Base.metadata.create_all()` only creates empty tables — it doesn't insert data. Seeded the `roles` table manually via SQL Editor:
  ```sql
  INSERT INTO roles (id, name, description) VALUES
    (1, 'Admin', 'Global administrative access'),
    (2, 'Manager', 'Department-scoped management access'),
    (3, 'Employee', 'Self-service access');
  ```
* Verified: 3 rows present, matching the `1 = Admin, 2 = Manager, 3 = Employee` mapping from `PREREQUISITES.md`/`DATABASE_SCHEMA.md`.

## ✅ Step 15: End-to-End Auth Testing

* Started the server: `uvicorn app.main:app --reload` — started cleanly, no errors.
* Tested `POST /api/auth/register` — user created with `role_id: 3` (Employee), no `password_hash` in the response.
* Tested `POST /api/auth/login` with correct password — valid JWT returned.
* Tested `POST /api/auth/login` with wrong password — correctly rejected with generic `401 Invalid email or password`.

## ✅ Step 16: First Admin Bootstrap

* Since there's no Admin-management endpoint yet, and public registration can only create Employees, the first Admin was bootstrapped manually:
  1. Registered a normal account via `/register` (created as Employee).
  2. Promoted it via SQL: `UPDATE users SET role_id = 1 WHERE email = 'testadmin@example.com';`
  3. Logged in again — new JWT correctly shows `role_id: 1`.
* This bootstrap approach (register normally, then promote via one-time SQL) is the agreed pattern for creating the first Admin. A proper Admin-only user-management endpoint is still a future step (see Next Steps).

---

## ✅ Step 17: Authentication Middleware

* Created `backend/app/core/dependencies.py` with `get_current_user()` — reads `Authorization: Bearer <token>` header, decodes the JWT, and enforces:
  1. Valid token signature and expiry
  2. **`token_version` matches the current database value** (the actual revocation mechanism)
  3. Account is active
* **Bug caught during review:** `uuid.UUID(payload.get("user_id"))` could raise an unhandled `ValueError` on a malformed payload, producing a raw `500` with a stack trace instead of a clean `401` — violates `SECURITY.md` Section 11.2 (no internal details in error responses). Fixed by wrapping in `try/except`.
* **Verified with a temporary test route** (`/api/test-protected`, later removed):
  - Valid token → `200 Access granted` ✅
  - No token → `401 Not authenticated` ✅
  - Garbage/tampered token → `401 Invalid or expired token` ✅
  - **`token_version` revocation confirmed working end-to-end:** bumped `token_version` in the DB via SQL, reused the old (still unexpired, correctly signed) token, and it was correctly rejected with `401` — proving the revocation mechanism actually works, not just that it's coded.

## ✅ Step 18: RBAC Role-Based Dependency

* Created `backend/app/core/rbac.py` with `require_roles(*allowed_role_ids)` — a dependency factory that runs authentication first (via `get_current_user`), then checks the user's `role_id` against an allowed list, returning `403 Insufficient permissions` on failure (not `401`, since the user is authenticated but unauthorized) — matches `RBAC.md` Section 14.
* Scope note: this only covers role-level checks (e.g., "Admin only"). Department-scope checks (Manager restricted to their own department) will need to be implemented per-endpoint later, since the comparison differs per resource.
* **Verified with temporary test routes** (later removed): Admin token → granted; Employee token → correctly blocked with `403`.

### ⚠️ Debugging issues encountered in this stretch (all resolved, worth remembering):

1. **Repeated venv-not-active errors** — running `uvicorn`/`curl` from a terminal where `.venv\Scripts\activate` hadn't been run keeps producing `ModuleNotFoundError`. Always confirm `(GRC-SAP)` is showing in the prompt before running Python/uvicorn commands.
2. **Running uvicorn from the wrong directory** (`C:\GRC-SAP` instead of `C:\GRC-SAP\backend`) causes `ModuleNotFoundError: No module named 'app'`.
3. **Testing with the literal placeholder text** (`YOUR_TOKEN_HERE`, `PASTE_TOKEN_HERE`, `EMPLOYEE_TOKEN_HERE`) instead of substituting the actual token — always replace placeholders with the real copied value before running a command.
4. **Test route code was accidentally pasted into the wrong file** (`core/rbac.py` instead of `main.py`), causing `NameError: name 'app' is not defined` since `rbac.py` has no `FastAPI()` instance. Fixed by moving the test routes to `main.py` and keeping `rbac.py` limited to just `require_roles`.
5. **Indentation error introduced while editing `routes/auth.py`** (email-lowercasing fix) — two lines lost their indentation, causing `IndentationError: unexpected indent` and the server failing to start entirely (which made `curl` appear to hang, since nothing was actually listening on the port). Fixed by re-pasting the full corrected file with consistent indentation.
* **General lesson reinforced:** when a server won't start or a request behaves unexpectedly, always check the **server terminal** for crash output first, not just the client terminal's response.

## ✅ Step 19: Two Security Gaps Found During a Full Audit and Fixed

After finishing the RBAC dependency, a full audit was done across every file against the frozen docs. No doc violations were found, but two general best-practice gaps (not specified in any doc, but normal expected practice) were identified and fixed:

1. **No minimum password length was enforced.** Fixed by adding `Field(min_length=8)` to `UserRegister.password` in `schemas/user.py`. Verified: a 5-character password is now correctly rejected with a clear validation error.
2. **Email uniqueness was case-sensitive**, meaning `Test@Example.com` and `test@example.com` could have registered as separate accounts. Fixed by normalizing email to lowercase in both `register` and `login` in `routes/auth.py`, before querying or saving. Verified: registering with mixed case stores lowercase, a duplicate with different case is correctly rejected, and login works regardless of case used.

* Removed all temporary test routes (`/api/test-protected`, `/api/test-admin-only`, `/api/test-admin-or-manager`) from `main.py` after verification — `main.py` is back to just the app setup and the auth router.

---

## ✅ Step 20: Access Request Creation & Listing

* Created `backend/app/schemas/access_request.py` with `AccessRequestCreate` (only accepts `resource_id` and `reason` — never `user_id` or `status` from the client) and `AccessRequestResponse`.
* Created `backend/app/routes/access_requests.py`:
  - `POST /api/access-requests` — creates a request. `user_id` always comes from the authenticated session (`current_user.id`), never the request body, per `RBAC.md` Section 6.1. `status` is hardcoded to `"PENDING"` on creation. Checks the target resource exists and is active before allowing the request.
  - `GET /api/access-requests/me` — lists only the current user's own requests, filtered server-side by `current_user.id`.
* **First real exercise of the unique partial index (`idx_unique_pending_request`) created weeks earlier:** attempting a duplicate `PENDING` request for the same user+resource pair is now caught at the database constraint level, wrapped in `try/except IntegrityError`, and returned as a clean `400` message instead of a raw `500` database error.
* Registered the new router in `main.py`.
* **Filename mismatch bug:** the routes file was initially named `access_request.py` (singular), while `main.py`'s import statement expected `access_requests.py` (plural) — caused `ModuleNotFoundError`. Fixed by renaming the file. (Note: the schemas file is correctly named `access_request.py` singular, matching its own import — only the routes file needed the "s".)
* **Verified end-to-end:**
  - Created a test resource directly via SQL (`INSERT INTO resources ...`) since no resource-management endpoint exists yet.
  - Created an access request as an Employee → `201`, correct fields, `status: PENDING`.
  - Attempted a duplicate pending request for the same resource → correctly rejected with `400`.
  - Listed own requests via `/me` → correctly returned only this user's request.

---

## ✅ Step 21: Manager Approval/Rejection with Department-Scope Enforcement

* Added `POST /api/access-requests/{request_id}/approve` and `POST /api/access-requests/{request_id}/reject` to `routes/access_requests.py`.
* Both endpoints require `ADMIN` or `MANAGER` role (via `require_roles`). Department-scope check applies only when the caller is a `MANAGER` — Admins bypass it (global scope), matching `RBAC.md` Section 6.2/6.4.
* Only `PENDING` requests can be approved/rejected, per `DATABASE_SCHEMA.md` Section 9.
* **Approval creates/updates a separate `user_resource_access` row (`status="GRANTED"`) in the same transaction as the request status update** — correctly preserving the separation between request lifecycle and actual access state that `DATABASE_SCHEMA.md` requires. Handles re-granting correctly (updates an existing row rather than inserting a duplicate) so it doesn't violate the `idx_unique_active_grant` constraint.
* Rejection does not touch `user_resource_access` at all, per `DATABASE_SCHEMA.md` Section 9.2.
* **Verified end-to-end with real cross-department test data:**
  - Created two departments (IT, HR) and two Managers, one per department, via the register + SQL-promote bootstrap pattern.
  - IT Manager approved an IT Employee's request → `status: APPROVED`, and confirmed via direct SQL query that `user_resource_access` was correctly created with `status: GRANTED`, correct `granted_by`/`granted_at`.
  - **HR Manager attempted to approve the same IT Employee's request → correctly blocked with `403 Insufficient permissions`.** This is the first real proof that department-scope enforcement works, not just that the code looks correct.
  - IT Manager then successfully approved a second request from the same Employee, confirming the correct-department path still works after the cross-department block was tested.

### ⚠️ Lesson reinforced again in this stretch:
Multiple failed test attempts in this step were caused by pasting literal placeholder text (`EMPLOYEE_TOKEN`, etc.) into curl commands instead of the actual copied token value. Going forward, tokens will be fully substituted into example commands before sharing them, to eliminate this failure mode entirely rather than relying on manual substitution.

---

## ✅ Step 22: Revoke Access Endpoint

* Added `POST /api/access-requests/revoke` to `routes/access_requests.py`, taking `user_id` + `resource_id` directly (rather than an access-record ID), since that matches how this would naturally be invoked from an admin/manager dashboard.
* Same `ADMIN`/`MANAGER` role requirement and department-scope rule as approve/reject — Manager restricted to their own department, Admin bypasses — per `RBAC.md` Section 7.2.
* Only revokes a record with current `status == "GRANTED"` (can't revoke something already revoked or never granted).
* Sets `status = "REVOKED"`, `revoked_at`, `revoked_by` — never deletes the row, preserving history per `DATABASE_SCHEMA.md` Section 10.2/10.3.
* **Indentation bug caught during this step:** a stray blank/indented line before `class RevokeRequest(BaseModel):` misaligned the class body, causing `IndentationError: expected an indented block after class definition`. Fixed by replacing the entire file with a cleanly re-indented version.
* **Verified end-to-end:**
  - IT Manager revoked the IT Employee's previously-granted VPN access → `status: REVOKED`, correct `revoked_at`/`revoked_by`, with `granted_at`/`granted_by` preserved (not wiped).
  - **HR Manager attempted to revoke the same Employee's (different resource's) access → correctly blocked with `403`,** consistent with the approve/reject department-scope behavior already proven in Step 21.

**Milestone: the full access governance lifecycle is now working end-to-end and verified with real test data — create request → department-scoped approve/reject → grant → department-scoped revoke.**

---

## ✅ Step 23: Audit Logging Implementation

* Created `backend/app/core/audit.py` with `log_audit_event()` — a helper that builds an `AuditLog` row and calls `db.add()` only (no commit), so it can be committed atomically together with whatever action it's logging, per `SECURITY.md` Section 7's transaction-safety requirement.
* Wired logging into: `register` (`USER_CREATED`), `login` (`LOGIN_SUCCESS` / `LOGIN_FAILURE`, including the inactive-account case with metadata), `create_access_request` (`ACCESS_REQUEST_CREATED`), `approve_access_request` (`ACCESS_REQUEST_APPROVED` + `ACCESS_GRANTED`), `reject_access_request` (`ACCESS_REQUEST_REJECTED`), `revoke_access` (`ACCESS_REVOKED`) — matching the action names in `ARCHITECTURE.md` Section 12.
* Used `db.flush()` (not `db.commit()`) before logging in `register` and `create_access_request`, so the new row's ID exists for the audit log to reference, without ending the transaction early.
* **Verified end-to-end with real data:** confirmed via direct SQL query that `LOGIN_SUCCESS` and `LOGIN_FAILURE` both appear correctly with the right `user_id`/`ip_address`/`timestamp`, and that `USER_CREATED` appears on registration with `user_id` and `target_user_id` both set to the new account (correctly reflecting self-registration, not an admin-initiated creation).

## ✅ Step 24 — Major Incident: Login Route Broken, Root Cause Found and Fixed

**Symptom:** After adding audit logging to `access_requests.py`, `/api/auth/login` started returning `404 Not Found`, even after multiple server restarts.

**What made this hard to diagnose:** Several misleading factors compounded at once:
- Multiple terminal tabs had been opened over the course of the session, each potentially running its own `uvicorn --reload` instance in the background without being noticed.
- Port 8000 had **multiple processes** competing for it at different points — confirmed via `netstat -ano | findstr :8000` showing more than one PID, and via a "Duplicate Operation ID" warning in the uvicorn startup log (which only happens when the same route is registered more than once in a single running app).
- Killing one PID at a time was unreliable, since `uvicorn --reload` spawns a reloader process *and* a worker process, and closing a terminal window doesn't always cleanly stop both.

**Actual root cause (found by reading files directly from disk with `type`, bypassing the editor):** When audit logging was added to `access_requests.py`, the updated content was accidentally saved into `auth.py` instead — likely a copy-paste into the wrong open editor tab. This meant:
- `auth.py` no longer contained `register`/`login` at all — it contained a duplicate copy of the access-requests routes, with `router = APIRouter(prefix="/api/access-requests", ...)`.
- `access_requests.py` still had its *old* content (pre-audit-logging).
- `main.py` correctly imported `auth_router` from `auth.py`, but that file's `router` variable was now the wrong router — hence login "not existing" despite `main.py` itself being correct all along.
- Both files defining the same routes under the same variable name (`router`) is exactly why FastAPI logged "Duplicate Operation ID" warnings.

**Fix:**
1. Force-killed all Python processes at once (`taskkill /IM python.exe /F`) and confirmed via `netstat` that port 8000 was completely empty before starting a single fresh server — eliminating any ambiguity about which process was answering requests.
2. Verified both files' actual content directly from disk (`type app\routes\auth.py`, `type app\routes\access_requests.py`) rather than trusting the editor, since editor tab confusion was the root cause.
3. Restored `auth.py` to its correct register/login content, and `access_requests.py` to its correct content (including the audit logging that had gone missing from it).
4. **Verified both are working again:** login returns a valid token, and `/api/access-requests/me` correctly returns the user's own (now-approved) requests.

**Lessons for the rest of this project:**
- When a route "disappears" unexpectedly despite the relevant import/include lines in `main.py` looking correct, suspect that the *content* of the imported file has been overwritten with something else — verify with `type <file>` directly from disk, not by trusting what the editor shows, since editor state and disk state can diverge.
- A "Duplicate Operation ID" warning at server startup is a strong, specific signal that the same router (or route) is registered twice — check for content accidentally duplicated across files with a similar structure.
- Keep to a single terminal tab for running the server where practical, and always confirm `netstat -ano | findstr :8000` is empty before starting a new server if anything seems inconsistent — don't assume closing a window fully stopped the process behind it.

---

## ✅ Step 25: Admin-Only User Management Endpoints

* Added `UserListResponse` and `RoleChangeRequest` schemas to `schemas/user.py`.
* Created `backend/app/routes/users.py`:
  - `GET /api/users` — Admin sees all users; Manager sees only their own department, per `RBAC.md` Section 12.
  - `PATCH /api/users/{user_id}/role` — Admin only. Changes a user's role.
  - `PATCH /api/users/{user_id}/deactivate` — Admin only. Deactivates a user.
* **Both role-change and deactivation increment `token_version`**, per `RBAC.md` Section 11.3 — any existing session for that user is invalidated on its next request rather than continuing under stale privileges.
* **Last-Admin protection included in both endpoints**, per `RBAC.md` Section 11.1 / `SECURITY.md` Section 9. **Honesty note recorded:** the current implementation uses a simple `count() <= 1` preflight check, not the fully transaction-safe `SELECT ... FOR UPDATE` lock-and-recheck pattern `SECURITY.md` Section 9.1 specifies. This is a known simplification, not a false claim of completeness — a proper fix would wrap this in a `SELECT ... FOR UPDATE` transaction to guard against concurrent demotion attempts.
* Both actions are audited (`ROLE_CHANGED` with old/new role in metadata, `USER_DEACTIVATED`).
* **Verified end-to-end:**
  - Attempted to demote the only Admin to Employee → correctly blocked with `400 Cannot remove the last active Admin`.
  - Promoted the test Employee to Manager via the new endpoint (instead of raw SQL) → response correctly showed `role_id: 2`.
  - **Confirmed via direct SQL query that `token_version` incremented from `0` to `1`** as a side effect of the role change — proving the mechanism that forces re-authentication after a privilege change actually fires, not just that the code looks like it should.

---

## ✅ Step 26: Admin-Only Resource Management Endpoints

* Created `backend/app/schemas/resource.py` with `ResourceCreate`/`ResourceResponse`.
* Created `backend/app/routes/resources.py`:
  - `GET /api/resources` — any authenticated user can view active resources (matches `RBAC.md`'s permission table: `resources.read` is available at some scope to all three roles).
  - `POST /api/resources` — Admin only, creates a resource. Uses `db.flush()` + `IntegrityError` catch for the `name` uniqueness constraint, same pattern as access requests.
  - `PATCH /api/resources/{resource_id}/deactivate` — Admin only.
* Both create/deactivate are audited (`RESOURCE_CREATED`, `RESOURCE_DEACTIVATED`) — flagged honestly as action names not verbatim listed in `ARCHITECTURE.md`'s example list, but consistent with its general "security-sensitive actions are auditable" principle.
* **Verified end-to-end:** created an `ERP` resource as Admin, confirmed duplicate name correctly rejected with `400`, confirmed `GET /api/resources` lists all three resources (VPN, CRM, ERP) correctly.

## ✅ Step 27: Transaction-Safe Last-Admin Protection — Fixed a Real Bug Along the Way

* Upgraded `change_user_role` and `deactivate_user` in `routes/users.py` to use `.with_for_update()` when checking the active-Admin count, replacing the earlier non-transactional `count() <= 1` preflight (flagged as a known gap in Step 25).
* **Bug caught during testing:** the first version combined `.with_for_update()` with SQLAlchemy's `.count()`, which compiles to a SQL `COUNT()` aggregate — Postgres rejects `FOR UPDATE` combined with an aggregate function outright (`psycopg2.errors.FeatureNotSupported`), causing a `500 Internal Server Error` instead of the intended clean `400`.
* **Fixed by locking the actual matching rows with `.with_for_update().all()`, then counting the locked results in Python with `len()`** — this is the textbook-correct pattern (lock actual rows, not an aggregate), and Postgres accepts it without error.
* **Verified end-to-end:** re-ran the last-Admin demotion attempt — now correctly returns `400 Cannot remove the last active Admin` instead of `500`. Also confirmed an ordinary (non-last-Admin) role change still works correctly after the fix.
* **Unrelated issue surfaced during this testing, diagnosed and fixed:** a `psycopg2.OperationalError: server closed the connection unexpectedly` appeared once — traced to Supabase's free-tier Session Pooler dropping idle connections, not an application bug (SQLAlchemy's connection pool was already holding a stale connection object). Fixed by adding `pool_pre_ping=True, pool_recycle=300` to the engine in `core/database.py`, which makes SQLAlchemy test/refresh connections before reuse rather than surfacing a `500` when Supabase silently closes one.

**Backend is now functionally complete for V1 scope:** auth, RBAC, department isolation, full access-request lifecycle, user management (with transaction-safe last-Admin protection), resource management, and audit logging are all implemented and verified end-to-end.

---

## ⬜ Next Steps (remaining)

## ✅ Step 28: Frontend Project Created & Connected to Backend

* Created React project via Vite: `npm create vite@latest frontend -- --template react`, chose Oxlint for the scaffold but switched to ESLint given the plan to extend the project toward V2 (broader plugin/community support).
* Ran `npm install` and confirmed dev server starts correctly at `http://localhost:5173/`.
* Updated `backend/.env`: `CORS_ALLOWED_ORIGIN=http://localhost:5173`.
* Added CORS middleware to `backend/app/main.py` via `CORSMiddleware`, restricted to the exact configured origin (`allow_credentials=False`, since auth is header-based, not cookie-based, per `SECURITY.md` Section 5.2).
* **Two bugs found and fixed while wiring this up:**
  1. `.env` had a duplicated key on one line — `CORS_ALLOWED_ORIGIN=CORS_ALLOWED_ORIGIN=http://localhost:5173` — which made the actual value nonsensical and caused every CORS check to fail. Fixed by correcting the line to a single `CORS_ALLOWED_ORIGIN=http://localhost:5173`.
  2. `.env` changes require a full server restart — `uvicorn --reload` only watches Python file changes, not `.env`. A restart was needed for the corrected value to take effect.
* **Verified end-to-end:** built a temporary test button in `App.jsx` that calls `fetch('http://127.0.0.1:8000/api/resources')` — confirmed it correctly reaches the backend and receives `401 Unauthorized` (expected, since no token was sent), proving the full frontend → CORS → backend chain works.

---

## ⬜ Next Steps (remaining)

* [ ] Build the actual frontend: login page, role-specific dashboards, access request forms, admin/manager views (per the verified sitemap discussed earlier in this project)
* [ ] Wire up JWT storage (in-memory, per `SECURITY.md` Section 2.2 — not localStorage by default) and attach it via `Authorization: Bearer` on protected requests
* [ ] Testing
* [ ] Deployment (Render + Vercel)

---

## ✅ Step 29: Tailwind CSS Setup & Verified

* Installed `tailwindcss` + `@tailwindcss/vite`.
* Updated `frontend/vite.config.js` to include the `tailwindcss()` plugin alongside `react()`.
* Replaced `frontend/src/index.css` content with a single `@import "tailwindcss";` line.
* **Verified visually:** styled test button/heading (dark background, bold heading, blue rounded button) rendered correctly, confirming Tailwind classes are being applied, not just that the CSS file loads.

## ✅ Step 30: Auth Context, Login Page, and Full Auth Flow Working

* Created `frontend/src/context/AuthContext.jsx` — holds `token` and decoded `user` in React state (`useState`) only. **Not `localStorage`**, per `SECURITY.md` Section 2.2's default (page refresh logs the user out — accepted V1 trade-off).
* Installed `jwt-decode` to read `role_id`/`department_id`/`user_id` out of the JWT client-side for UI display (role label, etc.) — this is purely for UI convenience; all real authorization stays backend-enforced.
* Created `frontend/src/components/Login.jsx` — calls `POST /api/auth/login`, displays the backend's exact generic error message on failure (no extra client-side interpretation), decodes and stores the token via `AuthContext` on success.
* Rebuilt `frontend/src/App.jsx` to route between `Login` (no token) and the main dashboard shell (token present), with a role label and Logout button (Logout just clears React state — no backend call needed, since there's no server-side session to invalidate).
* **File-save issue encountered and resolved:** `App.jsx` updates weren't taking effect in the browser — turned out the file still had the old test-button content; a full manual "select all, delete, paste, save" cleared it up. Reinforces the same lesson from the backend file mix-ups: always verify the file's actual saved content when behavior doesn't match expectations.
* **Verified end-to-end in the browser:**
  - Correct login (`testemployee@example.com`) → dashboard shell shown, correctly labeled "Logged in as Employee".
  - Logout → correctly returns to the login page.
  - Wrong password → correct red-banner display of the backend's exact "Invalid email or password" message.

## ✅ Step 31: Access Request Creation & Listing (Employee Dashboard) — Working End-to-End

* Created `frontend/src/components/CreateRequest.jsx` — fetches the resource list from `GET /api/resources` for the dropdown, submits to `POST /api/access-requests` with the selected resource and optional reason, shows success/error inline, and triggers a list refresh via an `onCreated` callback.
* Created `frontend/src/components/MyRequests.jsx` — fetches and displays `GET /api/access-requests/me` in a table, with color-coded status badges (PENDING/APPROVED/REJECTED), and renders `CreateRequest` above it.
* Wired both into `App.jsx`'s dashboard view.
* **Verified end-to-end in the browser:** the two pre-existing approved requests (from earlier backend-only testing) displayed correctly with correct status/reason/date; submitted a brand-new request through the actual UI form, and it appeared instantly in the table with `PENDING` status and today's date, with a "Request submitted successfully" confirmation and automatic form reset.
* **Noted improvement for later:** the table currently shows a truncated resource UUID (e.g. `11bcd9a8...`) rather than the resource's actual name (e.g. "CRM"), since the request response doesn't include the resource name directly. A future refinement should map resource IDs to names (e.g. by fetching `/api/resources` once and joining client-side).

**Milestone: the full Employee-side workflow — login, submit an access request, view request history and status — is now working end-to-end through the actual UI, not just via curl.**

---

## ⬜ Next Steps (remaining)

* [ ] Minor UX improvement: show resource names instead of truncated UUIDs in the requests table
* [ ] Manager dashboard: view department requests, approve/reject buttons
* [ ] Admin dashboard: view all requests/users/resources, role management, resource management, revoke access
* [ ] Route protection / role-based view switching in the frontend (currently only one dashboard view exists, built for Employee use)
## ✅ Step 32: Manager Dashboard — Pending Requests, Approve/Reject, Granted Access, Revoke — All Working End-to-End

**Backend gap found and fixed:** while building the Manager UI, discovered there was no endpoint to list "all pending requests for review" or "all currently granted access" — only `create`, `/me`, `approve`, `reject`, and `revoke` existed, none of which let a Manager/Admin *discover* what needs reviewing or revoking without already knowing a specific ID. This had gone unnoticed because earlier backend testing always used IDs already known from a prior `create` response.

* Added `GET /api/access-requests/pending` — Admin sees all pending requests; Manager sees only requests from users in their own department (via a `JOIN` on `users.department_id`, since `access_requests` itself doesn't store department).
* Added `GET /api/access-requests/granted` — same department-scoping pattern, but against `user_resource_access` filtered to `status == "GRANTED"`.
* **Verified both via curl** with a Manager token: `/pending` correctly returned only the department's request; `/granted` correctly returned only the department's granted VPN access.

**Frontend built and verified in the browser:**
* `frontend/src/components/DepartmentRequests.jsx` — lists pending requests with Approve/Reject buttons, calling the existing `approve`/`reject` endpoints.
* `frontend/src/components/GrantedAccess.jsx` — lists granted access with a Revoke button, calling the existing `revoke` endpoint.
* Wired both into `App.jsx`'s dashboard view for Manager/Admin roles (Employee still sees `MyRequests`).
* **Verified end-to-end as Manager (`testmanager@example.com`):**
  - Approved a pending request → success message shown, request disappeared from the pending list (now `APPROVED` in the DB, `GRANTED` access created).
  - Rejected a pending request → success message shown, request disappeared from the pending list.
  - Revoked a granted access → success message shown, entry disappeared from the granted list.
* **Minor recurring hiccup, not a real bug:** a duplicate-looking "Pending Requests" section appeared once after a live code edit — resolved by a hard refresh (`Ctrl+Shift+R`); confirmed via `type src\App.jsx` that the component was only referenced once in the file, so this was a stale Hot Module Reload state, not a code duplication issue.

**Milestone: both Employee and Manager dashboards are now fully functional end-to-end through the actual UI** — the complete access governance lifecycle (request → department-scoped approve/reject → grant → department-scoped revoke) works from the browser, not just via curl.

---

## ⬜ Next Steps (remaining)

* [ ] Admin dashboard: user management (list/role-change/deactivate), resource management (create/deactivate) — Admin currently reuses the Manager view, which works for requests/grants but has no UI yet for user/resource management
* [ ] Minor UX improvement: show resource/user names instead of truncated UUIDs throughout the UI
* [ ] Testing
* [ ] Deployment (Render + Vercel)

---

## Useful Commands Reference

| Task | Command |
|------|---------|
| Activate venv | `.venv\Scripts\activate` |
| Deactivate venv | `deactivate` |
| Install a package | `uv pip install <package>` |
| List installed packages | `uv pip list` |
| Run FastAPI server (later) | `uvicorn app.main:app --reload` |
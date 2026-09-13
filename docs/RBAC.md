# Role-Based Access Control (RBAC)

**Project:** Access Governance System (V1 — Semester Scope)

**Scope note:** This document reflects the trimmed V1 scope in `PREREQUISITES.md`. MFA-related restrictions and `security_alerts.read` (threat detection) are removed — see Section 16.

---

## 1. Purpose

The system uses three application roles:

* **Admin**
* **Manager**
* **Employee**

Authorization is enforced exclusively by the backend API. Frontend visibility is a UI convenience only and must never be treated as a security control.

---

## 2. RBAC Principles

1. **Least Privilege** — users receive only the permissions required for their role.
2. **Role-Based Authorization** — permissions are assigned through roles, not individually to users.
3. **Backend Enforcement** — every protected endpoint validates authentication, role, permission, and scope.
4. **Department Isolation** — Managers are restricted to their own department; a Manager cannot view or modify another department's users, requests, or access records.
5. **Global Administrative Scope** — Admins operate across all departments.
6. **Self-Service Scope** — Employees can access only their own profile, access records, and access requests.
7. **Auditability** — security-sensitive and privileged actions generate audit log entries.

---

# 3. Roles

## 3.1 Admin

### Scope
**GLOBAL** — system-wide administrative authority.

### Responsibilities
* Manage users
* Manage departments
* Manage roles
* Manage resources
* Review access requests
* Grant and revoke application-level resource access
* View audit logs
* Maintain system configuration within V1 capabilities

### Restrictions
An Admin:
* Must not be able to remove or deactivate the final active Admin account.
* Must not be able to remove the final Admin privilege unless another active Admin already exists.
* Must not have access to plaintext passwords.
* Must have privileged actions recorded in the audit log.
* Can force-invalidate a user's sessions by incrementing that user's `token_version` (see `DATABASE_SCHEMA.md` Section 6.1) — this is the V1 mechanism for "logout everywhere," since there is no session store to clear directly.

---

## 3.2 Manager

### Scope
**DEPARTMENT** — a Manager operates only within their assigned department.

### Responsibilities
* View users within their own department
* View access requests from their own department
* Review, approve, or reject eligible requests within their department
* View resource access states for users within their department
* Grant or revoke application-level access where authorized

### Restrictions
A Manager:
* Cannot access another department's users.
* Cannot approve or reject another department's requests.
* Cannot grant or revoke access for users outside their department.
* Cannot manage global roles.
* Cannot create or manage Admin privileges.
* Cannot modify system-wide security configuration.
* Cannot bypass backend department-scope checks.

If a Manager attempts to access a resource outside their department, the backend returns `403 Forbidden`. No unauthorized data is returned and no unauthorized state is modified.

---

## 3.3 Employee

### Scope
**SELF** — the most restricted role.

### Responsibilities
* View their own profile and resource access
* Create access requests for themselves
* View their own access-request history and status

### Restrictions
An Employee:
* Cannot view other users' profiles or access requests.
* Cannot approve, reject, grant, or revoke access.
* Cannot manage departments, roles, or resources.
* Cannot view audit logs.

---

# 4. Permission Model

| Permission                        | Admin  | Manager     | Employee |
| ---------------------------------- | ------ | ----------- | -------- |
| `users.read`                       | GLOBAL | DEPARTMENT  | SELF     |
| `users.manage`                     | GLOBAL | DEPARTMENT* | NO       |
| `departments.read`                 | GLOBAL | OWN         | NO       |
| `departments.manage`                | YES    | NO          | NO       |
| `roles.read`                        | YES    | NO          | NO       |
| `roles.manage`                      | YES    | NO          | NO       |
| `resources.read`                    | GLOBAL | DEPARTMENT  | SELF     |
| `resources.manage`                  | YES    | NO          | NO       |
| `access_requests.create`            | YES    | YES         | SELF     |
| `access_requests.read_own`          | YES    | YES         | SELF     |
| `access_requests.read_department`   | YES    | OWN         | NO       |
| `access_requests.approve`           | YES    | OWN         | NO       |
| `access_requests.reject`            | YES    | OWN         | NO       |
| `access.read_own`                   | YES    | YES         | SELF     |
| `access.read_department`            | YES    | OWN         | NO       |
| `access.grant`                       | YES    | OWN         | NO       |
| `access.revoke`                      | YES    | OWN         | NO       |
| `audit_logs.read`                    | GLOBAL | LIMITED     | NO       |

`*` Manager user-management permissions are limited to department-scoped operations explicitly implemented in V1. They must never provide global user-management privileges.

`security_alerts.read` is removed for V1 — threat/security alert monitoring is deferred to V2 (Section 16).

---

# 5. Authorization Scopes

## 5.1 GLOBAL
Applies across the entire organization. Primarily used by Admin (e.g. view all departments, view system-wide audit logs, manage resources).

## 5.2 DEPARTMENT
Restricted to the authenticated Manager's department, determined from `authenticated_user.department_id` — never from a client-provided `department_id`.

Example:
```text
Manager A, Department: IT
Allowed: IT users, IT access requests, IT access records
Denied:  HR users, HR access requests, HR access records
```

## 5.3 SELF
Restricted to the authenticated user. The backend determines the target user from the authenticated session, never from a client-supplied user ID.

```text
Employee A
Allowed: GET /me, GET /me/access, GET /me/access-requests
Denied:  GET /users/Employee-B, GET /access-requests/Employee-B
```

---

# 6. Access Request Authorization

```text
REQUEST → PENDING → APPROVED / REJECTED
```

Request lifecycle is separate from actual access state (`GRANTED → REVOKED`) — this prevents workflow state from being mixed with provisioning state.

## 6.1 Employee Request
An Employee may create a request for their own account + a valid resource only. The backend derives the requester from the authenticated user; an Employee cannot create a request on behalf of another user by modifying a requester ID in the payload.

## 6.2 Manager Approval
A Manager may approve a request only when: the request exists, its status is `PENDING`, the requester belongs to the Manager's department, the target resource is active, and the Manager has the required permission. If the department-scope condition fails → `403 Forbidden`, and no access state is modified.

## 6.3 Manager Rejection
Same preconditions minus the resource-active check. Transitions the request to `REJECTED` and records the rejection in the audit log.

## 6.4 Admin Approval or Rejection
An Admin may approve or reject eligible requests across all departments. Approval may set access to `GRANTED`; rejection results in `REJECTED`. Privileged Admin actions are recorded in `audit_logs`.

---

# 7. Grant and Revoke Authorization

Modifies `user_resource_access`.

## 7.1 Grant Access
Only authorized Admins and Managers may grant access.
* **Admin scope:** GLOBAL — may grant access for an eligible user across departments.
* **Manager scope:** `Manager.department_id == TargetUser.department_id` — cannot grant to a user in another department.

On grant: `status = GRANTED`, `granted_at = NOW()`.

## 7.2 Revoke Access
Same authorization rules apply. On revoke: `status = REVOKED`, `revoked_at = NOW()`. Historical records are never silently deleted to remove current access.

---

# 8. Department Isolation

A backend authorization rule applying to user records, access requests, resource access records, and department-scoped views.

**Prohibited:** treating `GET /users?department_id=HR` as authorized merely because the frontend supplied `department_id=HR`.

**Correct logic:**
```text
Authenticated Manager → Load authenticated user's department_id →
Determine requested target → Determine target's department →
Compare departments → Allow OR 403
```

---

# 9. Frontend vs Backend Authorization

The frontend may hide navigation items by role (e.g. hide Admin Dashboard/User Management/Audit Logs from Employees; hide Global Administration/Role Management from Managers) — but this is never a security mechanism. A malicious user can call backend API endpoints directly. Every protected endpoint independently enforces:

```text
Authentication → Role → Permission → Scope → Operation
```

The backend is the final authority.

---

# 10. Authorization Flow

```text
1. Receive API request
2. Validate JWT signature + expiry
3. Validate token_version against current DB value (see ARCHITECTURE.md Section 6) — mismatch → 401
4. Load authenticated user
5. Verify account is active
6. Determine user's role
7. Verify required permission
8. Apply GLOBAL / DEPARTMENT / SELF scope
9. Perform authorized operation
10. Create audit log where required
11. Return response
```

Authentication failure → `401 Unauthorized`. Authentication succeeds but authorization fails → `403 Forbidden`.

---

# 11. Sensitive Authorization Rules

## 11.1 Last Active Admin Protection
The system must prevent accidental removal of the final active Admin. Operations that could leave the system without an active Admin (deactivation, privilege removal, deletion if implemented) must be rejected unless another active Admin already exists. This check must be enforced atomically at the transaction level — a simple non-transactional `COUNT(active_admins) == 1` check is insufficient, since concurrent requests could bypass it.

## 11.2 Inactive Users
An inactive user must not authenticate or perform protected operations. The backend verifies `users.is_active = TRUE` before allowing access.

## 11.3 Privilege Escalation Prevention
Users must not modify their own `role_id`, `department_id`, or permissions through ordinary self-service endpoints. Role and department changes require administrative authorization, and must increment the affected user's `token_version` so any existing session reflects the change on the next request rather than continuing under stale privileges.

## 11.4 Cross-Department Manipulation
A Manager must not bypass department restrictions by modifying `user_id`, `department_id`, `request_id`, or `resource_id` in an API request. The backend resolves and validates the complete authorization context from server-side data only.

---

# 12. Endpoint Authorization Matrix

| Endpoint Category     | Admin  | Manager              | Employee             |
| ----------------------| ------ | --------------------- | --------------------- |
| Authentication         | Own    | Own                    | Own                    |
| Own Profile             | Full   | Full                    | Full                    |
| Other Users             | Global | Own Department         | Denied                 |
| Departments             | Manage | Read permitted scope    | Denied                 |
| Roles                   | Manage | Denied                  | Denied                 |
| Resources               | Manage | Read permitted scope    | Read permitted scope    |
| Create Access Request   | Yes    | Yes                     | Own only                |
| Own Requests            | Yes    | Yes                     | Own only                |
| Department Requests     | Yes    | Own Department          | Denied                 |
| Approve Request         | Yes    | Own Department          | Denied                 |
| Reject Request          | Yes    | Own Department          | Denied                 |
| Grant Access            | Yes    | Own Department          | Denied                 |
| Revoke Access           | Yes    | Own Department          | Denied                 |
| Own Access              | Yes    | Own                     | Own only                |
| Department Access       | Yes    | Own Department          | Denied                 |
| Audit Logs              | Global | Limited Scope           | Denied                 |

---

# 13. Audit Requirements

Actions that generate audit events:
* Login success / failure
* Logout, where implemented
* User creation, modification, activation/deactivation
* Role changes (and the resulting `token_version` increment)
* Department changes
* Resource creation/modification
* Access request creation, approval, rejection
* Access grant, revocation
* Privileged administrative actions

Audit records capture: `timestamp, acting user, department snapshot, action, target user, resource, IP address, status`. The record must represent the action that actually occurred, not merely a frontend event.

Audit records are append-only, enforced at both the API level and the database permission level (see `DATABASE_SCHEMA.md` Section 12.3). V1 does not claim protection against a compromised database superuser — only that the application itself cannot alter history.

---

# 14. Error Handling

* Unauthenticated → `401 Unauthorized`
* Authenticated but insufficient permission → `403 Forbidden`
* Resource outside authorized scope → `403 Forbidden`

The API avoids leaking sensitive information through detailed authorization error messages.

---

# 15. RBAC and Database Relationship

```text
roles → users → department_id
```

Role permissions: `roles`, `permissions`, `role_permissions`.
Department-scoped authorization: `users.department_id`.
Access governance: `access_requests`.
Actual resource access: `user_resource_access`.
Security/privileged activity tracking: `audit_logs`.
Session revocation: `users.token_version`.

This separation keeps authorization logic, request lifecycle, provisioning state, and audit history logically distinct.

---

# 16. Deferred to V2 (Removed From V1 RBAC Model)

Consistent with `PREREQUISITES.md` Section 8 and `ARCHITECTURE.md` Section 15:

* MFA-related restrictions (plaintext TOTP secret/recovery code access rules)
* `security_alerts.read` permission and any threat-monitoring authorization
* CSRF-token-related authorization steps (not applicable — V1 uses header-based JWT, no cookie session)
* External SSO / Google / Microsoft authentication
* Automatic VPN/CRM/ERP provisioning authorization
* Automatic IP blocking
* Paid SIEM integration authorization

V1 represents access governance and provisioning state at the application level only. A `GRANTED` record means the user has been granted access within this application — it does not provision access in a real external system.

---

# 17. Security Principle

```text
Authentication proves who the user is.
RBAC determines what the user is allowed to do.
Scope determines which records the user is allowed to affect.
The backend enforces all three.
```

No frontend control, request parameter, client-side role value, or manipulated identifier can override backend authorization.

---

# 18. Final RBAC Rule

For every protected operation:

```text
ALLOW = Authenticated AND Active Account AND Valid token_version
        AND Required Permission AND Valid Scope
```

Otherwise: `DENY`. The backend enforces this rule consistently across all protected API endpoints.
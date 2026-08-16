# DealGuard AI — Authentication, Session Lifecycle & RBAC Specification

> **Status**: Production Architecture Baseline  
> **Security Baseline**: Argon2id Hashing + Short-Lived JWT + Persistent Refresh Sessions (Token Family Rotation & Reuse Detection)  
> **Multi-Tenancy Model**: Server-side Authoritative Context Binding (`TenantContext`)  

---

## 1. Authentication Architecture & Token Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor Client as Web Frontend / API Client
    participant API as FastAPI Router (/api/v1/auth)
    participant AuthSvc as AuthService
    participant DB as PostgreSQL (users, auth_sessions, audit_events)

    Note over Client,DB: 1. User Authentication (Login)
    Client->>API: POST /api/v1/auth/login {email, password}
    API->>AuthSvc: login(email, password)
    AuthSvc->>DB: Fetch user by email (Argon2id verify)
    AuthSvc->>DB: Create AuthSession with SHA-256(refresh_token) & TokenFamilyUUID
    AuthSvc->>DB: Log AuditEvent(LOGIN_SUCCESS)
    AuthSvc-->>Client: {access_token (15m), refresh_token (7d), user, organization, role, permissions}

    Note over Client,DB: 2. Authenticated API Request
    Client->>API: GET /api/v1/deals (Authorization: Bearer <access_token>)
    API->>API: Decode JWT -> Extract user_id, org_id, role
    API->>DB: Validate user active & tenant membership -> Inject TenantContext
    API-->>Client: 200 OK [Deals List]

    Note over Client,DB: 3. Token Rotation & Reuse Detection (Refresh)
    Client->>API: POST /api/v1/auth/refresh {refresh_token}
    API->>AuthSvc: refresh_session(refresh_token)
    AuthSvc->>DB: Lookup session by SHA-256(refresh_token)
    alt Token already revoked (Reuse anomaly detected)
        AuthSvc->>DB: Revoke ALL sessions in token_family_id!
        AuthSvc->>DB: Log AuditEvent(REFRESH_REUSE_DETECTED)
        AuthSvc-->>Client: 401 Unauthorized (Compromised session invalidated)
    else Token valid and active
        AuthSvc->>DB: Mark old session revoked_at = now()
        AuthSvc->>DB: Create new AuthSession (same token_family_id)
        AuthSvc->>DB: Log AuditEvent(REFRESH)
        AuthSvc-->>Client: {new_access_token, new_refresh_token}
    end

    Note over Client,DB: 4. Explicit Session Revocation (Logout)
    Client->>API: POST /api/v1/auth/logout {refresh_token}
    API->>AuthSvc: logout(refresh_token)
    AuthSvc->>DB: Mark session revoked_at = now()
    AuthSvc->>DB: Log AuditEvent(LOGOUT)
    AuthSvc-->>Client: 200 OK {success: true}
```

---

## 2. RBAC Permission Matrix

| Permission | Description | `ADMIN` | `LEAD` | `ANALYST` | `REVIEWER` | `AUDITOR` |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `organization:read` | View institutional organization profile | ✅ | ✅ | ✅ | ✅ | ✅ |
| `organization:manage` | Manage institutional tenant settings | ✅ | ❌ | ❌ | ❌ | ❌ |
| `users:read` | View institutional team members | ✅ | ✅ | ❌ | ❌ | ❌ |
| `users:manage` | Invite, assign, or deactivate users | ✅ | ❌ | ❌ | ❌ | ❌ |
| `deals:read` | View permitted deal rooms | ✅ | ✅ | ✅ | ✅ | ✅ |
| `deals:create` | Create new deal rooms & target company profiles | ✅ | ✅ | ✅ | ❌ | ❌ |
| `deals:update` | Edit deal parameters and metadata | ✅ | ✅ | ✅ | ❌ | ❌ |
| `deals:delete` | Archive / delete deal room | ✅ | ✅ | ❌ | ❌ | ❌ |
| `deals:manage_members` | Add/remove team members to deal room | ✅ | ✅ | ❌ | ❌ | ❌ |
| `documents:read` | Read data room documents and citations | ✅ | ✅ | ✅ | ✅ | ✅ |
| `documents:upload` | Ingest new documents into data room | ✅ | ✅ | ✅ | ❌ | ❌ |
| `documents:delete` | Delete uploaded documents | ✅ | ✅ | ❌ | ❌ | ❌ |
| `financials:read` | View 3-statement tables & metrics | ✅ | ✅ | ✅ | ✅ | ✅ |
| `financials:write` | Modify financial line items & manual inputs | ✅ | ✅ | ✅ | ❌ | ❌ |
| `risks:read` | View 17-pillar risk register & citations | ✅ | ✅ | ✅ | ✅ | ✅ |
| `risks:write` | Create / adjust risk scores | ✅ | ✅ | ✅ | ❌ | ❌ |
| `risks:review` | Approve, override, or accept risk findings | ✅ | ✅ | ❌ | ✅ | ❌ |
| `audit:read` | View immutable audit trail and review history | ✅ | ✅ | ❌ | ✅ | ✅ |
| `analysis:run` | Trigger valuation & sensitivity engines | ✅ | ✅ | ✅ | ❌ | ❌ |
| `analysis:review` | Review and sign off on investment committee pack | ✅ | ✅ | ❌ | ✅ | ❌ |

---

## 3. Deal-Level Team Scoping (`validate_deal_membership`)

1. **Organization Boundary**: A user must belong to the tenant organization owning the deal.
2. **Deal Team Assignment**: Non-admin users must have an active assignment record in `deal_members` (`LEAD`, `ANALYST`, `REVIEWER`, `LEGAL`, `AUDITOR`).
3. **Admin Override**: Users with role `ADMIN` or `is_superuser = True` have institutional administrative access across all deal rooms in their organization.
4. **IDOR Defense**: Accessing a deal without membership returns `403 Forbidden` (or `404 Not Found` if the deal belongs to an alien tenant, preventing resource existence enumeration).

---

## 4. Evaluation Credentials (Synthetic Seed Data)

| Role | Email | Password | Granted Scope |
| :--- | :--- | :--- | :--- |
| **Tenant Admin** | `admin@dealguard.ai` | `DemoPassword123!` | Full tenant administration across all deal rooms & users |
| **M&A Analyst** | `analyst@dealguard.ai` | `DemoPassword123!` | Financial modeling, document upload, risk analysis on assigned deals |
| **IC Reviewer** | `reviewer@dealguard.ai` | `DemoPassword123!` | Read-only diligence + risk review, override, and IC sign-off |

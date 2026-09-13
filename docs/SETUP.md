# Setup Log — GRC Access Governance System

Is file mein ab tak ke saare setup steps likhe hain, taake baad mein yaad rahe kya kar chuke hain aur kya baaki hai.

---

## ✅ Step 1: Project Folder

Location: `C:\GRC-SAP`

Reason: OneDrive se bahar rakha (sync conflicts avoid karne ke liye), simple path (special characters/spaces nahi).

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

Activate hone ke baad prompt `(GRC-SAP) C:\GRC-SAP>` dikhta hai — iska matlab venv active hai.

Dobara activate karne ke liye (naya terminal khulne par):
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

Result: `backend/`, `frontend/`, `docs/`, `tests/` folders ban gaye `C:\GRC-SAP` ke andar.

---

## ✅ Step 4: Backend Dependencies

```bash
cd backend
uv pip install fastapi uvicorn pydantic sqlalchemy psycopg2-binary argon2-cffi "python-jose[cryptography]" python-dotenv
```

Result: 27 packages installed successfully, koi error nahi. Verified via `uv pip list` output — sab expected packages maujood: `fastapi==0.141.1`, `uvicorn==0.52.4`, `sqlalchemy==2.0.52`, `psycopg2-binary==2.9.13`, `argon2-cffi==25.1.0`, `python-jose==3.5.0` (with `cryptography==50.0.1`), `python-dotenv==1.2.3`.

---

## ⬜ Next Steps (baaki hain)

* [ ] `docs/` mein finalized docs daalna (PREREQUISITES.md, ARCHITECTURE.md, DATABASE_SCHEMA.md, RBAC.md, REQUIREMENTS.md, SECURITY.md)
* [ ] `README.md` ko **project root** `C:\GRC-SAP\README.md` mein rakhna — `docs/` mein nahi. Ye GitHub/Render/Vercel ke liye standard convention hai (root README project overview ke liye pehla point of contact hota hai).
* [ ] Supabase project banana, `DATABASE_URL` lena
* [ ] `.env` file banana (`.env.example` se copy karke)
* [ ] Restricted DB role (`app_role`) banana Supabase mein (SECURITY.md Section 8.2 ke mutabiq — audit_logs ke liye)
* [ ] FastAPI project structure banana (`backend/app/` wagera)
* [ ] Database models likhna (SQLAlchemy)
* [ ] Auth endpoints banana (register/login, Argon2id, JWT + token_version)
* [ ] RBAC middleware banana
* [ ] Access request/approval endpoints banana
* [ ] Audit logging implement karna
* [ ] Frontend setup (React + Tailwind on Vercel)
* [ ] Testing
* [ ] Deployment (Render + Vercel)

---

## Useful Commands Reference

| Kaam | Command |
|------|---------|
| Venv activate karna | `.venv\Scripts\activate` |
| Venv se nikalna | `deactivate` |
| Package install karna | `uv pip install <package>` |
| Installed packages dekhna | `uv pip list` |
| FastAPI server chalana (baad mein) | `uvicorn app.main:app --reload` |
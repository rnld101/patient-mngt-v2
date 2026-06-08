# Patient Management System

A full-stack web application for managing patient records with secure medical document storage.

Built with **FastAPI** (Python) + **React** (Vite/Tailwind) + **MySQL** + **AWS** (S3, KMS, Secrets Manager).

---

## What It Does

- Register and log in as a healthcare user
- Create, view, edit, and delete patient records
- Upload medical documents per patient (Prescriptions, Blood Reports, X-Rays, MRI, CT Scans, etc.)
- View documents securely via time-limited pre-signed S3 URLs
- All data is isolated per user — you only see your own patients

---

## Project Structure

```
patient-mngt-v2/
├── backend/                     # FastAPI application
│   ├── app/
│   │   ├── api/                 # Route handlers
│   │   │   ├── auth.py          # Register, Login
│   │   │   ├── patients.py      # Patient CRUD
│   │   │   └── documents.py     # Document upload/view/delete
│   │   ├── core/
│   │   │   ├── config.py        # App settings (pydantic-settings)
│   │   │   ├── security.py      # JWT + bcrypt
│   │   │   └── dependencies.py  # get_current_user dependency
│   │   ├── database/            # SQLAlchemy engine + session
│   │   ├── models/              # User, Patient, PatientDocument models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── auth.py          # Auth business logic
│   │   │   ├── patient.py       # Patient CRUD logic
│   │   │   └── document.py      # Document CRUD logic
│   │   ├── utils/
│   │   │   ├── aws.py           # S3 upload, pre-signed URLs, Secrets Manager
│   │   │   └── validators.py    # File type + size validation
│   │   └── main.py              # App entry point, lifespan, CORS, routers
│   ├── requirements.txt
│   ├── .env.example
│   ├── nginx.conf
│   ├── patient-app.service      # Systemd service file
│   └── Dockerfile
│
├── frontend/                    # React application
│   ├── src/
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx
│   │   │   ├── RegisterPage.jsx
│   │   │   ├── DashboardPage.jsx
│   │   │   ├── PatientsPage.jsx
│   │   │   ├── AddPatientPage.jsx
│   │   │   ├── EditPatientPage.jsx
│   │   │   └── PatientDocumentsPage.jsx   # NEW
│   │   ├── services/
│   │   │   ├── api.js            # Axios instance + auth interceptor
│   │   │   ├── authService.js    # Login/register calls
│   │   │   ├── patientService.js # Patient API calls
│   │   │   └── documentService.js # Document API calls — NEW
│   │   ├── context/AuthContext.jsx
│   │   ├── routes/PrivateRoute.jsx
│   │   ├── utils/errorHandler.js
│   │   └── App.jsx
│   ├── package.json
│   └── .env.example
│
└── docs/
    ├── README.md                 # This file
    ├── aws/
    │   ├── AWS_SETUP.md          # AWS infrastructure setup guide
    │   └── ARCHITECTURE.md       # Architecture reference
    └── deployment/
        └── DEPLOYMENT.md         # Step-by-step EC2 deployment guide
```

---

## API Endpoints

### Authentication
```
POST  /api/auth/register    Register a new user
POST  /api/auth/login       Login, returns JWT
```

### Patients  *(all require Bearer token)*
```
POST   /api/patients                    Create patient
GET    /api/patients                    List all patients
GET    /api/patients/{id}               Get patient by ID
PUT    /api/patients/{id}               Update patient
DELETE /api/patients/{id}               Delete patient
```

### Documents  *(all require Bearer token)*
```
POST   /api/patients/{id}/documents              Upload a document
GET    /api/patients/{id}/documents              List documents
GET    /api/patients/{id}/documents/{doc_id}/url Get pre-signed view URL (1 hr)
DELETE /api/patients/{id}/documents/{doc_id}     Delete document
```

### System
```
GET  /health    Health check
GET  /          API info + docs link
```

---

## Database Schema

### `users`
| Column | Type | Notes |
|---|---|---|
| id | INT | Primary key |
| username | VARCHAR(255) | Unique |
| email | VARCHAR(255) | Unique |
| hashed_password | VARCHAR(255) | bcrypt |
| created_at | DATETIME | Auto |

### `patients`
| Column | Type | Notes |
|---|---|---|
| id | INT | Primary key |
| name | VARCHAR(255) | |
| age | INT | 1–150 |
| gender | VARCHAR(50) | Male / Female / Other |
| blood_group | VARCHAR(10) | A+, B-, O+, etc. |
| phone | VARCHAR(20) | |
| address | VARCHAR(500) | |
| user_id | INT | FK → users.id |
| created_at | DATETIME | Auto |

### `patient_documents`
| Column | Type | Notes |
|---|---|---|
| id | INT | Primary key |
| patient_id | INT | FK → patients.id |
| user_id | INT | Ownership enforcement |
| document_type | VARCHAR(50) | Prescription, X-Ray, etc. |
| file_name | VARCHAR(255) | Original filename |
| s3_key | VARCHAR(500) | S3 object path |
| uploaded_at | DATETIME | Auto |

---

## AWS Services

| Service | Purpose |
|---|---|
| EC2 | Compute for backend, frontend, database |
| S3 | Private document storage (`patient_documents/` prefix) |
| KMS | Server-side encryption for S3 objects (SSE-KMS) |
| Secrets Manager | Stores DB credentials, JWT secret, bucket name |
| IAM | EC2 instance role — no access keys in code |

---

## Security

- Passwords hashed with **bcrypt** (12 rounds)
- All API routes protected with **JWT Bearer tokens**
- S3 bucket is **fully private** — documents accessed only via backend-generated **pre-signed URLs** (1-hour expiry)
- AWS credentials via **IAM instance role** — nothing hardcoded
- Secrets loaded from **AWS Secrets Manager** at startup
- Per-user data isolation — all queries enforce `user_id` ownership

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| Auth | JWT (python-jose), bcrypt (pwdlib) |
| Database | MySQL 8 |
| Frontend | React 18, Vite 5, Tailwind CSS 3, Axios |
| Routing | React Router v6 |
| Cloud | AWS (EC2, S3, KMS, Secrets Manager, IAM) |
| Server | Gunicorn + Uvicorn workers, Nginx |

---

## Quick Start (Local Development)

```bash
# Terminal 1 — Backend
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy and fill environment variables
cp .env.example .env
# Edit .env with your local DB and AWS settings

uvicorn app.main:app --reload

# Terminal 2 — Frontend
cd frontend
npm install
cp .env.example .env
# Edit VITE_API_URL if needed
npm run dev
```

Open: `http://localhost:5173`  
API docs: `http://localhost:8000/docs`

---

## Documentation

| Document | Purpose |
|---|---|
| `docs/aws/AWS_SETUP.md` | Create S3, KMS, Secrets Manager, IAM role |
| `docs/aws/ARCHITECTURE.md` | Architecture diagrams, data flows, security details |
| `docs/deployment/DEPLOYMENT.md` | Step-by-step EC2 deployment with verification |

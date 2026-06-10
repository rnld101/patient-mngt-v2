# Patient Management System

A full-stack web application for managing patient records with secure medical document storage.

Built with **FastAPI** (Python) + **React** (Vite/Tailwind) + **AWS RDS MySQL** + **AWS S3 / CloudFront** + **Terraform**.

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
│   │   │   └── PatientDocumentsPage.jsx
│   │   ├── services/
│   │   │   ├── api.js            # Axios instance + auth interceptor
│   │   │   ├── authService.js    # Login/register calls
│   │   │   ├── patientService.js # Patient API calls
│   │   │   └── documentService.js # Document API calls
│   │   ├── context/AuthContext.jsx
│   │   ├── routes/PrivateRoute.jsx
│   │   ├── utils/errorHandler.js
│   │   └── App.jsx
│   ├── package.json
│   └── .env.example
│
├── terraform/                   # Infrastructure as Code (IaC)
│   ├── modules/                 # Modular AWS sub-components
│   │   ├── vpc/                 # Multi-tier network
│   │   ├── asg/                 # Autoscaling & Application Load Balancer
│   │   ├── rds/                 # Managed MySQL DB
│   │   ├── frontend/            # S3 + CloudFront CDN + OAC
│   │   ├── iam/                 # Instance profiles & least privilege
│   │   ├── kms/                 # Key management for S3 SSE
│   │   ├── secrets/             # Dynamic secret store
│   │   ├── dns/                 # Route53 record binding
│   │   └── security-groups/     # Layered security groups
│   ├── main.tf                  # Main orchestrator
│   ├── variables.tf             # Inputs
│   ├── outputs.tf               # Outputs
│   └── terraform.tfvars         # Environment settings
│
└── docs/
    ├── aws/
    │   ├── AWS_SETUP.md          # AWS setup & prerequisites
    │   └── ARCHITECTURE.md       # Architecture reference
    └── deployment/
        └── DEPLOYMENT.md         # Automated deployment guide
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

| Service | Purpose | Benefit |
|---|---|---|
| **VPC** | Custom network segmentation | Isolates tiers into public, private, database subnets |
| **Route53** | Public DNS management | Resolves domains and points to ALB / CloudFront |
| **CloudFront** | Global Content Delivery Network (CDN) | Distributes static frontend React assets; secures bucket access |
| **S3** | Storage for frontend build and patient docs | Secure, serverless, durable, low-cost file store |
| **ALB** | Public Application Load Balancer | Performs SSL termination and routes to private backend hosts |
| **ASG** | Auto Scaling Group (EC2 nodes) | Handles backend FastAPI workloads with high availability |
| **RDS** | Managed AWS MySQL Database | Multi-AZ database engines; eliminates patching/backup overhead |
| **KMS** | Key Management Service | Centralized key controls for S3 SSE-KMS encryption |
| **Secrets Manager** | Application runtime secrets | Secures database credentials and JWT keys without local disk files |
| **IAM** | Least-privilege roles & instance profiles | Grants EC2 instances API access without hardcoded credentials |
| **VPC Endpoints** | Private interface & gateway endpoints | Keeps system traffic (SSM, S3, Secrets Manager) off public internet |

---

## Security

- Passwords hashed with **bcrypt** (12 rounds)
- All API routes protected with **JWT Bearer tokens**
- Document S3 bucket is **fully private** — documents accessed only via backend-generated **pre-signed URLs** (1-hour expiry)
- AWS credentials via **IAM instance role** — nothing hardcoded
- Secrets loaded from **AWS Secrets Manager** at startup
- Per-user data isolation — all queries enforce `user_id` ownership
- Network-level protection: compute nodes and database reside in private subnets with strict security groups

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| Auth | JWT (python-jose), bcrypt (pwdlib) |
| Database | Managed RDS MySQL 8.4 |
| Frontend | React 18, Vite 5, Tailwind CSS 3, Axios |
| Routing | React Router v6 |
| Cloud | AWS (VPC, Route53, CloudFront, ALB, ASG, S3, RDS, Secrets Manager, KMS, IAM) |
| IaC | Terraform (~> 1.5) |

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
| [`docs/aws/AWS_SETUP.md`](file:///c:/Users/RAPHEL%20M%20L/Desktop/patient-mngt-v2/docs/aws/AWS_SETUP.md) | AWS prerequisites (Route53 zone, ACM wildcard certificate) and Terraform execution |
| [`docs/aws/ARCHITECTURE.md`](file:///c:/Users/RAPHEL%20M%20L/Desktop/patient-mngt-v2/docs/aws/ARCHITECTURE.md) | Terraform production network layout, data flows, and security boundaries |
| [`docs/deployment/DEPLOYMENT.md`](file:///c:/Users/RAPHEL%20M%20L/Desktop/patient-mngt-v2/docs/deployment/DEPLOYMENT.md) | Step-by-step automated deployment, frontend build & sync, and health checking |

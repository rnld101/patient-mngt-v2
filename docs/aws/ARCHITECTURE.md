# AWS Architecture Reference

## Architecture Diagram

```
                    ┌──────────────────────────────────┐
                    │            Internet               │
                    └──────────────┬───────────────────┘
                                   │
                    ┌──────────────▼───────────────────┐
                    │       Frontend EC2 (Nginx)        │
                    │         React SPA (Vite)          │
                    │        t3.small — port 80         │
                    └──────────────┬───────────────────┘
                                   │ HTTP (Axios + JWT)
                    ┌──────────────▼───────────────────┐
                    │       Backend EC2 (Nginx)         │
                    │  FastAPI + Gunicorn — port 8000   │
                    │          t3.medium                │
                    │   IAM Role: PatientAppRole        │
                    └──────┬───────────┬───────────────┘
                           │           │
          ┌────────────────▼──┐   ┌────▼──────────────────────┐
          │    Database EC2   │   │         AWS S3             │
          │   MySQL 8.0       │   │   patient-documents/       │
          │   t3.small:3306   │   │   Private — SSE-KMS        │
          └───────────────────┘   └────────────────────────────┘

  ┌──────────────────────────┐    ┌──────────────────────────┐
  │   AWS Secrets Manager    │    │        AWS KMS            │
  │  patient-management-     │    │  Customer-managed key     │
  │  secrets                 │    │  (S3 encryption)         │
  └──────────────────────────┘    └──────────────────────────┘

  ┌──────────────────────────┐
  │       IAM Role           │
  │  PatientManagementAppRole│
  │  Attached to backend EC2 │
  └──────────────────────────┘
```

---

## EC2 Instances

| Instance | Type | RAM | Storage | Role |
|---|---|---|---|---|
| Database | t3.small | 2 GB | 20 GB GP3 | MySQL 8.0 |
| Backend | t3.medium | 4 GB | 30 GB GP3 | FastAPI + Gunicorn + Nginx |
| Frontend | t3.small | 2 GB | 20 GB GP3 | React build served via Nginx |

All instances run **Ubuntu 22.04 LTS**.

The **backend instance** must have the `PatientManagementAppRole` IAM role attached.  
The **database** and **frontend** instances require no IAM role.

---

## AWS Secrets Manager

**Secret name**: `patient-management-secrets`

```json
{
  "db_host":       "10.0.x.x",
  "db_name":       "patient_db",
  "db_user":       "patient_app",
  "db_password":   "<strong-password>",
  "jwt_secret":    "<random-64-char-string>",
  "s3_bucket_name": "patient-docs-<account-id>",
  "aws_region":    "us-east-1"
}
```

The backend loads this secret **at startup** via `boto3`. No credentials are stored in code or environment files.

---

## S3 Bucket

| Setting | Value |
|---|---|
| Name | `patient-docs-<account-id>` |
| Region | us-east-1 (or your chosen region) |
| Public access | ❌ Blocked completely |
| Encryption | SSE-KMS (customer-managed key) |
| Versioning | Enabled (recommended) |
| Object prefix | `patient_documents/<uuid>.<ext>` |

Documents are **never served from a public URL**. The backend generates a **pre-signed URL** valid for 1 hour on demand.

---

## IAM Role: `PatientManagementAppRole`

Attach this role to the **backend EC2 instance profile**.

### Policy 1 — Secrets Manager

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["secretsmanager:GetSecretValue"],
    "Resource": "arn:aws:secretsmanager:us-east-1:ACCOUNT-ID:secret:patient-management-secrets*"
  }]
}
```

### Policy 2 — S3

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::patient-docs-ACCOUNT-ID/*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::patient-docs-ACCOUNT-ID"
    }
  ]
}
```

> **Important**: `s3:GetObject` is required for pre-signed URL generation even on private buckets.  
> `s3:DeleteObject` is required for document deletion.

### Policy 3 — KMS

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["kms:Decrypt", "kms:GenerateDataKey", "kms:DescribeKey"],
    "Resource": "arn:aws:kms:us-east-1:ACCOUNT-ID:key/KEY-ID"
  }]
}
```

---

## Security Groups

### `patient-app-backend-sg` (Backend EC2)

| Direction | Port | Protocol | Source | Purpose |
|---|---|---|---|---|
| Inbound | 22 | TCP | Your IP only | SSH |
| Inbound | 80 | TCP | 0.0.0.0/0 | HTTP (Nginx) |
| Inbound | 443 | TCP | 0.0.0.0/0 | HTTPS (optional) |
| Outbound | All | All | 0.0.0.0/0 | Allow all outbound |

> Port 8000 (Gunicorn) should **not** be publicly exposed. Nginx proxies from 80 → 8000 locally.

### `patient-app-db-sg` (Database EC2)

| Direction | Port | Protocol | Source | Purpose |
|---|---|---|---|---|
| Inbound | 22 | TCP | Your IP only | SSH |
| Inbound | 3306 | TCP | patient-app-backend-sg | MySQL from backend only |
| Outbound | All | All | 0.0.0.0/0 | Allow all outbound |

### `patient-app-frontend-sg` (Frontend EC2)

| Direction | Port | Protocol | Source | Purpose |
|---|---|---|---|---|
| Inbound | 22 | TCP | Your IP only | SSH |
| Inbound | 80 | TCP | 0.0.0.0/0 | HTTP |
| Inbound | 443 | TCP | 0.0.0.0/0 | HTTPS (optional) |
| Outbound | All | All | 0.0.0.0/0 | Allow all outbound |

---

## Data Flows

### Application Startup
```
Backend EC2 boots
  → boto3 calls Secrets Manager (via IAM role — no keys needed)
  → Secrets loaded into settings (DB URL, JWT secret, bucket name)
  → SQLAlchemy connects to MySQL
  → Tables created if not exist (including patient_documents)
  → App ready to serve
```

### Patient Document Upload
```
User selects file + document type in browser
  → POST /api/patients/{id}/documents (multipart/form-data)
  → Backend validates: JWT token, patient ownership, file type, file size
  → boto3.upload_fileobj → S3 (SSE-KMS encrypts automatically)
  → S3 key stored in patient_documents table
  → DocumentResponse returned (no S3 URL — key only)
```

### Document View (Pre-signed URL)
```
User clicks "View" on a document
  → GET /api/patients/{id}/documents/{doc_id}/url
  → Backend validates ownership
  → boto3.generate_presigned_url → temporary URL (1 hour TTL)
  → Frontend opens URL in new tab
  → Browser fetches file directly from S3 (URL expires after 1 hr)
```

### Document Delete
```
User clicks "Delete"
  → DELETE /api/patients/{id}/documents/{doc_id}
  → DB record deleted first
  → boto3.delete_object → S3 file deleted
  → 204 No Content returned
```

---

## KMS Encryption

S3 encryption is handled entirely by AWS — the application code does not deal with KMS key IDs.

When a file is uploaded:
1. S3 receives the object
2. S3 checks the bucket's **default encryption** setting (SSE-KMS)
3. S3 calls KMS to generate a data key
4. S3 encrypts the object with that key
5. Only principals with `kms:Decrypt` + `kms:GenerateDataKey` can access the object

The backend EC2's IAM role has these KMS permissions, which is why pre-signed URLs and direct reads work.

---

## Cost Estimate (Monthly)

| Service | Details | Est. Cost |
|---|---|---|
| EC2 (3 instances) | 2× t3.small + 1× t3.medium | ~$28 |
| EBS Storage | 70 GB GP3 total | ~$6 |
| Secrets Manager | 1 secret | $0.40 |
| S3 Storage | 10 GB documents | ~$0.23 |
| S3 Requests | PutObject + GetObject + presigned | ~$0.10 |
| KMS | 1 key + API calls | ~$1.50 |
| Data Transfer | 5 GB outbound | ~$0.45 |
| **Total** | | **~$37/month** |

---

## Security Checklist

- [x] No hardcoded credentials anywhere in code
- [x] IAM role instead of access keys on EC2
- [x] S3 bucket public access fully blocked
- [x] Documents accessed only via pre-signed URLs
- [x] KMS encryption on all S3 objects
- [x] JWT authentication on all patient/document endpoints
- [x] Per-user data isolation enforced in all queries
- [x] bcrypt password hashing (12 rounds)
- [x] Input validation on all endpoints (Pydantic)
- [ ] HTTPS / TLS via Certbot (recommended for production)
- [ ] VPC Flow Logs
- [ ] CloudTrail enabled
- [ ] GuardDuty enabled

---

**Last updated**: June 2026

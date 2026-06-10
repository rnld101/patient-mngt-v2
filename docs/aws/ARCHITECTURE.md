# AWS Production Architecture Reference

This document describes the production architecture for the Patient Management System. The infrastructure is fully provisioned and managed using Terraform.

## Overview

The application is a secure patient and medical document management platform that enables healthcare professionals to manage patient information and securely store associated documents.

To protect sensitive medical records and personal health information (PHI), the network is designed with strict segmentation. The frontend assets are served serverlessly via a Content Delivery Network (CDN), and the compute and database tiers are completely isolated in private subnets with no direct public internet ingress.

---

## Architecture Diagram

```text
                                         Users
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │ AWS Route53  │
                                    └──────┬───────┘
                     ┌─────────────────────┴──────────────────────┐
                     │ (lavenbloom.xyz)                           │ (api.lavenbloom.xyz)
                     ▼ (HTTPS)                                    ▼ (HTTPS)
           ┌──────────────────┐                         ┌──────────────────┐
           │  AWS CloudFront  │                         │ Application Load │
           │ CDN Distribution │                         │  Balancer (ALB)  │
           └─────────┬────────┘                         └─────────┬────────┘
                     │                                            │
                     │ (Origin Access Control)                    │
                     ▼                                            │
           ┌──────────────────┐                                   │
           │    AWS S3        │                                   │
           │ Frontend Bucket  │                                   │
           └──────────────────┘                                   │
                                                                  │ (Forward to port 8000)
    ┌─────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────┐
    │ VPC (10.0.0.0/16)                                           │                                                        │
    │                                                             ▼                                                        │
    │   ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
    │   │ Public Subnets (10.0.1.0/24 & 10.0.2.0/24)                                                                   │   │
    │   │                                                                                                              │   │
    │   │   [ NAT Gateway ] (Provides outbound internet access for private subnets during bootstrap)                   │   │
    │   │                                                                                                              │   │
    │   └─────────────────────────────────────────────────────────┬────────────────────────────────────────────────────┘   │
    │                                                             │                                                        │
    │   ┌─────────────────────────────────────────────────────────┼────────────────────────────────────────────────────┐   │
    │   │ Private Subnets (10.0.11.0/24 & 10.0.12.0/24)           │                                                    │   │
    │   │                                                         │                                                    │   │
    │   │  ┌──────────────────────────────────────────────────────┼─────────────────────────────────────────────────┐  │   │
    │   │  │ Auto Scaling Group (ASG)                             │                                                 │  │   │
    │   │  │                                                      ▼                                                 │  │   │
    │   │  │  ┌────────────────────────────────────────┐     ┌────────────────────────────────────────┐             │  │   │
    │   │  │  │ Availability Zone A (us-east-1a)      │     │ Availability Zone B (us-east-1b)      │             │  │   │
    │   │  │  │                                        │     │                                        │             │  │   │
    │   │  │  │  [ Backend EC2 Instance ]              │     │  [ Backend EC2 Instance ]              │             │  │   │
    │   │  │  │  FastAPI + Gunicorn (port 8000)        │     │  FastAPI + Gunicorn (port 8000)        │             │  │   │
    │   │  │  │  No Public IP                          │     │  No Public IP                          │             │  │   │
    │   │  │  └───────────────────┬────────────────────┘     └───────────────────┬────────────────────┘             │  │   │
    │   │  └──────────────────────┼──────────────────────────────────────────────┼──────────────────────────────────┘  │   │
    │   │                         │                                              │                                     │   │
    │   │                         └──────────────────────┬───────────────────────┘                                     │   │
    │   │                                                │                                                             │   │
    │   │                                                ▼                                                             │   │
    │   │                      ┌──────────────────────────────────────────────────┐                                    │   │
    │   │                      │ VPC Endpoints                                    │                                    │   │
    │   │                      │  - Interface: SSM, Secrets Manager               │                                    │   │
    │   │                      │  - Gateway: S3 Gateway Endpoint                  │                                    │   │
    │   │                      └─────────────────────────┬────────────────────────┘                                    │   │
    │   └────────────────────────────────────────────────│─────────────────────────────────────────────────────────────┘   │
    │                                                    │                                                                 │
    │                                                    ▼ (Write/Read Objects)                                            │
    │                                          ┌──────────────────┐                                                        │
    │                                          │  AWS S3 Document │                                                        │
    │                                          │  Storage Bucket  │                                                        │
    │                                          └─────────┬────────┘                                                        │
    │                                                    │                                                                 │
    │                                                    ▼ (Server-Side Encryption)                                        │
    │                                          ┌──────────────────┐                                                        │
    │                                          │     AWS KMS      │                                                        │
    │                                          │  (SSE-KMS Key)   │                                                        │
    │                                          └──────────────────┘                                                        │
    │                                                                                                                      │
    │   ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
    │   │ Database Subnets (10.0.21.0/24 & 10.0.22.0/24)                                                               │   │
    │   │                                                                                                              │   │
    │   │   [ Managed RDS MySQL Database Instance ] (db.t3.micro - Primary/Standby)                                    │   │
    │   │   (Allowed Ingress: Port 3306 from Backend SG only)                                                          │   │
    │   └──────────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
    └──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

                                           ┌──────────────────────────┐
                                           │   AWS Secrets Manager    │
                                           │ (Dynamic secret store -  │
                                           │  loaded by app at boot)  │
                                           └──────────────────────────┘
```

---

## Compute & Host Sizing

| Tier | Resource | Type / Details | Storage | Role |
|---|---|---|---|---|
| **Database** | RDS Instance | `db.t3.micro` | 20 GB GP3 (Autoscaling to 50 GB) | Managed MySQL 8.4 engine |
| **Backend** | EC2 Instances | `t3.micro` (ASG Min: 1, Max: 2) | 20 GB GP3 | FastAPI + Gunicorn |
| **Frontend** | S3 + CloudFront | Serverless Static Site | N/A | React Build distribution |

---

## Network Architecture & Subnets

The network is built inside a custom VPC with a CIDR block of `10.0.0.0/16` and spans two Availability Zones (`us-east-1a` and `us-east-1b`).

### Subnet Allocation
1. **Public Subnets** (`10.0.1.0/24` and `10.0.2.0/24`):
   * Host the public Application Load Balancer (ALB).
   * Host the NAT Gateway for outbound traffic from the private subnets.
2. **Private Subnets** (`10.0.11.0/24` and `10.0.12.0/24`):
   * Host the Backend EC2 instances in an Auto Scaling Group.
   * Do not assign public IP addresses to instances.
3. **Database Subnets** (`10.0.21.0/24` and `10.0.22.0/24`):
   * Host the managed RDS MySQL database instance.
   * Completely isolated; database is unreachable from outside the VPC.

### VPC Endpoints
To keep application communications inside the private network boundary and avoid NAT Gateway data costs for AWS API requests:
* **Interface VPC Endpoints**: Deployed in private subnets for Systems Manager (`ssm`, `ssmmessages`), EC2 Messages (`ec2messages`), and Secrets Manager (`secretsmanager`).
* **Gateway VPC Endpoint**: Deployed inside the VPC route tables for Amazon S3 (`s3`), allowing high-bandwidth, direct private access to the S3 Document Storage Bucket.

---

## AWS Services Detail

### Route53
* **Purpose**: Manages public DNS records.
* **Benefit**: Acts as the initial entry point. Resolves requests for the apex domain (`lavenbloom.xyz`) to the CloudFront distribution, and the API subdomain (`api.lavenbloom.xyz`) to the ALB.

### CloudFront & S3 Frontend
* **Purpose**: Hosts static React single page application (SPA) files in a private S3 bucket and serves them globally.
* **Benefit**: Using Origin Access Control (OAC) prevents users from downloading files directly from S3. CloudFront caches assets at edge locations, while custom error rules rewrite 403 and 404 responses to `index.html` to support client-side React Router navigation.

### Application Load Balancer (ALB)
* **Purpose**: Acts as the single entry point for API traffic, routing requests to the Auto Scaling Group.
* **Benefit**: Terminates HTTPS/TLS traffic using certificates managed in ACM. Routes traffic to port 8000 on backend nodes and performs active health checking on the `/health` endpoint.

### Auto Scaling Group (ASG) & Launch Templates
* **Purpose**: Dynamically provisions backend EC2 instances based on CPU utilization and health metrics.
* **Benefit**: Automates fault tolerance. Launch templates define the standard configuration and execute user-data bootstrap scripts to pull code, set up virtual environments, configure systemd, and launch Gunicorn.

### AWS Relational Database Service (RDS)
* **Purpose**: Deploys a managed MySQL 8.4 database inside the isolated database subnets.
* **Benefit**: Offloads database patching, backups, and scalability. Multi-AZ replication (optional) provides high availability.

### AWS Secrets Manager
* **Purpose**: Securely stores application secrets (`db_host`, `db_name`, `db_user`, `db_password`, `jwt_secret`, `s3_bucket_name`, `aws_region`).
* **Benefit**: Prevents hardcoded credentials in the repository. The backend queries Secrets Manager during startup via `boto3` and loads the credentials strictly in-memory.

### AWS KMS
* **Purpose**: Manages a Customer Managed Key (CMK) alias `patient-app-s3-key`.
* **Benefit**: Enforces Server-Side Encryption (SSE-KMS) on all files uploaded to the patient document S3 bucket. All cryptographic operations are handled transparently by S3.

### IAM Roles & Instance Profiles
* **Purpose**: Attaches the `PatientManagementAppRole` to the backend instances.
* **Benefit**: Allows the backend instances to read from Secrets Manager, write/read from S3, and use the KMS key without needing static AWS access keys.

---

## Security Group Matrix

| Security Group | Inbound Rules | Outbound Rules | Purpose |
|---|---|---|---|
| **ALB SG** | Ports `80` & `443` from `0.0.0.0/0` | Port `8000` to Backend SG | Public HTTP/HTTPS ingress and routing to backend |
| **Backend SG** | Port `8000` from ALB SG | All traffic (`0.0.0.0/0`) | Computes API requests; permits updates/git cloning |
| **RDS SG** | Port `3306` from Backend SG | None | Strict database protection |
| **VPC Endpoint SG** | Port `443` from VPC CIDR (`10.0.0.0/16`) | All traffic (`0.0.0.0/0`) | Secure connection to AWS API endpoints |

---

## Data Flows

### 1. Application Startup
```text
Backend EC2 boots
  → Executes user-data scripts to configure environment
  → Systemd starts FastAPI via Gunicorn binding to port 8000
  → Application requests 'patient-management-secrets' from Secrets Manager via VPC Interface Endpoint
  → Secrets returned and loaded in-memory (DB host, password, JWT key)
  → SQLAlchemy connects to RDS MySQL
  → Database tables created if they do not exist
  → App is healthy and registers as online with the ALB target group
```

### 2. General API Request
```text
User Browser makes API call (HTTPS)
  → Route53 DNS resolves to ALB
  → ALB terminates SSL, validates target group health
  → ALB forwards HTTP request to a private Backend EC2 instance on port 8000
  → Backend authenticates request via JWT token
  → Backend queries RDS MySQL on port 3306
  → RDS returns SQL dataset
  → Backend compiles response and returns it via ALB to the Browser
```

### 3. Patient Document Upload
```text
User uploads diagnostic file in Browser
  → POST request sent to ALB → Backend EC2 instance
  → Backend validates JWT token and validates file constraints (type, size)
  → Backend calls S3 API via S3 Gateway Endpoint (inside VPC) to upload the file
  → S3 receives object, and S3 handles Server-Side Encryption using the Customer-Managed Key (SSE-KMS)
  → S3 key ('patient_documents/<uuid>.<ext>') is returned
  → Backend records S3 key index in RDS MySQL table 'patient_documents'
  → Response 201 Created sent to client
```

### 4. Patient Document Access (Pre-signed URL)
```text
User requests to view diagnostic file in Browser
  → GET request sent to /api/patients/{id}/documents/{doc_id}/url
  → Backend authenticates user and verifies they own the patient record
  → Backend uses boto3 to generate an S3 pre-signed URL (1-hour TTL)
  → URL is returned to Browser
  → Browser opens URL in a new tab, loading file directly from S3
  → S3 verifies signature and handles decryption via KMS Server-Side Encryption (SSE-KMS) before streaming to Browser
```

### 5. Patient Document Deletion
```text
User clicks delete on a file in Browser
  → DELETE request sent to /api/patients/{id}/documents/{doc_id}
  → Backend verifies JWT and patient ownership
  → Backend deletes index row from MySQL table 'patient_documents'
  → Backend calls S3 API to delete the object from the bucket
  → Response 204 No Content returned
```

---

**Last updated**: June 2026

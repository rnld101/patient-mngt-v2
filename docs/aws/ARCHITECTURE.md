# AWS Architecture Documentation

## Overview

This document provides a detailed technical reference for the AWS infrastructure used to deploy the Patient Management Application.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Internet                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                    ┌────▼─────┐
                    │   Route53 │ (Optional - for DNS)
                    └────┬─────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐  ┌───────▼──────┐  ┌──────▼─────┐
   │Frontend  │  │  Nginx ALB   │  │  S3 Bucket │
   │EC2       │  │ (Optional)   │  │  + KMS     │
   │(React)   │  └───────┬──────┘  └────────────┘
   └────┬─────┘          │
        │         ┌──────▼─────────┐
        └────────►│  Backend EC2   │
                  │  (FastAPI)     │
                  └──────┬─────────┘
                         │
                  ┌──────▼─────────┐
                  │  Database EC2  │
                  │  (MySQL 8)     │
                  └────────────────┘
        
        ┌─────────────────────────────┐
        │  AWS Secrets Manager        │
        │ (Credentials & JWT Secret)  │
        └─────────────────────────────┘
        
        ┌─────────────────────────────┐
        │  AWS KMS                    │
        │ (S3 Encryption Key)         │
        └─────────────────────────────┘
        
        ┌─────────────────────────────┐
        │  IAM Roles                  │
        │ (EC2 Instance Profiles)     │
        └─────────────────────────────┘
```

---

## AWS Service Details

### 1. EC2 Instances

#### Frontend Instance
- **Instance Type**: t3.small
- **vCPU**: 2
- **Memory**: 2 GB
- **Storage**: 20 GB EBS GP3
- **OS**: Ubuntu 22.04 LTS
- **Applications**: Node.js, React, Nginx
- **Port**: 80 (HTTP), 443 (HTTPS)
- **IAM Role**: None required (static content only)

#### Backend Instance
- **Instance Type**: t3.medium
- **vCPU**: 2
- **Memory**: 4 GB
- **Storage**: 30 GB EBS GP3
- **OS**: Ubuntu 22.04 LTS
- **Applications**: Python 3.13, FastAPI, Gunicorn, Nginx
- **Port**: 8000 (FastAPI), 80 (Nginx), 443 (HTTPS)
- **IAM Role**: PatientManagementAppRole
- **Required Permissions**: S3, Secrets Manager, KMS

#### Database Instance
- **Instance Type**: t3.small
- **vCPU**: 2
- **Memory**: 2 GB
- **Storage**: 20 GB EBS GP3
- **OS**: Ubuntu 22.04 LTS
- **Applications**: MySQL 8
- **Port**: 3306 (MySQL)
- **IAM Role**: None required
- **Networking**: Private subnet recommended

### 2. AWS Secrets Manager

**Secret Name**: `patient-management-secrets`

**Secret Contents**:
```json
{
  "db_host": "10.0.2.50",
  "db_name": "patient_db",
  "db_user": "patient_app",
  "db_password": "xxxxxxxxxx",
  "jwt_secret": "xxxxxxxxxx",
  "s3_bucket_name": "patient-images-bucket-1234567890",
  "aws_region": "us-east-1"
}
```

**Access Pattern**:
- Backend EC2 retrieves secret on startup
- Secret ARN: `arn:aws:secretsmanager:us-east-1:ACCOUNT-ID:secret:patient-management-secrets`

### 3. S3 Bucket

**Bucket Configuration**:
- **Name**: `patient-images-bucket-ACCOUNT-ID`
- **Region**: us-east-1
- **Versioning**: Enabled
- **Encryption**: SSE-KMS (customer-managed key)
- **Public Access**: Blocked
- **Lifecycle**: Optional - delete old versions after 30 days

**Bucket Contents**:
```
patient-images-bucket/
└── patient_images/
    ├── uuid-1.jpg
    ├── uuid-2.png
    └── uuid-3.gif
```

**Permissions**:
- Backend EC2 can: `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`
- Backend EC2 can list: `s3:ListBucket`

### 4. AWS KMS

**Key Policy**:
- **Usage**: Encrypt/Decrypt S3 objects
- **Type**: Customer-managed key
- **Rotation**: Automatic (optional)
- **Access**: Granted to Backend EC2 via IAM role

**Key ARN**: `arn:aws:kms:us-east-1:ACCOUNT-ID:key/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

**Key Policy** (Example):
```json
{
  "Sid": "Enable Backend EC2 to use the key",
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:iam::ACCOUNT-ID:role/PatientManagementAppRole"
  },
  "Action": [
    "kms:Decrypt",
    "kms:GenerateDataKey",
    "kms:DescribeKey"
  ],
  "Resource": "*"
}
```

### 5. IAM Roles and Policies

#### PatientManagementAppRole

**Attached Policies**:
1. PatientAppSecretsManagerPolicy
2. PatientAppS3Policy
3. PatientAppKMSPolicy

**Policy 1: Secrets Manager**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["secretsmanager:GetSecretValue"],
      "Resource": "arn:aws:secretsmanager:us-east-1:ACCOUNT-ID:secret:patient-management-secrets*"
    }
  ]
}
```

**Policy 2: S3**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::patient-images-bucket-ACCOUNT-ID/*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::patient-images-bucket-ACCOUNT-ID"
    }
  ]
}
```

**Policy 3: KMS**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:GenerateDataKey",
        "kms:DescribeKey"
      ],
      "Resource": "arn:aws:kms:us-east-1:ACCOUNT-ID:key/KEY-ID"
    }
  ]
}
```

### 6. Security Groups

#### Frontend Security Group (patient-app-frontend-sg)

| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 80 | TCP | 0.0.0.0/0 | HTTP |
| 443 | TCP | 0.0.0.0/0 | HTTPS |
| 22 | TCP | [Your IP] | SSH |

#### Backend Security Group (patient-app-backend-sg)

| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 80 | TCP | 0.0.0.0/0 | HTTP (Nginx) |
| 443 | TCP | 0.0.0.0/0 | HTTPS (Nginx) |
| 8000 | TCP | 0.0.0.0/0 | FastAPI (internal) |
| 22 | TCP | [Your IP] | SSH |

#### Database Security Group (patient-app-db-sg)

| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 3306 | TCP | patient-app-backend-sg | MySQL |
| 22 | TCP | [Your IP] | SSH |

### 7. VPC and Networking (Optional)

**Recommended Setup**:
- **VPC**: Single VPC with multiple subnets
- **Frontend**: Public subnet (has internet gateway)
- **Backend**: Private subnet with NAT gateway
- **Database**: Private subnet (no direct internet access)
- **Route Tables**: Separate for public/private subnets

### 8. CloudWatch Monitoring (Optional)

**Recommended Metrics**:
- EC2 CPU Utilization
- EC2 Memory Usage (CloudWatch Agent required)
- Network In/Out
- EBS Volume Read/Write
- MySQL Connection Count
- S3 Upload Frequency

**Alarms**:
- High CPU (>80%)
- High Memory (>80%)
- MySQL Connection Errors
- S3 Upload Failures

---

## Data Flow Diagrams

### 1. User Registration Flow

```
┌─────────┐
│ Browser │
└────┬────┘
     │ POST /api/auth/register
     ▼
┌──────────────────┐
│ Frontend React   │
└────┬─────────────┘
     │ Axios HTTP
     ▼
┌──────────────────┐
│ Nginx (Backend)  │
└────┬─────────────┘
     │ Proxy Pass
     ▼
┌──────────────────┐
│ FastAPI          │
│ - Hash Password  │
│ - Save User      │
└────┬─────────────┘
     │ SQLAlchemy ORM
     ▼
┌──────────────────┐
│ MySQL Database   │
└──────────────────┘
```

### 2. Patient Image Upload Flow

```
┌─────────┐
│ Browser │
└────┬────┘
     │ POST /api/patients/{id}/upload-image
     ▼
┌──────────────────┐
│ Frontend React   │
└────┬─────────────┘
     │ FormData with File
     ▼
┌──────────────────┐
│ Nginx (Backend)  │
└────┬─────────────┘
     │ Proxy Pass
     ▼
┌──────────────────┐
│ FastAPI          │
│ - Validate File  │
│ - Generate Name  │
└────┬─────────────┘
     │ boto3.upload_fileobj
     ▼
┌──────────────────┐
│ S3 Bucket        │
│ (Auto-encrypted  │
│  with KMS)       │
└──────────────────┘
     │
     ▼
┌──────────────────┐
│ AWS KMS          │
│ (Encrypt object) │
└──────────────────┘
```

### 3. Secrets Retrieval Flow

```
┌──────────────────┐
│ Backend EC2      │
│ Startup          │
└────┬─────────────┘
     │ boto3.client('secretsmanager')
     ▼
┌──────────────────┐
│ AWS Secrets Mgr  │
│ (Validate Role)  │
└────┬─────────────┘
     │ Check IAM Role Permissions
     ▼
┌──────────────────┐
│ IAM Service      │
└────┬─────────────┘
     │ Return Secret
     ▼
┌──────────────────┐
│ Backend EC2      │
│ (Load into       │
│  settings)       │
└──────────────────┘
```

---

## Cost Analysis

### Monthly Cost Breakdown (Approximate)

| Service | Details | Cost |
|---------|---------|------|
| EC2 | 3x t3.small/medium | $25 |
| EBS Storage | 70 GB | $5 |
| Secrets Manager | 1 secret | $0.40 |
| S3 Storage | 10 GB @ $0.023/GB | $0.23 |
| S3 Requests | 1000 uploads/month | $0.05 |
| KMS | 1 key + requests | $1.50 |
| Data Transfer | 1 GB @ $0.09/GB | $0.09 |
| **Total** | | **~$32/month** |

**Cost Optimization**:
- Use Reserved Instances for 30-40% savings
- Use S3 Intelligent-Tiering for archival
- Enable S3 Lifecycle policies
- Use CloudFront for static assets CDN

---

## Security Best Practices

### Implemented
✓ No hardcoded credentials (Secrets Manager)
✓ IAM roles instead of access keys
✓ Security groups restrict traffic
✓ Passwords hashed with bcrypt
✓ JWT for authentication
✓ S3 encryption with KMS
✓ HTTPS recommended (Certbot)

### Recommended
- [ ] Enable VPC Flow Logs
- [ ] Enable CloudTrail
- [ ] Enable Config Rules
- [ ] Use WAF (Web Application Firewall)
- [ ] Enable GuardDuty
- [ ] Enable Macie for S3 scanning
- [ ] Encrypt EBS volumes
- [ ] Regular security audits

---

## Scaling Considerations

### Horizontal Scaling (Add More Instances)
- Add more backend instances behind ALB
- Use RDS for managed MySQL
- Add CloudFront for frontend caching

### Vertical Scaling (Bigger Instances)
- Upgrade to t3.large for backend
- Upgrade to t3.medium for database
- Increase EBS volume size

### Auto-Scaling (Optional)
- Use AWS Auto Scaling Groups
- Scale based on CPU/Memory
- Requires load balancer (ALB/NLB)

### Database Scaling
- Switch to RDS with Multi-AZ
- Enable Read Replicas
- Use Aurora for better performance

---

## Disaster Recovery

### Backup Strategy
```bash
# Daily MySQL backups
* 2 * * * * mysqldump -h [host] -u [user] -p[pass] [db] > /backup/$(date +\%Y\%m\%d).sql

# S3 versioning enabled for image recovery
# Secrets Manager has automatic audit trail
```

### Recovery Time Objectives (RTO)
- **Frontend**: 5 minutes (redeploy)
- **Backend**: 15 minutes (restore from backup)
- **Database**: 30 minutes (restore from backup)

### Backup Locations
- Database backups: S3 or external storage
- Configuration: AWS Secrets Manager
- Code: Git repository

---

## Monitoring and Alerting

### Key Metrics
1. **Application**: Request latency, error rate, throughput
2. **Infrastructure**: CPU, memory, disk usage, network
3. **Database**: Connections, queries/sec, replication lag
4. **Storage**: S3 requests, bucket size

### Alerting Rules
- Backend down → PagerDuty
- High error rate (>5%) → Slack
- Database connection pool full → SMS
- S3 upload failures → Email

### Logging
- Application logs: CloudWatch
- Access logs: Nginx access.log
- Error logs: Nginx error.log
- Database logs: MySQL error.log

---

## Compliance Considerations

### HIPAA (Healthcare)
- Encryption at rest (KMS) ✓
- Encryption in transit (HTTPS)
- Access logging (CloudTrail)
- Data residency (region-specific)

### GDPR (EU Data Protection)
- Data deletion on request
- Data portability
- Consent management
- Privacy policy

### CCPA (California Privacy)
- Similar to GDPR
- Additional requirements for California residents

---

## Next Steps

1. Review this architecture with your team
2. Adjust instance types based on expected load
3. Implement monitoring and alerting
4. Set up automated backups
5. Plan for disaster recovery
6. Configure HTTPS/SSL certificates
7. Document runbooks for operations
8. Schedule regular security audits

---

**Document Version**: 1.0
**Last Updated**: January 2024
**Author**: DevOps Team

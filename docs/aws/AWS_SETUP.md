# AWS Infrastructure Setup Guide

Complete guide to create every AWS resource this application needs.

**Time required**: ~30–45 minutes  
**Prerequisites**: AWS account with admin access, AWS CLI installed and configured

---

## Overview

You need to create these resources in order:

1. **KMS key** — for S3 encryption
2. **S3 bucket** — for document storage
3. **IAM role** — for backend EC2 permissions
4. **Secrets Manager secret** — for app credentials
5. **Security groups** — for network access control

---

## Step 1: Create KMS Key (Customer-Managed)

### Via AWS Console

1. Go to **AWS KMS** → **Customer managed keys** → **Create key**
2. Key type: **Symmetric**
3. Key usage: **Encrypt and decrypt**
4. Click **Next**
5. Add alias: `patient-app-s3-key`
6. Add tag: `Project` = `patient-management`
7. Click **Next**
8. Key administrators: select your IAM user/admin role
9. Key usage permissions: **leave empty for now** (we'll add the EC2 role later)
10. Click **Finish**

**Copy the Key ARN** — you'll need it for the IAM policy and S3 bucket.

### Via AWS CLI

```bash
aws kms create-key \
  --description "S3 encryption key for Patient Management App" \
  --tags TagKey=Project,TagValue=patient-management

# Note the KeyId from the output, then create an alias:
aws kms create-alias \
  --alias-name alias/patient-app-s3-key \
  --target-key-id YOUR-KEY-ID
```

---

## Step 2: Create S3 Bucket

### Via AWS Console

1. Go to **S3** → **Create bucket**
2. Bucket name: `patient-docs-YOUR-ACCOUNT-ID` *(must be globally unique)*
3. Region: `us-east-1` *(or your preferred region)*
4. **Block all public access**: ✅ Enable all four options
5. **Versioning**: Enable
6. **Default encryption**:
   - Encryption type: **SSE-KMS**
   - KMS key: select the key you just created (`patient-app-s3-key`)
   - ✅ **Bucket Key**: Enable *(reduces KMS API call costs)*
7. Click **Create bucket**

### Via AWS CLI

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET_NAME="patient-docs-${ACCOUNT_ID}"
REGION="us-east-1"
KMS_KEY_ARN="arn:aws:kms:us-east-1:${ACCOUNT_ID}:key/YOUR-KEY-ID"

# Create bucket
aws s3api create-bucket \
  --bucket ${BUCKET_NAME} \
  --region ${REGION} \
  --create-bucket-configuration LocationConstraint=${REGION}

# Block all public access
aws s3api put-public-access-block \
  --bucket ${BUCKET_NAME} \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket ${BUCKET_NAME} \
  --versioning-configuration Status=Enabled

# Set default encryption (SSE-KMS)
aws s3api put-bucket-encryption \
  --bucket ${BUCKET_NAME} \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "aws:kms",
        "KMSMasterKeyID": "'${KMS_KEY_ARN}'"
      },
      "BucketKeyEnabled": true
    }]
  }'

echo "Bucket created: ${BUCKET_NAME}"
```

---

## Step 3: Create IAM Role for Backend EC2

### 3a. Create the IAM role

```bash
# Create role with EC2 trust policy
aws iam create-role \
  --role-name PatientManagementAppRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ec2.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'
```

### 3b. Create and attach Policy 1 — Secrets Manager

```bash
aws iam create-policy \
  --policy-name PatientAppSecretsManagerPolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["secretsmanager:GetSecretValue"],
      "Resource": "arn:aws:secretsmanager:us-east-1:ACCOUNT-ID:secret:patient-management-secrets*"
    }]
  }'

aws iam attach-role-policy \
  --role-name PatientManagementAppRole \
  --policy-arn arn:aws:iam::ACCOUNT-ID:policy/PatientAppSecretsManagerPolicy
```

### 3c. Create and attach Policy 2 — S3

```bash
aws iam create-policy \
  --policy-name PatientAppS3Policy \
  --policy-document '{
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
  }'

aws iam attach-role-policy \
  --role-name PatientManagementAppRole \
  --policy-arn arn:aws:iam::ACCOUNT-ID:policy/PatientAppS3Policy
```

> **Note**: `s3:GetObject` is required for pre-signed URL generation (even on private buckets). `s3:DeleteObject` is required for document deletion.

### 3d. Create and attach Policy 3 — KMS

```bash
aws iam create-policy \
  --policy-name PatientAppKMSPolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["kms:Decrypt", "kms:GenerateDataKey", "kms:DescribeKey"],
      "Resource": "arn:aws:kms:us-east-1:ACCOUNT-ID:key/YOUR-KEY-ID"
    }]
  }'

aws iam attach-role-policy \
  --role-name PatientManagementAppRole \
  --policy-arn arn:aws:iam::ACCOUNT-ID:policy/PatientAppKMSPolicy
```

### 3e. Create instance profile (required for EC2)

```bash
aws iam create-instance-profile \
  --instance-profile-name PatientManagementAppRole

aws iam add-role-to-instance-profile \
  --instance-profile-name PatientManagementAppRole \
  --role-name PatientManagementAppRole
```

### 3f. Grant KMS role access to the key

Go back to **KMS** → select your key → **Key policy** → Edit.

Under `"Statement"`, add this block:

```json
{
  "Sid": "AllowEC2RoleToUseKey",
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:iam::ACCOUNT-ID:role/PatientManagementAppRole"
  },
  "Action": ["kms:Decrypt", "kms:GenerateDataKey", "kms:DescribeKey"],
  "Resource": "*"
}
```

---

## Step 4: Create Secrets Manager Secret

**Important**: Create this secret after you know the database private IP (from Part 1 of the deployment guide).

### Via Console

1. Go to **Secrets Manager** → **Store a new secret**
2. Secret type: **Other type of secret**
3. Key/value pairs — enter these:

| Key | Value |
|---|---|
| `db_host` | Private IP of your database EC2 |
| `db_name` | `patient_db` |
| `db_user` | `patient_app` |
| `db_password` | The password you set when creating MySQL user |
| `jwt_secret` | A random 64-character string (see command below) |
| `s3_bucket_name` | `patient-docs-YOUR-ACCOUNT-ID` |
| `aws_region` | `us-east-1` |

4. Secret name: `patient-management-secrets`
5. Description: `Credentials for Patient Management Application`
6. Rotation: **Disable** (for now)
7. Click **Store**

### Generate a strong JWT secret

```bash
# Generate a random 64-character JWT secret
python3 -c "import secrets; print(secrets.token_hex(32))"
# or
openssl rand -hex 32
```

### Via AWS CLI

```bash
aws secretsmanager create-secret \
  --name patient-management-secrets \
  --description "Credentials for Patient Management Application" \
  --secret-string '{
    "db_host": "DB-PRIVATE-IP",
    "db_name": "patient_db",
    "db_user": "patient_app",
    "db_password": "YOUR-DB-PASSWORD",
    "jwt_secret": "YOUR-64-CHAR-RANDOM-STRING",
    "s3_bucket_name": "patient-docs-YOUR-ACCOUNT-ID",
    "aws_region": "us-east-1"
  }'
```

### Verify the secret

```bash
aws secretsmanager get-secret-value \
  --secret-id patient-management-secrets \
  --query SecretString \
  --output text
```

---

## Step 5: Create Security Groups

Run these from AWS CLI (replace `VPC-ID` with your VPC ID):

```bash
VPC_ID="vpc-xxxxxxxxx"   # your default or custom VPC

# ── Backend security group ──────────────────────────────
aws ec2 create-security-group \
  --group-name patient-app-backend-sg \
  --description "Backend EC2 for Patient Management App" \
  --vpc-id ${VPC_ID}

BACKEND_SG_ID=$(aws ec2 describe-security-groups \
  --filters Name=group-name,Values=patient-app-backend-sg \
  --query 'SecurityGroups[0].GroupId' --output text)

# Allow SSH from your IP
aws ec2 authorize-security-group-ingress \
  --group-id ${BACKEND_SG_ID} \
  --protocol tcp --port 22 --cidr YOUR.IP.ADDRESS/32

# Allow HTTP from anywhere
aws ec2 authorize-security-group-ingress \
  --group-id ${BACKEND_SG_ID} \
  --protocol tcp --port 80 --cidr 0.0.0.0/0

# ── Database security group ──────────────────────────────
aws ec2 create-security-group \
  --group-name patient-app-db-sg \
  --description "Database EC2 for Patient Management App" \
  --vpc-id ${VPC_ID}

DB_SG_ID=$(aws ec2 describe-security-groups \
  --filters Name=group-name,Values=patient-app-db-sg \
  --query 'SecurityGroups[0].GroupId' --output text)

# Allow SSH from your IP
aws ec2 authorize-security-group-ingress \
  --group-id ${DB_SG_ID} \
  --protocol tcp --port 22 --cidr YOUR.IP.ADDRESS/32

# Allow MySQL from backend security group only
aws ec2 authorize-security-group-ingress \
  --group-id ${DB_SG_ID} \
  --protocol tcp --port 3306 \
  --source-group ${BACKEND_SG_ID}

# ── Frontend security group ──────────────────────────────
aws ec2 create-security-group \
  --group-name patient-app-frontend-sg \
  --description "Frontend EC2 for Patient Management App" \
  --vpc-id ${VPC_ID}

FRONTEND_SG_ID=$(aws ec2 describe-security-groups \
  --filters Name=group-name,Values=patient-app-frontend-sg \
  --query 'SecurityGroups[0].GroupId' --output text)

aws ec2 authorize-security-group-ingress \
  --group-id ${FRONTEND_SG_ID} \
  --protocol tcp --port 22 --cidr YOUR.IP.ADDRESS/32

aws ec2 authorize-security-group-ingress \
  --group-id ${FRONTEND_SG_ID} \
  --protocol tcp --port 80 --cidr 0.0.0.0/0
```

---

## Verify Everything

```bash
# Check secret exists and is readable
aws secretsmanager get-secret-value \
  --secret-id patient-management-secrets \
  --query SecretString --output text

# Check bucket exists and is private
aws s3api get-public-access-block --bucket patient-docs-ACCOUNT-ID

# Check bucket encryption
aws s3api get-bucket-encryption --bucket patient-docs-ACCOUNT-ID

# Check IAM role exists with policies
aws iam list-attached-role-policies --role-name PatientManagementAppRole

# List KMS keys
aws kms list-aliases | grep patient
```

---

## Summary of Resources Created

| Resource | Name / ID |
|---|---|
| KMS key | `alias/patient-app-s3-key` |
| S3 bucket | `patient-docs-<account-id>` |
| IAM role | `PatientManagementAppRole` |
| IAM instance profile | `PatientManagementAppRole` |
| IAM policies | `PatientAppSecretsManagerPolicy`, `PatientAppS3Policy`, `PatientAppKMSPolicy` |
| Secret | `patient-management-secrets` |
| Security groups | `patient-app-backend-sg`, `patient-app-db-sg`, `patient-app-frontend-sg` |

All of the above are ready to be referenced in the deployment guide and later in Terraform.

---

**Next step**: See `docs/deployment/DEPLOYMENT.md` to launch EC2 instances and deploy the application.

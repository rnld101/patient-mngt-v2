# AWS Infrastructure Setup Guide

## Prerequisites
- AWS Account with appropriate permissions
- AWS CLI installed and configured
- Three EC2 instances ready (or will be created)

---

## 1. AWS Secrets Manager Setup

### Step 1: Create Secret in AWS Secrets Manager

1. **Login to AWS Console**
   - Navigate to: https://console.aws.amazon.com

2. **Open AWS Secrets Manager**
   - Search for "Secrets Manager" in the service search
   - Click "Secrets Manager"

3. **Create New Secret**
   - Click "Store a new secret"
   - Choose "Other type of secret"
   - Under "Key/value pairs", enter the following:

```json
{
  "db_host": "your-database-private-ip",
  "db_name": "patient_db",
  "db_user": "patient_app",
  "db_password": "your-secure-password",
  "jwt_secret": "your-jwt-secret-key-change-this",
  "s3_bucket_name": "patient-images-bucket-your-account-id",
  "aws_region": "us-east-1"
}
```

4. **Configure Secret**
   - Secret name: `patient-management-secrets`
   - Description: "Secrets for Patient Management Application"
   - Click "Next"

5. **Configure rotation**
   - Choose "Disable automatic rotation"
   - Click "Next"

6. **Review and Create**
   - Click "Store secret"

**Note the Secret ARN** - You'll need this later.

---

## 2. S3 Bucket Setup

### Step 1: Create S3 Bucket

1. **Open S3 Console**
   - Navigate to S3 service
   - Click "Create bucket"

2. **Configure Bucket**
   - Bucket name: `patient-images-bucket-your-account-id`
   - Region: Select your region (e.g., us-east-1)
   - Leave ACL settings as default
   - Click "Create bucket"

### Step 2: Block Public Access

1. **Select your bucket**
2. **Go to "Permissions" tab**
3. **Click "Edit" under "Block public access"**
4. **Enable all four options:**
   - Block all public access
   - Click "Save changes"

### Step 3: Enable Versioning

1. **Go to "Properties" tab**
2. **Click "Edit" under "Versioning"**
3. **Select "Enable"**
4. **Click "Save changes"**

### Step 4: Enable Default Encryption (SSE-KMS)

1. **Go to "Properties" tab**
2. **Scroll to "Default encryption"**
3. **Click "Edit"**

4. **Configure Encryption:**
   - Choose "Server-side encryption with AWS KMS"
   - If you don't have a customer-managed key, create one first (see step below)
   - Select your KMS key
   - Click "Save changes"

### Create Customer-Managed KMS Key (Optional but Recommended)

1. **Go to AWS KMS Console**
2. **Click "Create key"**
3. **Configure Key:**
   - Key type: "Symmetric"
   - Key usage: "Encrypt and decrypt"
   - Click "Next"

4. **Add Tags:**
   - Key: `Environment`, Value: `Production`
   - Click "Next"

5. **Define Key Administrative Permissions:**
   - Select your AWS account or specific admin users
   - Click "Next"

6. **Define Key Usage Permissions:**
   - Select the IAM role created in step 3 (see below)
   - This allows EC2 instances to use the key
   - Click "Next"

7. **Review and Create:**
   - Click "Finish"
   - **Note the Key ID** - You'll need this for IAM policy

---

## 3. IAM Role Setup

### Step 1: Create IAM Role for EC2

1. **Go to IAM Console**
2. **Click "Roles"**
3. **Click "Create role"**

4. **Select Entity Type:**
   - Choose "EC2"
   - Click "Next"

### Step 2: Add Permissions

1. **Create Custom Policy for Secrets Manager:**
   - Click "Create policy"
   - Choose "JSON" tab
   - Paste this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:YOUR-ACCOUNT-ID:secret:patient-management-secrets*"
    }
  ]
}
```

   - Click "Next"
   - Name: `PatientAppSecretsManagerPolicy`
   - Click "Create policy"

2. **Create Custom Policy for S3:**
   - Click "Create policy"
   - Choose "JSON" tab
   - Paste this policy:

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
      "Resource": "arn:aws:s3:::patient-images-bucket-your-account-id/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::patient-images-bucket-your-account-id"
    }
  ]
}
```

   - Click "Next"
   - Name: `PatientAppS3Policy`
   - Click "Create policy"

3. **Create Custom Policy for KMS (If using customer-managed key):**
   - Click "Create policy"
   - Choose "JSON" tab
   - Paste this policy:

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
      "Resource": "arn:aws:kms:us-east-1:YOUR-ACCOUNT-ID:key/YOUR-KEY-ID"
    }
  ]
}
```

   - Replace `YOUR-KEY-ID` with your KMS key ID
   - Click "Next"
   - Name: `PatientAppKMSPolicy`
   - Click "Create policy"

### Step 3: Attach Policies to Role

1. **Go back to "Create role" page**
2. **Refresh and filter for the policies you created:**
   - `PatientAppSecretsManagerPolicy`
   - `PatientAppS3Policy`
   - `PatientAppKMSPolicy` (if created)
3. **Check all three policies**
4. **Click "Next"**
5. **Name the role:** `PatientManagementAppRole`
6. **Click "Create role"**

### Step 4: Attach Role to EC2 Instance

This will be done during EC2 setup (see deployment guide).

---

## 4. Additional AWS Configurations

### Create EC2 Security Groups

#### Backend Security Group

```
Name: patient-app-backend-sg
Inbound Rules:
  - Port 22 (SSH) - From: Your IP
  - Port 8000 (FastAPI) - From: Frontend SG or 0.0.0.0/0
  - Port 80 (HTTP) - From: 0.0.0.0/0
  - Port 443 (HTTPS) - From: 0.0.0.0/0
Outbound Rules:
  - All traffic
```

#### Database Security Group

```
Name: patient-app-db-sg
Inbound Rules:
  - Port 22 (SSH) - From: Your IP
  - Port 3306 (MySQL) - From: Backend SG
Outbound Rules:
  - All traffic
```

#### Frontend Security Group

```
Name: patient-app-frontend-sg
Inbound Rules:
  - Port 22 (SSH) - From: Your IP
  - Port 80 (HTTP) - From: 0.0.0.0/0
  - Port 443 (HTTPS) - From: 0.0.0.0/0
Outbound Rules:
  - All traffic
```

---

## 5. Important Notes

### Environment Variables
- The application loads secrets from AWS Secrets Manager at startup
- The Backend container/instance must have the IAM role attached
- No hardcoded credentials should be in code

### S3 Encryption
- The bucket has default encryption enabled (SSE-KMS)
- The application does NOT specify KMS key IDs in code
- S3 automatically handles encryption when files are uploaded
- The backend only needs s3:PutObject permission

### Database
- Database must be accessible from backend instance
- Use security groups to restrict MySQL traffic to only backend instances

---

## AWS CLI Commands (Optional)

### Create Secrets Manager Secret
```bash
aws secretsmanager create-secret \
  --name patient-management-secrets \
  --secret-string '{"db_host":"your-ip","db_name":"patient_db","db_user":"patient_app","db_password":"password","jwt_secret":"secret","s3_bucket_name":"bucket-name","aws_region":"us-east-1"}'
```

### Get Secret Value
```bash
aws secretsmanager get-secret-value \
  --secret-id patient-management-secrets \
  --query SecretString \
  --output text
```

### Create S3 Bucket
```bash
aws s3 mb s3://patient-images-bucket-your-account-id --region us-east-1
```

### Block Public Access
```bash
aws s3api put-public-access-block \
  --bucket patient-images-bucket-your-account-id \
  --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

---

## Next Steps

1. Create the EC2 instances
2. Configure security groups
3. Install and configure MySQL on database instance
4. Install Python 3.13 and dependencies on backend instance
5. Install Node.js and build frontend on frontend instance
6. See [Deployment Guide](./DEPLOYMENT.md) for complete steps

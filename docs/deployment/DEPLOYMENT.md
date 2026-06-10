# Deployment Guide — Automated Terraform & S3 Deployment

This guide outlines the steps to deploy the Patient Management System. Provisioning is automated using Terraform, and the frontend assets are deployed serverlessly to AWS S3 and distributed via CloudFront.

---

## Deployment Process Overview

```text
Step 1: Prep DNS & SSL Certs (ACM)
  → Step 2: Configure terraform.tfvars
  → Step 3: Run 'terraform apply' to provision AWS resources
  → Step 4: Compile React frontend locally
  → Step 5: Sync static build to Frontend S3 Bucket
  → Step 6: Invalidate CloudFront CDN Cache
  → Step 7: Verify backend & database endpoints
```

---

## Part 1 — Provisioning Infrastructure

Perform all setup steps described in [AWS_SETUP.md](file:///c:/Users/RAPHEL%20M%20L/Desktop/patient-mngt-v2/docs/aws/AWS_SETUP.md):
1. Ensure your Route53 hosted zone and ACM certificate are ready.
2. Initialize and run Terraform:
   ```bash
   cd terraform
   terraform init
   terraform apply
   ```
3. Note down the outputs, specifically:
   * `frontend_bucket_name`
   * `cloudfront_domain_name` (or your custom `domain_name`)
   * `api_endpoint` (your API URL)

---

## Part 2 — Deploying the Frontend (React SPA)

Terraform provisions the Frontend S3 bucket and CloudFront distribution, but leaves the bucket empty. You must build the React application locally and upload the compiled assets.

### 2.1 Set up Environment Variables
Navigate to the `frontend/` directory and configure the environment variables to point to your new Route53 API endpoint.

```bash
cd frontend
cat > .env << EOF
VITE_API_URL=https://api.yourdomain.com/api
EOF
```
*(Replace `api.yourdomain.com` with the actual value of the `api_endpoint` output).*

### 2.2 Compile the React Build
Install node dependencies and compile the production build:

```bash
npm install
npm run build
```
This generates a `dist/` directory containing `index.html` and optimized static assets under `assets/`.

### 2.3 Upload Build to S3 Frontend Bucket
Sync the `dist/` folder to your private S3 frontend bucket. Terraform blocks public access, but CloudFront is authorized via Origin Access Control (OAC).

```bash
# Sync files to S3 bucket
aws s3 sync dist/ s3://YOUR-FRONTEND-BUCKET-NAME/ --region us-east-1 --delete
```
*(Replace `YOUR-FRONTEND-BUCKET-NAME` with the `frontend_bucket_name` output).*

### 2.4 Invalidate CloudFront Cache
To ensure CloudFront serves the new files immediately and doesn't return cached 403/404 errors, create a cache invalidation:

```bash
# Get your distribution ID from AWS Console or CLI:
DIST_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Aliases.Items[0]=='yourdomain.com'].Id" --output text)

# Run invalidation
aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*"
```
Once the invalidation completes, open `https://yourdomain.com` in your browser. The login screen should load successfully.

---

## Part 3 — Verifying the Private Backend Compute Tier

The backend instances launch inside private subnets and are not assigned public IP addresses. This prevents direct SSH access from the internet.

### 3.1 Session Manager Connection (SSM)
To connect securely to a backend EC2 instance for debugging, use AWS Systems Manager (SSM) Session Manager. There is no need for a bastion host or open inbound SSH ports.

1. Ensure the AWS CLI and Session Manager plugin are installed locally.
2. Query the instance ID:
   ```bash
   aws ec2 describe-instances \
     --filters "Name=tag:Name,Values=patient-mngt-backend-asg-node" "Name=instance-state-name,Values=running" \
     --query "Reservations[*].Instances[*].InstanceId" --output text
   ```
3. Start the terminal session:
   ```bash
   aws ssm start-session --target i-xxxxxxxxxxxxxxxxx
   ```

### 3.2 Troubleshooting Node Bootstrap
The Launch Template automatically boots the node, clones the repository, sets up virtualenv, fetches secrets, and starts systemd.
To audit this boot process, connect via SSM and inspect the logs:

```bash
# 1. View the user-data execution log
cat /var/log/user-data.log

# 2. Check the status of the FastAPI backend service
sudo systemctl status patient-app

# 3. View live application logs
sudo journalctl -u patient-app -f --no-pager
```

---

## Part 4 — Verification Checklist

### 4.1 Browser Smoke Test
Open your domain `https://yourdomain.com` in your browser and verify:

| Action | Expected Result |
|---|---|
| Page loads | Login screen displays without JS console errors |
| Register User | Redirected to empty dashboard; user record saved in RDS |
| Add Patient | Form submits, redirects to list, patient appears in grid |
| Upload Document | Select PDF/image and upload; S3 object created, DB index logged |
| View Document | Click "View"; pre-signed S3 URL opens in new tab with 1-hr expiry |
| Delete Document | Click "Delete"; file removed from S3, index row deleted in RDS |
| Logout | Session cleared; redirected back to login page |

### 4.2 API Testing via curl
Verify your API routes directly from the command line:

```bash
BASE="https://api.yourdomain.com"

# 1. Health check
curl -s $BASE/health | grep -o "ok"
# Expected output: ok

# 2. Register account
curl -s -X POST $BASE/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"prodtest","email":"prod@test.com","password":"ProdPassword123!"}'

# 3. Login and capture JWT
TOKEN=$(curl -s -X POST $BASE/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"prod@test.com","password":"ProdPassword123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 4. List patients (authenticated)
curl -s $BASE/api/patients -H "Authorization: Bearer $TOKEN"
# Expected output: {"total":0,"patients":[]}
```

### 4.3 Database Validation
To verify data structures are populated in RDS MySQL:
1. Log in to your database via a database client from a machine inside the VPC or via an SSM session on the backend.
2. Query the RDS database endpoint:
   ```sql
   mysql -h YOUR-RDS-ENDPOINT -u patient_app -p patient_db;
   ```
3. Run schema audits:
   ```sql
   SHOW TABLES;
   -- Expected tables: users, patients, patient_documents
   ```

### 4.4 S3 Document Storage Validation
Confirm files uploaded are encrypted at rest using your KMS Customer Managed Key:
```bash
# List files in the document bucket
aws s3 ls s3://YOUR-DOCUMENT-BUCKET-NAME/patient_documents/

# Check object encryption configuration
aws s3api get-object-acl --bucket YOUR-DOCUMENT-BUCKET-NAME --key patient_documents/sample-uuid.pdf
```

# Deployment Guide — Step-by-Step EC2 Deployment

Complete guide to deploy the Patient Management System to AWS EC2.

**Estimated time**: 60–90 minutes  
**Prerequisites**: AWS setup from `docs/aws/AWS_SETUP.md` must be complete.

---

## What You Will Deploy

| Component | Instance | Service |
|---|---|---|
| MySQL 8 database | Database EC2 | `mysql` (systemd) |
| FastAPI backend | Backend EC2 | `patient-app` (systemd) + Nginx |
| React frontend | Frontend EC2 | Nginx (serves static files) |

---

## Part 1 — Database EC2

### 1.1 Launch the Instance

In **EC2 → Launch instance**:
- Name: `patient-db`
- AMI: **Ubuntu Server 22.04 LTS**
- Instance type: `t3.small`
- Storage: 20 GB GP3
- Security group: `patient-app-db-sg`
- IAM role: *(none needed)*
- Key pair: select or create one

**Note the private IP address** of this instance after it launches — you will need it for Secrets Manager.

---

### 1.2 Connect via SSH

```bash
ssh -i your-key.pem ubuntu@DB-PUBLIC-IP
```

---

### 1.3 Update System

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget vim
```

---

### 1.4 Install MySQL 8

```bash
sudo apt install -y mysql-server mysql-client

# Verify
mysql --version
# Expected: mysql  Ver 8.x.x ...

# Start and enable
sudo systemctl start mysql
sudo systemctl enable mysql
sudo systemctl status mysql
# Expected: Active: active (running)
```

---

### 1.5 Secure MySQL

```bash
sudo mysql_secure_installation
```

When prompted:
- VALIDATE PASSWORD component → **Y**
- Password strength level → **2** (Strong)
- New password → *(set a strong password, save it!)*
- Remove anonymous users → **Y**
- Disallow root login remotely → **Y**
- Remove test database → **Y**
- Reload privilege tables → **Y**

---

### 1.6 Allow Remote Connections

```bash
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
```

Find this line:
```
bind-address = 127.0.0.1
```

Change it to:
```
bind-address = 0.0.0.0
```

Save (Ctrl+X → Y → Enter), then restart:

```bash
sudo systemctl restart mysql
```

---

### 1.7 Create Application Database and User

```bash
sudo mysql -u root -p
# Enter the root password you just set
```

Inside MySQL:
```sql
CREATE DATABASE patient_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER 'patient_app'@'%' IDENTIFIED BY 'YOUR-STRONG-DB-PASSWORD';

GRANT ALL PRIVILEGES ON patient_db.* TO 'patient_app'@'%';

FLUSH PRIVILEGES;

-- Verify
SHOW DATABASES;
SELECT User, Host FROM mysql.user;

EXIT;
```

**Save these values** — you will put them in Secrets Manager:
- `db_host`: private IP of this EC2 instance
- `db_name`: `patient_db`
- `db_user`: `patient_app`
- `db_password`: the password you set above

---

### ✅ Database Verification Checkpoint

```bash
# Confirm MySQL is running and listening
sudo systemctl status mysql
sudo ss -tlnp | grep mysql
# Expected: 0.0.0.0:3306 LISTEN

# Test local login with app credentials
mysql -u patient_app -p patient_db -e "SELECT 'DB OK' AS status;"
# Expected: DB OK
```

---

## Part 2 — Backend EC2

### 2.1 Create Secrets Manager Secret

Before deploying the backend, go to AWS Secrets Manager and create the secret now that you have the database IP.

```bash
aws secretsmanager create-secret \
  --name patient-management-secrets \
  --description "Patient Management App credentials" \
  --secret-string '{
    "db_host":       "DB-PRIVATE-IP",
    "db_name":       "patient_db",
    "db_user":       "patient_app",
    "db_password":   "YOUR-DB-PASSWORD",
    "jwt_secret":    "GENERATE-WITH: python3 -c \"import secrets; print(secrets.token_hex(32))\"",
    "s3_bucket_name": "patient-docs-YOUR-ACCOUNT-ID",
    "aws_region":    "us-east-1"
  }'
```

---

### 2.2 Launch the Instance

In **EC2 → Launch instance**:
- Name: `patient-backend`
- AMI: **Ubuntu Server 22.04 LTS**
- Instance type: `t3.medium`
- Storage: 30 GB GP3
- Security group: `patient-app-backend-sg`
- **IAM instance profile: `PatientManagementAppRole`** ← critical
- Key pair: same as database

---

### 2.3 Connect via SSH

```bash
ssh -i your-key.pem ubuntu@BACKEND-PUBLIC-IP
```

---

### 2.4 Update System and Install Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget vim git build-essential \
  libssl-dev libffi-dev python3-dev pkg-config \
  default-libmysqlclient-dev
```

---

### 2.5 Install Python 3.11+

Ubuntu 22.04 ships with Python 3.10. Install a newer version:

```bash
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Verify
python3.11 --version
```

---

### 2.6 Deploy Application Code

**Option A — via Git** (recommended):
```bash
sudo mkdir -p /opt/patient-app
sudo chown ubuntu:ubuntu /opt/patient-app
cd /opt/patient-app

git clone https://YOUR-REPO-URL .
```

**Option B — via SCP from your local machine**:
```bash
# Run this from your local machine:
scp -i your-key.pem -r ./backend/* ubuntu@BACKEND-PUBLIC-IP:/opt/patient-app/
```

---

### 2.7 Set Up Python Virtual Environment

```bash
cd /opt/patient-app
python3.11 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# Verify key packages installed
pip show fastapi boto3 sqlalchemy pymysql
```

---

### 2.8 Create Environment File

```bash
cat > /opt/patient-app/.env << 'EOF'
# App settings
APP_NAME=Patient Management API
DEBUG=False
API_PREFIX=/api

# JWT settings (algorithm only — secret comes from Secrets Manager)
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# AWS region (bucket name + secrets also come from Secrets Manager)
AWS_REGION=us-east-1
EOF
```

> The database URL, JWT secret, and S3 bucket name are loaded automatically from Secrets Manager at startup. Do not put them in `.env`.

---

### 2.9 Verify AWS Connectivity

```bash
# Still inside /opt/patient-app with venv active
# Test that the IAM role is attached and Secrets Manager is reachable
aws sts get-caller-identity
# Expected: shows Account, UserId, Arn for the role

aws secretsmanager get-secret-value \
  --secret-id patient-management-secrets \
  --region us-east-1 \
  --query SecretString --output text
# Expected: JSON with your db_host, db_name, etc.
```

If either command fails, check that the IAM role is attached to this EC2 instance.

---

### 2.10 Install Gunicorn

```bash
cd /opt/patient-app
source venv/bin/activate
pip install gunicorn
```

---

### 2.11 Test the Application Manually First

```bash
cd /opt/patient-app
source venv/bin/activate

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Watch the output. You should see:
```
✓ Secrets loaded from AWS Secrets Manager
✓ Database tables created (if not already exists)
✓ Database initialized
INFO:     Started server process
INFO:     Application startup complete.
```

If you see errors at this point, fix them before proceeding.

Press **Ctrl+C** to stop.

---

### 2.12 Test Database Connectivity from Backend

```bash
# From the backend instance, test MySQL connection
mysql -h DB-PRIVATE-IP -u patient_app -p patient_db -e "SHOW TABLES;"
# After tables are created by the app:
# Expected: users, patients, patient_documents
```

---

### 2.13 Create Systemd Service

```bash
sudo nano /etc/systemd/system/patient-app.service
```

Paste:

```ini
[Unit]
Description=Patient Management API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/patient-app
Environment="PATH=/opt/patient-app/venv/bin"
ExecStart=/opt/patient-app/venv/bin/gunicorn \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
    app.main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl start patient-app
sudo systemctl enable patient-app

# Check status
sudo systemctl status patient-app
# Expected: Active: active (running)
```

---

### 2.14 Install and Configure Nginx (Backend)

```bash
sudo apt install -y nginx

sudo nano /etc/nginx/sites-available/patient-app
```

Paste:

```nginx
upstream patient_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name _;

    # Allow large document uploads (10 MB)
    client_max_body_size 15M;

    access_log /var/log/nginx/patient_app_access.log;
    error_log  /var/log/nginx/patient_app_error.log;

    location / {
        proxy_pass         http://patient_backend;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_redirect     off;
        proxy_read_timeout 120s;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/patient-app /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

sudo nginx -t
# Expected: nginx: configuration file /etc/nginx/nginx.conf test is successful

sudo systemctl start nginx
sudo systemctl enable nginx
sudo systemctl reload nginx
```

---

### ✅ Backend Verification Checkpoint

Run all of these — each must pass before continuing:

```bash
# 1. Gunicorn process is running
sudo systemctl status patient-app
# Expected: Active: active (running)

# 2. App logs look clean
sudo journalctl -u patient-app -n 30 --no-pager
# Expected: no error lines, see "✓ Secrets loaded" and "Application startup complete"

# 3. Health endpoint responds locally
curl -s http://localhost:8000/health
# Expected: {"status":"ok"}

# 4. Nginx is proxying correctly
curl -s http://localhost/health
# Expected: {"status":"ok"}

# 5. API docs are reachable
curl -s http://localhost/docs | grep -o "<title>.*</title>"
# Expected: <title>FastAPI - Swagger UI</title>

# 6. Test register from the backend itself
curl -s -X POST http://localhost/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123"}' | python3 -m json.tool
# Expected: JSON with id, username, email, created_at

# 7. Test login and get token
TOKEN=$(curl -s -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "Token: ${TOKEN:0:30}..."

# 8. Test protected endpoint
curl -s http://localhost/api/patients \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# Expected: {"total":0,"patients":[]}

# 9. Test database tables were created
mysql -h DB-PRIVATE-IP -u patient_app -p patient_db -e "SHOW TABLES;"
# Expected: users, patients, patient_documents

# 10. Test S3 access
aws s3 ls s3://patient-docs-ACCOUNT-ID/ --region us-east-1
# Expected: (empty or existing files, no permission denied error)
```

---

## Part 3 — Frontend EC2

### 3.1 Launch the Instance

In **EC2 → Launch instance**:
- Name: `patient-frontend`
- AMI: **Ubuntu Server 22.04 LTS**
- Instance type: `t3.small`
- Storage: 20 GB GP3
- Security group: `patient-app-frontend-sg`
- IAM role: *(none needed)*
- Key pair: same as before

---

### 3.2 Connect via SSH

```bash
ssh -i your-key.pem ubuntu@FRONTEND-PUBLIC-IP
```

---

### 3.3 Update System and Install Node.js

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget vim git

# Install Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify
node --version   # Expected: v20.x.x
npm --version    # Expected: 10.x.x
```

---

### 3.4 Deploy Frontend Code

**Option A — via Git**:
```bash
sudo mkdir -p /opt/patient-frontend
sudo chown ubuntu:ubuntu /opt/patient-frontend
cd /opt/patient-frontend

git clone https://YOUR-REPO-URL repo
cp -r repo/frontend/* .
```

**Option B — via SCP from your local machine**:
```bash
# Run this from your local machine:
scp -i your-key.pem -r ./frontend/* ubuntu@FRONTEND-PUBLIC-IP:/opt/patient-frontend/
```

---

### 3.5 Build the React Application

```bash
cd /opt/patient-frontend

# Install dependencies
npm install

# Create the .env file pointing to backend
cat > .env << EOF
VITE_API_URL=http://BACKEND-PUBLIC-IP/api
EOF

# Build production bundle
npm run build

# Verify dist directory was created
ls -la dist/
# Expected: index.html, assets/ directory
```

---

### 3.6 Install and Configure Nginx (Frontend)

```bash
sudo apt install -y nginx

sudo nano /etc/nginx/sites-available/patient-frontend
```

Paste (replace `BACKEND-PUBLIC-IP`):

```nginx
server {
    listen 80;
    server_name _;

    access_log /var/log/nginx/patient_frontend_access.log;
    error_log  /var/log/nginx/patient_frontend_error.log;

    root  /opt/patient-frontend/dist;
    index index.html;

    # Static assets with long cache
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|webp|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # React Router — serve index.html for all unknown paths
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/patient-frontend /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

sudo nginx -t
# Expected: test is successful

sudo systemctl start nginx
sudo systemctl enable nginx
```

---

### 3.7 Fix File Permissions

```bash
sudo chown -R www-data:www-data /opt/patient-frontend/dist
sudo chmod -R 755 /opt/patient-frontend/dist
sudo systemctl reload nginx
```

---

### ✅ Frontend Verification Checkpoint

```bash
# 1. Nginx is running
sudo systemctl status nginx
# Expected: Active: active (running)

# 2. Static files are served
curl -s -o /dev/null -w "%{http_code}" http://localhost/
# Expected: 200

# 3. React app HTML is returned
curl -s http://localhost/ | grep -o "<title>.*</title>"
# Expected: <title>Vite App</title> or similar

# 4. React Router fallback works
curl -s -o /dev/null -w "%{http_code}" http://localhost/dashboard
# Expected: 200 (not 404)
```

Then open your browser:

```
http://FRONTEND-PUBLIC-IP
```

---

## Part 4 — End-to-End Application Testing

Test the full workflow from the browser and from the command line.

---

### 4.1 Browser Smoke Test

Open `http://FRONTEND-PUBLIC-IP` in your browser.

| Action | Expected Result |
|---|---|
| Page loads | Login page appears, no JS console errors |
| Click "Register" | Register page appears |
| Register a new account | Redirected to dashboard |
| Dashboard loads | Shows "Total Patients: 0" |
| Click "Add Patient" | Add patient form appears |
| Fill form and submit | Patient created, redirected to list |
| Patient list shows | New patient appears in table |
| Click "Documents" | Patient documents page loads |
| Upload a file | File appears in documents list |
| Click "View" | File opens in new browser tab |
| Click "Delete" on document | Document removed from list |
| Click "Edit" on patient | Edit form pre-filled |
| Update and save | Redirected to list, changes saved |
| Click "Delete" on patient | Confirmation dialog, patient removed |
| Click "Logout" | Redirected to login page |
| Visit `/dashboard` directly | Redirected to login (protected) |

---

### 4.2 API Tests via curl

Run these from the **backend EC2** or any machine with access.

```bash
BASE="http://BACKEND-PUBLIC-IP"

# Register
curl -s -X POST $BASE/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"smoketest","email":"smoke@test.com","password":"Test@12345"}' \
  | python3 -m json.tool

# Login and capture token
TOKEN=$(curl -s -X POST $BASE/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"smoke@test.com","password":"Test@12345"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "Got token: ${TOKEN:0:20}..."

# Create patient
PATIENT=$(curl -s -X POST $BASE/api/patients \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","age":35,"gender":"Male","blood_group":"O+","phone":"555-1234","address":"123 Main St"}')
echo $PATIENT | python3 -m json.tool
PATIENT_ID=$(echo $PATIENT | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# List patients
curl -s $BASE/api/patients \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Upload a document (creates a test PDF)
echo "%PDF-1.0 test" > /tmp/test.pdf
curl -s -X POST $BASE/api/patients/$PATIENT_ID/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test.pdf" \
  -F "document_type=Prescription" | python3 -m json.tool

# List documents
DOC_RESPONSE=$(curl -s $BASE/api/patients/$PATIENT_ID/documents \
  -H "Authorization: Bearer $TOKEN")
echo $DOC_RESPONSE | python3 -m json.tool
DOC_ID=$(echo $DOC_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin)['documents'][0]['id'])")

# Get pre-signed URL
curl -s $BASE/api/patients/$PATIENT_ID/documents/$DOC_ID/url \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# Expected: {"url": "https://s3.amazonaws.com/...", "expires_in_seconds": 3600}

# Delete document
curl -s -X DELETE $BASE/api/patients/$PATIENT_ID/documents/$DOC_ID \
  -H "Authorization: Bearer $TOKEN" -w "%{http_code}"
# Expected: 204

# Delete patient
curl -s -X DELETE $BASE/api/patients/$PATIENT_ID \
  -H "Authorization: Bearer $TOKEN" -w "%{http_code}"
# Expected: 204
```

---

### 4.3 S3 Verification

```bash
# After uploading a document via the app, check the file is in S3
aws s3 ls s3://patient-docs-ACCOUNT-ID/patient_documents/ --region us-east-1
# Expected: one or more files listed

# After deleting a document, confirm it's removed
aws s3 ls s3://patient-docs-ACCOUNT-ID/patient_documents/ --region us-east-1
# Expected: file is gone (or fewer files)

# Confirm bucket has no public access
aws s3api get-public-access-block --bucket patient-docs-ACCOUNT-ID
# Expected: all four values are "true"
```

---

### 4.4 Database Verification

```bash
# SSH into backend or database EC2
mysql -h DB-PRIVATE-IP -u patient_app -p patient_db

# Run these queries:
SHOW TABLES;
-- Expected: patient_documents, patients, users

DESCRIBE patient_documents;
-- Expected: id, patient_id, user_id, document_type, file_name, s3_key, uploaded_at

SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM patients;
SELECT * FROM patient_documents LIMIT 5\G

EXIT;
```

---

## Part 5 — Troubleshooting

### Backend service won't start

```bash
sudo journalctl -u patient-app -n 50 --no-pager
```

**Common causes and fixes:**

| Error | Fix |
|---|---|
| `Failed to retrieve secret` | Check IAM role is attached to backend EC2 |
| `DATABASE_URL not set` | Check `.env` has `AWS_REGION`, check secret has all keys |
| `Access denied for user` | Check `db_password` in secret matches MySQL user |
| `Can't connect to MySQL server` | Check security group allows 3306 from backend, MySQL bind-address is 0.0.0.0 |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` inside the venv |

---

### Frontend shows blank page or 404

```bash
# Check Nginx error log
sudo tail -f /var/log/nginx/patient_frontend_error.log

# Check dist directory exists
ls /opt/patient-frontend/dist/

# Check file permissions
stat /opt/patient-frontend/dist/index.html
```

---

### Frontend can't reach backend (CORS or network error)

1. Check `VITE_API_URL` in `/opt/patient-frontend/.env` — must be `http://BACKEND-IP/api`
2. Rebuild after changing: `npm run build`
3. Check backend security group allows port 80 from `0.0.0.0/0`
4. Test from frontend EC2: `curl http://BACKEND-PRIVATE-IP/health`

---

### S3 upload fails

```bash
# From the backend EC2, test S3 access
aws s3 ls s3://patient-docs-ACCOUNT-ID/

# If "Access Denied":
# → Check IAM role is attached (aws sts get-caller-identity)
# → Check S3 policy has PutObject, GetObject, DeleteObject
# → Check bucket name in secret matches actual bucket name

# Test KMS access
aws kms describe-key --key-id alias/patient-app-s3-key
```

---

### Pre-signed URL doesn't work

- Pre-signed URLs expire after **1 hour** — generate a new one
- Check `s3:GetObject` is in the IAM S3 policy
- Check the KMS policy grants `kms:Decrypt` to the EC2 role

---

## Part 6 — Manual Database Migration

The `image_url` column in the `patients` table from the previous version should be dropped:

```sql
-- Connect to MySQL on database EC2
mysql -h DB-PRIVATE-IP -u patient_app -p patient_db

-- Check current columns
DESCRIBE patients;

-- Drop old column if it exists
ALTER TABLE patients DROP COLUMN image_url;

-- Verify
DESCRIBE patients;
-- Expected: id, name, age, gender, blood_group, phone, address, user_id, created_at

EXIT;
```

> This is safe to run at any time. SQLAlchemy does not auto-drop columns — it simply ignores ones it doesn't know about. The `patient_documents` table is created automatically on first startup.

---

## Part 7 — Update Deployment (Code Changes)

When you push new code:

### Backend update

```bash
ssh -i your-key.pem ubuntu@BACKEND-PUBLIC-IP

cd /opt/patient-app
git pull origin main

source venv/bin/activate
pip install -r requirements.txt    # only needed if requirements changed

sudo systemctl restart patient-app
sudo systemctl status patient-app  # verify it came back up

# Tail logs for 30 seconds to confirm clean startup
sudo journalctl -u patient-app -f --no-pager &
sleep 30 && kill %1
```

### Frontend update

```bash
ssh -i your-key.pem ubuntu@FRONTEND-PUBLIC-IP

cd /opt/patient-frontend
git pull origin main
npm install                         # only if package.json changed
npm run build
sudo systemctl reload nginx

# Quick verify
curl -s -o /dev/null -w "%{http_code}" http://localhost/
# Expected: 200
```

---

## Quick Reference Commands

```bash
# View backend logs live
sudo journalctl -u patient-app -f

# Restart backend
sudo systemctl restart patient-app

# Restart nginx (both servers)
sudo systemctl reload nginx

# Check all services at once (database EC2)
sudo systemctl status mysql

# Check all services at once (backend EC2)
sudo systemctl status patient-app nginx

# Check disk space (all instances)
df -h

# Check memory
free -h

# Test S3 from backend
aws s3 ls s3://patient-docs-ACCOUNT-ID/ --region us-east-1

# Get Secrets Manager value
aws secretsmanager get-secret-value \
  --secret-id patient-management-secrets \
  --query SecretString --output text | python3 -m json.tool
```

---

## Pre-Terraform Checklist

Before moving to Terraform, confirm all of the following manually:

- [ ] Database EC2: MySQL running, `patient_db` database exists, `patient_app` user has access
- [ ] Backend EC2: `patient-app` service running, `/health` returns `{"status":"ok"}`
- [ ] Backend EC2: Secrets Manager secret is readable via IAM role
- [ ] Backend EC2: S3 upload works (test via API)
- [ ] Backend EC2: Pre-signed URL is generated correctly (URL opens a file)
- [ ] Backend EC2: S3 delete works (file removed after document delete)
- [ ] Frontend EC2: Nginx serving React app at port 80
- [ ] Frontend EC2: Login, register, patient CRUD all work in browser
- [ ] Frontend EC2: Document upload, view (pre-signed URL opens), delete all work
- [ ] Database: `patient_documents` table created automatically on startup
- [ ] Database: `image_url` column dropped from `patients` table
- [ ] S3: No public access (all four block settings = true)
- [ ] S3: Encryption is SSE-KMS (verify in bucket Properties)

Once all boxes are checked, you have a working deployment to model your Terraform from.

---

**Last updated**: June 2026

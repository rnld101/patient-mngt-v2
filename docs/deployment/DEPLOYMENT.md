# Complete Deployment Guide

## Architecture Overview

```
┌─────────────────┐
│  Frontend EC2   │
│  (React/Nginx)  │
└────────┬────────┘
         │ (HTTP/HTTPS)
         │
┌────────▼────────┐
│  Backend EC2    │
│  (FastAPI)      │
└────────┬────────┘
         │ (MySQL)
┌────────▼────────┐
│  Database EC2   │
│  (MySQL 8)      │
└─────────────────┘
```

All instances use AWS IAM roles for authentication (no access keys).

---

## Part 1: Database EC2 Setup

### Step 1: Launch EC2 Instance

**Specifications:**
- AMI: Ubuntu 22.04 LTS
- Instance Type: t3.small (2 GB RAM)
- Storage: 20 GB GP3
- Security Group: patient-app-db-sg

### Step 2: Connect and Update System

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install common utilities
sudo apt install -y curl wget vim git
```

### Step 3: Install MySQL 8

```bash
# Install MySQL Server
sudo apt install -y mysql-server mysql-client

# Verify installation
mysql --version
```

### Step 4: Configure MySQL

```bash
# Start MySQL service
sudo systemctl start mysql
sudo systemctl enable mysql

# Run security script
sudo mysql_secure_installation

# When prompted:
# - Would you like to setup VALIDATE PASSWORD component? → Y
# - Set password validation policy: → 2 (Strong)
# - Enter password: [Create strong password - save this!]
# - Remove anonymous users? → Y
# - Disable remote root login? → Y
# - Remove test database? → Y
# - Reload privilege tables? → Y
```

### Step 5: Configure MySQL for Remote Access

```bash
# Edit MySQL configuration
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf

# Find the line: bind-address = 127.0.0.1
# Change it to: bind-address = 0.0.0.0
# Save (Ctrl+X, Y, Enter)

# Restart MySQL
sudo systemctl restart mysql
```

### Step 6: Create Application Database and User

```bash
# Connect to MySQL as root
mysql -u root -p
# Enter the password you set above

# Run these commands:
CREATE DATABASE patient_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'patient_app'@'%' IDENTIFIED BY 'your-secure-password';
GRANT ALL PRIVILEGES ON patient_db.* TO 'patient_app'@'%';
FLUSH PRIVILEGES;
EXIT;
```

**Save these credentials:**
- Database: patient_db
- User: patient_app
- Password: your-secure-password
- Host: [Database EC2 Private IP]

### Step 7: Verify Connection from Backend

(Do this after setting up backend instance)

```bash
# From backend instance, test connection:
mysql -h [database-private-ip] -u patient_app -p patient_db -e "SELECT 1"
```

---

## Part 2: Backend EC2 Setup

### Step 1: Launch EC2 Instance

**Specifications:**
- AMI: Ubuntu 22.04 LTS
- Instance Type: t3.medium (2 GB RAM)
- Storage: 30 GB GP3
- Security Group: patient-app-backend-sg
- **IMPORTANT: Attach IAM role `PatientManagementAppRole`**

### Step 2: Connect and Update System

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget vim git build-essential libssl-dev libffi-dev python3-dev
```

### Step 3: Install Python 3.13

```bash
# Add deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Install Python 3.13
sudo apt install -y python3.13 python3.13-venv python3.13-dev

# Set as default python3
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.13 1

# Verify
python3 --version
```

### Step 4: Install Application Code

```bash
# Create application directory
sudo mkdir -p /opt/patient-app
cd /opt/patient-app
sudo chown ubuntu:ubuntu .

# Clone or copy your repository
# Example: git clone https://your-repo-url . (if using Git)
# Or copy files manually

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Update AWS Secrets Manager Configuration

```bash
# Edit .env file with AWS region
nano /opt/patient-app/.env

# Add/Update:
AWS_REGION=us-east-1

# Save and exit
```

### Step 6: Run Alembic Migrations

```bash
cd /opt/patient-app

# Activate virtual environment
source venv/bin/activate

# Run migrations
alembic upgrade head
```

### Step 7: Create Systemd Service File

```bash
# Create service file
sudo nano /etc/systemd/system/patient-app.service
```

**Paste this content:**

```ini
[Unit]
Description=Patient Management API
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/opt/patient-app
Environment="PATH=/opt/patient-app/venv/bin"
ExecStart=/opt/patient-app/venv/bin/gunicorn \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    app.main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Save (Ctrl+X, Y, Enter)
# Reload systemd
sudo systemctl daemon-reload

# Start service
sudo systemctl start patient-app
sudo systemctl enable patient-app

# Check status
sudo systemctl status patient-app
```

### Step 8: Install and Configure Gunicorn

```bash
cd /opt/patient-app
source venv/bin/activate
pip install gunicorn
```

### Step 9: Install and Configure Nginx

```bash
# Install Nginx
sudo apt install -y nginx

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/patient-app
```

**Paste this content:**

```nginx
upstream patient_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name _;
    client_max_body_size 10M;

    access_log /var/log/nginx/patient_app_access.log;
    error_log /var/log/nginx/patient_app_error.log;

    location / {
        proxy_pass http://patient_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    location /static/ {
        alias /opt/patient-app/static/;
    }
}
```

```bash
# Save (Ctrl+X, Y, Enter)

# Enable site
sudo ln -s /etc/nginx/sites-available/patient-app /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Reload Nginx
sudo systemctl reload nginx
```

### Step 10: Verify Backend is Running

```bash
# Check service status
sudo systemctl status patient-app

# Check logs
sudo journalctl -u patient-app -n 50 -f

# Test API locally
curl http://localhost:8000/health

# Test from frontend instance
curl http://[backend-private-ip]:8000/health
```

---

## Part 3: Frontend EC2 Setup

### Step 1: Launch EC2 Instance

**Specifications:**
- AMI: Ubuntu 22.04 LTS
- Instance Type: t3.small (2 GB RAM)
- Storage: 20 GB GP3
- Security Group: patient-app-frontend-sg

### Step 2: Connect and Update System

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget vim git
```

### Step 3: Install Node.js

```bash
# Install Node.js LTS (Latest stable)
curl -sL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# Verify installation
node --version
npm --version
```

### Step 4: Install Application Code

```bash
# Create application directory
sudo mkdir -p /opt/patient-frontend
cd /opt/patient-frontend
sudo chown ubuntu:ubuntu .

# Clone or copy your repository
# git clone https://your-repo-url . (if using Git)
# Or copy files manually

# Install dependencies
npm install
```

### Step 5: Build React Application

```bash
cd /opt/patient-frontend

# Create .env file with backend URL
echo "VITE_API_URL=http://[backend-private-ip]:8000/api" > .env

# Build production bundle
npm run build

# Verify build
ls -la dist/
```

### Step 6: Install and Configure Nginx

```bash
# Install Nginx
sudo apt install -y nginx

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/patient-frontend
```

**Paste this content:**

```nginx
server {
    listen 80;
    server_name _;

    access_log /var/log/nginx/patient_frontend_access.log;
    error_log /var/log/nginx/patient_frontend_error.log;

    root /opt/patient-frontend/dist;
    index index.html;

    # Serve static assets with cache
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|webp)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API proxy
    location /api {
        proxy_pass http://[backend-private-ip]:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # React Router fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

**Replace `[backend-private-ip]` with actual backend IP**

```bash
# Save (Ctrl+X, Y, Enter)

# Enable site
sudo ln -s /etc/nginx/sites-available/patient-frontend /etc/nginx/sites-enabled/

# Disable default site
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### Step 7: Configure HTTPS (Optional but Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Generate SSL certificate
sudo certbot certonly --standalone -d your-domain.com

# Update Nginx to use SSL
# (Edit /etc/nginx/sites-available/patient-frontend to add SSL config)
```

### Step 8: Verify Frontend is Running

```bash
# Check Nginx status
sudo systemctl status nginx

# Check logs
sudo tail -f /var/log/nginx/patient_frontend_error.log

# Open in browser
# http://[frontend-public-ip]
```

---

## Post-Deployment Verification

### Check All Services

```bash
# On Database EC2
sudo systemctl status mysql

# On Backend EC2
sudo systemctl status patient-app
sudo systemctl status nginx

# On Frontend EC2
sudo systemctl status nginx
```

### Test API Endpoints

```bash
# From backend instance
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"password123"}'

# Get health status
curl http://localhost:8000/health
```

### Test Frontend Access

1. Open browser
2. Navigate to: `http://[frontend-public-ip]`
3. Register a new account
4. Login
5. Add a patient

---

## Troubleshooting

### Backend Service Won't Start

```bash
# Check logs
sudo journalctl -u patient-app -n 100

# Check if port 8000 is in use
sudo lsof -i :8000

# Check if secrets are accessible
aws secretsmanager get-secret-value --secret-id patient-management-secrets
```

### Database Connection Failed

```bash
# Test connection from backend
mysql -h [db-ip] -u patient_app -p -e "SELECT 1"

# Check MySQL is listening
sudo netstat -tulnp | grep mysql

# Check security group rules
# (From AWS console, verify port 3306 is open)
```

### Frontend Not Loading

```bash
# Check Nginx logs
sudo tail -f /var/log/nginx/patient_frontend_error.log

# Test Nginx configuration
sudo nginx -t

# Check file permissions
ls -la /opt/patient-frontend/dist/
```

---

## Backup and Maintenance

### Database Backup

```bash
# Create backup
mysqldump -h [db-ip] -u patient_app -p patient_db > backup.sql

# Restore from backup
mysql -h [db-ip] -u patient_app -p patient_db < backup.sql
```

### Update Application

```bash
# On backend instance
cd /opt/patient-app
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart patient-app

# On frontend instance
cd /opt/patient-frontend
git pull origin main
npm install
npm run build
sudo systemctl reload nginx
```

---

## Security Recommendations

1. **Enable HTTPS** using Let's Encrypt/Certbot
2. **Use security groups** restrictively
3. **Monitor logs** regularly
4. **Rotate secrets** periodically in AWS Secrets Manager
5. **Enable CloudWatch monitoring** for all instances
6. **Use strong passwords** for all services
7. **Enable VPC Flow Logs** for traffic monitoring
8. **Disable root login** on EC2 instances (already disabled by default)
9. **Use AWS Config** for compliance checking
10. **Enable S3 versioning** for disaster recovery

---

## Estimated Costs (AWS)

- **EC2 Instances** (3x t3.small): ~$25/month
- **Database Volume**: ~$3/month
- **Data Transfer**: ~$0.09/GB (outbound)
- **Secrets Manager**: $0.40/secret/month
- **S3 Storage**: ~$0.023/GB
- **KMS**: ~$1/month

**Total Estimated: $30-50/month** for small deployment

---

## Next Steps

1. Complete all AWS setup (see AWS_SETUP.md)
2. Deploy all three EC2 instances using this guide
3. Run migrations
4. Test all endpoints (see TESTING.md)
5. Configure monitoring and alerts
6. Set up automated backups

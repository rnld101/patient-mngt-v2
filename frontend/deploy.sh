#!/bin/bash

# Patient Management Application - Frontend Deployment Script
# Run this on the Frontend EC2 instance after copying the application code

set -e

echo "=== Patient Management Frontend Deployment Script ==="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as non-root
if [ "$EUID" -eq 0 ]; then
   echo "Please do not run this script as root"
   exit 1
fi

DEPLOY_DIR="/opt/patient-frontend"

# Step 1: Update system packages
echo -e "\n${BLUE}[1/6] Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Step 2: Install Node.js
echo -e "\n${BLUE}[2/6] Installing Node.js...${NC}"
curl -sL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# Step 3: Install Nginx
echo -e "\n${BLUE}[3/6] Installing Nginx...${NC}"
sudo apt install -y nginx

# Step 4: Install dependencies
echo -e "\n${BLUE}[4/6] Installing Node.js dependencies...${NC}"
cd "$DEPLOY_DIR"
npm install

# Step 5: Build application
echo -e "\n${BLUE}[5/6] Building React application...${NC}"
npm run build

# Step 6: Configure Nginx
echo -e "\n${BLUE}[6/6] Configuring Nginx...${NC}"

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/patient-frontend > /dev/null <<'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name _;

    access_log /var/log/nginx/patient_frontend_access.log;
    error_log /var/log/nginx/patient_frontend_error.log;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    root /opt/patient-frontend/dist;
    index index.html index.htm;

    # Serve static files with long expiry
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|webp)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # React Router fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/patient-frontend /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable nginx

echo -e "\n${GREEN}=== Deployment Complete ===${NC}"
echo -e "\n${GREEN}Next steps:${NC}"
echo "1. Start Nginx: sudo systemctl start nginx"
echo "2. Check status: sudo systemctl status nginx"
echo "3. View logs: sudo tail -f /var/log/nginx/patient_frontend_error.log"
echo ""
echo "Frontend will be available at: http://[server-ip]"
echo "Update the backend URL in .env if needed"

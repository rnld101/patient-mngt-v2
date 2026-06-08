#!/bin/bash

# Patient Management Application - Backend Deployment Script
# Run this on the Backend EC2 instance after copying the application code

set -e

echo "=== Patient Management API Deployment Script ==="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as non-root
if [ "$EUID" -eq 0 ]; then
   echo "Please do not run this script as root"
   exit 1
fi

DEPLOY_DIR="/opt/patient-app"
VENV_DIR="$DEPLOY_DIR/venv"

# Step 1: Update system packages
echo -e "\n${BLUE}[1/8] Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Step 2: Install system dependencies
echo -e "\n${BLUE}[2/8] Installing system dependencies...${NC}"
sudo apt install -y \
    python3.13 \
    python3.13-venv \
    python3.13-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    libmysqlclient-dev \
    pkg-config \
    nginx \
    curl \
    wget \
    git

# Step 3: Create virtual environment
echo -e "\n${BLUE}[3/8] Creating Python virtual environment...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    python3.13 -m venv "$VENV_DIR"
fi

# Step 4: Install Python dependencies
echo -e "\n${BLUE}[4/8] Installing Python dependencies...${NC}"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$DEPLOY_DIR/requirements.txt"

# Step 5: Copy and configure environment file
echo -e "\n${BLUE}[5/7] Setting up environment file...${NC}"
if [ ! -f "$DEPLOY_DIR/.env" ]; then
    cp "$DEPLOY_DIR/.env.example" "$DEPLOY_DIR/.env"
    echo "Please edit $DEPLOY_DIR/.env with your configuration"
fi

# Step 6: Configure systemd service
echo -e "\n${BLUE}[6/7] Configuring systemd service...${NC}"
sudo cp "$DEPLOY_DIR/patient-app.service" /etc/systemd/system/patient-app.service
sudo chown root:root /etc/systemd/system/patient-app.service
sudo chmod 644 /etc/systemd/system/patient-app.service
sudo systemctl daemon-reload
sudo systemctl enable patient-app

# Step 7: Configure Nginx
echo -e "\n${BLUE}[7/7] Configuring Nginx...${NC}"
sudo cp "$DEPLOY_DIR/nginx.conf" /etc/nginx/sites-available/patient-app
sudo ln -sf /etc/nginx/sites-available/patient-app /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable nginx

echo -e "\n${GREEN}=== Deployment Complete ===${NC}"
echo -e "\n${GREEN}Next steps:${NC}"
echo "1. Edit $DEPLOY_DIR/.env with your database credentials"
echo "2. Start the service: sudo systemctl start patient-app"
echo "3. Start Nginx: sudo systemctl start nginx"
echo "4. Check status: sudo systemctl status patient-app"
echo "5. View logs: sudo journalctl -u patient-app -f"
echo ""
echo "API will be available at: http://[server-ip]:8000"

#!/bin/bash

# Patient Management Application - Database Setup Script
# Run this on the Database EC2 instance

set -e

echo "=== Patient Management Database Setup Script ==="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Update system packages
echo -e "\n${BLUE}[1/5] Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Step 2: Install MySQL Server
echo -e "\n${BLUE}[2/5] Installing MySQL Server...${NC}"
sudo apt install -y mysql-server mysql-client

# Step 3: Start MySQL service
echo -e "\n${BLUE}[3/5] Starting MySQL service...${NC}"
sudo systemctl start mysql
sudo systemctl enable mysql

# Step 4: Configure MySQL
echo -e "\n${BLUE}[4/5] Configuring MySQL...${NC}"

# Edit bind address to allow remote connections
sudo sed -i "s/bind-address.*= 127.0.0.1/bind-address = 0.0.0.0/" /etc/mysql/mysql.conf.d/mysqld.cnf

# Restart MySQL to apply changes
sudo systemctl restart mysql

# Step 5: Create database and user
echo -e "\n${BLUE}[5/5] Creating database and user...${NC}"

# Set default password (change this!)
DB_PASSWORD="patient_password_123"

sudo mysql -e "CREATE DATABASE IF NOT EXISTS patient_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'patient_app'@'%' IDENTIFIED BY '$DB_PASSWORD';"
sudo mysql -e "GRANT ALL PRIVILEGES ON patient_db.* TO 'patient_app'@'%';"
sudo mysql -e "FLUSH PRIVILEGES;"

echo -e "\n${GREEN}=== Database Setup Complete ===${NC}"
echo -e "\n${YELLOW}Database Credentials:${NC}"
echo "Host: [This server's private IP]"
echo "Database: patient_db"
echo "Username: patient_app"
echo "Password: $DB_PASSWORD"
echo ""
echo -e "${YELLOW}IMPORTANT: Change the password in production!${NC}"
echo ""
echo -e "${BLUE}To test connection from another server:${NC}"
echo "mysql -h [database-ip] -u patient_app -p patient_db -e \"SELECT 1\""

# Testing Guide

## Setup

All endpoints are at: `http://localhost:8000/api`

---

## Authentication Endpoints

### 1. Register User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePassword123"
  }'
```

**Response (201 Created):**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "created_at": "2024-01-15T10:30:00"
}
```

### 2. Login User

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePassword123"
  }'
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 1
}
```

**Save the access_token for subsequent requests:**

```bash
export TOKEN="your-access-token-here"
```

---

## Patient Endpoints

### 1. Create Patient

```bash
curl -X POST http://localhost:8000/api/patients \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Alice Smith",
    "age": 35,
    "gender": "Female",
    "blood_group": "O+",
    "phone": "+1-555-123-4567",
    "address": "123 Main Street, Springfield, IL 62701"
  }'
```

**Response (201 Created):**
```json
{
  "id": 1,
  "name": "Alice Smith",
  "age": 35,
  "gender": "Female",
  "blood_group": "O+",
  "phone": "+1-555-123-4567",
  "address": "123 Main Street, Springfield, IL 62701",
  "image_url": null,
  "user_id": 1,
  "created_at": "2024-01-15T10:35:00"
}
```

### 2. Get All Patients

```bash
curl -X GET http://localhost:8000/api/patients \
  -H "Authorization: Bearer $TOKEN"
```

**Response (200 OK):**
```json
{
  "total": 1,
  "patients": [
    {
      "id": 1,
      "name": "Alice Smith",
      "age": 35,
      "gender": "Female",
      "blood_group": "O+",
      "phone": "+1-555-123-4567",
      "address": "123 Main Street, Springfield, IL 62701",
      "image_url": null,
      "user_id": 1,
      "created_at": "2024-01-15T10:35:00"
    }
  ]
}
```

### 3. Get Patient by ID

```bash
curl -X GET http://localhost:8000/api/patients/1 \
  -H "Authorization: Bearer $TOKEN"
```

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Alice Smith",
  "age": 35,
  "gender": "Female",
  "blood_group": "O+",
  "phone": "+1-555-123-4567",
  "address": "123 Main Street, Springfield, IL 62701",
  "image_url": null,
  "user_id": 1,
  "created_at": "2024-01-15T10:35:00"
}
```

### 4. Update Patient

```bash
curl -X PUT http://localhost:8000/api/patients/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "age": 36,
    "phone": "+1-555-987-6543"
  }'
```

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Alice Smith",
  "age": 36,
  "gender": "Female",
  "blood_group": "O+",
  "phone": "+1-555-987-6543",
  "address": "123 Main Street, Springfield, IL 62701",
  "image_url": null,
  "user_id": 1,
  "created_at": "2024-01-15T10:35:00"
}
```

### 5. Upload Patient Image

```bash
curl -X POST http://localhost:8000/api/patients/1/upload-image \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/image.jpg"
```

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Alice Smith",
  "age": 36,
  "gender": "Female",
  "blood_group": "O+",
  "phone": "+1-555-987-6543",
  "address": "123 Main Street, Springfield, IL 62701",
  "image_url": "https://patient-images-bucket.s3.amazonaws.com/patient_images/uuid-1234.jpg",
  "user_id": 1,
  "created_at": "2024-01-15T10:35:00"
}
```

### 6. Delete Patient

```bash
curl -X DELETE http://localhost:8000/api/patients/1 \
  -H "Authorization: Bearer $TOKEN"
```

**Response (204 No Content):**
```
[No body]
```

---

## Health Check

```bash
curl -X GET http://localhost:8000/health
```

**Response:**
```json
{
  "status": "ok"
}
```

---

## Error Responses

### 401 Unauthorized (Invalid Token)

```bash
curl -X GET http://localhost:8000/api/patients \
  -H "Authorization: Bearer invalid-token"
```

**Response (401):**
```json
{
  "detail": "Invalid or expired token"
}
```

### 400 Bad Request (Validation Error)

```bash
curl -X POST http://localhost:8000/api/patients \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "",
    "age": -5
  }'
```

**Response (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

### 404 Not Found

```bash
curl -X GET http://localhost:8000/api/patients/999 \
  -H "Authorization: Bearer $TOKEN"
```

**Response (404):**
```json
{
  "detail": "Patient not found"
}
```

---

## Sample Data for Testing

### Test User Accounts

```json
{
  "users": [
    {
      "username": "doctor_alice",
      "email": "alice@hospital.com",
      "password": "SecurePass123!"
    },
    {
      "username": "doctor_bob",
      "email": "bob@hospital.com",
      "password": "SecurePass456!"
    }
  ]
}
```

### Sample Patients

```json
{
  "patients": [
    {
      "name": "Alice Smith",
      "age": 35,
      "gender": "Female",
      "blood_group": "O+",
      "phone": "+1-555-123-4567",
      "address": "123 Main Street, Springfield, IL 62701"
    },
    {
      "name": "Bob Johnson",
      "age": 42,
      "gender": "Male",
      "blood_group": "A+",
      "phone": "+1-555-234-5678",
      "address": "456 Oak Avenue, Chicago, IL 60601"
    },
    {
      "name": "Carol Davis",
      "age": 28,
      "gender": "Female",
      "blood_group": "B-",
      "phone": "+1-555-345-6789",
      "address": "789 Pine Road, Detroit, MI 48201"
    },
    {
      "name": "David Wilson",
      "age": 55,
      "gender": "Male",
      "blood_group": "AB+",
      "phone": "+1-555-456-7890",
      "address": "321 Elm Street, Houston, TX 77001"
    },
    {
      "name": "Emma Brown",
      "age": 31,
      "gender": "Female",
      "blood_group": "O-",
      "phone": "+1-555-567-8901",
      "address": "654 Maple Drive, Phoenix, AZ 85001"
    }
  ]
}
```

---

## Automated Testing Script

Save this as `test-api.sh`:

```bash
#!/bin/bash

API_URL="http://localhost:8000/api"
USER_EMAIL="test@example.com"
USER_PASSWORD="TestPass123!"

echo "=== Testing Patient Management API ==="

# Register user
echo -e "\n1. Registering user..."
REGISTER_RESPONSE=$(curl -s -X POST $API_URL/auth/register \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"testuser\",
    \"email\": \"$USER_EMAIL\",
    \"password\": \"$USER_PASSWORD\"
  }")
echo $REGISTER_RESPONSE | jq .

# Login user
echo -e "\n2. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST $API_URL/auth/login \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$USER_EMAIL\",
    \"password\": \"$USER_PASSWORD\"
  }")
echo $LOGIN_RESPONSE | jq .

# Extract token
TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "Token: $TOKEN"

# Create patient
echo -e "\n3. Creating patient..."
PATIENT_RESPONSE=$(curl -s -X POST $API_URL/patients \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Test Patient",
    "age": 30,
    "gender": "Male",
    "blood_group": "O+",
    "phone": "+1-555-123-4567",
    "address": "123 Test St"
  }')
echo $PATIENT_RESPONSE | jq .

# Get patients
echo -e "\n4. Getting all patients..."
curl -s -X GET $API_URL/patients \
  -H "Authorization: Bearer $TOKEN" | jq .

echo -e "\n=== Testing Complete ==="
```

**Run the script:**

```bash
chmod +x test-api.sh
./test-api.sh
```

---

## Performance Testing with Apache Bench

```bash
# Install Apache Bench
sudo apt install -y apache2-utils

# Simple load test (100 requests, 10 concurrent)
ab -n 100 -c 10 http://localhost:8000/health

# Test with authentication header
ab -n 100 -c 10 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/patients
```

---

## Postman Collection

See [postman-collection.json](./postman-collection.json) for complete Postman collection.

### Import into Postman:

1. Open Postman
2. Click "Import"
3. Select "postman-collection.json"
4. Set environment variable:
   - `base_url`: `http://localhost:8000/api`
   - `token`: Your JWT token

---

## Frontend Testing

### Manual Test Flow

1. **Register**: Go to `/register`, create new account
2. **Login**: Go to `/login`, login with credentials
3. **Dashboard**: View total patients count
4. **Add Patient**: Click "Add Patient", fill form, submit
5. **View Patients**: See all patients in table
6. **Edit Patient**: Click "Edit" on a patient, modify data
7. **Upload Image**: Upload patient profile picture
8. **Delete Patient**: Delete a patient (with confirmation)
9. **Logout**: Logout button redirects to login

### Browser Developer Tools

1. Open DevTools (F12)
2. Go to "Application" → "Storage" → "LocalStorage"
3. Verify `access_token` and `user_id` are saved
4. Network tab shows API calls

---

## Debugging

### Check API Logs

```bash
# On backend EC2
sudo journalctl -u patient-app -f

# Check Nginx access logs
sudo tail -f /var/log/nginx/patient_app_access.log
```

### Check Database

```bash
# Connect to database
mysql -h [db-ip] -u patient_app -p patient_db

# View users
SELECT * FROM users;

# View patients
SELECT * FROM patients;

# Count patients per user
SELECT user_id, COUNT(*) as count FROM patients GROUP BY user_id;
```

### Test S3 Upload Locally

```bash
# Install AWS CLI
pip install awscli

# Configure credentials (uses IAM role on EC2)
# No configuration needed if IAM role is attached

# Test upload
aws s3 cp test.jpg s3://your-bucket-name/

# Verify encryption
aws s3api head-object \
  --bucket your-bucket-name \
  --key test.jpg \
  --query 'ServerSideEncryption'
```

---

## Issues and Solutions

### API Returns 401 Unauthorized

**Cause:** Token expired or invalid

**Solution:**
```bash
# Get new token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"password"}'

# Use new token
export TOKEN="new-token"
```

### S3 Upload Fails

**Cause:** IAM role missing permissions or invalid bucket

**Solution:**
- Verify IAM role is attached to EC2 instance
- Verify bucket name in secrets
- Check bucket exists and encryption is enabled
- Review S3 bucket policy

### Database Connection Failed

**Cause:** Network or credentials issue

**Solution:**
```bash
# Test from backend instance
mysql -h [db-ip] -u patient_app -p -e "SELECT 1"

# Check security group allows port 3306
# Check database is running on database instance
```

---

## Next Steps

1. Run all tests above
2. Verify all CRUD operations work
3. Test image uploads
4. Load test the API
5. Monitor logs for errors
6. Configure monitoring alerts

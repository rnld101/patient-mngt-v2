# API Testing Guide

All examples assume:

```bash
BASE="http://localhost:8000"   # or your API custom domain (e.g., https://api.yourdomain.com)
```

---

## 1. Health Check

```bash
curl -s $BASE/health
```
**Expected**:
```json
{"status": "ok"}
```

---

## 2. Authentication

### Register a new user

```bash
curl -s -X POST $BASE/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"SecurePass1!"}' \
  | python3 -m json.tool
```

**Expected**:
```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "created_at": "2026-06-08T..."
}
```

### Login and store token

```bash
TOKEN=$(curl -s -X POST $BASE/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"SecurePass1!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "Token acquired: ${TOKEN:0:30}..."
```

All subsequent requests use:
```bash
-H "Authorization: Bearer $TOKEN"
```

---

## 3. Patient Management

### Create a patient

```bash
curl -s -X POST $BASE/api/patients \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "age": 42,
    "gender": "Male",
    "blood_group": "A+",
    "phone": "+1-555-123-4567",
    "address": "123 Main Street, Springfield"
  }' | python3 -m json.tool
```

**Expected**: Patient JSON with `id`, no `image_url` field.

Store the ID:
```bash
PATIENT_ID=1   # use the id from the response
```

### List all patients

```bash
curl -s $BASE/api/patients \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Expected**:
```json
{
  "total": 1,
  "patients": [...]
}
```

### Get a single patient

```bash
curl -s $BASE/api/patients/$PATIENT_ID \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### Update a patient

```bash
curl -s -X PUT $BASE/api/patients/$PATIENT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"age": 43, "phone": "+1-555-999-0000"}' \
  | python3 -m json.tool
```

**Expected**: Updated patient JSON.

### Delete a patient

```bash
curl -s -X DELETE $BASE/api/patients/$PATIENT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -w "\nHTTP Status: %{http_code}\n"
```

**Expected**: `HTTP Status: 204`

---

## 4. Document Management

### Upload a document

```bash
# Create a test file
echo "Test prescription content" > /tmp/prescription.pdf

curl -s -X POST $BASE/api/patients/$PATIENT_ID/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/prescription.pdf" \
  -F "document_type=Prescription" \
  | python3 -m json.tool
```

**Expected**:
```json
{
  "id": 1,
  "patient_id": 1,
  "user_id": 1,
  "document_type": "Prescription",
  "file_name": "prescription.pdf",
  "uploaded_at": "2026-06-08T..."
}
```

Store the document ID:
```bash
DOC_ID=1   # use the id from the response
```

### List documents for a patient

```bash
curl -s $BASE/api/patients/$PATIENT_ID/documents \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Expected**:
```json
{
  "total": 1,
  "documents": [...]
}
```

### Get a pre-signed URL to view a document

```bash
curl -s $BASE/api/patients/$PATIENT_ID/documents/$DOC_ID/url \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Expected**:
```json
{
  "url": "https://patient-docs-xxxx.s3.amazonaws.com/patient_documents/uuid.pdf?X-Amz-...",
  "expires_in_seconds": 3600
}
```

Open the URL in a browser — the file should open or download directly from S3.

### Delete a document

```bash
curl -s -X DELETE $BASE/api/patients/$PATIENT_ID/documents/$DOC_ID \
  -H "Authorization: Bearer $TOKEN" \
  -w "\nHTTP Status: %{http_code}\n"
```

**Expected**: `HTTP Status: 204`

---

## 5. Allowed Document Types

The `document_type` field must be one of:

| Value | Description |
|---|---|
| `Prescription` | Doctor prescriptions |
| `Blood Report` | Lab blood test results |
| `X-Ray` | X-ray images |
| `MRI` | MRI scans |
| `CT Scan` | CT/CAT scans |
| `Other` | Any other medical document |

Any other value returns:
```json
{"detail": "Invalid document type. Allowed types: Blood Report, CT Scan, MRI, Other, Prescription, X-Ray"}
```

---

## 6. Allowed File Types

| Extension | Mime Type |
|---|---|
| `.pdf` | PDF documents |
| `.jpg`, `.jpeg` | JPEG images |
| `.png` | PNG images |
| `.gif` | GIF images |
| `.webp` | WebP images |
| `.dcm` | DICOM medical images |

Maximum file size: **10 MB**

---

## 7. Common Error Responses

### 401 Unauthorized
```json
{"detail": "Invalid or expired token"}
```
→ Log in again to get a new token.

### 404 Not Found
```json
{"detail": "Patient not found"}
```
→ Patient doesn't exist or belongs to another user.

### 400 Bad Request — Validation error
```json
{
  "detail": [
    {"loc": ["body", "age"], "msg": "Input should be greater than 0", "type": "greater_than"}
  ]
}
```

### 400 Bad Request — File type
```json
{"detail": "File type not allowed. Allowed types: .dcm, .gif, .jpg, .jpeg, .pdf, .png, .webp"}
```

### 400 Bad Request — File too large
```json
{"detail": "File size exceeds the maximum allowed size of 10 MB"}
```

### 500 Internal Server Error — S3 failure
```json
{"detail": "Failed to upload document: ..."}
```
→ Check IAM role has S3 permissions; check bucket name in Secrets Manager is correct.

---

## 8. Interactive API Documentation

When the backend is running, Swagger UI is available at:

```
http://localhost:8000/docs          (Swagger UI)
http://localhost:8000/redoc         (ReDoc)
```

Use the **Authorize** button in Swagger UI and enter your JWT token to test endpoints interactively.

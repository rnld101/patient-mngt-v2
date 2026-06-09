from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.dependencies import get_current_user
from app.schemas import (
    DocumentResponse,
    DocumentListResponse,
    DocumentUrlResponse,
    ALLOWED_DOCUMENT_TYPES,
)
from app.services.patient import PatientService
from app.services.document import DocumentService
from app.utils.aws import upload_file_to_s3, generate_presigned_url, delete_file_from_s3
from app.utils.validators import validate_document_file, validate_file_size, generate_unique_filename
from app.core.config import settings

router = APIRouter(prefix="/patients", tags=["Documents"])

# Pre-signed URL validity in seconds (1 hour)
PRESIGNED_URL_EXPIRY = 900


@router.post(
    "/{patient_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED
)
def upload_document(
    patient_id: int,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a medical document for a patient."""
    # Validate document type
    if document_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document type. Allowed types: {', '.join(sorted(ALLOWED_DOCUMENT_TYPES))}"
        )

    # Validate file type and size
    validate_document_file(file)
    validate_file_size(file)

    # Ensure the patient belongs to the current user
    patient = PatientService.get_patient_by_id(db, patient_id, current_user["user_id"])
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    # Generate a unique S3 key and upload
    s3_key = generate_unique_filename(file.filename)
    try:
        upload_file_to_s3(file.file, settings.s3_bucket_name, s3_key, content_type=file.content_type)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )

    # Save metadata to the database
    doc = DocumentService.create_document(
        db,
        patient_id=patient_id,
        user_id=current_user["user_id"],
        document_type=document_type,
        file_name=file.filename,
        s3_key=s3_key
    )
    return doc


@router.get("/{patient_id}/documents", response_model=DocumentListResponse)
def list_documents(
    patient_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all documents for a patient."""
    # Ensure the patient belongs to the current user
    patient = PatientService.get_patient_by_id(db, patient_id, current_user["user_id"])
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    docs = DocumentService.get_documents_for_patient(db, patient_id, current_user["user_id"])
    return DocumentListResponse(total=len(docs), documents=docs)


@router.get("/{patient_id}/documents/{document_id}/url", response_model=DocumentUrlResponse)
def get_document_url(
    patient_id: int,
    document_id: int,
    mode: str = "view",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a temporary pre-signed URL to view or download a document."""
    if mode not in ["view", "download"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid mode. Allowed values: view, download"
        )

    doc = DocumentService.get_document_by_id(db, document_id, current_user["user_id"])
    if not doc or doc.patient_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    try:
        url = generate_presigned_url(
            settings.s3_bucket_name,
            doc.s3_key,
            PRESIGNED_URL_EXPIRY,
            mode=mode,
            filename=doc.file_name
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate document URL: {str(e)}"
        )

    return DocumentUrlResponse(url=url, expires_in_seconds=PRESIGNED_URL_EXPIRY)


@router.delete("/{patient_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    patient_id: int,
    document_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a patient document (removes from database and S3)."""
    s3_key = DocumentService.delete_document(db, document_id, current_user["user_id"])
    if s3_key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Best-effort S3 deletion — log failure but don't surface it to the user
    try:
        delete_file_from_s3(settings.s3_bucket_name, s3_key)
    except Exception as e:
        print(f"Warning: failed to delete S3 object {s3_key}: {e}")

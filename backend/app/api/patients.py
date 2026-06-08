from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form
)
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.dependencies import get_current_user
from app.schemas import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientsListResponse
)
from app.services.patient import PatientService
from app.utils.aws import upload_image_to_s3
from app.utils.validators import (
    validate_image_file,
    validate_image_size,
    generate_unique_filename
)
from app.core.config import settings

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_data: PatientCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new patient."""
    patient = PatientService.create_patient(
        db,
        patient_data,
        user_id=current_user["user_id"]
    )
    return patient


@router.get("", response_model=PatientsListResponse)
async def get_patients(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all patients for the authenticated user."""
    patients = PatientService.get_all_patients(db, user_id=current_user["user_id"])
    return PatientsListResponse(
        total=len(patients),
        patients=patients
    )


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific patient by ID."""
    patient = PatientService.get_patient_by_id(db, patient_id, current_user["user_id"])
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a patient."""
    patient = PatientService.update_patient(
        db,
        patient_id,
        current_user["user_id"],
        patient_data
    )
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    return patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a patient."""
    success = PatientService.delete_patient(db, patient_id, current_user["user_id"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )


@router.post("/{patient_id}/upload-image", response_model=PatientResponse)
async def upload_patient_image(
    patient_id: int,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a profile image for a patient."""
    # Validate image file
    validate_image_file(file)
    await validate_image_size(file)
    
    # Check if patient exists
    patient = PatientService.get_patient_by_id(db, patient_id, current_user["user_id"])
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)
    
    # Upload to S3
    try:
        s3_url = upload_image_to_s3(
            file.file,
            settings.s3_bucket_name,
            unique_filename
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}"
        )
    
    # Update patient with image URL
    updated_patient = PatientService.update_patient_image(
        db,
        patient_id,
        current_user["user_id"],
        s3_url
    )
    
    return updated_patient

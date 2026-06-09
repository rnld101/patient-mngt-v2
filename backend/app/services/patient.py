from sqlalchemy.orm import Session
from app.models import Patient, PatientDocument
from app.schemas import PatientCreate, PatientUpdate
from typing import Optional
from app.utils.aws import delete_file_from_s3
from app.core.config import settings


class PatientService:
    """Service for patient operations."""

    @staticmethod
    def create_patient(db: Session, patient_data: PatientCreate, user_id: int) -> Patient:
        """Create a new patient."""
        new_patient = Patient(
            **patient_data.model_dump(),
            user_id=user_id
        )
        db.add(new_patient)
        db.commit()
        db.refresh(new_patient)
        return new_patient

    @staticmethod
    def get_patient_by_id(db: Session, patient_id: int, user_id: int) -> Optional[Patient]:
        """Get a patient by ID (must belong to the authenticated user)."""
        return db.query(Patient).filter(
            Patient.id == patient_id,
            Patient.user_id == user_id
        ).first()

    @staticmethod
    def get_all_patients(db: Session, user_id: int) -> list[Patient]:
        """Get all patients for the authenticated user."""
        return db.query(Patient).filter(Patient.user_id == user_id).all()

    @staticmethod
    def update_patient(
        db: Session,
        patient_id: int,
        user_id: int,
        update_data: PatientUpdate
    ) -> Optional[Patient]:
        """Update a patient's fields."""
        patient = db.query(Patient).filter(
            Patient.id == patient_id,
            Patient.user_id == user_id
        ).first()

        if not patient:
            return None

        for key, value in update_data.model_dump(exclude_unset=True).items():
            setattr(patient, key, value)

        db.commit()
        db.refresh(patient)
        return patient

    @staticmethod
    def delete_patient(db: Session, patient_id: int, user_id: int) -> bool:
        """Delete a patient and all their associated documents (S3 + DB metadata)."""
        patient = db.query(Patient).filter(
            Patient.id == patient_id,
            Patient.user_id == user_id
        ).first()

        if not patient:
            return False

        # Find and delete all associated documents
        docs = db.query(PatientDocument).filter(
            PatientDocument.patient_id == patient_id,
            PatientDocument.user_id == user_id
        ).all()

        for doc in docs:
            # Best-effort S3 file deletion
            try:
                delete_file_from_s3(settings.s3_bucket_name, doc.s3_key)
            except Exception as e:
                print(f"Warning: failed to delete S3 object {doc.s3_key} during patient deletion: {e}")
            
            # Delete document metadata record
            db.delete(doc)

        # Delete patient record
        db.delete(patient)
        db.commit()
        return True

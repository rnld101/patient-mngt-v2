from sqlalchemy.orm import Session
from app.models import Patient
from app.schemas import PatientCreate, PatientUpdate
from typing import Optional


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
        """Get a patient by ID (belongs to the authenticated user)."""
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
        """Update a patient."""
        patient = db.query(Patient).filter(
            Patient.id == patient_id,
            Patient.user_id == user_id
        ).first()
        
        if not patient:
            return None
        
        # Update only provided fields
        for key, value in update_data.model_dump(exclude_unset=True).items():
            setattr(patient, key, value)
        
        db.commit()
        db.refresh(patient)
        return patient
    
    @staticmethod
    def delete_patient(db: Session, patient_id: int, user_id: int) -> bool:
        """Delete a patient."""
        patient = db.query(Patient).filter(
            Patient.id == patient_id,
            Patient.user_id == user_id
        ).first()
        
        if not patient:
            return False
        
        db.delete(patient)
        db.commit()
        return True
    
    @staticmethod
    def update_patient_image(
        db: Session,
        patient_id: int,
        user_id: int,
        image_url: str
    ) -> Optional[Patient]:
        """Update patient's image URL."""
        patient = db.query(Patient).filter(
            Patient.id == patient_id,
            Patient.user_id == user_id
        ).first()
        
        if not patient:
            return None
        
        patient.image_url = image_url
        db.commit()
        db.refresh(patient)
        return patient
    
    @staticmethod
    def count_patients(db: Session, user_id: int) -> int:
        """Count total patients for a user."""
        return db.query(Patient).filter(Patient.user_id == user_id).count()

from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(50), nullable=False)
    blood_group = Column(String(10), nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(String(500), nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class PatientDocument(Base):
    __tablename__ = "patient_documents"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    document_type = Column(String(50), nullable=False)
    file_name = Column(String(255), nullable=False)
    s3_key = Column(String(500), nullable=False)
    uploaded_at = Column(DateTime, server_default=func.now(), nullable=False)

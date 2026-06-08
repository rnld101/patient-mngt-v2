from sqlalchemy.orm import Session
from app.models import User
from app.core.security import hash_password, verify_password, create_access_token


class AuthService:
    """Service for authentication operations."""
    
    @staticmethod
    def register_user(db: Session, username: str, email: str, password: str) -> User:
        """Register a new user."""
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            raise ValueError("Username or email already exists")
        
        # Hash password and create user
        hashed_password = hash_password(password)
        new_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User:
        """Authenticate a user and return user object if valid."""
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            raise ValueError("Invalid email or password")
        
        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")
        
        return user
    
    @staticmethod
    def generate_token(user_id: int) -> str:
        """Generate JWT token for a user."""
        return create_access_token({"sub": str(user_id)})

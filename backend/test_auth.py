import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, User
from app.services.auth import AuthService
from app.core.security import hash_password, verify_password

class TestAuthService(unittest.TestCase):
    def setUp(self):
        # Create an in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.SessionLocal()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_successful_registration_and_login_case_1(self):
        # Case 2: password "rnld12"
        password = "rnld12"
        user = AuthService.register_user(self.db, "arnold", "arnold@example.com", password)
        self.assertEqual(user.username, "arnold")
        self.assertEqual(user.email, "arnold@example.com")
        self.assertNotEqual(user.hashed_password, password)
        
        # Verify login
        authenticated_user = AuthService.authenticate_user(self.db, "arnold@example.com", password)
        self.assertEqual(authenticated_user.id, user.id)

    def test_successful_registration_and_login_case_2(self):
        # Case 3: password "rnld12345"
        password = "rnld12345"
        user = AuthService.register_user(self.db, "arnold2", "arnold2@example.com", password)
        self.assertEqual(user.username, "arnold2")
        self.assertEqual(user.email, "arnold2@example.com")
        
        # Verify login
        authenticated_user = AuthService.authenticate_user(self.db, "arnold2@example.com", password)
        self.assertEqual(authenticated_user.id, user.id)

    def test_other_passwords(self):
        # Other passwords requested: "rnld123", "password123", "Arnold@123", "MySecurePassword2026"
        passwords = ["rnld123", "password123", "Arnold@123", "MySecurePassword2026"]
        for idx, password in enumerate(passwords):
            username = f"user_{idx}"
            email = f"user_{idx}@example.com"
            user = AuthService.register_user(self.db, username, email, password)
            self.assertEqual(user.username, username)
            
            # Verify login
            authenticated_user = AuthService.authenticate_user(self.db, email, password)
            self.assertEqual(authenticated_user.id, user.id)

    def test_password_too_long(self):
        # Password > 72 bytes should raise ValueError
        long_password = "a" * 73
        with self.assertRaises(ValueError) as context:
            AuthService.register_user(self.db, "long_user", "long@example.com", long_password)
        self.assertIn("Password is too long. Maximum 72 bytes allowed", str(context.exception))

    def test_invalid_login(self):
        password = "valid_password"
        AuthService.register_user(self.db, "test_user", "test@example.com", password)
        
        # Wrong password
        with self.assertRaises(ValueError) as context:
            AuthService.authenticate_user(self.db, "test@example.com", "wrong_password")
        self.assertEqual(str(context.exception), "Invalid email or password")
        
        # Wrong email
        with self.assertRaises(ValueError) as context:
            AuthService.authenticate_user(self.db, "nonexistent@example.com", password)
        self.assertEqual(str(context.exception), "Invalid email or password")

    def test_jwt_token_generation_and_decoding(self):
        from app.core.config import settings
        from app.core.security import decode_access_token
        
        # Ensure a secret key is set for testing
        old_secret = settings.jwt_secret_key
        settings.jwt_secret_key = "test-secret-key"
        
        try:
            # Generate token
            token = AuthService.generate_token(123)
            self.assertIsNotNone(token)
            
            # Decode token
            decoded = decode_access_token(token)
            self.assertEqual(decoded["user_id"], 123)
            self.assertIsInstance(decoded["user_id"], int)  # Must be an integer!
        finally:
            settings.jwt_secret_key = old_secret

if __name__ == "__main__":
    unittest.main()

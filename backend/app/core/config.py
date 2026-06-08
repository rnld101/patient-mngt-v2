from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Patient Management API"
    debug: bool = False
    api_prefix: str = "/api"
    
    # Database will be loaded from secrets
    database_url: Optional[str] = None
    
    # JWT will be loaded from secrets
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # S3 will be loaded from secrets
    s3_bucket_name: Optional[str] = None
    
    # AWS Region
    aws_region: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

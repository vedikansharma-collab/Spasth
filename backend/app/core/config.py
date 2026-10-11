import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    PROJECT_NAME: str = "Spasth — Insurance Policy Intelligence & Treatment Cost Estimator"
    VERSION: str = "0.1.0-phase1"
    API_V1_STR: str = "/api"
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./fin01.db")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    CANONICAL_DEMO_POLICY_ID: str = os.getenv("CANONICAL_DEMO_POLICY_ID", "945c5b0b-c71e-4e0b-abf0-ed0211b93052")
    
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOADS_DIR: Path = BASE_DIR / "uploads"
    DATA_DIR: Path = BASE_DIR.parent / "data"
    BACKEND_DATA_DIR: Path = BASE_DIR / "data"
    CANONICAL_JSON_PATH: Path = BASE_DIR / "data" / "policy.json"

    def validate_jwt_secret(self) -> str:
        """Validates that JWT secret is set and sufficiently strong. Fails closed."""
        secret = self.JWT_SECRET_KEY.strip()
        insecure_secrets = {
            "spasth_production_super_secret_jwt_key_2025",
            "secret",
            "jwt_secret",
            "change_me",
            "test_secret"
        }
        if not secret or len(secret) < 32 or secret.lower() in insecure_secrets:
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR: JWT_SECRET_KEY is missing, "
                "too short (must be >= 32 characters), or using an insecure default. Failing closed."
            )
        return secret

settings = Settings()

# Ensure directories exist
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
settings.BACKEND_DATA_DIR.mkdir(parents=True, exist_ok=True)
(settings.DATA_DIR / "processed").mkdir(parents=True, exist_ok=True)
(settings.DATA_DIR / "sample_policies").mkdir(parents=True, exist_ok=True)
(settings.DATA_DIR / "treatment_costs").mkdir(parents=True, exist_ok=True)

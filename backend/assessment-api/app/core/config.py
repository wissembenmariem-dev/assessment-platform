from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        protected_namespaces=("settings_",),
    )

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""

    anthropic_api_key: str = ""
    llm_fast: str = "claude-sonnet-4-6"
    llm_report: str = "claude-opus-4-6"

    resend_api_key: str = ""

    recruiter_email: str = ""
    recruiter_password: str = ""

    app_secret_key: str = ""
    app_base_url: str = "http://localhost:8000"
    cors_origins: List[str] = ["http://localhost:3000"]

    legal_contact_email: str = "privacy@example.com"

    notification_email: str = "notifications@example.com"

    environment: str = "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    def validate_production_config(self) -> list[str]:
        missing = []
        required = {
            "SUPABASE_URL":          self.supabase_url,
            "SUPABASE_ANON_KEY":     self.supabase_anon_key,
            "SUPABASE_SERVICE_KEY":  self.supabase_service_key,
            "ANTHROPIC_API_KEY":     self.anthropic_api_key,
            "RESEND_API_KEY":        self.resend_api_key,
            "RECRUITER_EMAIL":       self.recruiter_email,
            "RECRUITER_PASSWORD":    self.recruiter_password,
            "APP_SECRET_KEY":        self.app_secret_key,
            "LEGAL_CONTACT_EMAIL":   self.legal_contact_email,
            "NOTIFICATION_EMAIL":    self.notification_email,
        }
        for key, value in required.items():
            if not value or value.startswith("TODO") or value in ("changeme", "dev-secret-change-in-production"):
                missing.append(key)
        return missing


settings = Settings()

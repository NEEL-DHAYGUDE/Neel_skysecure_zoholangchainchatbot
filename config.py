import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ZOHO_CLIENT_ID: str
    ZOHO_CLIENT_SECRET: str
    ZOHO_REDIRECT_URI: str
    MISTRAL_API_KEY: str
    
    # Regional datacenter settings (.in vs .com)
    ZOHO_ACCOUNTS_URL: str = "https://accounts.zoho.in"
    ZOHO_BASE_API_URL: str = "https://projectsapi.zoho.in/restapi"

    class Config:
        env_file = ".env"

settings = Settings()
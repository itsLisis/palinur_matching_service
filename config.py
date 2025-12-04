from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://palmin:palinur_2025*@userservice.cd4ke84oq9bq.us-east-2.rds.amazonaws.com:5432/postgres"
    # URL of the user service (can be overridden via environment)
    USER_SERVICE_URL: str = "http://localhost:8000"
    #SECRET_KEY: str =  
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
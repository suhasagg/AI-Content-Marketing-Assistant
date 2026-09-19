from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    app_name: str = "ContentAlchemy"
    llm_provider: str = "mock"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = "provider-model"
    max_revisions: int = 2
settings = Settings()

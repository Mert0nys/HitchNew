from pydantic_settings import BaseSettings
from typing import List, Optional
from pydantic import Field
import os
import json


class Settings(BaseSettings):
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_BASE_URL: str = Field(default="https://api.openai.com/v1", env="OPENAI_BASE_URL")

    USE_LOCAL_LLM: bool = Field(default=True, env="USE_LOCAL_LLM")
    LOCAL_LLM_URL: str = Field(default="http://localhost:11434", env="LOCAL_LLM_URL")
    LOCAL_LLM_MODEL: str = Field(default="mistral", env="LOCAL_LLM_MODEL")
    
    # Airtable
    AIRTABLE_API_KEY: Optional[str] = Field(default=None, env="AIRTABLE_API_KEY")
    AIRTABLE_BASE_ID: Optional[str] = Field(default=None, env="AIRTABLE_BASE_ID")
    
    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(default=None, env="TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: Optional[str] = Field(default=None, env="TELEGRAM_CHAT_ID")
    
    # Slack
    SLACK_WEBHOOK_URL: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")
    
    # Google
    GOOGLE_API_KEY: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    GOOGLE_SEARCH_ENGINE_ID: Optional[str] = Field(default=None, env="GOOGLE_SEARCH_ENGINE_ID")
    
    # Twitter
    TWITTER_BEARER_TOKEN: Optional[str] = Field(default=None, env="TWITTER_BEARER_TOKEN")
    
    # Application Settings
    PRIORITY_GEO_STR: str = Field(default="Germany,Brazil,USA,India", env="PRIORITY_GEO")
    MAX_NEWS_PER_GEO: int = Field(default=30, env="MAX_NEWS_PER_GEO")
    NEWS_DAYS_BACK: int = Field(default=7, env="NEWS_DAYS_BACK")
    
    # LLM Settings
    LLM_MODEL: str = Field(default="gpt-4o", env="LLM_MODEL")
    LLM_TEMPERATURE_CLASSIFY: float = Field(default=0.3, env="LLM_TEMPERATURE_CLASSIFY")
    LLM_TEMPERATURE_GENERATE: float = Field(default=0.8, env="LLM_TEMPERATURE_GENERATE")
    
    # Monitoring Schedule
    MONITORING_INTERVAL_HOURS: int = Field(default=72, env="MONITORING_INTERVAL_HOURS")
    
    # Redis
    REDIS_URL: Optional[str] = Field(default=None, env="REDIS_URL")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    @property
    def PRIORITY_GEO(self) -> List[str]:
        """Преобразуем строку в список"""
        return [geo.strip() for geo in self.PRIORITY_GEO_STR.split(',')]
    
    class Config:
        # Загружаем из переменных окружения OS, а не из .env файла
        env_file = None  # Отключаем загрузку из .env файла
        case_sensitive = False
        extra = "ignore"


def load_settings_from_env():
    """Загружает настройки из переменных окружения OS"""
    try:
        # Пытаемся загрузить из переменных окружения через pydantic
        settings = Settings()
        
        # Дополнительная проверка и загрузка из os.environ если нужно
        if not settings.USE_LOCAL_LLM and not settings.OPENAI_API_KEY:
            settings.OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
        
        if not settings.AIRTABLE_API_KEY:
            settings.AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
        
        if not settings.AIRTABLE_BASE_ID:
            settings.AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
        
        if not settings.TELEGRAM_BOT_TOKEN:
            settings.TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
        
        if not settings.TELEGRAM_CHAT_ID:
            settings.TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
        
        if not settings.SLACK_WEBHOOK_URL:
            settings.SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
        
        if not settings.GOOGLE_API_KEY:
            settings.GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
        
        if not settings.GOOGLE_SEARCH_ENGINE_ID:
            settings.GOOGLE_SEARCH_ENGINE_ID = os.environ.get("GOOGLE_SEARCH_ENGINE_ID")
        
        if not settings.TWITTER_BEARER_TOKEN:
            settings.TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")
        
        if not settings.REDIS_URL:
            settings.REDIS_URL = os.environ.get("REDIS_URL")
        
        # Переопределяем из os.environ приоритетные значения
        settings.PRIORITY_GEO_STR = os.environ.get("PRIORITY_GEO", settings.PRIORITY_GEO_STR)
        settings.MAX_NEWS_PER_GEO = int(os.environ.get("MAX_NEWS_PER_GEO", settings.MAX_NEWS_PER_GEO))
        settings.NEWS_DAYS_BACK = int(os.environ.get("NEWS_DAYS_BACK", settings.NEWS_DAYS_BACK))
        settings.MONITORING_INTERVAL_HOURS = int(os.environ.get("MONITORING_INTERVAL_HOURS", settings.MONITORING_INTERVAL_HOURS))
        settings.LOG_LEVEL = os.environ.get("LOG_LEVEL", settings.LOG_LEVEL)
        
        print("✅ Settings loaded successfully from environment variables")
        print(f"   OpenAI API Key: {'✓ set' if settings.OPENAI_API_KEY else '✗ not set'}")
        print(f"   Local LLM: {'✓ enabled' if settings.USE_LOCAL_LLM else '✗ disabled'}")
        print(f"   Local LLM URL: {settings.LOCAL_LLM_URL}")
        print(f"   Local LLM Model: {settings.LOCAL_LLM_MODEL}")
        print(f"   Airtable: {'✓ set' if settings.AIRTABLE_API_KEY else '✗ not set (using memory)'}")
        print(f"   Telegram: {'✓ set' if settings.TELEGRAM_BOT_TOKEN else '✗ not set'}")
        print(f"   Google: {'✓ set' if settings.GOOGLE_API_KEY else '✗ not set'}")
        print(f"   Twitter: {'✓ set' if settings.TWITTER_BEARER_TOKEN else '✗ not set'}")
        print(f"   Redis: {'✓ set' if settings.REDIS_URL else '✗ not set'}")
        print(f"   Priority GEO: {settings.PRIORITY_GEO}")
        print(f"   Max news per GEO: {settings.MAX_NEWS_PER_GEO}")
        print(f"   News days back: {settings.NEWS_DAYS_BACK}")
        print(f"   Monitoring interval: {settings.MONITORING_INTERVAL_HOURS} hours")
        print(f"   Log level: {settings.LOG_LEVEL}")
        
        return settings
        
    except Exception as e:
        print(f"❌ Error loading settings: {e}")
        print("\n📝 Creating default settings...")
        
        # Создаем настройки по умолчанию
        settings = Settings(
            OPENAI_API_KEY=os.environ.get("OPENAI_API_KEY"),
            USE_LOCAL_LLM=os.environ.get("USE_LOCAL_LLM", "true").lower() == "true",
            LOCAL_LLM_URL=os.environ.get("LOCAL_LLM_URL", "http://localhost:11434"),
            LOCAL_LLM_MODEL=os.environ.get("LOCAL_LLM_MODEL", "mistral"),
            AIRTABLE_API_KEY=os.environ.get("AIRTABLE_API_KEY"),
            AIRTABLE_BASE_ID=os.environ.get("AIRTABLE_BASE_ID")
        )
        return settings


# Создаем экземпляр настроек
settings = load_settings_from_env()


# Функция для установки переменных окружения программно
def set_env_variables(values: dict):
    """Устанавливает переменные окружения программно"""
    for key, value in values.items():
        if value is not None:
            os.environ[key] = str(value)
    print("✅ Environment variables set")


# Функция для получения всех настроек в виде словаря
def get_settings_dict() -> dict:
    """Возвращает все настройки в виде словаря"""
    return {
        "OPENAI_API_KEY": settings.OPENAI_API_KEY,
        "OPENAI_BASE_URL": settings.OPENAI_BASE_URL,
        "USE_LOCAL_LLM": settings.USE_LOCAL_LLM,
        "LOCAL_LLM_URL": settings.LOCAL_LLM_URL,
        "LOCAL_LLM_MODEL": settings.LOCAL_LLM_MODEL,
        "AIRTABLE_API_KEY": settings.AIRTABLE_API_KEY,
        "AIRTABLE_BASE_ID": settings.AIRTABLE_BASE_ID,
        "TELEGRAM_BOT_TOKEN": settings.TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": settings.TELEGRAM_CHAT_ID,
        "SLACK_WEBHOOK_URL": settings.SLACK_WEBHOOK_URL,
        "GOOGLE_API_KEY": settings.GOOGLE_API_KEY,
        "GOOGLE_SEARCH_ENGINE_ID": settings.GOOGLE_SEARCH_ENGINE_ID,
        "TWITTER_BEARER_TOKEN": settings.TWITTER_BEARER_TOKEN,
        "PRIORITY_GEO": settings.PRIORITY_GEO,
        "PRIORITY_GEO_STR": settings.PRIORITY_GEO_STR,
        "MAX_NEWS_PER_GEO": settings.MAX_NEWS_PER_GEO,
        "NEWS_DAYS_BACK": settings.NEWS_DAYS_BACK,
        "MONITORING_INTERVAL_HOURS": settings.MONITORING_INTERVAL_HOURS,
        "REDIS_URL": settings.REDIS_URL,
        "LOG_LEVEL": settings.LOG_LEVEL,
    }


# Пример использования
if __name__ == "__main__":
    print("\n" + "="*50)
    print("Current Settings:")
    print("="*50)
    for key, value in get_settings_dict().items():
        if "KEY" in key or "TOKEN" in key or "SECRET" in key:
            # Маскируем чувствительные данные при выводе
            print(f"{key}: {'*' * 10 if value else 'None'}")
        else:
            print(f"{key}: {value}")
from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

# 尝试加载.env文件，如果不存在则忽略
load_dotenv(override=True)

class Settings(BaseSettings):
    AMAP_API_KEY: str = os.getenv("AMAP_API_KEY", "")
    AMAP_API_BASE_URL: str = os.getenv("AMAP_API_BASE_URL", "https://restapi.amap.com/v3")
    DEFAULT_ORIGIN: str = os.getenv("DEFAULT_ORIGIN", "")
    DEFAULT_DESTINATION: str = os.getenv("DEFAULT_DESTINATION", "")
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings() 
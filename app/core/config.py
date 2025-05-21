import os
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "智能简历筛选系统"
    
    # MongoDB配置
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB: str = os.getenv("MONGODB_DB", "resume_analyzer")
    
    # Redis配置
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))  # 添加Redis数据库选择
    
    # AI提供商配置
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "openai")  # 默认使用OpenAI
    
    # OpenAI配置
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    
    # 硅基平台(智谱AI)配置
    ZHIPUAI_API_KEY: str = os.getenv("ZHIPUAI_API_KEY", "")
    ZHIPUAI_MODEL: str = os.getenv("ZHIPUAI_MODEL", "glm-4")
    
    # 邮件通知配置
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", 587))
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "")
    MAIL_FROM_NAME: str = os.getenv("MAIL_FROM_NAME", "智能简历筛选系统")
    
    # 文件上传配置
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", 10 * 1024 * 1024))  # 10MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "html", "txt", "docx"]

    # 添加缺失的字段定义
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your_jwt_secret_key_here")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # 使用 model_config 替代 Config 内部类，兼容 Pydantic v2
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"  # 允许额外的环境变量
    }

settings = Settings()

# 确保上传目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True) 
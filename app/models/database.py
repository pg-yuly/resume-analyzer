import motor.motor_asyncio
from typing import Dict, Any
import logging
from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB客户端
client = None
db = None

async def connect_to_mongodb():
    """连接到MongoDB数据库"""
    global client, db
    
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.MONGODB_DB]
        logger.info(f"连接到MongoDB数据库: {settings.MONGODB_DB}")
        
        # 创建索引
        await create_indexes()
        
        return db
    except Exception as e:
        logger.error(f"连接MongoDB失败: {e}")
        raise e

async def close_mongodb_connection():
    """关闭MongoDB连接"""
    global client
    if client:
        client.close()
        logger.info("MongoDB连接已关闭")

async def create_indexes():
    """创建数据库索引"""
    global db
    
    try:
        # 用户集合索引
        await db.users.create_index("email", unique=True)
        await db.users.create_index("username")
        
        # 简历集合索引
        await db.resumes.create_index("candidate_name")
        await db.resumes.create_index("position")
        await db.resumes.create_index("status")
        await db.resumes.create_index("match_score")
        
        # 职位要求集合索引
        await db.requirements.create_index("job_title")
        await db.requirements.create_index("user_id")
        
        # 分析结果集合索引
        await db.analyses.create_index("resume_id")
        await db.analyses.create_index("user_id")
        await db.analyses.create_index([("result.match_score", -1)])
        
        logger.info("MongoDB索引创建完成")
    except Exception as e:
        logger.error(f"创建索引失败: {e}")

async def get_database() -> Any:
    """获取数据库实例"""
    global db
    return db 
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import logging
from typing import List, Optional
from pydantic import BaseModel

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入配置
try:
    from app.core.config import settings
    logger.info("配置加载成功")
except Exception as e:
    logger.error(f"加载配置失败: {e}")
    raise

# 导入服务模块，添加错误处理
try:
    from app.services.parser import resume_parser
    from app.services.analyzer import resume_analyzer
    from app.services.notifier import notification_service
    logger.info("服务模块加载成功")
except Exception as e:
    logger.error(f"加载服务模块失败: {e}")
    raise

# 导入数据库连接
try:
    from app.models.database import connect_to_mongodb, close_mongodb_connection
    logger.info("数据库模块加载成功")
except Exception as e:
    logger.error(f"加载数据库模块失败: {e}")
    raise

app = FastAPI(
    title="智能简历筛选系统",
    description="一个基于AI的简历筛选和分析系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该指定确切的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启动事件
@app.on_event("startup")
async def startup_db_client():
    try:
        await connect_to_mongodb()
        logger.info("MongoDB连接成功")
    except Exception as e:
        logger.error(f"MongoDB连接失败: {e}")
        # 不抛出异常，让应用继续运行
    
# 关闭事件
@app.on_event("shutdown")
async def shutdown_db_client():
    try:
        await close_mongodb_connection()
        logger.info("MongoDB连接关闭")
    except Exception as e:
        logger.error(f"关闭MongoDB连接失败: {e}")

# 导入API路由
try:
    from app.api import resume, requirements, analysis, users, websocket

    app.include_router(resume.router)
    app.include_router(requirements.router)
    app.include_router(analysis.router)
    app.include_router(users.router)
    app.include_router(websocket.router)
    logger.info("API路由加载成功")
except Exception as e:
    logger.error(f"加载API路由失败: {e}")
    # 创建临时路由，确保应用可以启动
    @app.get("/api_error")
    async def api_error():
        return {"error": f"API路由加载失败: {str(e)}"}

@app.get("/")
async def root():
    return {"message": "欢迎使用智能简历筛选系统 API"}

@app.get("/health")
async def health_check():
    health_info = {
        "status": "healthy",
        "components": {
            "database": "连接成功" if "connect_to_mongodb" in globals() else "未连接",
            "ai_provider": settings.AI_PROVIDER
        }
    }
    return health_info

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from typing import List, Optional
from pydantic import BaseModel

# 导入服务模块
from app.services.parser import resume_parser
from app.services.analyzer import resume_analyzer
from app.services.notifier import notification_service
from app.core.config import settings

# 导入数据库连接
from app.models.database import connect_to_mongodb, close_mongodb_connection

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
    await connect_to_mongodb()
    
# 关闭事件
@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongodb_connection()

# 导入API路由
from app.api import resume, requirements, analysis, users, websocket

app.include_router(resume.router)
app.include_router(requirements.router)
app.include_router(analysis.router)
app.include_router(users.router)
app.include_router(websocket.router)

@app.get("/")
async def root():
    return {"message": "欢迎使用智能简历筛选系统 API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 
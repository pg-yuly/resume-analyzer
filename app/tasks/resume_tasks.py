from app.core.celery_app import celery_app
from app.services.parser.resume_parser import default_parser
from app.services.analyzer.resume_analyzer import default_analyzer
from app.services.notifier.notification_service import notification_service
from app.models.database import get_database
import logging
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery_app.task(name="app.tasks.resume_tasks.analyze_resume_task")
def analyze_resume_task(resume_id: str, requirements: dict, user_id: str):
    """
    异步分析简历任务
    
    Args:
        resume_id: 简历ID
        requirements: 职位要求
        user_id: 用户ID
    """
    logger.info(f"开始分析简历: {resume_id}")
    
    # 创建事件循环
    loop = asyncio.get_event_loop()
    
    try:
        # 执行异步分析
        analysis_result = loop.run_until_complete(
            _analyze_resume_async(resume_id, requirements, user_id)
        )
        
        logger.info(f"简历 {resume_id} 分析完成，匹配分数: {analysis_result.match_score}")
        return {
            "resume_id": resume_id,
            "success": True,
            "match_score": analysis_result.match_score,
            "matches_requirements": analysis_result.matches_requirements
        }
    except Exception as e:
        logger.error(f"分析简历 {resume_id} 失败: {e}")
        return {
            "resume_id": resume_id,
            "success": False,
            "error": str(e)
        }

async def _analyze_resume_async(resume_id: str, requirements: dict, user_id: str):
    """
    异步执行简历分析流程
    """
    # 创建MongoDB客户端
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB]
    
    try:
        # 查询简历
        resume = await db["resumes"].find_one({"_id": resume_id})
        if not resume:
            raise ValueError(f"找不到指定的简历: {resume_id}")
        
        # 分析简历
        analysis_result = await default_analyzer.analyze_resume(
            resume_content=resume["content"],
            requirements=requirements
        )
        
        # 将分析结果保存到数据库
        analysis_data = {
            "resume_id": resume_id,
            "requirements": requirements,
            "result": analysis_result.dict(),
            "user_id": user_id,
            "created_at": datetime.now()
        }
        
        await db["analyses"].insert_one(analysis_data)
        
        # 更新简历状态
        update_data = {
            "status": "analyzed", 
            "last_analyzed_at": datetime.now(),
            "matches_requirements": analysis_result.matches_requirements,
            "match_score": analysis_result.match_score
        }
        
        await db["resumes"].update_one(
            {"_id": resume_id},
            {"$set": update_data}
        )
        
        # 如果匹配度高，发送通知
        if analysis_result.match_score >= 70:  # 可以配置阈值
            # 获取用户邮箱
            user = await db["users"].find_one({"_id": user_id})
            user_email = user.get("email") if user else None
            
            # 发送通知
            await notification_service.notify_resume_match(
                user_id=user_id,
                user_email=user_email,
                resume_data={
                    "id": resume_id,
                    "candidate_name": resume["candidate_name"],
                    "position": resume["position"],
                    "timestamp": datetime.now().isoformat()
                },
                analysis_result=analysis_result.dict()
            )
            
            # 更新简历状态为匹配
            await db["resumes"].update_one(
                {"_id": resume_id},
                {"$set": {"status": "matched"}}
            )
        
        return analysis_result
    
    finally:
        # 关闭MongoDB连接
        client.close() 
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.models.database import get_database
from app.api.users import get_current_user

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/analyses",
    tags=["analyses"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[Dict[str, Any]])
async def list_analyses(
    resume_id: Optional[str] = None,
    requirement_id: Optional[str] = None,
    user_id: Optional[str] = None,
    min_score: Optional[float] = None,
    limit: int = 20,
    skip: int = 0,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    获取分析结果列表
    """
    # 构建查询条件
    query = {}
    if resume_id:
        query["resume_id"] = resume_id
    if requirement_id:
        query["requirements.id"] = requirement_id
    if user_id:
        query["user_id"] = user_id
    if min_score:
        query["result.match_score"] = {"$gte": min_score}
        
    # 默认只查询当前用户的分析结果
    if "user_id" not in query:
        query["user_id"] = current_user["_id"]
    
    # 查询数据库
    cursor = db["analyses"].find(query).skip(skip).limit(limit).sort("created_at", -1)
    analyses = await cursor.to_list(length=limit)
    
    # 补充简历信息
    result = []
    for analysis in analyses:
        # 获取简历信息
        resume = await db["resumes"].find_one({"_id": analysis["resume_id"]})
        resume_info = {
            "id": analysis["resume_id"],
            "candidate_name": resume["candidate_name"] if resume else "未知",
            "position": resume["position"] if resume else "未知",
        }
        
        result.append({
            "id": str(analysis["_id"]),
            "resume": resume_info,
            "requirements": analysis["requirements"],
            "result": analysis["result"],
            "user_id": analysis["user_id"],
            "created_at": analysis["created_at"]
        })
    
    return result

@router.get("/{analysis_id}", response_model=Dict[str, Any])
async def get_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    获取分析结果详情
    """
    # 查询分析结果
    analysis = await db["analyses"].find_one({"_id": analysis_id})
    if not analysis:
        raise HTTPException(status_code=404, detail="分析结果不存在")
    
    # 检查权限（只有结果的所有者才能查看）
    if analysis["user_id"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="没有权限查看此分析结果")
    
    # 获取简历信息
    resume = await db["resumes"].find_one({"_id": analysis["resume_id"]})
    resume_info = {
        "id": analysis["resume_id"],
        "candidate_name": resume["candidate_name"] if resume else "未知",
        "position": resume["position"] if resume else "未知",
        "content": resume["content"] if resume else ""
    }
    
    return {
        "id": str(analysis["_id"]),
        "resume": resume_info,
        "requirements": analysis["requirements"],
        "result": analysis["result"],
        "user_id": analysis["user_id"],
        "created_at": analysis["created_at"]
    }

@router.get("/statistics/summary", response_model=Dict[str, Any])
async def get_analysis_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    获取分析统计摘要
    """
    # 构建查询条件
    query = {"user_id": current_user["_id"]}
    if start_date or end_date:
        query["created_at"] = {}
        if start_date:
            query["created_at"]["$gte"] = start_date
        if end_date:
            query["created_at"]["$lte"] = end_date
    
    # 获取总分析数
    total_analyses = await db["analyses"].count_documents(query)
    
    # 获取匹配的简历数量（匹配分数大于等于70分）
    match_query = {**query, "result.match_score": {"$gte": 70}}
    matched_resumes = await db["analyses"].count_documents(match_query)
    
    # 获取按职位分组的简历数量
    pipeline = [
        {"$match": query},
        {"$lookup": {
            "from": "resumes",
            "localField": "resume_id",
            "foreignField": "_id",
            "as": "resume"
        }},
        {"$unwind": "$resume"},
        {"$group": {
            "_id": "$resume.position",
            "count": {"$sum": 1},
            "avg_score": {"$avg": "$result.match_score"}
        }}
    ]
    
    position_stats_cursor = db["analyses"].aggregate(pipeline)
    position_stats = await position_stats_cursor.to_list(length=100)
    
    return {
        "total_analyses": total_analyses,
        "matched_resumes": matched_resumes,
        "match_rate": matched_resumes / total_analyses if total_analyses > 0 else 0,
        "position_statistics": position_stats
    } 
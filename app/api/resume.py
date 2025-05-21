from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
import os
from bson.objectid import ObjectId

from app.services.parser.resume_parser import default_parser
from app.services.analyzer.resume_analyzer import default_analyzer
from app.services.notifier.notification_service import notification_service
from app.core.config import settings
from app.models.database import get_database
from app.schemas.resume import ResumeCreate, ResumeResponse, ResumeAnalysisRequest

router = APIRouter(
    prefix="/api/v1/resumes",
    tags=["resumes"],
    responses={404: {"description": "Not found"}},
)

@router.post("/upload", response_model=ResumeResponse)
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    candidate_name: str = Form(...),
    position: str = Form(...),
    db = Depends(get_database)
):
    """
    上传简历文件
    """
    # 检查文件类型
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext[1:] not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {file_ext}")
    
    # 保存文件
    try:
        file_path = await default_parser.save_upload_file(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存文件失败: {str(e)}")
    
    # 解析简历
    try:
        parsed_resume = default_parser.parse_resume(file_path)
    except Exception as e:
        # 清理文件
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"解析简历失败: {str(e)}")
    
    # 准备存储数据
    resume_id = str(ObjectId())
    resume_data = {
        "_id": resume_id,
        "candidate_name": candidate_name,
        "position": position,
        "file_path": file_path,
        "file_name": file.filename,
        "file_type": file_ext[1:],
        "content": parsed_resume["content"],
        "uploaded_at": datetime.now(),
        "status": "pending",  # pending, analyzed, matched
    }
    
    # 存储到数据库
    try:
        await db["resumes"].insert_one(resume_data)
    except Exception as e:
        # 清理文件
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"保存简历数据失败: {str(e)}")
    
    # 响应结果
    return {
        "id": resume_id,
        "candidate_name": candidate_name,
        "position": position,
        "file_name": file.filename,
        "file_type": file_ext[1:],
        "uploaded_at": resume_data["uploaded_at"],
        "message": "简历上传成功，等待分析"
    }

@router.post("/{resume_id}/analyze", response_model=Dict[str, Any])
async def analyze_resume(
    resume_id: str,
    analysis_request: ResumeAnalysisRequest,
    db = Depends(get_database)
):
    """
    根据特定要求分析简历
    """
    # 查找简历
    resume = await db["resumes"].find_one({"_id": resume_id})
    if not resume:
        raise HTTPException(status_code=404, detail="找不到指定的简历")
    
    # 分析简历
    try:
        analysis_result = await default_analyzer.analyze_resume(
            resume_content=resume["content"],
            requirements=analysis_request.requirements.dict()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析简历失败: {str(e)}")
    
    # 将分析结果保存到数据库
    analysis_data = {
        "resume_id": resume_id,
        "requirements": analysis_request.requirements.dict(),
        "result": analysis_result.dict(),
        "user_id": analysis_request.user_id,
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
        user = await db["users"].find_one({"_id": analysis_request.user_id})
        user_email = user.get("email") if user else None
        
        # 发送通知
        await notification_service.notify_resume_match(
            user_id=analysis_request.user_id,
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
    
    # 返回分析结果
    return {
        "resume_id": resume_id,
        "candidate_name": resume["candidate_name"],
        "analysis_result": analysis_result.dict(),
        "message": "简历分析完成"
    }

@router.get("/", response_model=List[ResumeResponse])
async def list_resumes(
    status: Optional[str] = None,
    limit: int = 20,
    skip: int = 0,
    db = Depends(get_database)
):
    """
    获取简历列表
    """
    # 构建查询条件
    query = {}
    if status:
        query["status"] = status
    
    # 查询数据库
    cursor = db["resumes"].find(query).skip(skip).limit(limit).sort("uploaded_at", -1)
    resumes = await cursor.to_list(length=limit)
    
    # 格式化返回结果
    result = []
    for resume in resumes:
        result.append({
            "id": resume["_id"],
            "candidate_name": resume["candidate_name"],
            "position": resume["position"],
            "file_name": resume["file_name"],
            "file_type": resume["file_type"],
            "uploaded_at": resume["uploaded_at"],
            "status": resume["status"],
            "match_score": resume.get("match_score", None)
        })
    
    return result

@router.get("/{resume_id}", response_model=Dict[str, Any])
async def get_resume(
    resume_id: str,
    db = Depends(get_database)
):
    """
    获取简历详情
    """
    # 查询简历
    resume = await db["resumes"].find_one({"_id": resume_id})
    if not resume:
        raise HTTPException(status_code=404, detail="找不到指定的简历")
    
    # 查询最新的分析结果
    analysis = await db["analyses"].find_one(
        {"resume_id": resume_id},
        sort=[("created_at", -1)]
    )
    
    # 格式化返回结果
    result = {
        "id": resume["_id"],
        "candidate_name": resume["candidate_name"],
        "position": resume["position"],
        "file_name": resume["file_name"],
        "file_type": resume["file_type"],
        "uploaded_at": resume["uploaded_at"],
        "status": resume["status"],
        "content": resume["content"],
        "analysis_result": analysis["result"] if analysis else None
    }
    
    return result 
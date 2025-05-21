from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any, List, Optional
from datetime import datetime
from bson.objectid import ObjectId
import logging

from app.models.database import get_database
from app.schemas.requirements import RequirementCreate, RequirementResponse, RequirementUpdate

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/requirements",
    tags=["requirements"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=RequirementResponse)
async def create_requirement(
    requirement: RequirementCreate,
    db = Depends(get_database)
):
    """
    创建新的职位要求
    """
    requirement_id = str(ObjectId())
    
    requirement_data = {
        "_id": requirement_id,
        "job_title": requirement.job_title,
        "experience_years": requirement.experience_years,
        "education": requirement.education,
        "skills": requirement.skills,
        "description": requirement.description,
        "user_id": requirement.user_id,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    
    try:
        await db["requirements"].insert_one(requirement_data)
    except Exception as e:
        logger.error(f"创建职位要求失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建职位要求失败: {str(e)}")
    
    return {
        "id": requirement_id,
        **requirement.dict(),
        "created_at": requirement_data["created_at"],
        "updated_at": requirement_data["updated_at"],
    }

@router.get("/", response_model=List[RequirementResponse])
async def list_requirements(
    user_id: Optional[str] = None,
    job_title: Optional[str] = None,
    limit: int = 20,
    skip: int = 0,
    db = Depends(get_database)
):
    """
    获取职位要求列表
    """
    # 构建查询条件
    query = {}
    if user_id:
        query["user_id"] = user_id
    if job_title:
        query["job_title"] = {"$regex": job_title, "$options": "i"}  # 不区分大小写的搜索
    
    # 查询数据库
    cursor = db["requirements"].find(query).skip(skip).limit(limit).sort("created_at", -1)
    requirements = await cursor.to_list(length=limit)
    
    # 格式化返回结果
    result = []
    for req in requirements:
        result.append({
            "id": req["_id"],
            "job_title": req["job_title"],
            "experience_years": req["experience_years"],
            "education": req["education"],
            "skills": req["skills"],
            "description": req["description"],
            "user_id": req["user_id"],
            "created_at": req["created_at"],
            "updated_at": req["updated_at"],
        })
    
    return result

@router.get("/{requirement_id}", response_model=RequirementResponse)
async def get_requirement(
    requirement_id: str,
    db = Depends(get_database)
):
    """
    获取职位要求详情
    """
    requirement = await db["requirements"].find_one({"_id": requirement_id})
    if not requirement:
        raise HTTPException(status_code=404, detail="职位要求不存在")
    
    return {
        "id": requirement["_id"],
        "job_title": requirement["job_title"],
        "experience_years": requirement["experience_years"],
        "education": requirement["education"],
        "skills": requirement["skills"],
        "description": requirement["description"],
        "user_id": requirement["user_id"],
        "created_at": requirement["created_at"],
        "updated_at": requirement["updated_at"],
    }

@router.put("/{requirement_id}", response_model=RequirementResponse)
async def update_requirement(
    requirement_id: str,
    requirement: RequirementUpdate,
    db = Depends(get_database)
):
    """
    更新职位要求
    """
    # 检查是否存在
    existing = await db["requirements"].find_one({"_id": requirement_id})
    if not existing:
        raise HTTPException(status_code=404, detail="职位要求不存在")
    
    # 准备更新数据
    update_data = requirement.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.now()
    
    # 更新数据库
    try:
        await db["requirements"].update_one(
            {"_id": requirement_id},
            {"$set": update_data}
        )
    except Exception as e:
        logger.error(f"更新职位要求失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新职位要求失败: {str(e)}")
    
    # 获取更新后的数据
    updated_requirement = await db["requirements"].find_one({"_id": requirement_id})
    
    return {
        "id": updated_requirement["_id"],
        "job_title": updated_requirement["job_title"],
        "experience_years": updated_requirement["experience_years"],
        "education": updated_requirement["education"],
        "skills": updated_requirement["skills"],
        "description": updated_requirement["description"],
        "user_id": updated_requirement["user_id"],
        "created_at": updated_requirement["created_at"],
        "updated_at": updated_requirement["updated_at"],
    }

@router.delete("/{requirement_id}")
async def delete_requirement(
    requirement_id: str,
    db = Depends(get_database)
):
    """
    删除职位要求
    """
    # 检查是否存在
    existing = await db["requirements"].find_one({"_id": requirement_id})
    if not existing:
        raise HTTPException(status_code=404, detail="职位要求不存在")
    
    # 删除数据
    try:
        await db["requirements"].delete_one({"_id": requirement_id})
    except Exception as e:
        logger.error(f"删除职位要求失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除职位要求失败: {str(e)}")
    
    return {"message": "职位要求已删除"} 
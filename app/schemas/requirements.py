from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class SkillRequirement(BaseModel):
    """技能要求模型"""
    name: str = Field(..., description="技能名称")
    level: str = Field(..., description="要求的水平，如'精通'、'熟练'")

class RequirementBase(BaseModel):
    """职位要求基础模型"""
    job_title: str = Field(..., description="职位名称")
    experience_years: int = Field(..., description="所需工作经验年限")
    education: str = Field(..., description="教育背景要求")
    skills: List[Dict[str, Any]] = Field(..., description="技能要求")
    description: Optional[str] = Field(None, description="职位描述")

class RequirementCreate(RequirementBase):
    """创建职位要求的请求体"""
    user_id: str = Field(..., description="用户ID")
    
    class Config:
        schema_extra = {
            "example": {
                "job_title": "资深前端开发工程师",
                "experience_years": 5,
                "education": "本科及以上",
                "skills": [
                    {"name": "Vue", "level": "精通"},
                    {"name": "JavaScript", "level": "精通"},
                    {"name": "TypeScript", "level": "熟练"}
                ],
                "description": "负责公司前端架构设计与实现，参与核心产品开发",
                "user_id": "60d5ec9f7c213e1c3c3d89c1"
            }
        }

class RequirementUpdate(BaseModel):
    """更新职位要求的请求体"""
    job_title: Optional[str] = None
    experience_years: Optional[int] = None
    education: Optional[str] = None
    skills: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "job_title": "高级前端开发工程师",
                "experience_years": 4,
                "skills": [
                    {"name": "Vue", "level": "精通"},
                    {"name": "React", "level": "熟练"}
                ]
            }
        }

class RequirementResponse(RequirementBase):
    """职位要求响应模型"""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "id": "60d5ec9f7c213e1c3c3d89c3",
                "job_title": "资深前端开发工程师",
                "experience_years": 5,
                "education": "本科及以上",
                "skills": [
                    {"name": "Vue", "level": "精通"},
                    {"name": "JavaScript", "level": "精通"},
                    {"name": "TypeScript", "level": "熟练"}
                ],
                "description": "负责公司前端架构设计与实现，参与核心产品开发",
                "user_id": "60d5ec9f7c213e1c3c3d89c1",
                "created_at": "2023-06-25T08:30:00",
                "updated_at": "2023-06-25T08:30:00"
            }
        } 
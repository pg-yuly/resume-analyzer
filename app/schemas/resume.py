from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class ResumeCreate(BaseModel):
    """创建简历的请求体"""
    candidate_name: str = Field(..., description="候选人姓名")
    position: str = Field(..., description="应聘职位")
    
    class Config:
        schema_extra = {
            "example": {
                "candidate_name": "张三",
                "position": "前端开发工程师"
            }
        }

class ResumeResponse(BaseModel):
    """简历响应模型"""
    id: str
    candidate_name: str
    position: str
    file_name: str
    file_type: str
    uploaded_at: datetime
    status: Optional[str] = None
    match_score: Optional[float] = None
    message: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": "60d5ec9f7c213e1c3c3d89c2",
                "candidate_name": "张三",
                "position": "前端开发工程师",
                "file_name": "张三-简历.pdf",
                "file_type": "pdf",
                "uploaded_at": "2023-06-25T08:30:00",
                "status": "matched",
                "match_score": 85.5,
                "message": "简历上传成功，等待分析"
            }
        }

class RequirementsModel(BaseModel):
    """职位要求模型"""
    id: Optional[str] = None
    job_title: str = Field(..., description="职位名称")
    experience_years: int = Field(..., description="所需工作经验年限")
    education: str = Field(..., description="教育背景要求")
    skills: List[Dict[str, Any]] = Field(..., description="技能要求")
    description: Optional[str] = Field(None, description="职位描述")
    
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
                "description": "负责公司前端架构设计与实现，参与核心产品开发"
            }
        }

class ResumeAnalysisRequest(BaseModel):
    """分析简历的请求体"""
    user_id: str = Field(..., description="用户ID")
    requirements: RequirementsModel = Field(..., description="职位要求")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "60d5ec9f7c213e1c3c3d89c1",
                "requirements": {
                    "job_title": "资深前端开发工程师",
                    "experience_years": 5,
                    "education": "本科及以上",
                    "skills": [
                        {"name": "Vue", "level": "精通"},
                        {"name": "JavaScript", "level": "精通"},
                        {"name": "TypeScript", "level": "熟练"}
                    ],
                    "description": "负责公司前端架构设计与实现，参与核心产品开发"
                }
            }
        } 
from pydantic import BaseModel, EmailStr, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class UserBase(BaseModel):
    """用户基础模型"""
    email: EmailStr = Field(..., description="用户邮箱")
    username: str = Field(..., description="用户名")
    full_name: Optional[str] = Field(None, description="用户全名")
    company: Optional[str] = Field(None, description="所属公司")
    position: Optional[str] = Field(None, description="职位")

class UserCreate(UserBase):
    """创建用户的请求体"""
    password: str = Field(..., description="密码", min_length=8)
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "testuser",
                "full_name": "张三",
                "company": "ABC科技有限公司",
                "position": "HR经理",
                "password": "securepassword"
            }
        }

class UserUpdate(BaseModel):
    """更新用户的请求体"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    password: Optional[str] = Field(None, description="密码", min_length=8)
    
    class Config:
        schema_extra = {
            "example": {
                "full_name": "李四",
                "company": "XYZ科技有限公司",
                "position": "HR总监"
            }
        }

class UserResponse(UserBase):
    """用户响应模型"""
    id: str
    is_active: bool
    created_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "id": "60d5ec9f7c213e1c3c3d89c1",
                "email": "user@example.com",
                "username": "testuser",
                "full_name": "张三",
                "company": "ABC科技有限公司",
                "position": "HR经理",
                "is_active": True,
                "created_at": "2023-06-25T08:30:00"
            }
        }

class Token(BaseModel):
    """令牌响应模型"""
    access_token: str
    token_type: str
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }

class TokenData(BaseModel):
    """令牌数据"""
    user_id: Optional[str] = None 
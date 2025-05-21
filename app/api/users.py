from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import EmailStr
from passlib.context import CryptContext
import jwt
from jwt.exceptions import PyJWTError
from bson.objectid import ObjectId
import logging
import os

from app.models.database import get_database
from app.schemas.user import UserCreate, UserResponse, UserUpdate, Token
from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 密码处理
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT设置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")  # 从环境变量中获取
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/token")

router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

# 帮助函数
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_database)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except PyJWTError:
        raise credentials_exception
    user = await db["users"].find_one({"_id": user_id})
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=UserResponse)
async def register_user(
    user: UserCreate,
    db = Depends(get_database)
):
    """
    注册新用户
    """
    # 检查邮箱是否已存在
    existing_user = await db["users"].find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="该邮箱已注册")
    
    # 生成用户ID和密码哈希
    user_id = str(ObjectId())
    hashed_password = get_password_hash(user.password)
    
    # 准备用户数据
    user_data = {
        "_id": user_id,
        "email": user.email,
        "username": user.username,
        "hashed_password": hashed_password,
        "full_name": user.full_name,
        "company": user.company,
        "position": user.position,
        "is_active": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    
    # 保存到数据库
    try:
        await db["users"].insert_one(user_data)
    except Exception as e:
        logger.error(f"用户注册失败: {e}")
        raise HTTPException(status_code=500, detail=f"用户注册失败: {str(e)}")
    
    # 返回用户信息（不包含密码）
    return {
        "id": user_id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "company": user.company,
        "position": user.position,
        "is_active": True,
        "created_at": user_data["created_at"],
    }

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db = Depends(get_database)
):
    """
    用户登录获取令牌
    """
    # 查找用户
    user = await db["users"].find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=401,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["_id"]},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: dict = Depends(get_current_user)
):
    """
    获取当前用户信息
    """
    return {
        "id": current_user["_id"],
        "email": current_user["email"],
        "username": current_user["username"],
        "full_name": current_user["full_name"],
        "company": current_user.get("company"),
        "position": current_user.get("position"),
        "is_active": current_user["is_active"],
        "created_at": current_user["created_at"],
    }

@router.put("/me", response_model=UserResponse)
async def update_user_me(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    更新当前用户信息
    """
    # 准备更新数据
    update_data = user_update.dict(exclude_unset=True, exclude={"password"})
    
    # 如果更新密码
    if user_update.password:
        update_data["hashed_password"] = get_password_hash(user_update.password)
    
    update_data["updated_at"] = datetime.now()
    
    # 更新数据库
    try:
        await db["users"].update_one(
            {"_id": current_user["_id"]},
            {"$set": update_data}
        )
    except Exception as e:
        logger.error(f"更新用户信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新用户信息失败: {str(e)}")
    
    # 获取更新后的用户信息
    updated_user = await db["users"].find_one({"_id": current_user["_id"]})
    
    return {
        "id": updated_user["_id"],
        "email": updated_user["email"],
        "username": updated_user["username"],
        "full_name": updated_user["full_name"],
        "company": updated_user.get("company"),
        "position": updated_user.get("position"),
        "is_active": updated_user["is_active"],
        "created_at": updated_user["created_at"],
    } 
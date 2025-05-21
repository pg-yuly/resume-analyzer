from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from app.services.notifier.notification_service import notification_service
from typing import Optional
from app.api.users import get_current_user
import logging
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ws",
    tags=["websocket"],
)

@router.websocket("/notifications/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, token: Optional[str] = None):
    """
    WebSocket连接，用于实时通知
    """
    # 验证用户访问权限（简单方式，实际应用中应更严格）
    if not token:
        await websocket.close(code=1008)
        return
    
    try:
        # 接受WebSocket连接
        await notification_service.connection_manager.connect(websocket, user_id)
        
        # 发送欢迎消息
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "成功连接到通知服务"
        }))
        
        try:
            # 保持连接并处理消息
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 处理收到的消息（此处可以根据需求扩展功能）
                await websocket.send_text(json.dumps({
                    "type": "message_received",
                    "message": f"收到消息: {message}"
                }))
                
        except WebSocketDisconnect:
            # 断开连接时移除
            notification_service.connection_manager.disconnect(websocket, user_id)
            logger.info(f"用户 {user_id} 断开WebSocket连接")
            
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        await websocket.close(code=1011)

@router.get("/notification-test/{user_id}")
async def test_notification(
    user_id: str,
    message: str = "这是一条测试通知"
):
    """
    测试发送通知的API
    """
    await notification_service.connection_manager.send_personal_message(
        {
            "type": "test_notification",
            "message": message,
            "timestamp": "2023-06-25T08:30:00"
        },
        user_id
    )
    return {"message": f"通知已发送到用户 {user_id}"}

@router.get("/broadcast-test")
async def test_broadcast(
    message: str = "这是一条广播通知"
):
    """
    测试广播通知的API
    """
    await notification_service.connection_manager.broadcast(
        {
            "type": "broadcast",
            "message": message,
            "timestamp": "2023-06-25T08:30:00"
        }
    )
    return {"message": "广播通知已发送"} 
import logging
from typing import Dict, Any, List, Optional, Union
from fastapi import WebSocket, WebSocketDisconnect
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.core.config import settings
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 活动连接
        self.active_connections: Dict[str, List[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str):
        """建立WebSocket连接"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"用户 {user_id} 建立WebSocket连接，当前连接数: {len(self.active_connections[user_id])}")
        
    def disconnect(self, websocket: WebSocket, user_id: str):
        """断开WebSocket连接"""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            logger.info(f"用户 {user_id} 断开WebSocket连接，剩余连接数: {len(self.active_connections[user_id])}")
            
    async def send_personal_message(self, message: Union[str, Dict], user_id: str):
        """向指定用户发送消息"""
        if user_id not in self.active_connections:
            logger.warning(f"用户 {user_id} 没有活动连接，无法发送消息")
            return
            
        # 将字典转换为JSON字符串
        if isinstance(message, dict):
            message = json.dumps(message, ensure_ascii=False)
            
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"发送WebSocket消息失败: {e}")
                
    async def broadcast(self, message: Union[str, Dict]):
        """广播消息给所有用户"""
        # 将字典转换为JSON字符串
        if isinstance(message, dict):
            message = json.dumps(message, ensure_ascii=False)
            
        for user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"广播WebSocket消息失败: {e}")


class EmailNotifier:
    """邮件通知服务"""
    
    def __init__(self):
        """初始化邮件配置"""
        self.conf = ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
        )
        self.fastmail = FastMail(self.conf)
        
    async def send_resume_match_notification(
        self, 
        recipient_email: str, 
        resume_id: str,
        candidate_name: str,
        position_name: str,
        match_score: float,
        analysis_summary: str
    ):
        """
        发送简历匹配通知邮件
        
        Args:
            recipient_email: 接收者邮箱
            resume_id: 简历ID
            candidate_name: 候选人姓名
            position_name: 职位名称
            match_score: 匹配分数
            analysis_summary: 分析摘要
        """
        
        # 构建邮件内容
        html_content = f"""
        <html>
            <body>
                <h2>简历匹配通知</h2>
                <p>尊敬的用户：</p>
                <p>我们发现一份符合您要求的简历：</p>
                <ul>
                    <li><strong>候选人</strong>: {candidate_name}</li>
                    <li><strong>职位</strong>: {position_name}</li>
                    <li><strong>匹配度</strong>: {match_score:.1f}%</li>
                </ul>
                <p><strong>分析摘要</strong>:</p>
                <p>{analysis_summary}</p>
                <p>请登录系统查看详情。</p>
                <p>此致，</p>
                <p>智能简历筛选系统</p>
            </body>
        </html>
        """
        
        message = MessageSchema(
            subject=f"简历匹配通知: {candidate_name} - {match_score:.1f}% 匹配",
            recipients=[recipient_email],
            body=html_content,
            subtype="html"
        )
        
        try:
            await self.fastmail.send_message(message)
            logger.info(f"成功发送匹配通知邮件到 {recipient_email}")
            return True
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False


class NotificationService:
    """通知服务，集成WebSocket和邮件通知"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.email_notifier = EmailNotifier()
        
    async def notify_resume_match(
        self,
        user_id: str,
        user_email: Optional[str],
        resume_data: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ):
        """
        通知用户匹配到的简历
        
        Args:
            user_id: 用户ID
            user_email: 用户邮箱（可选）
            resume_data: 简历数据
            analysis_result: 分析结果
        """
        
        # 准备通知数据
        notification_data = {
            "type": "resume_match",
            "resume_id": resume_data.get("id", ""),
            "candidate_name": resume_data.get("candidate_name", "未知候选人"),
            "position": resume_data.get("position", "未指定职位"),
            "match_score": analysis_result.get("match_score", 0),
            "analysis_summary": analysis_result.get("summary", ""),
            "timestamp": resume_data.get("timestamp", "")
        }
        
        # WebSocket通知
        await self.connection_manager.send_personal_message(
            notification_data,
            user_id
        )
        
        # 邮件通知（如果提供了邮箱）
        if user_email:
            await self.email_notifier.send_resume_match_notification(
                recipient_email=user_email,
                resume_id=notification_data["resume_id"],
                candidate_name=notification_data["candidate_name"],
                position_name=notification_data["position"],
                match_score=notification_data["match_score"],
                analysis_summary=notification_data["analysis_summary"]
            )

# 创建默认通知服务实例
notification_service = NotificationService() 
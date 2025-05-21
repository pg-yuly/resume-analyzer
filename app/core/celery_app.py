from celery import Celery
import os
from app.core.config import settings
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Redis URL，包含密码和DB选择
def get_redis_url(db_number):
    # 构建Redis URL，如果有密码则添加
    if settings.REDIS_PASSWORD:
        return f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{db_number}"
    else:
        return f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{db_number}"

# 创建Celery实例
try:
    celery_app = Celery(
        "resume_analyzer",
        broker=get_redis_url(settings.REDIS_DB),  # 使用环境变量中配置的DB
        backend=get_redis_url(settings.REDIS_DB + 1)  # 结果后端使用下一个DB
    )

    # 加载任务模块
    celery_app.conf.imports = [
        "app.tasks.resume_tasks",
    ]

    # 配置Celery
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="Asia/Shanghai",
        enable_utc=False,
        task_track_started=True,
        worker_prefetch_multiplier=1,  # 一次只处理一个任务，避免一个worker占用过多资源
        task_acks_late=True,  # 任务完成后再确认，这样如果worker中断任务会重新分配
    )

    # 创建任务队列
    celery_app.conf.task_routes = {
        "app.tasks.resume_tasks.analyze_resume_task": {"queue": "resume_analysis"},
    }

    # 配置任务默认过期时间（30分钟）
    celery_app.conf.task_soft_time_limit = 1800
    celery_app.conf.task_time_limit = 1800

except Exception as e:
    logger.error(f"初始化Celery时出错: {e}")
    # 创建一个哑Celery实例，避免项目无法启动
    celery_app = Celery()
    celery_app.conf.task_always_eager = True  # 本地执行任务而不是发送到队列

# 初始化Celery日志
@celery_app.task
def test_celery():
    logger.info("Celery任务测试成功!")
    return "Celery任务测试成功!" 
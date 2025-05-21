import uvicorn
import argparse
import os
import sys
import traceback
from dotenv import load_dotenv
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
try:
    load_dotenv()
    logger.info("环境变量加载成功")
except Exception as e:
    logger.error(f"加载.env文件失败: {e}")

def main():
    try:
        parser = argparse.ArgumentParser(description="启动智能简历筛选系统")
        parser.add_argument(
            "--host", 
            type=str, 
            default=os.getenv("SERVER_HOST", "0.0.0.0"),
            help="服务主机地址"
        )
        
        parser.add_argument(
            "--port", 
            type=int, 
            default=int(os.getenv("SERVER_PORT", "8000")),
            help="服务端口"
        )
        
        parser.add_argument(
            "--reload", 
            action="store_true",
            default=os.getenv("DEBUG", "False").lower() == "true",
            help="是否启用自动重载（开发模式）"
        )
        
        args = parser.parse_args()
        
        print(f"启动应用，访问地址: http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port}")
        print(f"API文档地址: http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port}/docs")
        
        # 尝试导入主应用模块
        try:
            import app.main
            logger.info("成功导入app.main模块")
        except ImportError as e:
            logger.error(f"导入app.main模块失败，请检查依赖是否安装: {e}")
            traceback.print_exc()
            sys.exit(1)
        
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=os.getenv("LOG_LEVEL", "info").lower()
        )
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 
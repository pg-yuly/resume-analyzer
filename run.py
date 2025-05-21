import uvicorn
import argparse
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def main():
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
    
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )

if __name__ == "__main__":
    main() 
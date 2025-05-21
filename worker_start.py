import subprocess
import os
import sys
import argparse

def start_worker(queue_name=None, concurrency=2, loglevel="INFO"):
    """启动Celery worker"""
    command = [
        "celery", 
        "-A", 
        "app.core.celery_app", 
        "worker", 
        "--concurrency", 
        str(concurrency),
        "--loglevel", 
        loglevel
    ]
    
    # 如果指定了队列名称
    if queue_name:
        command.extend(["-Q", queue_name])
    
    # 执行命令启动worker
    print(f"启动Celery worker: {' '.join(command)}")
    subprocess.run(command)

def start_flower(port=5555, loglevel="INFO"):
    """启动Flower监控"""
    command = [
        "celery", 
        "-A", 
        "app.core.celery_app", 
        "flower", 
        "--port", 
        str(port),
        "--loglevel", 
        loglevel
    ]
    
    # 执行命令启动Flower
    print(f"启动Flower监控: {' '.join(command)}")
    subprocess.run(command)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="启动Celery worker和Flower监控")
    
    parser.add_argument(
        "--queue", 
        type=str, 
        default="resume_analysis",
        help="指定要监听的队列名称"
    )
    
    parser.add_argument(
        "--concurrency", 
        type=int, 
        default=2,
        help="Worker并发数量"
    )
    
    parser.add_argument(
        "--flower", 
        action="store_true",
        help="是否启动Flower监控"
    )
    
    parser.add_argument(
        "--flower-port", 
        type=int, 
        default=5555,
        help="Flower监控端口"
    )
    
    parser.add_argument(
        "--loglevel", 
        type=str, 
        default="INFO",
        help="日志级别"
    )
    
    args = parser.parse_args()
    
    if args.flower:
        print("启动Flower监控...")
        start_flower(port=args.flower_port, loglevel=args.loglevel)
    else:
        print(f"启动Celery worker，队列: {args.queue}，并发: {args.concurrency}...")
        start_worker(queue_name=args.queue, concurrency=args.concurrency, loglevel=args.loglevel) 
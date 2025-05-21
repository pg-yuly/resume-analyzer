# 智能简历筛选系统

这是一个基于 AI 的简历筛选系统，可以根据用户指定的要求自动分析和筛选简历，并将符合条件的简历推送给用户。

## 功能特点

- 支持多种格式简历解析（PDF、HTML、DOCX 等）
- 自定义筛选条件（如工作经验年限、技能要求等）
- AI 驱动的智能匹配算法
- 实时通知匹配结果

## 技术栈

- **后端框架**: FastAPI (Python)
- **文档解析**:
  - PyPDF2/pdf2text (PDF 文档)
  - BeautifulSoup4 (HTML 文档)
- **AI 分析**:
  - LangChain 框架
  - OpenAI GPT 模型
- **数据库**:
  - MongoDB (存储简历和分析结果)
  - Redis (缓存和任务队列)
- **任务队列**: Celery (处理异步简历分析任务)
- **通知系统**:
  - WebSocket (实时通知)
  - 邮件服务
  - 可选的短信服务
- **前端** (可选):
  - Vue.js (用户界面)

## 项目结构

```
resume-analyzer/
├── app/
│   ├── api/                  # API路由
│   ├── core/                 # 核心配置和设置
│   ├── models/               # 数据模型
│   ├── services/
│   │   ├── parser/           # 简历解析服务
│   │   ├── analyzer/         # AI分析服务
│   │   └── notifier/         # 通知服务
│   ├── schemas/              # Pydantic模型
│   ├── tasks/                # Celery任务
│   └── utils/                # 工具函数
├── uploads/                  # 上传文件目录
├── tests/                    # 测试
├── .env.example              # 环境变量模板
├── .env                      # 环境变量（本地开发）
├── requirements.txt          # 依赖
├── run.py                    # 主应用启动脚本
└── worker_start.py           # Celery Worker启动脚本
```

## 安装和配置

1. 克隆仓库

```bash
git clone https://github.com/pg-yuly/resume-analyzer.git
cd resume-analyzer
```

2. 创建虚拟环境

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. 安装依赖

```bash
pip install -r requirements.txt
```

4. 设置环境变量

```bash
# 复制环境变量模板
cp .env.example .env
# 编辑.env文件，填写必要的配置（如OpenAI API密钥）
```

5. 启动 MongoDB 和 Redis

```bash
# 如果使用Docker
docker run -d -p 27017:27017 --name mongodb mongo
docker run -d -p 6379:6379 --name redis redis
```

## 运行应用

1. 启动主应用

```bash
python run.py
```

2. 启动 Celery Worker（用于异步任务处理）

```bash
python worker_start.py
```

3. （可选）启动 Flower 监控 Celery 任务

```bash
python worker_start.py --flower
```

## API 文档

启动应用后，可以通过以下 URL 访问 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 使用流程

1. 用户注册/登录 (`/api/v1/users/register`, `/api/v1/users/token`)
2. 创建职位要求 (`/api/v1/requirements`)
3. 上传简历 (`/api/v1/resumes/upload`)
4. 分析简历 (`/api/v1/resumes/{resume_id}/analyze`)
5. 接收匹配通知 (WebSocket 或邮件)

## 贡献指南

欢迎贡献代码或提出问题！请遵循以下步骤：

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

MIT

## 致谢

- [OpenAI](https://openai.com/) - GPT 模型
- [LangChain](https://langchain.readthedocs.io/) - AI 应用框架
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架

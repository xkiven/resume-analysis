# AI 智能简历分析系统

基于阿里云 Serverless + 通义千问 AI 的智能简历解析与匹配服务。

## 功能特性

- 📄 PDF 简历上传与解析
- 🤖 AI 智能提取关键信息（姓名、电话、邮箱、技能等）
- 🎯 简历与岗位匹配度分析
- ⚡ Redis 缓存支持
- 🌐 RESTful API 设计

## 技术架构

| 技术 | 说明 |
|------|------|
| 后端框架 | Flask + 阿里云函数计算 |
| AI 模型 | 阿里云 DashScope (通义千问) |
| PDF 解析 | pdfplumber |
| 缓存 | Redis |
| 前端 | HTML/CSS/JS |

## 项目结构

```
resume-analysis/
├── backend/
│   ├── src/
│   │   ├── main.py         # Flask 应用入口
│   │   ├── parser.py       # PDF 解析模块
│   │   ├── extractor.py    # AI 信息提取
│   │   ├── matcher.py      # 岗位匹配
│   │   └── cache.py        # Redis 缓存
│   ├── tests/
│   ├── serverless.yml      # 阿里云 FC 配置
│   └── requirements.txt   # Python 依赖
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并配置：

```bash
DASHSCOPE_API_KEY=your_api_key_here
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 3. 启动本地服务

```bash
cd backend/src
python main.py
```

服务将在 http://localhost:5000 启动。

### 4. API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/resume/upload` | POST | 上传 PDF 简历 |
| `/api/resume/extract` | POST | 提取简历信息 |
| `/api/resume/match` | POST | 岗位匹配评分 |

## API 使用示例

### 上传简历

```bash
curl -X POST http://localhost:5000/api/resume/upload \
  -F "file=@resume.pdf"
```

响应：
```json
{
  "success": true,
  "data": {
    "resume_id": "uuid",
    "text": "...",
    "status": "success"
  }
}
```

### 提取信息

```bash
curl -X POST http://localhost:5000/api/resume/extract \
  -H "Content-Type: application/json" \
  -d '{"resume_id": "uuid"}'
```

### 岗位匹配

```bash
curl -X POST http://localhost:5000/api/resume/match \
  -H "Content-Type: application/json" \
  -d '{"resume_id": "uuid", "job_description": "Python开发工程师..."}'
```

## 部署到阿里云

### 1. 安装 Serverless CLI

```bash
npm install -g serverless
```

### 2. 配置阿里云凭证

```bash
serverless config --provider aliyun --access-key-id YOUR_ACCESS_KEY --access-key-secret YOUR_ACCESS_KEY_SECRET
```

### 3. 部署

```bash
cd backend
serverless deploy
```

## 前端部署

前端文件位于 `frontend/` 目录，可以部署到任何静态托管服务：

```bash
# GitHub Pages
# 1. 创建 GitHub 仓库
# 2. 推送 frontend 目录
# 3. 在仓库设置中启用 GitHub Pages
```

## 注意事项

1. 需要有效的阿里云 DashScope API Key
2. PDF 文件大小限制为 10MB
3. 建议配置 Redis 以启用缓存功能

## License

MIT

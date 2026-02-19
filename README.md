# AI Dashboard

AI 驱动的个人管理 Dashboard。Agent 在后台持续工作，成果以卡片形式展示。

## 技术栈

- **后端**: Python 3.12+ / FastAPI / Jinja2
- **前端**: HTMX 2.x / Alpine.js / Tailwind CSS 4.x
- **Agent**: pi (CLI)
- **定时任务**: APScheduler

## 快速开始

### 1. 安装依赖

```bash
# Python 依赖 (使用 uv)
uv sync

# 前端依赖
cd frontend && pnpm install
```

### 2. 构建前端

```bash
cd frontend && pnpm build
```

### 3. 启动服务

```bash
# 开发模式
uvicorn app.main:app --reload

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. 启动定时任务（可选）

```bash
python -m scheduler.main
```

## 开发

### 前端开发

```bash
cd frontend
pnpm dev  # Vite 开发服务器
```

### 后端开发

```bash
uvicorn app.main:app --reload
```

### 手动触发 Agent

```bash
# 执行特定 skill
pi -p "检查新闻更新" --skill skills/news_hn.md

# 与 Dashboard 对话
pi -p "帮我添加一个待办事项：明天开会" --skill skills/_system.md
```

## 目录结构

```
ai-dashboard/
├── app/                  # FastAPI 后端
│   ├── main.py
│   ├── routes/
│   ├── services/
│   └── templates/
├── frontend/             # 前端资源 (pnpm)
├── scheduler/            # 定时任务
├── skills/               # Agent Skills
├── data/                 # 数据文件
│   ├── dashboard.json
│   └── tasks.json
└── static/               # 构建输出
```

## 文档

- [PLAN.md](PLAN.md) - 详细设计方案
- [docs/DESIGN.md](docs/DESIGN.md) - UI 设计规范

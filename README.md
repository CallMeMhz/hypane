# AI Dashboard

AI 驱动的个人 Dashboard。通过聊天创建和管理 Panel，数据持久化。

## 技术栈

- **后端**: Python 3.12+ / FastAPI / Jinja2
- **前端**: HTMX 2.x / Alpine.js / Tailwind CSS 4.x
- **Agent**: pi (CLI)
- **定时任务**: APScheduler

## 快速开始

```bash
# 1. 安装依赖
uv sync
cd frontend && pnpm install

# 2. 构建前端
cd frontend && pnpm build

# 3. 启动服务
uvicorn app.main:app --reload

# 4. 启动 scheduler（可选，用于定时采集）
python -m scheduler.panel_scheduler
```

访问 http://localhost:8000

## Panel 系统

每个 Panel 是独立目录：

```
data/panels/{panel_id}/
├── facade.html   # 外观 (HTML + Alpine.js)
├── data.json     # 数据和配置
└── handler.py    # 后端逻辑 (可选)
```

### Handler 模式

handler.py 支持两种触发：

```python
# HTTP 触发（用户交互）
async def handle_action(action: str, payload: dict, data: dict) -> dict:
    pass

# Scheduler 触发（定时采集）
async def collect(data: dict) -> dict:
    # 调用外部 API、爬取数据等
    return data
```

定时采集需要在 data.json 设置 `schedule`（cron）：
```json
{"schedule": "*/30 * * * *"}
```

### API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/panels` | 列出所有 panel |
| POST | `/api/panels` | 创建 panel |
| GET | `/api/panels/{id}` | 获取 panel |
| PATCH | `/api/panels/{id}` | 更新 panel |
| DELETE | `/api/panels/{id}` | 删除 panel |
| PATCH | `/api/panels/{id}/data` | 更新数据 |
| POST | `/api/panels/{id}/action` | 调用 handle_action |

### 创建 Panel 示例

```bash
curl -X POST http://localhost:8000/api/panels \
  -H "Content-Type: application/json" \
  -d '{
    "title": "天气",
    "desc": "显示实时天气",
    "icon": "cloud-sun",
    "headerColor": "cyan",
    "facade": "<div>...</div>",
    "handler": "async def collect(data): ...",
    "schedule": "*/30 * * * *",
    "size": "3x3"
  }'
```

## 目录结构

```
├── app/                  # FastAPI 后端
│   ├── routes/           # API 路由
│   ├── services/         # 业务逻辑
│   └── templates/        # Jinja2 模板
├── frontend/             # 前端 (Vite + Tailwind)
├── data/
│   ├── dashboard.json    # 布局信息
│   └── panels/           # Panel 数据目录
├── scheduler/            # 定时任务
│   └── panel_scheduler.py
├── skills/               # Agent Skills
└── extensions/           # pi 扩展
```

## 开发

```bash
# 前端开发 (热重载)
cd frontend && pnpm dev

# 后端开发
uvicorn app.main:app --reload

# 定时采集
python -m scheduler.panel_scheduler
```

## Skills

- `skills/_system.md` - 系统提示词
- `skills/panel_examples.md` - Panel 模板和示例

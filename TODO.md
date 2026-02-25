# Storage Binding Architecture

## 核心概念

```
Storage Layer (独立 JSON 对象)
  ┌─────────┐  ┌─────────┐  ┌─────────┐
  │   s1    │  │   s2    │  │   s3    │
  └────┬────┘  └─┬────┬──┘  └────┬────┘
       │         │    │          │
  ┌────┴────┐    │    │     ┌────┴────┐
  │ Panel A │────┘    └─────│ Panel B │
  │ [s1,s2] │               │ [s2,s3] │
  └─────────┘               └─────────┘

Task 绑定 storage，沙箱执行，独立于 Panel
```

## 数据模型

- **Storage**: 独立 JSON 对象，可被多个 Panel/Task 共享
- **Panel**: template (Jinja2) + handler (Python) + storage_ids
- **Task**: schedule (cron) + handler (Python) + storage_ids

---

## Implementation TODO

### Phase 1: 数据模型
- [x] 定义 Storage 模型 (`app/models/storage.py`)
- [x] 定义 Panel 模型 (`app/models/panel.py`)  
- [x] 定义 Task 模型 (`app/models/task.py`)
- [x] 数据持久化 (先用文件系统: `data/storages/`, `data/panels/`, `data/tasks/`)

### Phase 2: Storage 服务
- [x] Storage CRUD (`app/services/storage.py`)
- [x] Storage API (`app/routes/api_storage.py`)
  - GET /api/storages
  - GET /api/storages/{id}
  - POST /api/storages
  - PUT /api/storages/{id} (full replace)
  - PATCH /api/storages/{id} (shallow merge)
  - DELETE /api/storages/{id}

### Phase 3: Handler 沙箱
- [x] 定义 handler 协议 (`app/sandbox/protocol.py`)
  - `on_action(action, payload, storage)` for Panel
  - `on_schedule(storage)` for Task
- [x] 沙箱执行器接口 (`app/sandbox/executor.py`)
- [x] 简单实现 (受限 exec) (`app/sandbox/simple.py`)
- [x] Docker 实现预留 (`app/sandbox/docker.py`)

### Phase 4: Panel 重构
- [x] Panel 服务 v2 (`app/services/panels_v2.py`)
  - 加载 panel + 关联 storages
  - 渲染 template (Jinja2 + storage context)
- [x] Panel action API (`POST /api/panels/{id}/action`)
  - 加载 storages
  - 沙箱执行 handler
  - 保存 storages
  - 返回渲染后 HTML
- [x] Demo: todo-v2-demo panel with storage binding

### Phase 5: Task 重构
- [x] Task 服务 (`app/services/tasks_v2.py`)
- [x] Task 调度器 (`app/services/task_scheduler.py`) - APScheduler + 沙箱执行
- [x] Task API (`app/routes/api_tasks.py`)
  - GET /api/tasks
  - GET /api/tasks/{id}
  - POST /api/tasks
  - PATCH /api/tasks/{id}
  - PUT /api/tasks/{id}/handler
  - POST /api/tasks/{id}/run (manual trigger)
  - DELETE /api/tasks/{id}
- [x] Scheduler auto-start on app startup
- [x] Demo: weather-refresh task

### Phase 6: Agent 集成
- [x] 抽象 Agent 接口 (`app/agent/base.py`)
  - AgentMessage, ToolDefinition, ToolResult dataclasses
  - AgentBase abstract class with chat, chat_stream, run_with_tools
- [x] Pi-mono 实现 (`app/agent/pi_mono.py`)
- [x] 定义 Panel 工具集 (`app/agent/tools.py`)
  - `create_storage`
  - `update_storage`
  - `create_panel`
  - `update_panel_template`
  - `update_panel_handler`
  - `create_task`
- [x] Agent API (`app/routes/api_agent.py`)
  - POST /api/agent/chat
  - POST /api/agent/chat/simple

---

## 文件结构 (目标)

```
app/
├── models/
│   ├── storage.py
│   ├── panel.py
│   └── task.py
├── services/
│   ├── storage.py
│   ├── panels.py
│   └── tasks.py
├── sandbox/
│   ├── protocol.py
│   ├── executor.py
│   ├── simple.py
│   └── docker.py
├── agent/
│   ├── base.py
│   └── pi_mono.py
└── routes/
    ├── api_storage.py
    ├── api_panels.py
    └── api_tasks.py

data/
├── storages/
│   └── {storage_id}.json
├── panels/
│   └── {panel_id}/
│       ├── metadata.json
│       ├── template.html
│       └── handler.py
└── tasks/
    └── {task_id}/
        ├── metadata.json
        └── handler.py
```

---

## Notes

- 沙箱先用简单 exec 实现，预留 Docker 接口
- Agent 先用 pi-mono，关闭 coding agent，只注入自定义工具
- 定时任务为付费功能，沙箱执行

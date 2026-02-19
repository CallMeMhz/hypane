# 数据采集 Skill

当用户要求追踪某个数据源时（新闻、价格、天气等），使用此指南。

## 文件结构

```
data/
├── sources/           # 信源配置
│   └── {id}.json
├── history/           # 采集的历史数据
│   └── sources/{id}/
│       └── 2026-02-19T08.json
collectors/
├── presets.py         # 预置抓取能力
├── executor.py        # 信源执行器
└── generated/         # Agent 生成的采集器
    └── {id}.py
```

## 创建信源

### 1. 创建配置文件

`data/sources/{id}.json`:

```json
{
  "id": "hn-ai-news",
  "name": "HN AI 新闻",
  "description": "Hacker News 上关于 AI 的热帖，score > 50",
  "fetchConfig": {
    "type": "api",
    "url": "https://hacker-news.firebaseio.com/v0/topstories.json"
  },
  "schedule": "0 * * * *",
  "transform": "过滤标题包含 AI/LLM/GPT 的，取前 10 条",
  "enabled": true,
  "collector": null,
  "createdAt": "2026-02-19T08:00:00Z",
  "updatedAt": "2026-02-19T08:00:00Z"
}
```

### 2. 抓取类型

| type | 用途 | fetchConfig 字段 |
|------|------|------------------|
| `api` | JSON API | `url`, `method`, `headers`, `params` |
| `webpage` | 静态 HTML | `url`, `selectors` (CSS 选择器映射), `headers` |
| `browser` | 动态页面 | `url`, `script` (JS), `waitSelector` |

### 3. 简单信源 - 无需采集器

如果只需要简单抓取，不写 collector，executor 会用 presets 自动处理：

```json
{
  "fetchConfig": {
    "type": "webpage",
    "url": "https://github.com/trending",
    "selectors": {"repos": "article h2 a"}
  },
  "collector": null
}
```

### 4. 复杂信源 - 自定义采集器

需要过滤、转换、多步骤时，创建采集器。

`collectors/generated/{id}.py`:

```python
"""
{name} 采集器
{description}
"""
from collectors.presets import fetch_api_sync, fetch_webpage_sync
from app.services.history import write_history

def collect(source: dict):
    """
    采集并写入历史
    source: 信源配置 dict
    """
    config = source["fetchConfig"]
    
    # 抓取
    result = fetch_api_sync(config["url"])
    if not result["success"]:
        print(f"Fetch failed: {result['error']}")
        return
    
    # 转换/过滤
    data = result["data"]
    # ... 自定义处理逻辑 ...
    
    # 写入历史
    write_history(
        source=f"sources/{source['id']}",
        data=processed_data,
        granularity="hour"
    )
    print(f"Collected: {source['name']}")

if __name__ == "__main__":
    # 测试用
    import json
    with open(f"data/sources/{source_id}.json") as f:
        source = json.load(f)
    collect(source)
```

然后更新信源配置：
```json
{
  "collector": "collectors/generated/{id}.py"
}
```

## 预置抓取函数

`collectors/presets.py` 提供：

```python
# 同步版本（在采集器中使用）
fetch_api_sync(url, method="GET", headers=None, params=None, timeout=30)
fetch_webpage_sync(url, selectors=None, headers=None, timeout=30)
fetch_browser_sync(url, script=None, wait_selector=None, timeout=30000)

# 返回: {"success": bool, "data": Any, "error": str}
```

## 执行采集

```bash
# 测试执行
python -c "
from collectors.executor import run_source_sync
result = run_source_sync('hn-ai-news')
print(result)
"
```

## 定时调度

编辑 `data/tasks.json` 添加任务：

```json
{
  "id": "hn-ai-collect",
  "name": "HN AI 新闻采集",
  "schedule": "0 * * * *",
  "type": "collector",
  "collector": "source",
  "args": {"source_id": "hn-ai-news"},
  "enabled": true
}
```

## 历史数据

采集的数据自动写入 `data/history/sources/{id}/`，可通过卡片数据提供者读取。

## 示例：追踪 Hacker News AI 新闻

1. 创建 `data/sources/hn-ai.json`
2. 创建 `collectors/generated/hn-ai.py` 实现过滤逻辑
3. 添加到 `data/tasks.json`
4. 创建 news-bundle 卡片，读取历史数据展示

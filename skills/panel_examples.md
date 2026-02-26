# Panel 示例

每个 Panel 是一个独立目录：
- `facade.html` - 前端渲染（Tailwind + Alpine.js）
- `data.json` - 数据和配置
- `handler.py` - 后端逻辑（可选）

## Handler 模式

handler.py 支持以下入口函数：

```python
# 用户交互（POST /api/panels/{id}/action）
def on_action(action: str, payload: dict, storage: dict) -> None:
    """处理用户操作，直接修改 storage"""
    s = storage.get("my-storage-id", {})
    s["count"] = s.get("count", 0) + 1

# 初始化（安装时调用一次）
def on_init(storage: dict) -> None:
    """面板安装时初始化数据"""
    s = storage.get("my-storage-id", {})
    s["initialized"] = True
```

定时采集用独立的 Task（不在 panel handler 中），通过 `POST /api/tasks` 创建。

常用 cron 表达式：
- `*/5 * * * *` - 每 5 分钟
- `*/30 * * * *` - 每 30 分钟
- `0 * * * *` - 每小时
- `0 */6 * * *` - 每 6 小时
- `0 9 * * *` - 每天 9:00
- `0 9 * * 1` - 每周一 9:00

## 元数据字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `title` | ✓ | 显示标题 |
| `desc` | | 自然语言描述 |
| `icon` | ✓ | Lucide 图标名 |
| `headerColor` | ✓ | 颜色预设名 |
| `schedule` | | Cron 表达式（启用定时采集） |
| `minSize` | | 最小尺寸，如 `"3x2"` |

## 标题颜色预设

| 颜色名 | 色值 |
|--------|------|
| `gray` | #6b7280 |
| `red` | #b45b5b |
| `orange` | #b87333 |
| `amber` | #a68a4c |
| `green` | #5b8a5b |
| `teal` | #4a8a8a |
| `cyan` | #5b8a9a |
| `blue` | #5b7b9a |
| `indigo` | #6b6b9a |
| `purple` | #7a5b8a |
| `pink` | #8a5b7a |
| `rose` | #9a5b6b |

## 图标列表 (Lucide)

- `check-square` - 待办
- `hourglass` - 倒计时
- `bell` - 提醒
- `calendar` - 日历
- `cloud-sun` - 天气
- `coins` - 加密货币
- `newspaper` - 新闻
- `cookie` - 游戏
- `code` / `terminal` - 开发
- `box` - 默认

## API

- `GET /api/panels/{id}/data` - 获取数据
- `PATCH /api/panels/{id}/data` - 更新数据
- `POST /api/panels/{id}/action` - 调用 handle_action

---

## 示例 1: 天气面板（带定时采集）

**创建参数：**
```json
{
  "title": "天气",
  "desc": "显示实时天气，每30分钟自动更新",
  "icon": "cloud-sun",
  "headerColor": "cyan",
  "size": "3x3",
  "data": {
    "location": "Singapore"
  }
}
```

**注意**：天气数据采集由独立 Task 完成（`POST /api/tasks`），Panel 只负责展示 storage 中的数据。

**facade.html:**
```html
<div x-data="{ data: {}, loading: true }" x-init="
  fetch('/api/panels/__PANEL_ID__/data')
    .then(r => r.json())
    .then(d => { data = d; loading = false; })
">
  <template x-if="!loading && data.temperature">
    <div class="flex items-center gap-3">
      <span class="text-3xl">☀️</span>
      <div>
        <div class="text-2xl font-semibold text-gray-100">
          <span x-text="data.temperature"></span>°C
        </div>
        <div class="text-sm text-gray-400" x-text="data.condition"></div>
      </div>
    </div>
  </template>
</div>
```

---

## 示例 2: Todo 列表（带用户交互）

**创建参数：**
```json
{
  "title": "待办事项",
  "desc": "可勾选完成的任务清单",
  "icon": "check-square",
  "headerColor": "teal",
  "size": "3x4",
  "minSize": "3x4",
  "data": {
    "items": []
  }
}
```

**handler.py:**
```python
import uuid

async def handle_action(action: str, payload: dict, data: dict) -> dict:
    items = data.get("items", [])
    
    if action == "add":
        items.append({
            "id": uuid.uuid4().hex[:8],
            "text": payload.get("text", ""),
            "done": False
        })
    elif action == "toggle":
        for item in items:
            if item["id"] == payload.get("id"):
                item["done"] = not item["done"]
    elif action == "remove":
        items = [i for i in items if i["id"] != payload.get("id")]
    
    data["items"] = items
    return data
```

**facade.html:** （使用 PATCH /data 直接更新，不经过 handler）
```html
<div x-data="todoList()" x-init="init()" data-panel-id="__PANEL_ID__">
  <ul class="space-y-2">
    <template x-for="item in items" :key="item.id">
      <li class="flex items-center gap-2 text-sm">
        <button @click="toggle(item.id)" class="w-4 h-4 rounded border border-gray-600"
                :class="item.done && 'bg-gray-700'">
          <span x-show="item.done" class="text-xs text-gray-400">✓</span>
        </button>
        <span :class="item.done && 'line-through text-gray-600'" x-text="item.text"></span>
      </li>
    </template>
  </ul>
</div>
<script>
window.todoList = window.todoList || function() {
  return {
    items: [], panelId: '',
    async init() {
      this.panelId = this.$el.dataset.panelId;
      const res = await fetch('/api/panels/' + this.panelId + '/data');
      const data = await res.json();
      this.items = data.items || [];
    },
    async save() {
      await fetch('/api/panels/' + this.panelId + '/data', {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ items: this.items })
      });
    },
    toggle(id) {
      const item = this.items.find(i => i.id === id);
      if (item) { item.done = !item.done; this.save(); }
    }
  };
};
</script>
```

---

## 示例 3: Hacker News（定时采集 + Agent 总结）

**创建参数：**
```json
{
  "title": "Hacker News",
  "desc": "HN 热帖摘要，每小时更新",
  "icon": "newspaper",
  "headerColor": "indigo",
  "size": "4x4"
}
```

**注意**：HN 数据采集由独立 Task 完成，Panel 只负责展示 storage 中的数据。

---

## 注意事项

1. **深色模式** - 用 `dark:` 前缀或直接用 `text-gray-*`
2. **Panel ID** - facade 中用 `__PANEL_ID__` 占位符
3. **数据持久化** - 用 `PATCH /api/panels/{id}/data`
4. **异步 handler** - 推荐用 `async def`
5. **定时任务** - 通过 Task API 创建独立 task，不在 panel handler 中
6. **错误处理** - handler 中 catch 异常，避免整个采集失败

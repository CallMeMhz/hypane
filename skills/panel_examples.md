# Panel 示例

所有 panel 都通过 `facade.html` 渲染外观，`data.json` 存储数据，可选 `handler.py` 处理后端逻辑。

## 通用规则

1. 使用 Tailwind CSS
2. 深色模式用 `dark:` 前缀
3. 颜色用 `gray-*` 系列保持简洁
4. 交互功能用 Alpine.js (`x-data`, `x-init`, 等)
5. 通过 `data.minSize` 指定最小尺寸，如 `"3x2"`
6. **Panel ID 占位符**：facade.html 中需要引用 panel ID 时，使用 `__PANEL_ID__`，系统会自动替换为实际 ID

## API

- `GET /api/panels/{id}/data` - 获取 panel 数据
- `PATCH /api/panels/{id}/data` - 更新 panel 数据（合并）
- `POST /api/panels/{id}/action` - 调用 handler (需要 handler.py)

---

## 天气卡片

**minSize**: `3x2`

```html
<div class="flex items-center gap-4">
  <div class="text-3xl">☀️</div>
  <div>
    <div class="text-xl font-medium text-gray-800 dark:text-gray-100">28°C</div>
    <div class="text-sm text-gray-500">Singapore · 晴</div>
  </div>
</div>
<div class="mt-3 text-sm text-gray-400 dark:text-gray-500">
  明天: 27-32°C 多云
</div>
```

天气图标参考：
- 晴: ☀️
- 多云: ⛅ 🌤️
- 雨: 🌧️
- 雪: ❄️

---

## 倒计时卡片

**minSize**: `2x2`

```html
<div class="text-center py-4" 
     x-data="{ days: 0, target: '2026-12-31' }" 
     x-init="setInterval(() => { 
       const diff = new Date(target + 'T00:00:00') - new Date();
       days = Math.max(0, Math.ceil(diff / 86400000));
     }, 3600000); $nextTick(() => { 
       const diff = new Date(target + 'T00:00:00') - new Date();
       days = Math.max(0, Math.ceil(diff / 86400000));
     })">
  <div class="text-4xl mb-3">🎄</div>
  <div class="text-5xl font-medium text-gray-800 dark:text-gray-100 mb-1" x-text="days"></div>
  <div class="text-sm text-gray-500 dark:text-gray-400">days until</div>
  <div class="text-lg text-gray-600 dark:text-gray-300 mt-2">Christmas</div>
</div>
```

---

## Todo 列表（交互版）

**minSize**: `3x4`

```html
<div 
  x-data="todoList()" 
  x-init="init()" 
  data-panel-id="__PANEL_ID__"
  style="display: flex; flex-direction: column; height: 100%;"
>
  <div style="flex: 1; overflow-y: auto; min-height: 0;">
    <ul class="space-y-2">
      <template x-for="item in items" :key="item.id">
        <li class="flex items-center gap-2 text-sm group">
          <button @click="toggle(item.id)" 
                  class="w-4 h-4 flex-shrink-0 flex items-center justify-center rounded border transition-colors"
                  :class="item.done ? 'border-gray-600 bg-gray-700' : 'border-gray-600 hover:border-gray-500'">
            <span x-show="item.done" class="text-xs text-gray-400">✓</span>
          </button>
          <span class="flex-1" :class="item.done ? 'line-through text-gray-600' : 'text-gray-300'" x-text="item.text"></span>
          <button @click="remove(item.id)" class="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-red-400 p-0.5 flex-shrink-0">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </li>
      </template>
    </ul>
    <p x-show="items.length === 0" class="text-gray-600 text-center py-4 text-sm">No items</p>
  </div>
  <form @submit.prevent="add()" style="flex-shrink: 0;" class="flex gap-2 pt-2 mt-2 border-t border-gray-800">
    <input type="text" x-model="newText" placeholder="Add item..."
           class="flex-1 text-sm px-2 py-1.5 rounded border border-gray-700 bg-gray-900 text-gray-300 placeholder-gray-600 focus:outline-none focus:border-gray-500">
    <button type="submit" :disabled="!newText.trim()"
            class="text-xs px-3 py-1.5 rounded bg-gray-800 text-gray-400 hover:bg-gray-700 disabled:opacity-50">Add</button>
  </form>
</div>
<script>
if (!window.todoList) {
  window.todoList = function() {
    return {
      items: [],
      newText: '',
      panelId: '',
      async init() {
        this.panelId = this.$el.dataset.panelId;
        try {
          const res = await fetch('/api/panels/' + this.panelId + '/data');
          if (res.ok) {
            const data = await res.json();
            this.items = data.items || [];
          }
        } catch (e) {
          console.error('Failed to load items:', e);
        }
      },
      async save() {
        await fetch('/api/panels/' + this.panelId + '/data', {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ items: this.items })
        });
      },
      toggle(id) {
        const item = this.items.find(i => i.id === id);
        if (item) { item.done = !item.done; this.save(); }
      },
      remove(id) {
        this.items = this.items.filter(i => i.id !== id);
        this.save();
      },
      add() {
        if (!this.newText.trim()) return;
        this.items.push({ id: Date.now().toString(16), text: this.newText.trim(), done: false });
        this.newText = '';
        this.save();
      }
    };
  };
}
</script>
```

创建时在 `data` 里提供初始 items：
```json
{
  "type": "todo",
  "title": "My Tasks",
  "facade": "...",
  "data": { "items": [{"id": "1", "text": "First task", "done": false}] },
  "size": "3x4",
  "minSize": "3x4"
}
```

---

## Cookie Clicker 游戏

**minSize**: `3x4`

```html
<div x-data="{ 
  cookies: parseInt(localStorage.getItem('cookies') || '0'),
  click() { 
    this.cookies++; 
    localStorage.setItem('cookies', this.cookies);
  }
}" class="text-center py-4">
  <button @click="click()" class="text-6xl hover:scale-110 transition-transform cursor-pointer select-none">
    🍪
  </button>
  <div class="mt-4 text-2xl font-bold text-gray-800 dark:text-gray-100" x-text="cookies.toLocaleString()"></div>
  <div class="text-sm text-gray-500 dark:text-gray-400">cookies</div>
</div>
```

---

## 加密货币价格

**minSize**: `3x2`

```html
<div class="space-y-3">
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-2">
      <span class="text-xl">₿</span>
      <span class="font-medium text-gray-800 dark:text-gray-100">Bitcoin</span>
    </div>
    <div class="text-right">
      <div class="font-medium text-gray-800 dark:text-gray-100">$97,245</div>
      <div class="text-xs text-green-500">+2.4%</div>
    </div>
  </div>
</div>
```

---

## 自定义 HTML 注意事项

1. **深色模式** 必须支持，用 `dark:` 前缀
2. **图片** 用 emoji 或 SVG，避免外部图片加载
3. **链接** 用 `target="_blank"` 打开新窗口
4. **间距** 用 Tailwind 的 `space-y-*`, `gap-*`, `p-*`, `m-*`
5. **持久化数据** 用 `fetch('/api/panels/{panelId}/data', { method: 'PATCH', ... })`

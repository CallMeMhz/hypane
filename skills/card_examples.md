# 卡片示例

所有卡片都是自定义类型，通过 `content.html` 渲染。以下是常用卡片的参考示例。

## 通用规则

1. 使用 Tailwind CSS
2. 深色模式用 `dark:` 前缀
3. 颜色用 `gray-*` 系列保持简洁
4. 交互功能用 Alpine.js (`x-data`, `x-init`, 等)
5. 通过 `content.minSize` 指定最小尺寸，如 `"3x2"`

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

## Todo 列表

**minSize**: `2x3`

简单静态版（无交互）：

```html
<ul class="space-y-2 text-sm">
  <li class="flex items-center gap-2">
    <span class="w-4 h-4 rounded border border-gray-300 dark:border-gray-600"></span>
    <span class="text-gray-600 dark:text-gray-300">买牛奶</span>
  </li>
  <li class="flex items-center gap-2">
    <span class="w-4 h-4 rounded border border-gray-400 dark:border-gray-600 bg-gray-100 dark:bg-gray-700 text-center text-xs text-gray-500">✓</span>
    <span class="line-through text-gray-400 dark:text-gray-600">写周报</span>
  </li>
</ul>
```

交互版需要后端 API 支持，参考 `app/templates/components/todo.html`。

---

## Cookie Clicker 游戏

**minSize**: `3x4`

```html
<div x-data="{ 
  cookies: parseInt(localStorage.getItem('cookies') || '0'),
  cps: 0,
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
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-2">
      <span class="text-xl">Ξ</span>
      <span class="font-medium text-gray-800 dark:text-gray-100">Ethereum</span>
    </div>
    <div class="text-right">
      <div class="font-medium text-gray-800 dark:text-gray-100">$2,712</div>
      <div class="text-xs text-red-500">-1.2%</div>
    </div>
  </div>
</div>
```

---

## 新闻聚合

**minSize**: `4x3`

```html
<div class="space-y-3 text-sm">
  <a href="#" class="block group">
    <div class="font-medium text-gray-800 dark:text-gray-100 group-hover:text-blue-500 transition-colors">
      GPT-5 发布，支持多模态推理
    </div>
    <div class="text-xs text-gray-400 mt-1">Hacker News · 2小时前 · 523 points</div>
  </a>
  <a href="#" class="block group">
    <div class="font-medium text-gray-800 dark:text-gray-100 group-hover:text-blue-500 transition-colors">
      Rust 2026 路线图公布
    </div>
    <div class="text-xs text-gray-400 mt-1">Hacker News · 4小时前 · 312 points</div>
  </a>
</div>
```

---

## 提醒卡片

**minSize**: `2x2`

```html
<div class="flex items-start gap-3">
  <div class="text-2xl">⏰</div>
  <div>
    <div class="font-medium text-gray-800 dark:text-gray-100">团队周会</div>
    <div class="text-sm text-gray-500 mt-1">今天 14:00</div>
    <div class="text-xs text-gray-400 mt-2">会议室 A</div>
  </div>
</div>
```

---

## 自定义 HTML 注意事项

1. **不要用** `<script>` 标签，Alpine.js 的 `x-data` 内联即可
2. **图片** 用 emoji 或 SVG，避免外部图片加载
3. **链接** 用 `target="_blank"` 打开新窗口
4. **深色模式** 必须支持，用 `dark:` 前缀
5. **间距** 用 Tailwind 的 `space-y-*`, `gap-*`, `p-*`, `m-*`

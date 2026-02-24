# Panel Market 使用指南

创建 Panel 时，优先从 Market 安装官方模板。

## 工作流程

1. 用户请求创建 panel（如 "添加一个天气面板"）
2. 搜索 Market：`GET /api/market/search?q=天气`
3. 如果有匹配，调用安装 API
4. 如果没有匹配或用户需要特殊定制，才创建全新 panel

## API

### 列出所有模板
```
GET /api/market
```

### 搜索模板
```
GET /api/market/search?q=关键词
```

### 安装模板
```
POST /api/market/{type}/install
{
  "title": "面板标题",
  "size": "3x3",        // 可选，使用默认
  "data": {             // 可选，覆盖默认配置
    "location": "Tokyo"
  }
}
```

## 可用模板

| 类型 | 名称 | 说明 |
|------|------|------|
| `todo` | 待办事项 | 任务清单，可添加/删除/勾选 |
| `weather` | 天气预报 | 7天天气，每小时自动刷新 |
| `countdown` | 倒计时 | 显示距离目标日期天数 |
| `iframe` | 嵌入网页 | 嵌入任意网页 |
| `youtube` | YouTube | 嵌入 YouTube 视频 |
| `poster` | 海报/图片 | 展示图片，可设置跳转链接 |

## 示例

### 安装天气 Panel（东京）
```bash
POST /api/market/weather/install
{
  "title": "东京天气",
  "data": {
    "location": "Tokyo",
    "latitude": 35.68,
    "longitude": 139.69
  }
}
```

### 安装待办 Panel
```bash
POST /api/market/todo/install
{
  "title": "工作任务",
  "size": "4x5"
}
```

### 安装 YouTube Panel
```bash
POST /api/market/youtube/install
{
  "title": "背景音乐",
  "data": {
    "videoId": "dQw4w9WgXcQ"
  }
}
```

## 何时创建全新 Panel

只有当以下情况时才创建新 panel：
1. Market 中没有相似模板
2. 用户明确需要定制功能
3. 需要组合多个数据源
4. 需要特殊的交互逻辑

全新 Panel 创建参考 `panel_examples.md`。

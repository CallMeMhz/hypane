# Panel Market

官方 Panel 模板，可直接安装使用。

## 使用方式

用户请求创建 panel 时：
1. 先搜索 market 是否有匹配的模板
2. 有则直接安装，根据用户需求调整参数
3. 没有匹配或用户需要深度定制时，才创建全新 panel

## 目录结构

```
market/
├── README.md
├── todo/           # 待办事项
├── weather/        # 天气预报
├── iframe/         # 嵌入网页
├── youtube/        # YouTube 视频
├── poster/         # 海报/图片展示
├── countdown/      # 倒计时
├── cookie-clicker/ # 饼干点击器
├── hackernews/     # Hacker News 热帖
└── bitcoin/        # 比特币价格
```

每个模板包含：
- `manifest.json` - 元数据、默认配置
- `facade.html` - 前端模板
- `handler.py` - 后端逻辑（可选）

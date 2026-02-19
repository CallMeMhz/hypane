# Hacker News 追踪

## 任务

定时抓取 Hacker News 热帖，根据用户兴趣筛选并更新 Dashboard。

## 数据源

- 网页: https://news.ycombinator.com/
- API: https://hacker-news.firebaseio.com/v0/topstories.json
- 单条: https://hacker-news.firebaseio.com/v0/item/{id}.json

## 执行步骤

1. 读取 `data/dashboard.json` 获取 userPreferences.interests
2. 抓取 HN 首页前 30 条热帖
3. 根据用户兴趣筛选相关内容
4. 判断更新策略：
   - 如果有 3+ 条相关新闻 → 更新/创建 `news-bundle` 卡片
   - 如果有 1 条特别重要的 → 单独创建 `news-single` 卡片
   - 如果没有新内容 → 不更新
5. 更新 `data/dashboard.json`

## 判断标准

- **相关性**: 标题或内容是否与 interests 相关
- **重要性**: 点赞数、评论数是否突出
- **新鲜度**: 是否已经推送过（检查现有卡片）

## 注意事项

- 避免重复推送同一条新闻
- 聚合卡片最多包含 5 条
- 为每条新闻生成简短中文摘要

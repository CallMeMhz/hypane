# Hacker News 摘要生成

## ⚠️ 输出要求 (最重要)

**必须输出 JSON 文件到正确路径！**

```
正确: data/history/hn-summary/2026-02-19_08.json
错误: data/history/hackernews/xxx.json (这是原始数据目录)
错误: xxx.md (不要写 markdown)
```

- 目录: `data/history/hn-summary/` (注意是 hn-summary，不是 hackernews)
- 文件名: `YYYY-MM-DD_HH.json` (UTC 时间)
- 写完后验证: `python -m json.tool < 文件路径`

## 任务

读取已采集的 HN 原始数据，抓取热门评论，生成中文摘要写入 JSON。

## 执行步骤

1. 读取 `data/history/hackernews/` 最新的 json
2. 筛选 5 条最热门的 (score 高 + 评论多)
3. 对每条用 API 抓取前 3 条评论:
   - `https://hacker-news.firebaseio.com/v0/item/{id}.json` 获取 kids
   - 获取评论内容
4. 生成中文摘要
5. **写入 JSON 文件** (不是 markdown)

## JSON 输出格式

```json
{
  "timestamp": "2026-02-19T08:30:00Z",
  "data": {
    "items": [
      {
        "id": 47066552,
        "title": "Sizing chaos",
        "url": "https://pudding.cool/2026/02/womens-sizing/",
        "summary": "👗 女装尺码混乱 (489分, 256评论)",
        "comment": "💬「M码在不同品牌能差好几个尺寸」— 评论区吐槽大会",
        "score": 489,
        "commentCount": 256
      }
    ],
    "generatedAt": "2026-02-19T08:30:00Z"
  }
}
```

## 字段说明

- `summary`: emoji + 中文标题 + (分数, 评论数)
- `comment`: 💬 + 评论引用 + 简短点评

## 再次强调

写 `.json` 文件，不是 `.md` 文件！

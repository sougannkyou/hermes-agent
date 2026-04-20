---
name: istarshine-data
description: 智慧星光舆情数据查询技能。支持搜索抖音、微博等中文社交媒体的帖子、评论、热词、话题、情感分析、趋势等。用于数据工程师角色查询实时舆情数据。
version: 1.0.0
author: OpenMAIC
license: MIT
metadata:
  hermes:
    tags: [Data, Social Media, Sentiment, Chinese, API]
    related_skills: []
---

# 智慧星光舆情数据查询

本技能提供智慧星光（iStarshine）舆情数据 API 的查询能力，支持搜索中国境内主流社交媒体平台的帖子、评论、热词、话题等数据。

## 重要说明

1. **API 密钥**：需要在环境变量中配置 `ISTARSHINE_API_KEY`
2. **数据范围**：支持抖音、微博、快手、小红书、B站等 40+ 平台
3. **时间范围**：默认查询最近 30 天数据
4. **响应格式**：兼容 Google Custom Search JSON API 格式

## 快速参考

| 功能 | 端点 |
|------|------|
| 关键词搜索 | `POST /api/search` |
| 热词查询 | `POST /api/trending` |
| 情感分析 | `POST /api/sentiment` |
| 平台对比 | `POST /api/compare` |
| 标签统计 | `POST /api/label-stats` |

## API 基础信息

```
Base URL: https://api.istarshine.com/v1
Authorization: Bearer {ISTARSHINE_API_KEY}
Content-Type: application/json
```

## 1. 关键词搜索

搜索帖子、评论、新闻等内容。

### 请求

```bash
curl -X POST "https://api.istarshine.com/v1/api/search" \
  -H "Authorization: Bearer $ISTARSHINE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "比亚迪",
    "platforms": ["douyin", "weibo"],
    "dateRange": {
      "start": "2025-04-01",
      "end": "2025-04-20"
    },
    "contentTypes": ["post", "comment"],
    "limit": 50,
    "sortBy": "engagement",
    "sortOrder": "desc"
  }'
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 是 | 搜索关键词，支持布尔运算 |
| platforms | string[] | 否 | 平台列表，默认全部 |
| dateRange | object | 否 | 时间范围 |
| contentTypes | string[] | 否 | 内容类型：post/comment/repost/danmaku |
| limit | number | 否 | 返回数量，默认 20，最大 100 |
| sortBy | string | 否 | 排序字段：time/engagement/sentiment |
| sortOrder | string | 否 | 排序方向：asc/desc |
| sentiment | string | 否 | 情感过滤：positive/negative/neutral |

### 支持的平台

| 平台代码 | 平台名称 | 数据类型 |
|----------|----------|----------|
| douyin | 抖音 | 视频、评论、弹幕 |
| weibo | 微博 | 帖子、评论、转发 |
| kuaishou | 快手 | 视频、评论 |
| xiaohongshu | 小红书 | 笔记、评论 |
| bilibili | B站 | 视频、评论、弹幕 |
| wechat_mp | 微信公众号 | 文章 |
| wechat_video | 微信视频号 | 视频 |
| toutiao | 今日头条 | 文章、评论 |
| zhihu | 知乎 | 问答、文章 |
| tieba | 百度贴吧 | 帖子、评论 |

### 响应示例

```json
{
  "success": true,
  "data": {
    "total": 1234,
    "items": [
      {
        "id": "7352xxx",
        "platform": "douyin",
        "contentType": "post",
        "author": {
          "id": "123456",
          "name": "汽车博主",
          "followers": 500000
        },
        "content": "比亚迪新车发布会现场...",
        "publishedAt": "2025-04-15T10:30:00Z",
        "engagement": {
          "likes": 50000,
          "comments": 3000,
          "shares": 1500,
          "views": 1000000
        },
        "sentiment": {
          "score": 0.85,
          "label": "positive"
        },
        "url": "https://www.douyin.com/video/7352xxx"
      }
    ],
    "aggregations": {
      "byPlatform": {
        "douyin": 800,
        "weibo": 434
      },
      "bySentiment": {
        "positive": 700,
        "neutral": 400,
        "negative": 134
      }
    }
  }
}
```

## 2. 热词/热搜查询

查询各平台热搜榜单和热词。

### 请求

```bash
curl -X POST "https://api.istarshine.com/v1/api/trending" \
  -H "Authorization: Bearer $ISTARSHINE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "platforms": ["weibo", "douyin", "baidu"],
    "category": "all",
    "limit": 50
  }'
```

### 响应示例

```json
{
  "success": true,
  "data": {
    "weibo": [
      {
        "rank": 1,
        "keyword": "比亚迪发布新车",
        "hotScore": 9876543,
        "category": "tech",
        "trend": "rising",
        "url": "https://s.weibo.com/weibo?q=比亚迪发布新车"
      }
    ],
    "douyin": [
      {
        "rank": 1,
        "keyword": "比亚迪",
        "hotScore": 5432100,
        "videoCount": 12345
      }
    ]
  }
}
```

## 3. 情感分析

对指定关键词或内容进行情感分析。

### 请求

```bash
curl -X POST "https://api.istarshine.com/v1/api/sentiment" \
  -H "Authorization: Bearer $ISTARSHINE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "比亚迪",
    "platforms": ["douyin", "weibo"],
    "dateRange": {
      "start": "2025-04-01",
      "end": "2025-04-20"
    },
    "granularity": "day"
  }'
```

### 响应示例

```json
{
  "success": true,
  "data": {
    "overall": {
      "positive": 0.65,
      "neutral": 0.25,
      "negative": 0.10
    },
    "trend": [
      {
        "date": "2025-04-01",
        "positive": 0.60,
        "neutral": 0.30,
        "negative": 0.10,
        "volume": 1234
      }
    ],
    "topPositiveKeywords": ["创新", "性价比", "好看"],
    "topNegativeKeywords": ["质量", "售后", "等待"]
  }
}
```

## 4. 平台对比

对比不同平台上同一话题的表现。

### 请求

```bash
curl -X POST "https://api.istarshine.com/v1/api/compare" \
  -H "Authorization: Bearer $ISTARSHINE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "比亚迪",
    "platforms": ["douyin", "weibo", "xiaohongshu"],
    "metrics": ["volume", "engagement", "sentiment"],
    "dateRange": {
      "start": "2025-04-01",
      "end": "2025-04-20"
    }
  }'
```

### 响应示例

```json
{
  "success": true,
  "data": {
    "comparison": [
      {
        "platform": "douyin",
        "volume": 50000,
        "totalEngagement": 5000000,
        "avgEngagement": 100,
        "sentiment": {
          "positive": 0.70,
          "neutral": 0.20,
          "negative": 0.10
        }
      }
    ]
  }
}
```

## 5. 标签统计

按标签（如 MCN、媒体类型）统计数据分布。

### 请求

```bash
curl -X POST "https://api.istarshine.com/v1/api/label-stats" \
  -H "Authorization: Bearer $ISTARSHINE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "比亚迪",
    "labelType": "mcn",
    "platforms": ["douyin"],
    "limit": 20
  }'
```

### 响应示例

```json
{
  "success": true,
  "data": {
    "labelType": "mcn",
    "distribution": [
      {
        "labelId": "mcn_001",
        "labelName": "无忧传媒",
        "postCount": 500,
        "totalEngagement": 10000000,
        "topAuthors": ["账号A", "账号B"]
      }
    ]
  }
}
```

## 使用示例

### 场景 1：品牌舆情监测

```bash
# 1. 搜索品牌相关帖子
python scripts/istarshine_api.py search "比亚迪" --platforms douyin,weibo --limit 100

# 2. 分析情感趋势
python scripts/istarshine_api.py sentiment "比亚迪" --granularity day

# 3. 查看热搜表现
python scripts/istarshine_api.py trending --platforms weibo
```

### 场景 2：竞品对比分析

```bash
# 对比多个品牌在各平台的表现
python scripts/istarshine_api.py compare "比亚迪 OR 特斯拉 OR 蔚来" \
  --platforms douyin,weibo,xiaohongshu
```

### 场景 3：KOL/MCN 分析

```bash
# 查看哪些 MCN 在讨论品牌
python scripts/istarshine_api.py label-stats mcn --query "比亚迪" --platforms douyin

# 查看哪些媒体在报道
python scripts/istarshine_api.py label-stats media --query "比亚迪" --platforms weibo
```

## 错误处理

| 错误码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | API 密钥无效或过期 |
| 403 | 无权限访问该数据 |
| 429 | 请求频率超限 |
| 500 | 服务器内部错误 |

## 注意事项

1. **查询耗时**：复杂查询可能需要 30-120 秒，请耐心等待
2. **数据延迟**：实时数据有 5-15 分钟延迟
3. **配额限制**：每日查询次数有限，请合理使用
4. **敏感词过滤**：部分敏感内容可能被过滤

## 与 OpenMAIC 集成

在 OpenMAIC 中，数据工程师角色会自动加载此 skill。当舆情分析师需要实时数据时，可以请求数据工程师帮忙查询。

示例对话：
- 舆情分析师："这个品牌最近在抖音上的表现如何？"
- 数据工程师：（使用此 skill 查询数据）"根据智慧星光数据，该品牌在抖音上..."

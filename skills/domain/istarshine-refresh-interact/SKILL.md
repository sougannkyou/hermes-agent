---
api:
  auth:
    env_key: ISTARSHINE_API_KEY
    obtain_url: https://skills.istarshine.com/settings/api-keys
    type: bearer
  endpoints:
  - description: 获取单条抖音视频的实时互动数据（播放量、点赞、评论、收藏、分享），无需 ctime
    method: POST
    params:
      url:
        description: 抖音视频详情页 URL
        required: true
        type: string
    path: /acp/v1/skill-run/istarshine-refresh-interact/api/dyInteractNoTime
  - description: 批量获取微博帖子的实时互动数据（最多 50 条）
    method: POST
    params:
      urls:
        description: 微博帖子链接列表（最多 50 条）
        required: true
        type: array
    path: /acp/v1/skill-run/istarshine-refresh-interact/api/weibo/batch_interact
  metering: per_request
  rate_limit: 100/day
description: '获取抖音视频和微博帖子的实时互动数据（播放量、点赞、评论、转发等），支持单条和批量获取。 当用户需要获取特定抖音视频或微博帖子的实时互动数据时使用。
  不要用于通用搜索、统计分析或热榜数据。

  '
license: Proprietary. See LICENSE.txt for complete terms.
metadata:
  author: istarshine
  display_name: 互动数据刷新
  openclaw:
    emoji: 📈
    primaryEnv: ISTARSHINE_API_KEY
    requires:
      bins:
      - node
      env:
      - ISTARSHINE_API_KEY
  tags:
  - 数据
  version: 0.21.2
name: istarshine-refresh-interact
---

# istarshine-refresh-interact — 互动数据刷新 Skill

## When to use

- 获取抖音视频的最新播放量、点赞、评论、收藏、分享数
- 获取微博帖子的最新评论数、点赞数、转发数、访问量
- 批量获取多条微博帖子的互动数据
- 搜索结果中的互动数据有延迟，需要获取最新值

## When NOT to use

- 搜索帖子或评论 → istarshine-douyin-weibo-search
- 统计分析 → istarshine-douyin-weibo-search 的 stats 工具
- URL 归一化 → istarshine-normalize-url
- 热榜/热搜数据 → istarshine-trending-search

## 配置

编辑 `scripts/config.json`：

```json
{
  "server_url": "http://your-server:8001"
}
```

API Key 通过环境变量配置：

```bash
export ISTARSHINE_API_KEY=<your-api-key>
```

## 工具列表

| 工具 | 用途 | 说明 |
|------|------|------|
| `fetch_douyin_interact` | 抖音实时互动数据 | 单条抖音视频的评论、点赞、收藏、分享、播放量 |
| `batch_refresh_weibo_interact` | 微博批量互动数据 | 批量获取多条微博互动数据（最多 50 条） |

## 互动数据获取工作流

```
Step 1: 如果是分享短链或移动端链接 → 先用 istarshine-normalize-url 转换为标准 URL
Step 2: 根据平台调用对应工具：
        - 抖音 → fetch_douyin_interact(url)
        - 微博 → batch_refresh_weibo_interact(urls)
```

## 工具详细说明

### fetch_douyin_interact

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `url` | string | 是 | 抖音视频详情页 URL |

返回：reply_count、like_count、collection_count、share_count、play_count、ctime（从视频 ID 自动提取的发布时间戳）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `urls` | list[str] | 是 | 微博帖子链接列表（最多 50 条） |

返回：每条 URL 的评论数、点赞数、转发数、访问量、ctime（从微博 mid 自动提取的发布时间戳）。
node scripts/cli.js fetch_douyin_interact --url https://...
node scripts/cli.js batch_refresh_weibo_interact --urls https://...,https://...
```

## On Failure

- 401：缺少 API Key → 检查 config.json
- 403：API Key 无效 → 更换 api_key
- 502：外部 API 异常 → 可重试一次

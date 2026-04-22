---
api:
  auth:
    env_key: ISTARSHINE_API_KEY
    obtain_url: https://skills.istarshine.com/settings/api-keys
    type: bearer
  endpoints:
  - description: 搜索帖子或评论（通过 cx 参数区分 posts/comments）
    method: GET
    params:
      cx:
        description: posts（原创帖/短视频）或 comments（评论/转发/弹幕）
        required: true
        type: string
      fields:
        description: 返回字段列表，逗号分隔
        required: false
        type: string
      num:
        description: 每页条数（1-100），默认 10
        required: false
        type: integer
      q:
        description: 查询字符串，支持运算符语法
        required: true
        type: string
      sort:
        description: 排序，默认 ctime:desc
        required: false
        type: string
      start:
        description: 起始位置（从 1 开始），默认 1
        required: false
        type: integer
    path: /acp/v1/skill-run/istarshine-douyin-weibo-search/customsearch/v1
  - description: 统计分析（热词、话题、情感、趋势、平台对比、MCN/采编权分布等）
    method: POST
    params:
      metrics:
        description: 统计指标列表，支持 hotWords/hotHashtags/sentiment/trend/platformCompare/labelDistribution/labelFirstPost
        required: true
        type: array
      q:
        description: 查询字符串（同 search）
        required: false
        type: string
    path: /acp/v1/skill-run/istarshine-douyin-weibo-search/api/stats
  - description: 查询可用 MCN 机构标签列表
    method: GET
    path: /acp/v1/skill-run/istarshine-douyin-weibo-search/api/labels/mcn
  - description: 查询可用采编权标签列表
    method: GET
    path: /acp/v1/skill-run/istarshine-douyin-weibo-search/api/labels/cbq
  metering: per_request
  rate_limit: 100/day
description: '搜索抖音和微博全量数据（近30天），包括帖子、评论、转发和弹幕。 支持关键词搜索、热词、话题、情感分析、趋势、平台对比、标签联合查询和统计分析。
  兼容 Google Custom Search JSON API 响应格式。 当用户需要搜索中文社交媒体（抖音和微博）上的帖子、评论、热词、话题、情感、趋势、平台对比或标签统计分析时使用。
  不要用于互动数据刷新（请使用 istarshine-refresh-interact）、 URL 归一化（请使用 istarshine-normalize-url）、
  或热榜/热搜数据（请使用 istarshine-trending-search）。

  '
license: Proprietary. See LICENSE.txt for complete terms.
metadata:
  author: istarshine
  display_name: 全量抖音微博搜索
  openclaw:
    emoji: 🔧
    primaryEnv: ISTARSHINE_API_KEY
    requires:
      bins:
      - node
      env:
      - ISTARSHINE_API_KEY
  tags:
  - 数据
  version: 0.22.1
name: istarshine-douyin-weibo-search
---

# istarshine-douyin-weibo-search — 抖音微博全量搜索 Skill

## When to use

- 搜索抖音或微博上的帖子、评论、转发
- 分析热词、话题、情感、趋势
- 对比抖音和微博的数据分布
- 标签联合查询和统计分析（配合标签 Skill 使用，如 `istarshine-label-mcn`、`istarshine-label-authorized-media` 等）

## When NOT to use

- 热榜/热搜/排行榜数据 → istarshine-trending-search
- 获取互动数据 → istarshine-refresh-interact
- URL 归一化 → istarshine-normalize-url
- 非中文社交媒体平台

## 配置

编辑 `scripts/config.json`：

```json
{
  "server_url": "http://your-server:8001",
  "timeout_seconds": 660
}
```

API Key 通过环境变量配置：

```bash
export ISTARSHINE_API_KEY=<your-api-key>
```

- `timeout_seconds`：请求超时时间（秒），默认 660（11 分钟），服务端统计聚合最长约 10 分钟

## 工具列表

| 工具 | 用途 | 说明 |
|------|------|------|
| `search` | 搜索帖子或评论 | `cx=posts` 搜原创帖/短视频，`cx=comments` 搜评论/转发/弹幕 |
| `stats` | 统计分析 | 7 种聚合指标，可一次请求多种 |
| `list_labels` | 查询可用标签 | 查询标签列表（详细信息参见对应标签 Skill） |

## 搜索查询优化（每次搜索前必须执行）

用户关键词通常是简短主题词，直接短语匹配会遗漏大量相关内容。**每次搜索前，必须将用户关键词扩展为多个搜索分支**。

扩展规则和示例详见 `references/query-optimization.md`。

核心要点：
1. 保留原始短语作为第一个搜索分支
2. 拆解为核心实体 + 事件词的 AND 组合
3. 补充同义词和相关表述（3-6 个分支即可）
4. 对于已经很具体的短语（如人名），无需扩展

## 搜索工作流

```
Step 1: 优化搜索条件 → 按扩展规则生成多个搜索分支（详见 references/query-optimization.md）
Step 2: search (cx=posts) → 了解整体数据量和内容概况
Step 3: search (cx=comments) → 分析网民观点和互动热度
Step 4: stats → 一次请求获取所需统计指标（按需组合）
Step 5: 迭代优化 → 根据结果补充扩展词，重新搜索/统计（如有必要）
```

根据用户需求选择相关步骤即可。stats 支持一次请求传入多种指标，无需分多次调用。

## On Failure

- 401：缺少 API Key → 检查 config.json
- 403：API Key 无效 → 更换 api_key
- 429：并发上限 → 稍后重试
- 502：外部 API 异常 → 可重试一次
- 504：查询超时 → 缩小查询范围
- 结果为空 → 放宽条件（减少关键词、扩大时间范围）
- 结果过少（< 50） → 按迭代优化规则补充扩展词后重新搜索

错误响应为 Google API 格式：`{"error": {"code": N, "message": "...", "errors": [...]}}`

## 工具详细说明

### search — 搜索帖子或评论

通过 `cx` 区分：`cx=posts` 搜原创帖，`cx=comments` 搜评论/转发/弹幕。返回字段包含 `video_urls`（视频下载地址），可通过 `fields` 参数指定返回字段。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `cx` | string | 是 | — | `posts`（原创帖）或 `comments`（评论/转发/弹幕） |
| `q` | string | 是 | — | 查询字符串，支持运算符语法（见 `references/operators.md`） |
| `num` | int | 否 | 10 | 每页条数（1-100） |
| `start` | int | 否 | 1 | 起始位置（从 1 开始） |
| `sort` | string | 否 | ctime:desc | 排序（见 `references/operators.md`） |
| `fields` | string | 否 | 全部 | 返回字段列表，逗号分隔 |

```bash
node scripts/cli.js search --cx posts --q "新能源 site:iesdouyin.com" --num 10
node scripts/cli.js search --cx comments --q "AI dateRestrict:d7" --num 5
```

### stats — 统计分析

对搜索条件匹配的内容做聚合统计。一次请求可同时获取多种指标。查询条件使用与 search 相同的运算符语法。

| 指标 type | 用途 | 典型场景 |
|-----------|------|----------|
| `hotWords` | 高频关键词 | "大家在聊什么" |
| `hotHashtags` | 热门话题标签 | "相关话题有哪些" |
| `sentiment` | 情感比例 | "舆论倾向如何" |
| `trend` | 发帖量趋势 | "什么时候讨论最多" |
| `platformCompare` | 平台对比 | "两个平台有什么区别" |
| `labelDistribution` | 标签分布 | "哪些机构参与了传播" |
| `labelFirstPost` | 标签首发 | "谁最先发的" |

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `q` | string | 否 | 查询字符串（同 search） |
| `metrics` | array | 是 | 统计指标列表 |

metrics 元素：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 是 | 指标类型 |
| `topN` | int | 否 | 返回前 N 条（hotWords/hotHashtags/labelDistribution/labelFirstPost） |
| `interval` | string | 否 | 时间粒度 `hour`/`day`/`week`（仅 trend） |
| `labelType` | string | 否 | 标签类型（labelDistribution/labelFirstPost 必填），具体值参见对应标签 Skill |
| `groupId` | string | 否 | 标签子分组 ID，具体值参见对应标签 Skill |

> 标签统计支持与多种标签 Skill 联合使用，`labelType` 和 `groupId` 的具体取值请参考对应标签 Skill 的文档（如 `istarshine-label-mcn`、`istarshine-label-authorized-media` 等）。

### list_labels — 查询可用标签

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `label_type` | string | 否 | "mcn" | 标签类型，具体值参见对应标签 Skill |

## 运算符语法与字段

运算符语法、排序参数、组合示例详见 `references/operators.md`。
查询优化规则详见 `references/query-optimization.md`。
可查询字段完整列表详见 `references/fields.md`。

## 数据范围

- 平台：抖音（iesdouyin.com）、微博（weibo.com）
- 数据类型：原创帖/短视频、转发帖、评论、弹幕
- 时间范围：近一个月全量数据，单次查询最大 30 天，默认最近 7 天
- `analysis` 下的字段均为 NLP 自动分析结果，仅供参考

---
api:
  auth:
    env_key: ISTARSHINE_API_KEY
    obtain_url: https://skills.istarshine.com/settings/api-keys
    type: bearer
  endpoints:
  - description: 热榜关键词搜索（cx 固定为 trending），支持平台、分类、地域、时间等多维筛选
    method: GET
    params:
      fields:
        description: 返回字段列表，逗号分隔
        required: false
        type: string
      num:
        description: 每页条数（1-100），默认 10
        required: false
        type: integer
      q:
        description: '查询字符串，支持运算符语法（platform:、category:、city:、dateRestrict: 等）'
        required: false
        type: string
      sort:
        description: 排序：hot:desc（默认）、time:desc、rank:asc
        required: false
        type: string
      start:
        description: 起始位置（从 1 开始），默认 1
        required: false
        type: integer
    path: /acp/v1/skill-run/istarshine-trending-search/customsearch/v1
  metering: per_request
  rate_limit: 100/day
description: '搜索 44 个中文平台（微博、抖音、百度、知乎、B站等）的热榜/热搜数据。 支持关键词搜索、平台/分类/地域筛选、时间范围过滤和多字段排序。
  兼容 Google Custom Search JSON API 响应格式。 当用户查询中文平台的热门话题、热搜、排行榜或实时热榜时使用。 不要用于内容/帖子搜索（请使用
  istarshine-douyin-weibo-search）、 互动数据刷新（请使用 istarshine-refresh-interact）、 或 URL
  归一化（请使用 istarshine-normalize-url）。

  '
license: Proprietary. See LICENSE.txt for complete terms.
metadata:
  author: istarshine
  display_name: 热榜热搜搜索
  openclaw:
    emoji: 🔥
    primaryEnv: ISTARSHINE_API_KEY
    requires:
      bins:
      - node
      env:
      - ISTARSHINE_API_KEY
  tags:
  - 数据
  version: 0.22.0
name: istarshine-trending-search
---

# istarshine-trending-search — 热榜热搜搜索 Skill

## When to use

- 查看某平台当前热搜/热榜（如"微博热搜"、"抖音热榜"）
- 搜索热榜中的特定关键词（如"AI 在哪些平台上热搜了"）
- 按分类、地域筛选热榜数据（如"北京同城热榜"）
- 对比不同平台的热搜排名和热度
- 查看某话题在热榜上的历史排名变化

## When NOT to use

- 搜索帖子、评论、转发等内容 → istarshine-douyin-weibo-search
- 获取互动数据 → istarshine-refresh-interact
- URL 归一化 → istarshine-normalize-url

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
| `search` | 热榜关键词搜索 | 支持平台、分类、地域、时间等多维筛选 |
| `trending_now` | 获取当前热榜 | 快速获取指定平台的实时热榜，无需关键词 |
| `list_platforms` | 查看所有平台 | 列出全部 44 个平台及状态，本地执行 |

## 平台优先级与权重

**大平台优先展示**：微博、抖音、快手、百度、今日头条、B站、知乎等大平台权重更高，应优先展示。跨平台搜索时建议分平台查询，确保大平台数据不被遗漏。

**同城热榜权重较低**：带 `_tongcheng` 后缀的同城平台（如 `weibo_tongcheng`、`douyin_tongcheng`）上榜门槛较低，权重低于全平台热榜。综合分析时应区分对待，避免高估话题热度。

**建议查询策略**：优先按大平台逐一查询（先查微博、再查抖音、快手），不同平台热度值量纲不同，直接比较可能导致大平台数据被淹没。

## 搜索词扩展策略

热榜搜索目标是标题（title），采用完全匹配（match_phrase），标题通常很短。搜索词必须尽可能短，并主动扩展同义词、关联词。

**核心原则**：
- 搜索词越短越好，一个词优于一个短语
- 每个搜索词独立查询，结果合并去重后展示
- 扩展维度：品牌名、英文名、创始人/关键人物、昵称/简称、核心产品名

**扩展示例**：

| 用户意图 | 扩展搜索词 |
|----------|-----------|
| 小米热榜 | 小米、xiaomi、雷军、雷总、SU7、小米汽车 |
| 华为热榜 | 华为、HUAWEI、Mate、鸿蒙、余承东 |
| 特斯拉热榜 | 特斯拉、Tesla、马斯克、Model |
| AI热榜 | AI、人工智能、大模型、ChatGPT、DeepSeek |

对每个扩展词分别调用 search，结果按平台分组、去重（同标题同平台只保留一条）、按热度排序后展示。

## 搜索工作流

```
Step 1: list_platforms → 了解可用平台
Step 2: trending_now (platform=xxx) → 查看指定平台当前热榜
Step 3: search (q=关键词) → 跨平台搜索特定话题
Step 4: search (q=关键词 + 筛选条件) → 按平台、分类、地域、时间精细筛选
```

根据用户需求选择相关步骤即可。

## On Failure

- 400：参数错误（无效平台名、排序字段、dateRestrict 格式等）
- 401：缺少 API Key → 检查 config.json
- 403：API Key 无效 → 更换 api_key
- 429：并发上限 → 稍后重试
- 503：服务不可用（ES 连接失败） → 可重试一次
- 504：查询超时 → 缩小查询范围
- 结果为空 → 放宽条件（减少关键词、扩大时间范围、换平台）

错误响应为 Google API 格式：`{"error": {"code": N, "message": "...", "errors": [...]}}`

## 工具详细说明

### search — 热榜关键词搜索

`cx` 始终为 `trending`（CLI 自动设置）。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `q` | string | 否 | — | 查询字符串，支持运算符语法（见 `references/operators.md`） |
| `num` | int | 否 | 10 | 每页条数（1-100） |
| `start` | int | 否 | 1 | 起始位置（从 1 开始） |
| `sort` | string | 否 | hot:desc | 排序：`hot:desc`、`time:desc`、`rank:asc` |
| `fields` | string | 否 | 全部 | 返回字段列表，逗号分隔 |

```bash
node scripts/cli.js search --q "AI platform:weibo" --num 10
node scripts/cli.js search --q "新能源 dateRestrict:d7"
node scripts/cli.js search --q "AI dateRestrict:d7" --sort hot:desc --num 20
```

### trending_now — 获取当前热榜

自动设置 `dateRestrict:h1` 和 `sort=hot:desc`。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `platform` | string | 是 | — | 平台英文名（weibo、douyin、baidu 等） |
| `level_1` | string | 否 | — | 一级分类筛选 |
| `city` | string | 否 | — | 城市筛选（同城榜单用） |
| `num` | int | 否 | 50 | 返回条数 |

```bash
node scripts/cli.js trending_now --platform weibo
node scripts/cli.js trending_now --platform douyin_tongcheng --city 北京
```

### list_platforms — 查看所有平台

本地执行，无需参数，无需调用服务端。返回 6 个分类、44 个平台（37 active、7 inactive）。inactive 平台默认排除，可通过 `platform:` 运算符显式指定。

```bash
node scripts/cli.js list_platforms
```

## 运算符语法与响应字段

运算符语法、排序参数、组合示例详见 `references/operators.md`。
响应格式、pagemap 字段说明详见 `references/fields.md`。

## 数据范围

- 44 个热榜/排行榜平台（ES 6689 集群 `rank_detail_*` 索引）
- 6 个分类：社交媒体、新闻资讯、搜索引擎、国际平台、汽车平台、其他平台
- 默认查询最近 24 小时，所有时间基于北京时间（UTC+8）

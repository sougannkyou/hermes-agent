---
name: istarshine-label-authorized-media
description: >
  采编权（媒体资质）标签库，提供约 140 个持有采编权的媒体机构标签 ID 和分组信息。
  配合 istarshine-douyin-weibo-search 或 istarshine-domestic-web-wide-search 的
  labelDistribution 和 labelFirstPost 统计功能使用。
  当需要按采编权媒体维度进行标签统计分析时，从本 Skill 获取 label_id 列表传给搜索 Skill。
license: "Proprietary. See LICENSE.txt for complete terms."
metadata:
  version: 0.21.3
  author: istarshine
  display_name: "采编权媒体标签"
  tags:
    - 标签
---

# istarshine-label-authorized-media — 采编权媒体标签

采编权（媒体资质）标签库，包含约 140 个持有采编权的媒体机构标签，按机构名称/主办单位、地域所在省、媒体性质、媒体等级四个维度分组。

本 Skill 是纯文档型，不包含 CLI 工具。它为搜索 Skill 的标签统计功能提供 label_id 参考：
- `istarshine-douyin-weibo-search` 的 `labelDistribution` / `labelFirstPost`
- `istarshine-domestic-web-wide-search` 的 `labelDistribution` / `labelFirstPost`

## 标签库结构

标签库 ID：`kg_1556`

| 分组 | group_id | 数量 | 说明 | 示例 |
|------|----------|------|------|------|
| 机构名称/主办单位 | `kg_group_1774836011313` | 100 | 媒体机构 | 上海报业集团、上海广播电视台 |
| 地域所在省 | `kg_group_1774836105342` | 32 | 省/市 | 北京市、上海市、广东省 |
| 媒体性质 | `kg_group_1774258977267` | 4 | 性质分类 | 中央、党媒、官媒、自媒 |
| 媒体等级 | `kg_group_1774259037898` | 4 | 等级分类 | 中央、省级、地方、商业 |

## 使用方式

在搜索 Skill 的 stats 工具中，`labelIds` 参数支持三种粒度：

| 格式 | 说明 | 示例 |
|------|------|------|
| `kg_1556` | 整个采编权标签库的所有标签 | 查询所有采编权媒体的分布 |
| `kg_group_1774836011313` | 某个分组下的所有标签 | 只查机构名称/主办单位分布 |
| `22998` | 单个具体的 label_id | 只查"党媒"这个标签的匹配数据 |

```json
{
  "q": "新能源汽车 dateRestrict:d7",
  "cx": "posts",
  "metrics": [
    {
      "type": "labelDistribution",
      "labelIds": ["kg_group_1774258977267"],
      "topN": 10
    }
  ]
}
```

## 常用 label_id 速查

### 媒体性质（kg_group_1774258977267）

| label_id | label_name |
|----------|------------|
| `22999` | 中央 |
| `22998` | 党媒 |
| `22995` | 官媒 |
| `22997` | 自媒 |

### 媒体等级（kg_group_1774259037898）

| label_id | label_name |
|----------|------------|
| `23039` | 中央 |
| `23038` | 省级 |
| `23040` | 地方 |
| `23035` | 商业媒体 |

### 机构名称/主办单位（kg_group_1774836011313）— 部分示例

| label_id | label_name |
|----------|------------|
| `23042` | 上海报业集团 |
| `23052` | 上海广播电视台 |
| `23063` | 深圳报业集团 |

> 完整的 label_id 列表可通过搜索 Skill 的 `list_labels` 工具获取（`label_type=cbq`）。

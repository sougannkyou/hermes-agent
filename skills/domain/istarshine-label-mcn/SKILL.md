---
name: istarshine-label-mcn
description: >
  MCN 机构标签库，提供约 11,000+ 个 MCN 机构的标签 ID 和分组信息。
  配合 istarshine-douyin-weibo-search 或 istarshine-domestic-web-wide-search 的
  labelDistribution 和 labelFirstPost 统计功能使用。
  当需要按 MCN 机构维度进行标签统计分析时，从本 Skill 获取 label_id 列表传给搜索 Skill。
license: "Proprietary. See LICENSE.txt for complete terms."
metadata:
  version: 0.21.2
  author: istarshine
  display_name: "MCN 机构标签"
  tags:
    - 标签
---

# istarshine-label-mcn — MCN 机构标签

MCN（Multi-Channel Network）机构标签库，包含约 11,000+ 个 MCN 机构标签，按公司名称、省/市、平台名称三个维度分组。

本 Skill 是纯文档型，不包含 CLI 工具。它为搜索 Skill 的标签统计功能提供 label_id 参考：
- `istarshine-douyin-weibo-search` 的 `labelDistribution` / `labelFirstPost`
- `istarshine-domestic-web-wide-search` 的 `labelDistribution` / `labelFirstPost`

## 标签库结构

标签库 ID：`kg_1333`

| 分组 | group_id | 数量 | 说明 | 示例 |
|------|----------|------|------|------|
| 公司名称 | `kg_group_26717` | ~11,577 | MCN 公司 | 无忧传媒、蜂群文化 |
| 省/市 | `kg_group_26718` | ~32 | 地域 | 北京、上海、广东 |
| 平台名称 | `kg_group_31468` | ~3 | 平台 | 抖音、微博、小红书 |

## 使用方式

在搜索 Skill 的 stats 工具中，`labelIds` 参数支持三种粒度：

| 格式 | 说明 | 示例 |
|------|------|------|
| `kg_1333` | 整个 MCN 标签库的所有标签 | 查询所有 MCN 机构的分布 |
| `kg_group_26717` | 某个分组下的所有标签 | 只查 MCN 公司名称分布 |
| `259242` | 单个具体的 label_id | 只查"抖音"这个标签的匹配数据 |

可以混合使用：

```json
{
  "q": "新能源汽车 dateRestrict:d7",
  "cx": "posts",
  "metrics": [
    {
      "type": "labelDistribution",
      "labelIds": ["kg_group_26717"],
      "topN": 20
    }
  ]
}
```

也可以查整个 MCN 标签库：

```json
{"type": "labelDistribution", "labelIds": ["kg_1333"], "topN": 20}
```

或查单个标签：

```json
{"type": "labelDistribution", "labelIds": ["259242", "259244"]}
```

## 常用 label_id 速查

### 平台名称（kg_group_31468）

| label_id | label_name |
|----------|------------|
| `259242` | 抖音 |
| `259244` | 新浪微博 |
| `259243` | 小红书 |

### 省/市（kg_group_26718）— 部分示例

| label_id | label_name |
|----------|------------|
| `168553` | 上海市 |
| `168558` | 云南省 |
| `168548` | 内蒙古自治区 |

> 完整的 label_id 列表可通过搜索 Skill 的 `list_labels` 工具获取（`label_type=mcn`）。

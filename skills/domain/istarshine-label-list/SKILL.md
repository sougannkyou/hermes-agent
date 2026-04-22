---
api:
  auth:
    env_key: ISTARSHINE_API_KEY
    obtain_url: https://skills.istarshine.com/settings/api-keys
    type: bearer
  endpoints:
  - description: 通用标签查询：按 kg_id 查分组，按 group_id 查标签列表，按 label_id 查标签详情
    method: GET
    params:
      group_id:
        description: 分组 ID，如 kg_group_26717
        required: false
        type: string
      kg_id:
        description: 标签库 ID，如 kg_1333（MCN）、kg_1556（采编权）
        required: true
        type: string
      label_id:
        description: 具体标签 ID，如 259242
        required: false
        type: string
    path: /acp/v1/skill-run/istarshine-label-list/api/labels/list
  metering: per_request
  rate_limit: 100/day
description: '通用标签查询工具，支持按标签库 ID（kg_xxxx）查询分组列表， 按分组 ID（kg_group_xxxx）查询标签列表，按具体标签
  ID 查询标签详情。 返回 label_id、label_name、label_desc 等信息，供搜索 Skill 的标签统计功能使用。

  '
license: Proprietary. See LICENSE.txt for complete terms.
metadata:
  author: istarshine
  display_name: 标签查询
  openclaw:
    emoji: 🏷️
    primaryEnv: ISTARSHINE_API_KEY
    requires:
      bins:
      - node
      env:
      - ISTARSHINE_API_KEY
  tags:
  - 标签
  version: 0.21.2
name: istarshine-label-list
---

# istarshine-label-list — 标签查询 Skill

通用标签查询工具，直接查询知识平台标签库，支持三种查询粒度。

## 三种查询方式

| 参数组合 | 返回内容 | 用途 |
|---------|---------|------|
| `kg_id` | 分组概览（group_id、group_name、count） | 了解标签库有哪些分组 |
| `kg_id` + `group_id` | 标签列表（label_id、label_name、label_desc） | 获取某分组下所有标签 |
| `kg_id` + `label_id` | 标签详情（label_id、label_name、label_desc、group） | 查询单个标签信息 |

## 已知标签库

| kg_id | 名称 | 说明 |
|-------|------|------|
| `kg_1333` | MCN 机构 | 详见 `istarshine-label-mcn` |
| `kg_1556` | 采编权 | 详见 `istarshine-label-authorized-media` |

## 配置

编辑 `scripts/config.json`：

```json
{
  "server_url": "http://your-server:8001"
}
```

## 工具

| 工具 | 用途 |
|------|------|
| `list` | 查询标签库分组 / 标签列表 / 标签详情 |

## 示例

```bash
# 查 MCN 标签库有哪些分组
node scripts/cli.js list --kg_id kg_1333

# 查 MCN 公司名称分组下的所有标签
node scripts/cli.js list --kg_id kg_1333 --group_id kg_group_26717

# 查单个标签详情
node scripts/cli.js list --kg_id kg_1333 --label_id 259242

# 查采编权标签库分组
node scripts/cli.js list --kg_id kg_1556
```

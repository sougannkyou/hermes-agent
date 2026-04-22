---
api:
  auth:
    env_key: ISTARSHINE_API_KEY
    obtain_url: https://skills.istarshine.com/settings/api-keys
    type: bearer
  endpoints:
  - description: 将分享短链、移动端链接转换为标准 URL
    method: POST
    params:
      site_domain:
        description: 平台域名（支持：微信、抖音、快手、小红书、头条、微博、西瓜）mp.weixin.qq.com、douyin.com、kuaishou.com、xiaohongshu.com、toutiao.com、weibo.com、ixigua.com
        required: true
        type: string
      url:
        description: 用户提供的原始链接
        required: true
        type: string
    path: /acp/v1/skill-run/istarshine-normalize-url/api/url/normalize
  metering: per_request
  rate_limit: 100/day
description: '将抖音、微博、微信、快手、小红书、头条、西瓜视频的分享短链、移动端链接等非标准 URL 转换为系统可查询的标准 URL。 当用户提供上述平台的分享短链、移动端链接或其他非标准
  URL，需要在查询前转换为标准格式时使用。 不要用于不支持的平台链接。

  '
license: Proprietary. See LICENSE.txt for complete terms.
metadata:
  author: istarshine
  display_name: URL 归一化
  openclaw:
    emoji: 🔗
    primaryEnv: ISTARSHINE_API_KEY
    requires:
      bins:
      - node
      env:
      - ISTARSHINE_API_KEY
  tags:
  - 数据
  version: 0.21.2
name: istarshine-normalize-url
---

# istarshine-normalize-url — URL 归一化 Skill

## When to use

- 用户提供了抖音、微博、微信、快手、小红书、头条或西瓜视频的分享短链、移动端链接
- 需要将非标准 URL 转换为系统可查询的标准 URL
- 在用搜索工具查询特定帖子前，需要先归一化链接

## When NOT to use

- 不在支持列表中的平台链接
- URL 已经是标准格式（完整的 PC 端链接）

## 支持的平台

| 平台 | site_domain | 说明 |
|------|-------------|------|
| 微信公众号 | `mp.weixin.qq.com` | 微信文章链接 |
| 抖音 | `douyin.com` | 抖音短视频链接 |
| 快手 | `kuaishou.com` | 快手短视频链接 |
| 小红书 | `xiaohongshu.com` | 小红书笔记链接 |
| 今日头条 | `toutiao.com` | 头条文章/视频链接 |
| 微博 | `weibo.com` | 微博帖子链接 |
| 西瓜视频 | `ixigua.com` | 西瓜视频链接 |

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
| `normalize_url` | URL 归一化 | 将分享短链、移动端链接转换为标准 URL（支持 7 个平台） |

## 工具详细说明

### normalize_url

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `url` | string | 是 | 用户提供的原始链接 |
| `site_domain` | string | 是 | 平台域名：`mp.weixin.qq.com`、`douyin.com`、`kuaishou.com`、`xiaohongshu.com`、`toutiao.com`、`weibo.com`、`ixigua.com` |

返回：`original_url`（原始链接）、`normalized_url`（标准链接）、`site_domain`（平台域名）。

```bash
node scripts/cli.js normalize_url --url https://v.douyin.com/xxx --site_domain douyin.com
node scripts/cli.js normalize_url --url https://m.weibo.cn/xxx --site_domain weibo.com
node scripts/cli.js normalize_url --url https://www.kuaishou.com/short-video/xxx --site_domain kuaishou.com
node scripts/cli.js normalize_url --url https://www.xiaohongshu.com/explore/xxx --site_domain xiaohongshu.com
node scripts/cli.js normalize_url --url https://mp.weixin.qq.com/s/xxx --site_domain mp.weixin.qq.com
node scripts/cli.js normalize_url --url https://www.toutiao.com/article/xxx --site_domain toutiao.com
node scripts/cli.js normalize_url --url https://www.ixigua.com/xxx --site_domain ixigua.com
```

## On Failure

- 401：缺少 API Key → 检查 config.json
- 403：API Key 无效 → 更换 api_key
- 502：外部 API 异常 → 可重试一次

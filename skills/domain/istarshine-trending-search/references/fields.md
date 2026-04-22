# 热榜响应字段说明

## pagemap 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | string | 热榜标题 |
| `platform` | string | 平台英文名 |
| `platform_cn` | string | 平台中文名 |
| `rank_top` | int | 最高排名（历史最佳名次） |
| `rank_num` | int | 上榜次数（被采集到在榜的次数） |
| `hot_top` | int | 历史最高热度值 |
| `level_1` | string | 一级分类（话题、热搜、热议、体育等） |
| `level_2` | string \| null | 二级分类（汽车热榜、实时上升热点等） |
| `city` | string \| null | 城市（同城榜单） |
| `province` | string \| null | 省份 |
| `roll_ctime` | string | 最近一次上榜时间（ISO 8601 北京时间） |
| `roll_etime` | string \| null | 最近一次下榜时间（ISO 8601 北京时间） |
| `rank_duration` | int \| null | 在榜总时长（秒） |
| `user_name` | string \| null | 发布者/来源 |
| `topic_tag` | array \| null | 话题标签（如 ["热"]） |
| `first_ctime` | string \| null | 首次上榜时间（ISO 8601 北京时间） |
| `gather_site_domain` | string \| null | 站点域名 |

## 响应结构（Google CSE JSON 格式）

```json
{
  "kind": "customsearch#search",
  "queries": {
    "request": [{
      "totalResults": "156",
      "count": 10,
      "startIndex": 1,
      "searchTerms": "AI platform:weibo",
      "cx": "trending"
    }]
  },
  "searchInformation": {
    "searchTime": 0.23,
    "totalResults": "156"
  },
  "items": [{
    "kind": "customsearch#result",
    "title": "AI大模型引发热议",
    "link": "https://s.weibo.com/weibo?q=AI大模型",
    "snippet": "微博 · 话题 · 最高第1名",
    "pagemap": { ... }
  }]
}
```

## 错误响应（Google API 格式）

```json
{
  "error": {
    "code": 400,
    "message": "Invalid platform: xxx",
    "errors": [{"message": "Invalid platform: xxx", "domain": "global", "reason": "invalid"}]
  }
}
```

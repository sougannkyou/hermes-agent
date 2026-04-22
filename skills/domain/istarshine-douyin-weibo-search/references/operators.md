# Google 搜索运算符语法

## q 参数运算符

| 运算符 | 说明 | 示例 |
|--------|------|------|
| （无前缀） | 关键词精确短语匹配，多个关键词之间为 AND 关系 | `新能源 汽车` |
| `"..."` | 显式引号短语匹配（行为与不加引号一致，均强制精确匹配） | `"新能源汽车"` |
| `site:` | 平台域名过滤 | `site:iesdouyin.com`、`site:weibo.com` |
| `url:` | 帖文链接精确匹配 | `url:https://www.iesdouyin.com/share/video/xxx` |
| `dateRestrict:` | 时间范围：`h[N]`=N小时、`d[N]`=N天、`w[N]`=N周、`m[N]`=N月 | `dateRestrict:d7` |
| `author:` | 作者精确匹配 | `author:张三` |
| `sentiment:` | 情感过滤：`positive`、`neutral`、`negative` | `sentiment:positive` |
| `followers:` | 粉丝数范围筛选 | `followers:500000..`（≥50万） |
| `replies:` | 评论数范围筛选 | `replies:10000..` |
| `likes:` | 点赞数范围筛选 | `likes:10000..` |
| `reposts:` | 转发数范围筛选 | `reposts:1000..` |
| `visits:` | 访问量范围筛选 | `visits:100000..` |
| `collections:` | 收藏数范围筛选 | `collections:5000..` |
| `friends:` | 关注数范围筛选 | `friends:..100` |
| `statuses:` | 发帖数范围筛选 | `statuses:1000..` |
| `-` 前缀 | 排除条件（可用于任何运算符） | `-site:weibo.com` |

范围筛选语法：`min..max`（双边）、`min..`（仅下限）、`..max`（仅上限）、`数值`（等价于 ≥ 该值）。

未识别的运算符会被当作普通关键词处理（同样强制精确匹配）。

## 排序参数

`sort` 参数格式为 `field:order`（order 为 `asc` 或 `desc`）：

| 排序字段 | 说明 | 示例 |
|----------|------|------|
| `ctime` | 发布时间（默认） | `sort=ctime:desc` |
| `user.followers_count` | 粉丝数 | `sort=user.followers_count:desc` |
| `reply_count` | 评论数 | `sort=reply_count:desc` |
| `like_count` | 点赞数 | `sort=like_count:desc` |
| `repost_count` | 转发数 | `sort=repost_count:desc` |
| `visit_count` | 访问量 | `sort=visit_count:desc` |
| `collection_count` | 收藏数 | `sort=collection_count:desc` |
| `user.friends_count` | 关注数 | `sort=user.friends_count:asc` |
| `user.statuses_count` | 发帖数 | `sort=user.statuses_count:desc` |

## 组合示例

```
新能源 site:iesdouyin.com dateRestrict:d7
```
搜索抖音平台最近 7 天内包含"新能源"的内容。

```
AI "人工智能" -site:weibo.com author:张三 sentiment:positive
```
搜索作者为"张三"、情感为正面、排除微博平台的包含"AI"和"人工智能"的内容。

```
新能源 followers:500000.. site:iesdouyin.com dateRestrict:d7
```
搜索抖音平台最近 7 天内、粉丝数 ≥ 50 万的大V发布的包含"新能源"的内容。

```
小米汽车 replies:10000.. likes:5000..
```
搜索评论数 ≥ 1 万且点赞数 ≥ 5000 的包含"小米汽车"的热门内容。

## 布尔逻辑运算符

支持 Google CSE 风格的布尔逻辑运算符，用于组合多个搜索条件：

| 运算符 | 说明 | 示例 |
|--------|------|------|
| （空格） | AND（默认），多个关键词同时匹配 | `特斯拉 电池` → 同时包含"特斯拉"和"电池" |
| `OR` | OR，匹配任一关键词（必须大写） | `特斯拉 OR 比亚迪` → 包含"特斯拉"或"比亚迪" |
| `(...)` | 括号分组，控制优先级 | `(特斯拉 OR 比亚迪) 电池` → ("特斯拉"或"比亚迪") 且 "电池" |
| `-` | 排除，不包含指定内容 | `特斯拉 -广告` → 包含"特斯拉"但不含"广告" |

### 布尔逻辑规则

- `OR` 必须大写，小写 `or` 会被当作普通关键词
- 运算符（`dateRestrict:`、`site:` 等）不参与 OR/括号分组，始终作为全局 AND 条件
- 排除词（`-xxx`）不参与 OR/括号分组，始终作为全局排除条件
- 括号可嵌套：`((A OR B) C) OR (D E)`

### 布尔逻辑示例

```
特斯拉 OR 比亚迪 dateRestrict:d7
```
搜索最近 7 天内包含"特斯拉"或"比亚迪"的内容。

```
(特斯拉 OR 比亚迪) 电池 dateRestrict:d7
```
搜索最近 7 天内包含"电池"且包含"特斯拉"或"比亚迪"的内容。

```
(新能源 OR 电动车) (补贴 OR 政策) dateRestrict:d7
```
搜索最近 7 天内同时满足两个条件的内容：包含"新能源"或"电动车"，且包含"补贴"或"政策"。

```
特斯拉 -广告 -推广 dateRestrict:d7
```
搜索最近 7 天内包含"特斯拉"但不含"广告"和"推广"的内容。

```
(AI OR 人工智能) -site:weibo.com dateRestrict:d3
```
搜索最近 3 天内包含"AI"或"人工智能"的内容，排除微博平台。

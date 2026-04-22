# 热榜搜索运算符语法

## q 参数运算符

| 运算符 | 说明 | 示例 |
|--------|------|------|
| （无前缀） | 关键词匹配 `title` 字段，多个关键词之间为 AND 关系 | `AI 人工智能` |
| `"..."` | 精确短语匹配（`title` 字段 `match_phrase`） | `"人工智能"` |
| `platform:` | 平台筛选，映射到 ES 索引选择，多个为 OR 关系 | `platform:weibo`、`platform:douyin` |
| `category:` | 一级分类精确匹配（`type.level_1`） | `category:话题`、`category:热搜` |
| `subcategory:` | 二级分类精确匹配（`type.level_2`） | `subcategory:足球` |
| `city:` | 城市精确匹配（`location.city`） | `city:北京`、`city:上海` |
| `province:` | 省份精确匹配（`location.province`） | `province:广东` |
| `dateRestrict:` | 时间范围：`h[N]`=N小时、`d[N]`=N天、`w[N]`=N周、`m[N]`=N月 | `dateRestrict:h1`、`dateRestrict:d7` |
| `-` 前缀 | 排除条件（可用于任何运算符） | `-platform:weibo`、`-category:广告` |

`q` 参数可以为空，此时仅通过运算符筛选。未识别的运算符会被当作普通关键词处理。

## 排序参数

`sort` 参数格式为 `field:order`：

| 排序字段 | ES 映射字段 | 说明 | 示例 |
|----------|-------------|------|------|
| `hot` | `rank.hot` | 热度值（默认） | `sort=hot:desc` |
| `time` | `roll.ctime` | 滚动排行时间 | `sort=time:desc` |
| `rank` | `rank.rank` | 排名位置 | `sort=rank:asc` |

默认排序为 `hot:desc`（按热度降序）。

## 组合示例

```
AI platform:weibo dateRestrict:d7
```
搜索微博平台最近 7 天内包含"AI"的热榜数据。

```
platform:douyin platform:weibo category:话题
```
搜索抖音和微博平台的话题类热榜（无关键词，纯筛选）。

```
"人工智能" -platform:baidu province:广东
```
搜索广东省、排除百度平台的包含"人工智能"精确短语的热榜数据。

```
city:北京 platform:douyin_tongcheng dateRestrict:h1
```
获取抖音同城北京最近 1 小时的热榜。

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

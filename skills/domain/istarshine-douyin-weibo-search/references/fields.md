# 可查询字段完整列表

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | text | 标题 |
| `content` | text | 正文内容 |
| `ocr` | text | 图片 OCR 文本 |
| `asr.text` | nested text | 语音识别文本（需使用 contains 操作符） |
| `url` | keyword | 帖文链接 |
| `ctime` | long | 发布时间（Unix 时间戳） |
| `utime` | long | 更新时间（Unix 时间戳） |
| `duration` | integer | 视频时长 |
| `wtype` | integer | 数据类型：1=原创, 2=转发, 7=评论, 8=弹幕 |
| `is_ad` | integer | 是否广告 |
| `deleted` | integer | 是否已删除 |
| `gather.site_domain` | keyword | 平台域名：iesdouyin.com / weibo.com |
| `gather.site_name` | keyword | 平台名称：抖音 / 微博 |
| `gather.stime` | long | 采集时间 |
| `gather.gtime` | long | 入库时间 |
| `analysis.sentiment` | integer | 情感值：>0 正面, =0 中性, <0 负面 |
| `analysis.emotion` | keyword | 情绪标签 |
| `analysis.hashtag` | keyword[] | 话题标签 |
| `analysis.keywords` | object | 关键词 |
| `analysis.summary` | text | 摘要 |
| `analysis.find_address` | keyword | 地址识别 |
| `user.name` | keyword | 用户名 |
| `user.gender` | keyword | 性别（仅微博） |
| `user.verified` | integer | 认证状态（抖音） |
| `user.verified_type` | integer | 认证类型（仅微博） |
| `user.followers_count` | integer | 粉丝数 |
| `user.friends_count` | integer | 关注数 |
| `user.statuses_count` | integer | 发帖数 |
| `user.like_count` | integer | 获赞数 |
| `visit_count` | integer | 播放/浏览量 |
| `reply_count` | integer | 评论数 |
| `repost_count` | integer | 转发数 |
| `like_count` | integer | 点赞数 |
| `collection_count` | integer | 收藏数 |
| `position` | keyword | 位置信息 |
| `retweeted.title` | text | 转发原文标题 |
| `retweeted.content` | text | 转发原文内容 |
| `retweeted.url` | keyword | 转发原文链接 |
| `retweeted.mid` | keyword | 转发原文 ID |
| `retweeted.reply_count` | integer | 转发原文评论数 |
| `retweeted.ctime` | long | 转发原文发布时间 |
| `label.label_ids` | keyword[] | 标签 ID 列表（MCN 机构、采编权等） |
| `video_urls` | keyword[] | 视频下载地址列表（仅响应字段，不可用于查询条件） |

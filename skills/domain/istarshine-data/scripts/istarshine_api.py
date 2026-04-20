#!/usr/bin/env python3
"""
智慧星光舆情数据 API 客户端

用于 Hermes Agent 调用智慧星光 API 查询舆情数据。

环境变量:
    ISTARSHINE_API_KEY: API 密钥
    ISTARSHINE_BASE_URL: API 基础 URL（可选，默认 https://api.istarshine.com/v1）

使用示例:
    python istarshine_api.py search "比亚迪" --platforms douyin,weibo --limit 50
    python istarshine_api.py trending --platforms weibo,douyin
    python istarshine_api.py sentiment "比亚迪" --granularity day
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def get_api_key() -> str:
    """获取 API 密钥"""
    key = os.environ.get("ISTARSHINE_API_KEY")
    if not key:
        raise ValueError("ISTARSHINE_API_KEY environment variable not set")
    return key


def get_base_url() -> str:
    """获取 API 基础 URL"""
    return os.environ.get("ISTARSHINE_BASE_URL", "https://api.istarshine.com/v1")


def api_request(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """发送 API 请求"""
    url = f"{get_base_url()}{endpoint}"
    headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }
    
    req = Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    
    try:
        with urlopen(req, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        return {
            "success": False,
            "error": f"HTTP {e.code}: {e.reason}",
            "details": error_body,
        }
    except URLError as e:
        return {
            "success": False,
            "error": f"URL Error: {e.reason}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def search(
    query: str,
    platforms: Optional[List[str]] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    content_types: Optional[List[str]] = None,
    limit: int = 20,
    sort_by: str = "engagement",
    sort_order: str = "desc",
    sentiment: Optional[str] = None,
) -> Dict[str, Any]:
    """搜索帖子、评论等内容"""
    if not date_end:
        date_end = datetime.now().strftime("%Y-%m-%d")
    if not date_start:
        date_start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    data = {
        "query": query,
        "dateRange": {"start": date_start, "end": date_end},
        "limit": min(limit, 100),
        "sortBy": sort_by,
        "sortOrder": sort_order,
    }
    
    if platforms:
        data["platforms"] = platforms
    if content_types:
        data["contentTypes"] = content_types
    if sentiment:
        data["sentiment"] = sentiment
    
    return api_request("/api/search", data)


def trending(
    platforms: Optional[List[str]] = None,
    category: str = "all",
    limit: int = 50,
) -> Dict[str, Any]:
    """查询热搜/热词"""
    data = {"category": category, "limit": limit}
    if platforms:
        data["platforms"] = platforms
    return api_request("/api/trending", data)


def sentiment_analysis(
    query: str,
    platforms: Optional[List[str]] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    granularity: str = "day",
) -> Dict[str, Any]:
    """情感分析"""
    if not date_end:
        date_end = datetime.now().strftime("%Y-%m-%d")
    if not date_start:
        date_start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    data = {
        "query": query,
        "dateRange": {"start": date_start, "end": date_end},
        "granularity": granularity,
    }
    if platforms:
        data["platforms"] = platforms
    return api_request("/api/sentiment", data)


def compare(
    query: str,
    platforms: List[str],
    metrics: Optional[List[str]] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
) -> Dict[str, Any]:
    """平台对比"""
    if not date_end:
        date_end = datetime.now().strftime("%Y-%m-%d")
    if not date_start:
        date_start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    return api_request("/api/compare", {
        "query": query,
        "platforms": platforms,
        "metrics": metrics or ["volume", "engagement", "sentiment"],
        "dateRange": {"start": date_start, "end": date_end},
    })


def label_stats(
    label_type: str,
    query: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """标签统计"""
    data = {"labelType": label_type, "limit": limit}
    if query:
        data["query"] = query
    if platforms:
        data["platforms"] = platforms
    return api_request("/api/label-stats", data)


def main():
    parser = argparse.ArgumentParser(description="智慧星光舆情数据 API 客户端")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # search
    sp = subparsers.add_parser("search", help="搜索帖子/评论")
    sp.add_argument("query", help="搜索关键词")
    sp.add_argument("--platforms", help="平台列表，逗号分隔")
    sp.add_argument("--start", help="开始日期 (YYYY-MM-DD)")
    sp.add_argument("--end", help="结束日期 (YYYY-MM-DD)")
    sp.add_argument("--types", help="内容类型，逗号分隔")
    sp.add_argument("--limit", type=int, default=20)
    sp.add_argument("--sort", default="engagement")
    sp.add_argument("--order", default="desc")
    sp.add_argument("--sentiment", help="情感过滤")
    
    # trending
    tp = subparsers.add_parser("trending", help="查询热搜/热词")
    tp.add_argument("--platforms", help="平台列表，逗号分隔")
    tp.add_argument("--category", default="all")
    tp.add_argument("--limit", type=int, default=50)
    
    # sentiment
    sep = subparsers.add_parser("sentiment", help="情感分析")
    sep.add_argument("query", help="关键词")
    sep.add_argument("--platforms", help="平台列表，逗号分隔")
    sep.add_argument("--start", help="开始日期")
    sep.add_argument("--end", help="结束日期")
    sep.add_argument("--granularity", default="day")
    
    # compare
    cp = subparsers.add_parser("compare", help="平台对比")
    cp.add_argument("query", help="关键词")
    cp.add_argument("--platforms", required=True, help="平台列表，逗号分隔")
    cp.add_argument("--metrics", help="对比指标，逗号分隔")
    cp.add_argument("--start", help="开始日期")
    cp.add_argument("--end", help="结束日期")
    
    # label-stats
    lp = subparsers.add_parser("label-stats", help="标签统计")
    lp.add_argument("label_type", help="标签类型 (mcn, media, kol, region)")
    lp.add_argument("--query", help="关键词过滤")
    lp.add_argument("--platforms", help="平台过滤，逗号分隔")
    lp.add_argument("--limit", type=int, default=20)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == "search":
            result = search(
                query=args.query,
                platforms=args.platforms.split(",") if args.platforms else None,
                date_start=args.start,
                date_end=args.end,
                content_types=args.types.split(",") if args.types else None,
                limit=args.limit,
                sort_by=args.sort,
                sort_order=args.order,
                sentiment=args.sentiment,
            )
        elif args.command == "trending":
            result = trending(
                platforms=args.platforms.split(",") if args.platforms else None,
                category=args.category,
                limit=args.limit,
            )
        elif args.command == "sentiment":
            result = sentiment_analysis(
                query=args.query,
                platforms=args.platforms.split(",") if args.platforms else None,
                date_start=args.start,
                date_end=args.end,
                granularity=args.granularity,
            )
        elif args.command == "compare":
            result = compare(
                query=args.query,
                platforms=args.platforms.split(","),
                metrics=args.metrics.split(",") if args.metrics else None,
                date_start=args.start,
                date_end=args.end,
            )
        elif args.command == "label-stats":
            result = label_stats(
                label_type=args.label_type,
                query=args.query,
                platforms=args.platforms.split(",") if args.platforms else None,
                limit=args.limit,
            )
        else:
            parser.print_help()
            sys.exit(1)
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except ValueError as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()

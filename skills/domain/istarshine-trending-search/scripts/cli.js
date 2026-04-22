#!/usr/bin/env node
/**
 * CLI 入口：将工具调用转发至 FastAPI Server（热榜热搜版）。
 *
 * 用法：node scripts/cli.js search --q "AI platform:weibo" --num 10
 *       node scripts/cli.js trending_now --platform weibo
 *       node scripts/cli.js list_platforms
 *       node scripts/cli.js search '{"q":"AI","num":10}'  (JSON 兼容)
 */

"use strict";

const fs = require("fs");
const path = require("path");
const http = require("http");
const https = require("https");

// ---------- 配置加载 ----------

const CONFIG_PATH = path.join(__dirname, "config.json");

function loadConfig() {
  const raw = fs.readFileSync(CONFIG_PATH, "utf-8");
  return JSON.parse(raw);
}

const config = loadConfig();
const SERVER_URL = config.server_url.replace(/\/+$/, "");
const API_KEY = process.env.ISTARSHINE_API_KEY;
const TIMEOUT_MS = (config.timeout_seconds || 120) * 1000;

if (!API_KEY) {
  console.error("错误: 未设置环境变量 ISTARSHINE_API_KEY\n\n  export ISTARSHINE_API_KEY=<your-api-key>\n\n获取 API Key: https://skills.istarshine.com/settings/api-keys");
  process.exit(1);
}

// ---------- 命令行参数解析 ----------

function parseCliArgs(args) {
  const result = {};
  let i = 0;
  while (i < args.length) {
    const arg = args[i];
    if (arg.startsWith("--")) {
      let key, value;
      if (arg.includes("=")) {
        const eqIdx = arg.indexOf("=");
        key = arg.slice(2, eqIdx);
        value = arg.slice(eqIdx + 1);
      } else {
        key = arg.slice(2);
        i++;
        value = i < args.length ? args[i] : "";
      }
      result[key] = coerceValue(value);
    }
    i++;
  }
  return result;
}

function coerceValue(v) {
  if ((v.startsWith("[") && v.endsWith("]")) || (v.startsWith("{") && v.endsWith("}"))) {
    try { return JSON.parse(v); } catch (_) { /* fall through */ }
  }
  if (v === "true") return true;
  if (v === "false") return false;
  if (/^-?\d+$/.test(v)) return parseInt(v, 10);
  if (/^-?\d+\.\d+$/.test(v)) return parseFloat(v);
  if (v.includes(",")) return v.split(",");
  return v;
}

async function resolveArgs(args) {
  if (args.length > 0 && args[0].startsWith("--")) {
    return parseCliArgs(args);
  }
  if (args.length > 0) {
    let raw = args[0];
    if (raw.charCodeAt(0) === 0xfeff) raw = raw.slice(1);
    return JSON.parse(raw);
  }
  const raw = await readStdin();
  return JSON.parse(raw);
}

// ---------- HTTP 转发（零依赖） ----------

function request(method, endpoint, body) {
  return new Promise((resolve) => {
    const url = new URL(`${SERVER_URL}${endpoint}`);
    url.searchParams.set("key", API_KEY);
    const isHttps = url.protocol === "https:";
    const mod = isHttps ? https : http;

    const headers = {};
    let payload;
    if (body !== undefined) {
      payload = Buffer.from(JSON.stringify(body), "utf-8");
      headers["Content-Type"] = "application/json";
      headers["Content-Length"] = payload.length;
    }

    const opts = {
      hostname: url.hostname,
      port: url.port || (isHttps ? 443 : 80),
      path: url.pathname + url.search,
      method,
      headers,
      timeout: TIMEOUT_MS,
    };

    const req = mod.request(opts, (res) => {
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => resolve(Buffer.concat(chunks).toString("utf-8")));
    });

    req.on("timeout", () => {
      req.destroy();
      resolve(JSON.stringify({ code: 504, message: "请求超时，请稍后重试", data: null }));
    });
    req.on("error", (err) => {
      if (err.code === "ECONNREFUSED" || err.code === "ENOTFOUND") {
        resolve(JSON.stringify({ code: 503, message: "无法连接到搜索服务，请检查服务地址配置", data: null }));
      } else {
        resolve(JSON.stringify({ code: 500, message: "请求失败，请稍后重试", data: null }));
      }
    });

    if (payload) req.write(payload);
    req.end();
  });
}

function forwardGet(endpoint) {
  return request("GET", endpoint);
}

// ---------- 内置平台数据（44 个平台） ----------

const PLATFORM_DATA = {
  "社交媒体": [
    { platform: "weibo", platform_cn: "微博", status: "active" },
    { platform: "weibo_tongcheng", platform_cn: "微博同城", status: "active" },
    { platform: "douyin", platform_cn: "抖音", status: "active" },
    { platform: "douyin_tongcheng", platform_cn: "抖音同城", status: "active" },
    { platform: "kuaishou", platform_cn: "快手", status: "active" },
    { platform: "kuaishou_tongcheng", platform_cn: "快手同城", status: "active" },
    { platform: "xiaohongshu", platform_cn: "小红书", status: "inactive" },
    { platform: "bilibili", platform_cn: "B站", status: "active" },
    { platform: "qq", platform_cn: "QQ", status: "active" },
  ],
  "新闻资讯": [
    { platform: "toutiao", platform_cn: "今日头条", status: "active" },
    { platform: "toutiao_tongcheng", platform_cn: "今日头条同城", status: "active" },
    { platform: "sina", platform_cn: "新浪", status: "active" },
    { platform: "163", platform_cn: "网易", status: "active" },
    { platform: "sohu", platform_cn: "搜狐", status: "active" },
    { platform: "ifeng", platform_cn: "凤凰网", status: "active" },
    { platform: "chinanews", platform_cn: "中新网", status: "active" },
    { platform: "guancha", platform_cn: "观察者网", status: "active" },
    { platform: "uc", platform_cn: "UC头条", status: "active" },
    { platform: "weixin", platform_cn: "微信公众号", status: "active" },
  ],
  "搜索引擎": [
    { platform: "baidu", platform_cn: "百度", status: "active" },
    { platform: "sogou", platform_cn: "搜狗", status: "active" },
    { platform: "360", platform_cn: "360搜索", status: "active" },
    { platform: "sm", platform_cn: "神马搜索", status: "inactive" },
    { platform: "so", platform_cn: "360搜索(so)", status: "active" },
    { platform: "chinaso", platform_cn: "中国搜索", status: "active" },
  ],
  "国际平台": [
    { platform: "google", platform_cn: "谷歌", status: "active" },
    { platform: "twitter", platform_cn: "推特(X)", status: "active" },
    { platform: "youtube", platform_cn: "YouTube", status: "inactive" },
    { platform: "cryptohunt", platform_cn: "CryptoHunt", status: "inactive" },
  ],
  "汽车平台": [
    { platform: "autohome", platform_cn: "汽车之家", status: "active" },
    { platform: "xcar", platform_cn: "爱卡汽车", status: "active" },
    { platform: "yiche", platform_cn: "易车网", status: "active" },
    { platform: "pcauto", platform_cn: "太平洋汽车", status: "inactive" },
    { platform: "dongchedi", platform_cn: "懂车帝", status: "active" },
  ],
  "其他平台": [
    { platform: "zhihu", platform_cn: "知乎", status: "active" },
    { platform: "douban", platform_cn: "豆瓣", status: "active" },
    { platform: "hupu", platform_cn: "虎扑", status: "active" },
    { platform: "xueqiu", platform_cn: "雪球", status: "active" },
    { platform: "eastmoney", platform_cn: "东方财富", status: "active" },
    { platform: "maimai", platform_cn: "脉脉", status: "active" },
    { platform: "chouti", platform_cn: "抽屉新热榜", status: "inactive" },
    { platform: "acfun", platform_cn: "AcFun", status: "active" },
    { platform: "bjd", platform_cn: "北京日报", status: "inactive" },
    { platform: "thepaper", platform_cn: "澎湃新闻", status: "active" },
  ],
};

// ---------- 工具实现 ----------

async function search({ q, num = 10, start = 1, sort = "hot:desc", fields } = {}) {
  const params = new URLSearchParams({ key: API_KEY, cx: "trending" });
  if (q) params.set("q", q);
  if (num !== 10) params.set("num", String(num));
  if (start !== 1) params.set("start", String(start));
  params.set("sort", sort || "hot:desc");
  if (fields) params.set("fields", Array.isArray(fields) ? fields.join(",") : fields);
  return forwardGet(`/customsearch/v1?${params.toString()}`);
}

async function trending_now({ platform, level_1, city, num = 50 } = {}) {
  if (!platform) {
    return JSON.stringify({
      code: 400,
      message: "必须指定 --platform 参数，可通过 list_platforms 工具查看所有可用平台",
      data: null,
    });
  }

  let q = `platform:${platform} dateRestrict:h1`;
  if (level_1) q += ` category:${level_1}`;
  if (city) q += ` city:${city}`;

  return search({ q, num, sort: "hot:desc" });
}

function list_platforms() {
  return JSON.stringify({
    kind: "istarshine#platforms",
    categories: PLATFORM_DATA,
  });
}

// ---------- CLI 分发 ----------

const TOOLS = {
  search,
  trending_now,
  list_platforms,
};

function readStdin() {
  return new Promise((resolve) => {
    if (process.stdin.isTTY) { resolve("{}"); return; }
    const chunks = [];
    process.stdin.setEncoding("utf-8");
    process.stdin.on("data", (c) => chunks.push(c));
    process.stdin.on("end", () => resolve(chunks.join("").trim() || "{}"));
  });
}

const HELP_TEXT = `istarshine-trending-search — 热榜热搜搜索 CLI

用法:
  node scripts/cli.js <tool> --param value ...
  node scripts/cli.js <tool> '<json>'

工具:
  search          热榜关键词搜索（44 个平台，支持平台/分类/地域/时间筛选）
  trending_now    获取指定平台的实时热榜（自动设置 dateRestrict:h1 + sort=hot:desc）
  list_platforms  查看全部 44 个平台及状态（本地执行，无需服务端）

search 参数:
  --q <string>       查询字符串，支持运算符（platform:、category:、city:、dateRestrict: 等）
  --num <int>        每页条数（1-100），默认 10
  --start <int>      起始位置（从 1 开始），默认 1
  --sort <string>    排序，默认 hot:desc（可选 time:desc、rank:asc）
  --fields <string>  返回字段列表，逗号分隔

trending_now 参数:
  --platform <string>  (必填) 平台英文名（weibo、douyin、baidu 等）
  --level_1 <string>   一级分类筛选
  --city <string>      城市筛选（同城榜单用）
  --num <int>          返回条数，默认 50

list_platforms 参数:
  （无参数）

示例:
  node scripts/cli.js search --q "AI platform:weibo" --num 10
  node scripts/cli.js search --q "新能源 dateRestrict:d7" --sort hot:desc --num 20
  node scripts/cli.js trending_now --platform weibo
  node scripts/cli.js trending_now --platform douyin_tongcheng --city 北京
  node scripts/cli.js list_platforms
`;

async function main() {
  const args = process.argv.slice(2);

  if (args.includes("--help") || args.includes("-h")) {
    console.log(HELP_TEXT);
    process.exit(0);
  }

  if (args.length < 1) {
    console.log(HELP_TEXT);
    process.exit(1);
  }

  const toolName = args[0];
  if (!TOOLS[toolName]) {
    console.log(JSON.stringify({
      code: 400,
      message: `未知工具: ${toolName}，可用工具: ${Object.keys(TOOLS).join(", ")}`,
      data: null,
    }));
    process.exit(1);
  }

  let parsed;
  try {
    parsed = await resolveArgs(args.slice(1));
  } catch (e) {
    console.log(JSON.stringify({ code: 400, message: `参数解析失败: ${e.message}`, data: null }));
    process.exit(1);
  }

  const result = await TOOLS[toolName](parsed);
  console.log(result);
}

main();

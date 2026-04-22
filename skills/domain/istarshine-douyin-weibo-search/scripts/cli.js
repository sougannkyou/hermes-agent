#!/usr/bin/env node
/**
 * CLI 入口：将工具调用转发至 FastAPI Server。
 *
 * 用法：node scripts/cli.js search --cx posts --q "新能源 site:iesdouyin.com" --num 10
 *       node scripts/cli.js stats --q "新能源" --metrics '[{"type":"hotWords","topN":10}]'
 *       node scripts/cli.js list_labels --label_type mcn
 *       node scripts/cli.js search '{"cx":"posts","q":"AI","num":5}'  (JSON 兼容)
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
const TIMEOUT_MS = (config.timeout_seconds || 660) * 1000; // 默认 11 分钟（服务端聚合最长 10 分钟）


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
  // 尝试解析 JSON 数组/对象（如 --metrics '[{"type":"hotWords"}]'）
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
    if (API_KEY) url.searchParams.set("key", API_KEY);
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

function forwardPost(endpoint, body) {
  return request("POST", endpoint, body);
}

function forwardGet(endpoint) {
  return request("GET", endpoint);
}

// ---------- 工具实现 ----------

async function search({ cx, q, num = 10, start = 1, sort, fields } = {}) {
  const params = new URLSearchParams({ ...(API_KEY && { key: API_KEY }), cx, q });
  if (num !== 10) params.set("num", String(num));
  if (start !== 1) params.set("start", String(start));
  if (sort) params.set("sort", sort);
  if (fields) params.set("fields", Array.isArray(fields) ? fields.join(",") : fields);
  return forwardGet(`/customsearch/v1?${params.toString()}`);
}

async function list_labels({ label_type = "mcn" } = {}) {
  if (label_type === "cbq") return forwardGet("/api/labels/cbq");
  return forwardGet("/api/labels/mcn");
}

async function stats({ q = null, cx = null, metrics = [] } = {}) {
  const body = { metrics };
  if (q) body.q = q;
  if (cx) body.cx = cx;

  // 启动 stats 请求（可能耗时数分钟）
  const statsPromise = forwardPost("/api/stats", body);

  // 并发轮询进度，每 3 秒查一次，输出到 stderr
  let polling = true;
  const pollProgress = async () => {
    await new Promise((r) => setTimeout(r, 3000));
    let lastPercent = -1;
    let staleCount = 0;
    while (polling) {
      try {
        const raw = await forwardGet("/api/stats/progress");
        const data = JSON.parse(raw);
        let percent = -1;
        if (data.tasks && data.tasks.length > 0) {
          const running = data.tasks.filter((t) => t.state === "running");
          if (running.length > 0) {
            running.sort((a, b) => a.percent - b.percent);
            percent = running[0].percent;
          }
        } else if (data.percent !== undefined) {
          percent = data.percent;
        }

        if (percent >= 0) {
          if (percent === lastPercent) { staleCount++; } else { staleCount = 0; lastPercent = percent; }
          if (percent === 99 && staleCount > 5) {
            process.stderr.write(`\r统计查询中... (服务端处理中)`);
          } else {
            process.stderr.write(`\r统计查询中... ${percent}%`);
          }
        } else {
          process.stderr.write(`\r统计查询中...`);
        }
      } catch (_) { /* ignore */ }
      await new Promise((r) => setTimeout(r, 3000));
    }
  };

  const progressPromise = pollProgress();
  const result = await statsPromise;
  polling = false;
  await progressPromise.catch(() => {});
  process.stderr.write("\r\x1b[K");
  return result;
}

// ---------- CLI 分发 ----------

const TOOLS = {
  search,
  stats,
  list_labels,
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

const HELP_TEXT = `istarshine-douyin-weibo-search — 抖音微博全量搜索 CLI

用法:
  node scripts/cli.js <tool> --param value ...
  node scripts/cli.js <tool> '<json>'

工具:
  search        搜索帖子或评论（cx=posts 搜原创帖/短视频，cx=comments 搜评论/转发/弹幕）
  stats         统计分析（热词、话题、情感、趋势、平台对比、MCN/采编权分布等，支持一次多指标）
  list_labels   查询可用 MCN 机构或采编权标签列表

search 参数:
  --cx <string>      (必填) posts 或 comments
  --q <string>       (必填) 查询字符串，支持运算符语法（site:、dateRestrict:、author:、sentiment: 等）
  --num <int>        每页条数（1-100），默认 10
  --start <int>      起始位置（从 1 开始），默认 1
  --sort <string>    排序，默认 ctime:desc（可选 user.followers_count:desc、like_count:desc 等）
  --fields <string>  返回字段列表，逗号分隔

stats 参数:
  --q <string>       查询字符串（同 search）
  --cx <string>      posts 或 comments（可选）
  --metrics <json>   (必填) 统计指标 JSON 数组，如 '[{"type":"hotWords","topN":10},{"type":"sentiment"}]'
                     支持指标: hotWords, hotHashtags, sentiment, trend, platformCompare, labelDistribution, labelFirstPost

list_labels 参数:
  --label_type <string>  mcn 或 cbq，默认 mcn

示例:
  node scripts/cli.js search --cx posts --q "新能源 site:iesdouyin.com" --num 10
  node scripts/cli.js search --cx comments --q "AI dateRestrict:d7" --num 5
  node scripts/cli.js stats --q "新能源 dateRestrict:d7" --metrics '[{"type":"hotWords","topN":10},{"type":"sentiment"}]'
  node scripts/cli.js list_labels --label_type cbq
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

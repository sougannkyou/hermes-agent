#!/usr/bin/env node
/**
 * CLI 入口：将互动数据刷新工具调用转发至 FastAPI Server。
 *
 * 用法：node scripts/cli.js fetch_douyin_interact --url https://...
 *       node scripts/cli.js batch_refresh_weibo_interact --urls https://a,https://b
 *       node scripts/cli.js fetch_douyin_interact '{"url":"...","ctime":1772000000}'
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
const TIMEOUT_MS = (config.timeout_seconds || 60) * 1000;

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

function forwardPost(endpoint, body) {
  return request("POST", endpoint, body);
}

// ---------- 工具实现 ----------

async function fetch_douyin_interact({ url }) {
  return forwardPost("/api/dyInteractNoTime", { url });
}

async function batch_refresh_weibo_interact({ urls }) {
  // --urls 逗号分隔时 parseCliArgs 已自动转为数组
  const urlList = Array.isArray(urls) ? urls : [urls];
  return forwardPost("/api/weibo/batch_interact", { urls: urlList });
}

// ---------- CLI 分发 ----------

const TOOLS = {
  fetch_douyin_interact,
  batch_refresh_weibo_interact,
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

const HELP_TEXT = `istarshine-refresh-interact — 互动数据刷新 CLI

用法:
  node scripts/cli.js <tool> --param value ...
  node scripts/cli.js <tool> '<json>'

工具:
  fetch_douyin_interact          单条抖音视频的实时互动数据（播放量、点赞、评论、收藏、分享）
  batch_refresh_weibo_interact   批量获取微博帖子互动数据（最多 50 条）

fetch_douyin_interact 参数:
  --url <string>    (必填) 抖音视频详情页 URL

batch_refresh_weibo_interact 参数:
  --urls <string>   (必填) 微博帖子链接，多条用逗号分隔

示例:
  node scripts/cli.js fetch_douyin_interact --url https://www.iesdouyin.com/share/video/xxx
  node scripts/cli.js batch_refresh_weibo_interact --urls https://weibo.com/xxx,https://weibo.com/yyy
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

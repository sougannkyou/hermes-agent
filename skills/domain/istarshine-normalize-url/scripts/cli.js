#!/usr/bin/env node
/**
 * CLI 入口：将 URL 归一化工具调用转发至 FastAPI Server。
 *
 * 用法：node scripts/cli.js normalize_url --url https://v.douyin.com/xxx --site_domain douyin.com
 *       node scripts/cli.js normalize_url '{"url":"...","site_domain":"douyin.com"}'
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

/**
 * 解析 --key value 形式的命令行参数为对象。
 * 支持：--key value, --key=value
 * 逗号分隔的值自动转为数组（如 --urls a,b,c）。
 * 纯数字字符串自动转为 number。
 */
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

/**
 * 从 toolName 之后的 args 中解析参数。
 * 优先尝试 JSON（第一个非 -- 开头的参数），否则解析 --key value。
 * 也支持 stdin JSON 输入。
 */
async function resolveArgs(args) {
  // 有 --key 形式参数
  if (args.length > 0 && args[0].startsWith("--")) {
    return parseCliArgs(args);
  }
  // 有 JSON 字符串参数
  if (args.length > 0) {
    let raw = args[0];
    if (raw.charCodeAt(0) === 0xfeff) raw = raw.slice(1);
    return JSON.parse(raw);
  }
  // stdin
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

async function normalize_url({ url, site_domain }) {
  return forwardPost("/api/url/normalize", { url, site_domain });
}

// ---------- CLI 分发 ----------

const TOOLS = { normalize_url };

function readStdin() {
  return new Promise((resolve) => {
    if (process.stdin.isTTY) { resolve("{}"); return; }
    const chunks = [];
    process.stdin.setEncoding("utf-8");
    process.stdin.on("data", (c) => chunks.push(c));
    process.stdin.on("end", () => resolve(chunks.join("").trim() || "{}"));
  });
}

const HELP_TEXT = `istarshine-normalize-url — URL 归一化 CLI

用法:
  node scripts/cli.js <tool> --param value ...
  node scripts/cli.js <tool> '<json>'

工具:
  normalize_url    将分享短链、移动端链接转换为标准 URL（仅抖音和微博）

normalize_url 参数:
  --url <string>          (必填) 用户提供的原始链接
  --site_domain <string>  (必填) 平台域名: mp.weixin.qq.com、douyin.com、kuaishou.com、xiaohongshu.com、toutiao.com、weibo.com、ixigua.com

示例:
  node scripts/cli.js normalize_url --url https://v.douyin.com/xxx --site_domain douyin.com
  node scripts/cli.js normalize_url --url https://m.weibo.cn/xxx --site_domain weibo.com
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

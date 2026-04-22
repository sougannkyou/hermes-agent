#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const http = require("http");
const https = require("https");

const CONFIG_PATH = path.join(__dirname, "config.json");
const config = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf-8"));
const SERVER_URL = config.server_url.replace(/\/+$/, "");
const API_KEY = process.env.ISTARSHINE_API_KEY;
const TIMEOUT_MS = (config.timeout_seconds || 30) * 1000;

if (!API_KEY) {
  console.error("错误: 未设置环境变量 ISTARSHINE_API_KEY");
  process.exit(1);
}

function request(endpoint) {
  return new Promise((resolve) => {
    const url = new URL(`${SERVER_URL}${endpoint}`);
    url.searchParams.set("key", API_KEY);
    const isHttps = url.protocol === "https:";
    const mod = isHttps ? https : http;
    const req = mod.request({
      hostname: url.hostname,
      port: url.port || (isHttps ? 443 : 80),
      path: url.pathname + url.search,
      method: "GET",
      timeout: TIMEOUT_MS,
    }, (res) => {
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => resolve(Buffer.concat(chunks).toString("utf-8")));
    });
    req.on("timeout", () => { req.destroy(); resolve(JSON.stringify({ code: 504, message: "请求超时" })); });
    req.on("error", () => resolve(JSON.stringify({ code: 503, message: "无法连接到服务" })));
    req.end();
  });
}

function parseArgs(args) {
  const result = {};
  let i = 0;
  while (i < args.length) {
    if (args[i].startsWith("--")) {
      const key = args[i].slice(2);
      i++;
      result[key] = i < args.length ? args[i] : "";
    }
    i++;
  }
  return result;
}

async function list(params) {
  const { kg_id, group_id, label_id } = params;
  if (!kg_id) return JSON.stringify({ code: 400, message: "kg_id 参数必填" });
  let endpoint = `/api/labels/list?kg_id=${encodeURIComponent(kg_id)}`;
  if (group_id) endpoint += `&group_id=${encodeURIComponent(group_id)}`;
  if (label_id) endpoint += `&label_id=${encodeURIComponent(label_id)}`;
  return request(endpoint);
}

const TOOLS = { list };

const HELP = `istarshine-label-list — 标签查询 CLI

用法:
  node scripts/cli.js list --kg_id <kg_id> [--group_id <group_id>] [--label_id <label_id>]

参数:
  --kg_id      (必填) 标签库 ID，如 kg_1333（MCN）、kg_1556（采编权）
  --group_id   (可选) 分组 ID，如 kg_group_26717
  --label_id   (可选) 具体标签 ID，如 259242

示例:
  node scripts/cli.js list --kg_id kg_1333
  node scripts/cli.js list --kg_id kg_1333 --group_id kg_group_26717
  node scripts/cli.js list --kg_id kg_1333 --label_id 259242
  node scripts/cli.js list --kg_id kg_1556
`;

async function main() {
  const args = process.argv.slice(2);
  if (args.includes("--help") || args.includes("-h") || args.length < 1) {
    console.log(HELP);
    process.exit(args.length < 1 ? 1 : 0);
  }
  const toolName = args[0];
  if (!TOOLS[toolName]) {
    console.log(JSON.stringify({ code: 400, message: `未知工具: ${toolName}` }));
    process.exit(1);
  }
  const parsed = parseArgs(args.slice(1));
  console.log(await TOOLS[toolName](parsed));
}

main();

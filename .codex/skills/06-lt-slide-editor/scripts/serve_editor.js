#!/usr/bin/env node
"use strict";

const fs = require("fs");
const http = require("http");
const Module = require("module");
const path = require("path");

function usage() {
  console.error("Usage: node serve_editor.js <index.html> [--host 127.0.0.1] [--port 4177]");
  process.exit(2);
}

const args = process.argv.slice(2);
if (!args[0] || args.includes("--help") || args.includes("-h")) usage();

const targetPath = path.resolve(args[0]);
const host = argValue("--host") || "127.0.0.1";
const requestedPort = Number(argValue("--port") || 4177);
const rootDir = path.dirname(targetPath);
let activePort = requestedPort;

if (!fs.existsSync(targetPath)) {
  console.error(`[lt-editor] File not found: ${targetPath}`);
  process.exit(1);
}

listenWithRetry(requestedPort, 20);

function argValue(name) {
  const index = args.indexOf(name);
  return index >= 0 ? args[index + 1] : "";
}

function listenWithRetry(port, remaining) {
  const server = http.createServer(handleRequest);
  server.on("error", (error) => {
    if (error.code === "EADDRINUSE" && remaining > 0) {
      listenWithRetry(port + 1, remaining - 1);
      return;
    }
    console.error(`[lt-editor] Server error: ${error.message}`);
    process.exit(1);
  });
  server.listen(port, host, () => {
    const address = server.address();
    activePort = address && typeof address === "object" ? address.port : port;
    console.log(`[lt-editor] Editing: ${targetPath}`);
    console.log(`[lt-editor] Open: http://${host}:${activePort}/?edit=1`);
    console.log("[lt-editor] Save HTML will overwrite the target file.");
    console.log(`[lt-editor] Export PDF will write: ${pdfPath()}`);
  });
}

function handleRequest(req, res) {
  const url = new URL(req.url || "/", `http://${host}:${activePort}`);
  if (req.method === "POST" && url.pathname === "/__lt_editor_save") {
    saveRequest(req, res);
    return;
  }
  if (req.method === "POST" && url.pathname === "/__lt_editor_export_pdf") {
    exportPdfRequest(req, res);
    return;
  }
  if (req.method !== "GET" && req.method !== "HEAD") {
    sendText(res, 405, "Method not allowed");
    return;
  }
  serveFile(req, res, url);
}

async function saveRequest(req, res) {
  try {
    const body = await readHtmlRequest(req);
    validateHtml(body);
    const result = await writeTargetHtml(body);
    sendJson(res, 200, { ok: true, htmlPath: targetPath, bytes: result.bytes, mtimeMs: result.mtimeMs });
  } catch (error) {
    sendText(res, error.statusCode || 500, error.message);
  }
}

async function exportPdfRequest(req, res) {
  try {
    const body = await readHtmlRequest(req);
    validateHtml(body);
    await writeTargetHtml(body);
    const result = await exportPdf();
    sendJson(res, 200, { ok: true, htmlPath: targetPath, pdfPath: result.pdfPath, slideCount: result.slideCount });
  } catch (error) {
    sendText(res, error.statusCode || 500, error.message);
  }
}

function serveFile(req, res, url) {
  const pathname = decodeURIComponent(url.pathname);
  const requestedPath = pathname === "/" ? targetPath : path.resolve(rootDir, `.${pathname}`);

  if (!isInside(rootDir, requestedPath)) {
    sendText(res, 403, "Forbidden");
    return;
  }

  fs.stat(requestedPath, (statError, stat) => {
    if (statError || !stat.isFile()) {
      sendText(res, 404, "Not found");
      return;
    }
    res.writeHead(200, {
      "content-type": contentType(requestedPath),
      "cache-control": "no-store"
    });
    if (req.method === "HEAD") {
      res.end();
      return;
    }
    fs.createReadStream(requestedPath).pipe(res);
  });
}

function readHtmlRequest(req) {
  return new Promise((resolve, reject) => {
    let body = "";
    let failed = false;
    req.setEncoding("utf8");
    req.on("data", (chunk) => {
      if (failed) return;
      body += chunk;
      if (Buffer.byteLength(body, "utf8") > 50 * 1024 * 1024) {
        failed = true;
        const error = new Error("HTML is too large.");
        error.statusCode = 413;
        reject(error);
        req.destroy(error);
      }
    });
    req.on("error", (error) => {
      if (!failed) reject(error);
    });
    req.on("end", () => {
      if (!failed) resolve(body);
    });
  });
}

function validateHtml(body) {
  const lower = String(body).toLowerCase();
  if (!lower.includes("<html") || !lower.includes("</html>")) {
    const error = new Error("Saved content does not look like a complete HTML document.");
    error.statusCode = 400;
    throw error;
  }
}

async function writeTargetHtml(body) {
  const tempPath = `${targetPath}.tmp-${process.pid}-${Date.now()}`;
  await fs.promises.writeFile(tempPath, body, "utf8");
  await fs.promises.rename(tempPath, targetPath);
  const stat = await fs.promises.stat(targetPath);
  const bytes = Buffer.byteLength(body, "utf8");
  console.log(`[lt-editor] Overwritten: ${targetPath}`);
  return { bytes, mtimeMs: stat.mtimeMs };
}

async function exportPdf() {
  const playwright = loadPlaywright();
  const browser = await launchBrowser(playwright);
  const outPath = pdfPath();
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
    await page.goto(`http://${host}:${activePort}/`, { waitUntil: "networkidle" });
    await page.emulateMedia({ media: "print" });
    const slideCount = await page.$$eval(".slide", (slides) => slides.length);
    if (!slideCount) throw new Error("Cannot export PDF: no .slide elements found.");
    await page.evaluate(async () => {
      window.slideDeck?.revealAll?.();
      await document.fonts?.ready;
    });
    await page.pdf({
      path: outPath,
      width: "13.333333in",
      height: "7.5in",
      printBackground: true,
      preferCSSPageSize: true,
      displayHeaderFooter: false,
      margin: { top: "0", right: "0", bottom: "0", left: "0" }
    });
    console.log(`[lt-editor] PDF exported: ${outPath}`);
    return { pdfPath: outPath, slideCount };
  } finally {
    await browser.close();
  }
}

function loadPlaywright() {
  const nodeRoot = path.resolve(path.dirname(process.execPath), "..");
  const candidates = [
    path.join(nodeRoot, "node_modules"),
    path.join(nodeRoot, "node_modules", ".pnpm", "node_modules"),
  ].filter((dir) => fs.existsSync(dir));
  const existing = process.env.NODE_PATH ? process.env.NODE_PATH.split(path.delimiter) : [];
  process.env.NODE_PATH = [...new Set([...existing, ...candidates])].join(path.delimiter);
  Module._initPaths();
  try {
    return require("playwright");
  } catch (error) {
    throw new Error(
      "Playwright was not found. Run with the bundled Codex Node.js or set NODE_PATH to the bundled node_modules. " +
      `Original error: ${error.message}`
    );
  }
}

async function launchBrowser(playwright) {
  try {
    return await playwright.chromium.launch({ channel: "chrome", headless: true });
  } catch (_) {
    return await playwright.chromium.launch({ headless: true });
  }
}

function pdfPath() {
  return path.join(rootDir, `${path.basename(targetPath, path.extname(targetPath))}.pdf`);
}

function isInside(parent, child) {
  const relative = path.relative(parent, child);
  return relative === "" || (!!relative && !relative.startsWith("..") && !path.isAbsolute(relative));
}

function contentType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  if (ext === ".html") return "text/html;charset=utf-8";
  if (ext === ".js") return "text/javascript;charset=utf-8";
  if (ext === ".css") return "text/css;charset=utf-8";
  if (ext === ".svg") return "image/svg+xml";
  if (ext === ".png") return "image/png";
  if (ext === ".jpg" || ext === ".jpeg") return "image/jpeg";
  if (ext === ".webp") return "image/webp";
  if (ext === ".gif") return "image/gif";
  if (ext === ".pdf") return "application/pdf";
  return "application/octet-stream";
}

function sendJson(res, status, data) {
  res.writeHead(status, {
    "content-type": "application/json;charset=utf-8",
    "cache-control": "no-store"
  });
  res.end(JSON.stringify(data));
}

function sendText(res, status, text) {
  res.writeHead(status, {
    "content-type": "text/plain;charset=utf-8",
    "cache-control": "no-store"
  });
  res.end(text);
}

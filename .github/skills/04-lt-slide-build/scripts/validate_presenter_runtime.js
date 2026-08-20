#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const Module = require("module");

function parseArgs(argv) {
  const args = { html: "", width: 1280, height: 720 };
  const rest = [...argv];
  if (rest[0] && !rest[0].startsWith("--")) args.html = rest.shift();
  for (let index = 0; index < rest.length; index++) {
    const key = rest[index];
    const value = rest[index + 1];
    if (key === "--width") { args.width = Number(value); index++; }
    else if (key === "--height") { args.height = Number(value); index++; }
    else if (key === "--help" || key === "-h") {
      console.log("Usage: validate_presenter_runtime.js <index.html> [--width 1280] [--height 720]");
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${key}`);
    }
  }
  if (!args.html) throw new Error("index.html is required");
  return args;
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
  return require("playwright");
}

function fileUrl(filePath) {
  const resolved = path.resolve(filePath).replace(/\\/g, "/");
  return `file:///${resolved}?presenter=1#1`;
}

async function launchBrowser(playwright) {
  try {
    return await playwright.chromium.launch({ channel: "chrome", headless: true });
  } catch (_) {
    return await playwright.chromium.launch({ headless: true });
  }
}

async function findScrollableNote(page) {
  const slideCount = await page.locator("body > .deck .slide").count();
  const phaseIndexes = await page.$$eval("body > .deck .slide", (slides) =>
    slides.map((slide, index) => slide.dataset.phaseQuestion ? index : -1).filter((index) => index >= 0)
  );
  const indexes = [...phaseIndexes, ...Array.from({ length: slideCount }, (_, index) => index).filter((index) => !phaseIndexes.includes(index))];
  for (const index of indexes) {
    await page.evaluate((slideIndex) => window.slideDeck?.show?.(slideIndex, false, false), index);
    await page.waitForTimeout(50);
    const metrics = await page.evaluate(() => {
      const primary = document.querySelector(".presenter-cue-primary .presenter-cue-body") ||
        [...document.querySelectorAll(".presenter-cue-row")].find((row) =>
          row.querySelector(".presenter-cue-label")?.textContent.trim() === "話す内容"
        )?.querySelector(".presenter-cue-body");
      if (!primary) return null;
      return { clientHeight: primary.clientHeight, scrollHeight: primary.scrollHeight };
    });
    if (metrics && metrics.scrollHeight > metrics.clientHeight + 4) return index;
  }
  return -1;
}

async function inspect(page, options) {
  const findings = [];
  const scrollableIndex = await findScrollableNote(page);
  const metrics = await page.evaluate(({ width, height }) => {
    const primary = document.querySelector(".presenter-cue-primary .presenter-cue-body") ||
      [...document.querySelectorAll(".presenter-cue-row")].find((row) =>
        row.querySelector(".presenter-cue-label")?.textContent.trim() === "話す内容"
      )?.querySelector(".presenter-cue-body");
    const context = document.getElementById("presenterContext");
    const question = document.querySelector(".presenter-context-row.is-question .presenter-context-body");
    const rect = (element) => {
      if (!element) return null;
      const value = element.getBoundingClientRect();
      return { width: Math.round(value.width), height: Math.round(value.height) };
    };
    return {
      viewport: { width, height },
      primary: rect(primary),
      context: rect(context),
      question: rect(question),
      structuredPrimary: Boolean(document.querySelector(".presenter-cue-primary")),
      structuredQuestion: Boolean(question),
      minimumPrimaryHeight: Math.round(Math.min(220, Math.max(160, height * 0.25))),
      minimumContextHeight: Math.round(Math.min(160, Math.max(120, height * 0.18))),
    };
  }, options);

  if (!metrics.structuredPrimary) {
    findings.push("話す内容が主表示領域として構造化されていません");
  }
  if (!metrics.primary || metrics.primary.height < metrics.minimumPrimaryHeight) {
    findings.push(`話す内容の可読領域が不足しています: ${metrics.primary?.height || 0}px < ${metrics.minimumPrimaryHeight}px`);
  }
  if (!metrics.structuredQuestion) {
    findings.push("phaseの問いが独立した表示領域として構造化されていません");
  }
  if (!metrics.context || metrics.context.height < metrics.minimumContextHeight) {
    findings.push(`問い・文脈領域が不足しています: ${metrics.context?.height || 0}px < ${metrics.minimumContextHeight}px`);
  }

  let scroll = { tested: false };
  if (scrollableIndex >= 0) {
    await page.evaluate((slideIndex) => window.slideDeck?.show?.(slideIndex, false, false), scrollableIndex);
    await page.waitForTimeout(80);
    const before = await page.evaluate(() => {
      const primary = document.querySelector(".presenter-cue-primary .presenter-cue-body") ||
        [...document.querySelectorAll(".presenter-cue-row")].find((row) =>
          row.querySelector(".presenter-cue-label")?.textContent.trim() === "話す内容"
        )?.querySelector(".presenter-cue-body");
      const maximum = Math.max(0, (primary?.scrollHeight || 0) - (primary?.clientHeight || 0));
      if (!primary || maximum < 8) return null;
      primary.scrollTop = Math.min(80, maximum);
      return {
        scrollTop: primary.scrollTop,
        timer: document.getElementById("presenterTime")?.textContent || "",
      };
    });
    if (before) {
      await page.waitForTimeout(1250);
      const after = await page.evaluate(() => {
        const primary = document.querySelector(".presenter-cue-primary .presenter-cue-body") ||
          [...document.querySelectorAll(".presenter-cue-row")].find((row) =>
            row.querySelector(".presenter-cue-label")?.textContent.trim() === "話す内容"
          )?.querySelector(".presenter-cue-body");
        return {
          scrollTop: primary?.scrollTop || 0,
          timer: document.getElementById("presenterTime")?.textContent || "",
        };
      });
      scroll = { tested: true, before, after, slideIndex: scrollableIndex };
      if (Math.abs(after.scrollTop - before.scrollTop) > 2) {
        findings.push(`タイマー更新後に話す内容のスクロール位置が変化しました: ${before.scrollTop}px -> ${after.scrollTop}px`);
      }
      if (after.timer === before.timer) {
        findings.push(`スクロール保持試験中にタイマーが進みませんでした: ${before.timer}`);
      }
    }
  }
  return { findings, metrics, scroll };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!fs.existsSync(args.html)) throw new Error(`File not found: ${args.html}`);
  const playwright = loadPlaywright();
  const browser = await launchBrowser(playwright);
  try {
    const page = await browser.newPage({ viewport: { width: args.width, height: args.height }, deviceScaleFactor: 1 });
    await page.goto(fileUrl(args.html), { waitUntil: "networkidle" });
    await page.waitForTimeout(300);
    const result = await inspect(page, args);
    console.log(JSON.stringify(result, null, 2));
    if (result.findings.length) process.exitCode = 1;
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(2);
});

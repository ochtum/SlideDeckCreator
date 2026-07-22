#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");

function usage() {
  console.error("Usage: validate_editor_workspace.js <index.html> [--width 1920] [--height 980] [--screenshot path] [--url http://127.0.0.1:4177/] [--test-save]");
  process.exit(2);
}

function parseArgs(argv) {
  if (!argv[0] || argv.includes("--help") || argv.includes("-h")) usage();
  const args = { html: path.resolve(argv[0]), width: 1920, height: 980, screenshot: null, url: null, testSave: false };
  for (let i = 1; i < argv.length; i++) {
    if (argv[i] === "--width") args.width = Number(argv[++i]);
    else if (argv[i] === "--height") args.height = Number(argv[++i]);
    else if (argv[i] === "--screenshot") args.screenshot = path.resolve(argv[++i]);
    else if (argv[i] === "--url") args.url = argv[++i];
    else if (argv[i] === "--test-save") args.testSave = true;
    else throw new Error(`Unknown argument: ${argv[i]}`);
  }
  return args;
}

function visible(rect, style) {
  return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
}

function loadPlaywright() {
  const Module = require("module");
  const nodeRoot = path.resolve(path.dirname(process.execPath), "..");
  const candidates = [
    path.join(nodeRoot, "node_modules"),
    path.join(nodeRoot, "node_modules", ".pnpm", "node_modules"),
  ].filter((directory) => fs.existsSync(directory));
  const existing = process.env.NODE_PATH ? process.env.NODE_PATH.split(path.delimiter) : [];
  process.env.NODE_PATH = [...new Set([...existing, ...candidates])].join(path.delimiter);
  Module._initPaths();
  return require("playwright");
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  let playwright;
  try {
    playwright = loadPlaywright();
  } catch (error) {
    throw new Error(`playwright is required. Set NODE_PATH to the bundled node_modules. ${error.message}`);
  }

  const browser = await playwright.chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: args.width, height: args.height } });
  const url = args.url ? new URL(args.url) : new URL(pathToFileURL(args.html));
  url.searchParams.set("edit", "1");
  url.hash = "1";
  await page.goto(url.toString(), { waitUntil: "networkidle" });
  await page.waitForSelector(".lt-editor-root");
  await page.waitForTimeout(250);

  const findings = [];
  const initial = await page.evaluate(() => {
    const box = (selector) => {
      const el = document.querySelector(selector);
      if (!el) return null;
      const rect = el.getBoundingClientRect();
      const style = getComputedStyle(el);
      return {
        x: rect.x, y: rect.y, width: rect.width, height: rect.height,
        right: rect.right, bottom: rect.bottom,
        display: style.display, visibility: style.visibility,
      };
    };
    return {
      bodyClasses: document.body.className,
      root: box(".lt-editor-root"),
      stageShell: box(".lt-editor-stage-shell"),
      viewport: box(".lt-editor-stage-viewport"),
      deck: box("body > .deck"),
      dock: box(".lt-editor-dock"),
      side: box(".lt-editor-side-shell"),
      note: box(".lt-editor-root textarea[data-spoken-note]"),
      dockFloating: document.querySelector(".lt-editor-dock")?.classList.contains("is-floating") || false,
      clippedDockControls: (() => {
        const dock = document.querySelector(".lt-editor-dock");
        if (!dock) return ["dock-missing"];
        const bounds = dock.getBoundingClientRect();
        return [...dock.querySelectorAll("button,input,select")].filter((control) => {
          const rect = control.getBoundingClientRect();
          const style = getComputedStyle(control);
          if (!rect.width || !rect.height || style.display === "none" || style.visibility === "hidden") return false;
          return rect.left < bounds.left - 1 || rect.top < bounds.top - 1 || rect.right > bounds.right + 1 || rect.bottom > bounds.bottom + 1;
        }).map((control) => control.getAttribute("data-action") || control.getAttribute("data-field") || control.tagName.toLowerCase());
      })(),
    };
  });

  const isVisible = (item) => item && visible(item, item);
  for (const [name, item] of Object.entries({ root: initial.root, viewport: initial.viewport, deck: initial.deck, dock: initial.dock, side: initial.side, note: initial.note })) {
    if (!isVisible(item)) findings.push(`${name} is missing or hidden`);
  }
  if (!initial.bodyClasses.includes("lt-editor-edit-mode")) findings.push("body is not in editor mode");
  if (initial.dockFloating) findings.push("editor dock must start in the presenter-style lower-left slot");
  if (initial.deck && initial.viewport) {
    const tolerance = 3;
    if (initial.deck.x < initial.viewport.x - tolerance || initial.deck.y < initial.viewport.y - tolerance || initial.deck.right > initial.viewport.right + tolerance || initial.deck.bottom > initial.viewport.bottom + tolerance) {
      findings.push("editable deck does not fit inside the upper-left stage viewport");
    }
  }
  if (initial.dock && initial.viewport && initial.dock.y < initial.viewport.bottom - 2) {
    findings.push("editor dock is not placed below the editable slide");
  }
  if (initial.side && initial.stageShell && initial.side.x <= initial.stageShell.right) {
    findings.push("script/output panel is not placed to the right of the editable slide");
  }
  if (initial.note && initial.note.height < 180) findings.push(`spoken note area is too short: ${Math.round(initial.note.height)}px`);
  if (initial.clippedDockControls.length) findings.push(`editor dock controls are clipped: ${initial.clippedDockControls.join(", ")}`);
  if (args.screenshot) await page.screenshot({ path: args.screenshot, fullPage: false });

  if (args.testSave) {
    await page.locator("[data-action='save']").click();
    try {
      await page.waitForFunction(() => /Overwritten HTML/.test(document.querySelector("[data-status]")?.textContent || ""), null, { timeout: 5000 });
    } catch (error) {
      const message = await page.locator("[data-status]").textContent().catch(() => "status unavailable");
      findings.push(`Save HTML did not report a successful overwrite: ${message}`);
    }
  }

  const editableZone = page.locator(".slide.active .zone").first();
  await editableZone.click({ position: { x: 12, y: 12 } });
  if (await page.locator(".slide.active .lt-editor-selected").count() !== 1) {
    findings.push("clicking an editable zone does not select it");
  }

  await page.locator("[data-action='dock']").click();
  if (!(await page.locator(".lt-editor-dock.is-floating").count())) findings.push("Float button does not undock the editor panel");
  await page.locator("[data-action='dock']").click();
  if (await page.locator(".lt-editor-dock.is-floating").count()) findings.push("Dock button does not return the editor panel to the lower-left slot");

  await page.evaluate(() => document.activeElement instanceof HTMLElement && document.activeElement.blur());
  await page.keyboard.press("v");
  await page.waitForTimeout(100);
  const viewMode = await page.evaluate(() => ({
    enabled: document.body.classList.contains("lt-editor-view-mode"),
    rootDisplay: getComputedStyle(document.querySelector(".lt-editor-root")).display,
  }));
  if (!viewMode.enabled || viewMode.rootDisplay !== "none") findings.push("V does not switch to the clean view mode");
  await page.keyboard.press("v");
  await page.waitForTimeout(100);
  if (!(await page.evaluate(() => document.body.classList.contains("lt-editor-edit-mode")))) findings.push("second V does not restore editor mode");

  await page.evaluate(() => document.activeElement instanceof HTMLElement && document.activeElement.blur());
  await page.keyboard.press("e");
  await page.waitForLoadState("domcontentloaded");
  await page.waitForTimeout(80);
  const normalUrl = new URL(page.url());
  if (normalUrl.searchParams.get("edit") === "1") findings.push("E does not leave the edit URL");
  if (await page.locator(".lt-editor-root").count()) findings.push("editor UI remains mounted after E returns to normal mode");

  await browser.close();
  const report = { viewport: { width: args.width, height: args.height }, initial, findings };
  console.log(JSON.stringify(report, null, 2));
  if (findings.length) process.exit(1);
}

main().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exit(1);
});

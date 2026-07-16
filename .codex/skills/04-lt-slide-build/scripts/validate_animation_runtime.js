#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const Module = require("module");

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
  return `file:///${resolved}#1`;
}

async function launchBrowser(playwright) {
  try {
    return await playwright.chromium.launch({ channel: "chrome", headless: true });
  } catch (_) {
    return await playwright.chromium.launch({ headless: true });
  }
}

async function state(page) {
  return page.evaluate(() => {
    const slide = document.querySelector("body > .deck .slide.active");
    const visible = (element) => {
      if (!element) return false;
      const style = getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      return style.display !== "none" && style.visibility !== "hidden" &&
        Number(style.opacity || 1) > 0.5 && rect.width > 0 && rect.height > 0;
    };
    const animated = [...slide.querySelectorAll("[data-anim]")];
    return {
      sid: slide.dataset.slideId || "unknown",
      runtimeStep: window.slideDeck?.step ?? -1,
      maxStep: Math.max(0, ...animated.map((element) => Number(element.dataset.step || 0))),
      titleVisible: visible(slide.querySelector(".slide-title")),
      reveals: [...slide.querySelectorAll('[data-reveal-item="true"]')].map((element) => ({
        label: element.dataset.motionTargets || [...element.classList].join(".") || element.tagName,
        step: Number(element.dataset.step || 0),
        visible: visible(element),
      })),
      conclusions: [...slide.querySelectorAll(".conclusion-bar, .thanks-anchor")].map((element) => ({
        step: Number(element.dataset.step || 0),
        visible: visible(element),
      })),
    };
  });
}

async function inspect(page) {
  const findings = [];
  const slideCount = await page.locator("body > .deck .slide").count();
  let checkedStates = 0;
  for (let index = 0; index < slideCount; index++) {
    await page.evaluate((slideIndex) => window.slideDeck.show(slideIndex, false, false), index);
    let current = await state(page);
    checkedStates++;
    if (!current.titleVisible) findings.push(`${current.sid} step 0: title is not visible`);
    for (const item of current.reveals.filter((entry) => entry.visible)) {
      findings.push(`${current.sid} step 0: future item is already visible (${item.label}, step ${item.step})`);
    }
    for (let step = 1; step <= current.maxStep; step++) {
      await page.evaluate(() => window.slideDeck.next());
      current = await state(page);
      checkedStates++;
      if (current.runtimeStep !== step) {
        findings.push(`${current.sid}: runtime skipped from expected step ${step} to ${current.runtimeStep}`);
      }
      if (!current.titleVisible) findings.push(`${current.sid} step ${step}: title became invisible`);
      for (const item of current.reveals) {
        const shouldBeVisible = item.step <= step;
        if (item.visible !== shouldBeVisible) {
          findings.push(
            `${current.sid} step ${step}: ${item.label} is ${item.visible ? "visible" : "hidden"}; ` +
            `expected ${shouldBeVisible ? "visible" : "hidden"} (assigned step ${item.step})`
          );
        }
      }
      for (const conclusion of current.conclusions) {
        const shouldBeVisible = conclusion.step <= step;
        if (conclusion.visible !== shouldBeVisible) {
          findings.push(
            `${current.sid} step ${step}: conclusion visibility disagrees with assigned step ${conclusion.step}`
          );
        }
      }
    }
  }
  return { findings, slideCount, checkedStates };
}

async function main() {
  const html = process.argv[2];
  if (!html || process.argv.includes("--help") || process.argv.includes("-h")) {
    console.log("Usage: validate_animation_runtime.js <index.html>");
    process.exit(html ? 0 : 2);
  }
  const playwright = loadPlaywright();
  const browser = await launchBrowser(playwright);
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
    await page.goto(fileUrl(html), { waitUntil: "load" });
    await page.addStyleTag({ content: "*,*::before,*::after{transition:none!important;animation:none!important}" });
    const result = await inspect(page);
    if (result.findings.length) {
      result.findings.forEach((finding) => console.error(`ERROR: ${finding}`));
      process.exitCode = 1;
    } else {
      console.log(`OK: ${result.slideCount} slides; ${result.checkedStates} initial/intermediate states`);
    }
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exit(1);
});

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

  let browser;
  try {
    browser = await playwright.chromium.launch({ channel: "chrome", headless: true });
  } catch (_) {
    browser = await playwright.chromium.launch({ headless: true });
  }
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
    const visibleRect = (element) => {
      const rect = element.getBoundingClientRect();
      const style = getComputedStyle(element);
      return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
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
      editorTabs: [...document.querySelectorAll("[data-editor-tab]")].map((tab) => ({
        name: tab.getAttribute("data-editor-tab"),
        selected: tab.getAttribute("aria-selected") === "true",
        visible: visibleRect(tab),
      })),
      activePanel: document.querySelector('[data-editor-panel]:not([hidden])')?.getAttribute("data-editor-panel") || "",
      dockOverflow: (() => {
        const body = document.querySelector(".lt-editor-dock-body");
        const panel = document.querySelector('[data-editor-panel]:not([hidden])');
        return {
          bodyClientWidth: body?.clientWidth || 0,
          bodyScrollWidth: body?.scrollWidth || 0,
          panelClientWidth: panel?.clientWidth || 0,
          panelScrollWidth: panel?.scrollWidth || 0,
        };
      })(),
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
  if (initial.editorTabs.length !== 3 || initial.editorTabs.some((tab) => !tab.visible)) findings.push("editor tool tabs are missing or hidden");
  if (initial.activePanel !== "element" || !initial.editorTabs.find((tab) => tab.name === "element")?.selected) findings.push("element editor tab is not active initially");
  if (initial.dockOverflow.bodyScrollWidth > initial.dockOverflow.bodyClientWidth + 1 || initial.dockOverflow.panelScrollWidth > initial.dockOverflow.panelClientWidth + 1) findings.push("editor panel has unnecessary horizontal overflow");
  if (initial.clippedDockControls.length) findings.push(`editor dock controls are clipped: ${initial.clippedDockControls.join(", ")}`);
  if (args.screenshot) await page.screenshot({ path: args.screenshot, fullPage: false });

  const profileBubbleGap = await page.evaluate(() => {
    const bubble = document.querySelector(".slide.active .profile-name-note.lt-editor-speech-bubble");
    const name = document.querySelector(".slide.active .profile-copy h3");
    const slide = bubble?.closest(".slide");
    if (!bubble || !name || !slide) return null;
    const bubbleRect = bubble.getBoundingClientRect();
    const nameRect = name.getBoundingClientRect();
    const slideRect = slide.getBoundingClientRect();
    const scale = slideRect.width ? slideRect.width / 1280 : 1;
    const tail = getComputedStyle(bubble, "::before");
    const tailBottom = bubbleRect.top + (Number.parseFloat(tail.top) + Number.parseFloat(tail.height)) * scale;
    return (nameRect.top - tailBottom) / scale;
  });
  if (profileBubbleGap !== null && profileBubbleGap < 5) {
    findings.push(`profile speech-bubble tail overlaps or nearly touches the display name: ${profileBubbleGap.toFixed(1)}px gap`);
  }

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

  const maxStepBeforeBubble = await page.locator(".slide.active [data-step]").evaluateAll((elements) =>
    Math.max(0, ...elements.map((el) => Number(el.getAttribute("data-step"))).filter(Number.isFinite))
  );
  await page.locator('[data-editor-tab="add"]').click();
  if (!(await page.locator('[data-editor-panel="add"]:not([hidden])').count())) findings.push("Add tab does not reveal the add controls");
  const bubbleButton = page.locator("[data-action='addSpeechBubble']");
  if (!(await bubbleButton.count())) {
    findings.push("speech-bubble add action is missing");
  } else {
    await bubbleButton.click();
    const bubble = page.locator('.slide.active .lt-editor-speech-bubble[data-editor-element="speech-bubble"]').last();
    if (!(await bubble.count())) {
      findings.push("speech-bubble add action did not create a bubble zone");
    } else {
      const bubbleState = await bubble.evaluate((el) => {
        const text = el.querySelector(":scope > .lt-editor-speech-text");
        const outerTail = getComputedStyle(el, "::before");
        const innerTail = getComputedStyle(el, "::after");
        return {
          selected: el.classList.contains("lt-editor-selected"),
          zone: el.getAttribute("data-zone"),
          step: Number(el.getAttribute("data-step")),
          editable: text?.getAttribute("contenteditable") === "true",
          opacity: Number.parseFloat(getComputedStyle(el).opacity),
          clipPath: getComputedStyle(el).clipPath,
          outerTailContent: outerTail.content,
          outerTailWidth: Number.parseFloat(outerTail.width),
          outerTailHeight: Number.parseFloat(outerTail.height),
          outerTailClip: outerTail.clipPath,
          outerTailColor: outerTail.backgroundColor,
          innerTailContent: innerTail.content,
          innerTailWidth: Number.parseFloat(innerTail.width),
          innerTailHeight: Number.parseFloat(innerTail.height),
          innerTailClip: innerTail.clipPath,
          innerTailColor: innerTail.backgroundColor,
        };
      });
      if (!bubbleState.selected) findings.push("new speech bubble is not selected");
      if (bubbleState.zone !== "callout") findings.push("new speech bubble does not use data-zone=callout");
      if (!bubbleState.editable) findings.push("new speech bubble text is not editable");
      if (bubbleState.opacity < 0.99) findings.push("new speech bubble is hidden while editing");
      if (bubbleState.clipPath !== "none") findings.push("new speech bubble clips the protruding tail");
      if (bubbleState.step !== maxStepBeforeBubble + 1) findings.push("new speech bubble is not assigned after the current maximum animation step");
      const stepField = page.locator('[data-field="step"]');
      if (!(await stepField.count()) || Number(await stepField.inputValue()) !== bubbleState.step) {
        findings.push("selected element animation step is not exposed in the editor");
      } else {
        await stepField.fill("1");
        await stepField.dispatchEvent("input");
        const editedStep = await bubble.getAttribute("data-step");
        if (editedStep !== "1") findings.push("editing the Step field does not update data-step");
        const lastButton = page.locator('[data-action="stepLast"]');
        if (!(await lastButton.count())) {
          findings.push("animation last-step action is missing");
        } else {
          await lastButton.click();
          const lastState = await page.locator(".slide.active").evaluate((slide, bubbleSelector) => {
            const bubbles = [...slide.querySelectorAll(bubbleSelector)];
            const bubble = bubbles[bubbles.length - 1];
            const steps = [...slide.querySelectorAll("[data-anim][data-step]")].map((el) => Number(el.getAttribute("data-step"))).filter(Number.isFinite);
            return { bubbleStep: Number(bubble?.getAttribute("data-step")), maxStep: Math.max(0, ...steps) };
          }, '.lt-editor-speech-bubble[data-editor-element="speech-bubble"]');
          if (lastState.bubbleStep !== lastState.maxStep) findings.push("Last-step action does not move the selected element to the final animation step");
        }
      }
      if (bubbleState.outerTailContent === "none" || bubbleState.outerTailWidth < 60 || bubbleState.outerTailHeight < 28 || bubbleState.outerTailClip === "none" || bubbleState.outerTailColor === "rgba(0, 0, 0, 0)" || bubbleState.innerTailContent === "none" || bubbleState.innerTailWidth < 48 || bubbleState.innerTailHeight < 18 || bubbleState.innerTailClip === "none" || bubbleState.innerTailColor === "rgba(0, 0, 0, 0)") {
        findings.push("new speech bubble does not have a clearly protruding rendered tail");
      }
      if (bubbleState.outerTailWidth - bubbleState.innerTailWidth > 6 || bubbleState.outerTailHeight - bubbleState.innerTailHeight > 5) {
        findings.push("new speech bubble tail outline is visually too thick");
      }
      const tailHandle = page.locator(".lt-editor-tail-handle");
      const handleBefore = await tailHandle.boundingBox();
      if (!(await tailHandle.count()) || !handleBefore) {
        findings.push("selecting a speech bubble does not show a draggable tail-tip handle");
      } else {
        await page.mouse.move(handleBefore.x + handleBefore.width / 2, handleBefore.y + handleBefore.height / 2);
        await page.mouse.down();
        await page.mouse.move(handleBefore.x + handleBefore.width / 2 + 70, handleBefore.y + handleBefore.height / 2 + 24, { steps: 5 });
        await page.mouse.up();
        const handleAfter = await tailHandle.boundingBox();
        const draggedTail = await bubble.evaluate((el) => ({
          tipX: Number.parseFloat(el.getAttribute("data-tail-tip-x")),
          tipY: Number.parseFloat(el.getAttribute("data-tail-tip-y")),
          side: el.getAttribute("data-tail-side"),
          outerBoxLeft: el.style.getPropertyValue("--lt-bubble-tail-outer-box-left"),
          outerBoxWidth: el.style.getPropertyValue("--lt-bubble-tail-outer-box-width"),
          outerClip: getComputedStyle(el, "::before").clipPath,
          innerClip: getComputedStyle(el, "::after").clipPath,
        }));
        if (!Number.isFinite(draggedTail.tipX) || !Number.isFinite(draggedTail.tipY)) {
          findings.push("dragging the tail-tip handle does not persist data-tail-tip coordinates");
        }
        if (!(["top", "right", "bottom", "left"].includes(draggedTail.side || ""))) {
          findings.push("dragging the tail-tip handle does not persist the followed bubble edge");
        }
        if (!draggedTail.outerBoxLeft || !draggedTail.outerBoxWidth || draggedTail.outerClip === "none" || draggedTail.innerClip === "none") {
          findings.push("dragging the tail-tip handle does not redraw both pseudo-element tail layers");
        }
        if (!handleAfter || Math.hypot(handleAfter.x - handleBefore.x, handleAfter.y - handleBefore.y) < 20) {
          findings.push("speech-bubble tail-tip handle does not follow the pointer");
        }
      }
      await bubble.evaluate((el) => el.remove());
      await page.keyboard.press("Escape");
    }
  }

  await page.locator('[data-editor-tab="mode"]').click();
  if (!(await page.locator('[data-editor-panel="mode"]:not([hidden])').count()) || !(await page.locator('[data-action="next"]:visible').count())) {
    findings.push("View/navigation tab does not reveal its controls");
  }
  await page.locator('[data-editor-tab="element"]').click();

  await page.locator("[data-action='dock']").click();
  if (!(await page.locator(".lt-editor-dock.is-floating").count())) findings.push("Float button does not undock the editor panel");
  const floatingLayout = await page.evaluate(() => {
    const dock = document.querySelector(".lt-editor-dock.is-floating");
    if (!dock) return null;
    dock.style.width = Math.min(960, innerWidth - 32) + "px";
    dock.style.height = Math.min(340, innerHeight - 32) + "px";
    const body = dock.querySelector(".lt-editor-dock-body");
    const panel = dock.querySelector('[data-editor-panel]:not([hidden])');
    const labelColor = getComputedStyle(dock.querySelector(".lt-editor-field") || dock).color;
    return {
      bodyClientWidth: body?.clientWidth || 0,
      bodyScrollWidth: body?.scrollWidth || 0,
      panelClientWidth: panel?.clientWidth || 0,
      panelScrollWidth: panel?.scrollWidth || 0,
      labelColor,
    };
  });
  if (!floatingLayout || floatingLayout.bodyScrollWidth > floatingLayout.bodyClientWidth + 1 || floatingLayout.panelScrollWidth > floatingLayout.panelClientWidth + 1) {
    findings.push("floating editor panel has unnecessary horizontal overflow");
  }
  if (floatingLayout?.labelColor === "rgb(56, 81, 112)") findings.push("editor field labels use the former low-contrast color");
  await page.locator("[data-action='dock']").click();
  if (await page.locator(".lt-editor-dock.is-floating").count()) findings.push("Dock button does not return the editor panel to the lower-left slot");

  await page.locator('[data-field="x"]').focus();
  await page.keyboard.press("p");
  if (await page.evaluate(() => document.body.classList.contains("overview"))) findings.push("P opens page overview while an editor form field has focus");
  await page.evaluate(() => document.activeElement instanceof HTMLElement && document.activeElement.blur());
  const pageIndexBeforeOverview = await page.locator(".slide").evaluateAll((slides) => slides.findIndex((slide) => slide.classList.contains("active")));
  await page.keyboard.press("p");
  await page.waitForTimeout(100);
  const overviewState = await page.evaluate(() => ({
    open: document.body.classList.contains("overview"),
    pagerDisplay: getComputedStyle(document.querySelector(".pager")).display,
    editorDisplay: getComputedStyle(document.querySelector(".lt-editor-root")).display,
    thumbnailCount: document.querySelectorAll(".pager-thumb").length,
  }));
  if (!overviewState.open || overviewState.pagerDisplay === "none" || overviewState.editorDisplay !== "none" || overviewState.thumbnailCount < 2) {
    findings.push("P does not open a clean, visible page overview in editor mode");
  } else {
    const targetIndex = (pageIndexBeforeOverview + 1) % overviewState.thumbnailCount;
    await page.locator(".pager-thumb").nth(targetIndex).click();
    await page.waitForTimeout(120);
    const afterOverviewSelection = await page.evaluate(() => ({
      open: document.body.classList.contains("overview"),
      editorMode: document.body.classList.contains("lt-editor-edit-mode"),
      editorDisplay: getComputedStyle(document.querySelector(".lt-editor-root")).display,
      activeIndex: [...document.querySelectorAll(".slide")].findIndex((slide) => slide.classList.contains("active")),
    }));
    if (afterOverviewSelection.open || !afterOverviewSelection.editorMode || afterOverviewSelection.editorDisplay === "none" || afterOverviewSelection.activeIndex !== targetIndex) {
      findings.push("selecting a page overview thumbnail does not move pages and restore editor mode");
    }
  }

  await page.evaluate(() => document.activeElement instanceof HTMLElement && document.activeElement.blur());
  await page.keyboard.press("p");
  await page.waitForTimeout(60);
  await page.keyboard.press("p");
  await page.waitForTimeout(80);
  if (await page.evaluate(() => document.body.classList.contains("overview") || !document.body.classList.contains("lt-editor-edit-mode"))) {
    findings.push("second P does not close page overview and restore editor mode");
  }

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

  await page.emulateMedia({ reducedMotion: "reduce" });
  const profileUrl = new URL(page.url());
  profileUrl.hash = "2";
  await page.goto(profileUrl.toString(), { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(100);
  const profileBubble = page.locator(".slide.active .profile-name-note.lt-editor-speech-bubble");
  if (await profileBubble.count()) {
    const initialProfile = await profileBubble.evaluate((el) => ({ shown: el.classList.contains("shown"), opacity: Number.parseFloat(getComputedStyle(el).opacity), step: Number(el.getAttribute("data-step")) }));
    if (initialProfile.step !== 4) findings.push(`profile speech bubble must remain at final step 4, got ${initialProfile.step}`);
    if (initialProfile.shown || initialProfile.opacity > .01) findings.push("profile speech bubble is visible before its final animation step under reduced-motion settings");
    for (let i = 0; i < Math.max(0, initialProfile.step - 1); i++) await page.keyboard.press("ArrowRight");
    const beforeFinal = await profileBubble.evaluate((el) => ({ shown: el.classList.contains("shown"), opacity: Number.parseFloat(getComputedStyle(el).opacity) }));
    if (beforeFinal.shown || beforeFinal.opacity > .01) findings.push("profile speech bubble appears before the final animation action");
    await page.keyboard.press("ArrowRight");
    const atFinal = await profileBubble.evaluate((el) => ({ shown: el.classList.contains("shown"), opacity: Number.parseFloat(getComputedStyle(el).opacity) }));
    if (!atFinal.shown || atFinal.opacity < .99) findings.push("profile speech bubble does not appear at the final animation action");
  }

  await browser.close();
  const report = { viewport: { width: args.width, height: args.height }, initial, findings };
  console.log(JSON.stringify(report, null, 2));
  if (findings.length) process.exit(1);
}

main().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exit(1);
});

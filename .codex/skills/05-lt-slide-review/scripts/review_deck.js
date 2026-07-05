#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

function parseArgs(argv) {
  const args = {
    html: "output/index.html",
    out: ".lt-slide-work/review",
    width: 1280,
    height: 720,
    minMargin: 40,
    overlapTolerance: 8,
    noFail: false,
    includePresenter: true,
    presenterOnly: false,
  };
  const rest = [...argv];
  if (rest[0] && !rest[0].startsWith("--")) args.html = rest.shift();
  for (let i = 0; i < rest.length; i++) {
    const key = rest[i];
    const value = rest[i + 1];
    if (key === "--out") { args.out = value; i++; }
    else if (key === "--width") { args.width = Number(value); i++; }
    else if (key === "--height") { args.height = Number(value); i++; }
    else if (key === "--min-margin") { args.minMargin = Number(value); i++; }
    else if (key === "--overlap-tolerance") { args.overlapTolerance = Number(value); i++; }
    else if (key === "--no-fail") args.noFail = true;
    else if (key === "--skip-presenter") args.includePresenter = false;
    else if (key === "--presenter") { args.presenterOnly = true; args.includePresenter = true; }
    else if (key === "--help" || key === "-h") {
      console.log("Usage: review_deck.js [html] [--out dir] [--min-margin px] [--skip-presenter] [--presenter] [--no-fail]");
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${key}`);
    }
  }
  return args;
}

function loadPlaywright() {
  const Module = require("module");
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
      "playwright が見つかりません。NODE_PATH に Playwright の node_modules を設定してください。\n" +
      `Original error: ${error.message}`
    );
  }
}

function fileUrl(filePath, presenter) {
  const resolved = path.resolve(filePath).replace(/\\/g, "/");
  const query = presenter ? "?presenter=1" : "";
  return `file:///${resolved}${query}#1`;
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function mdEscape(value) {
  return String(value).replace(/\|/g, "\\|").replace(/\n/g, " ");
}

async function launchBrowser(playwright) {
  try {
    return await playwright.chromium.launch({ channel: "chrome", headless: true });
  } catch (_) {
    return await playwright.chromium.launch({ headless: true });
  }
}

async function revealSlide(page, index) {
  await page.evaluate(async (slideIndex) => {
    const deck = window.slideDeck;
    const slides = [...document.querySelectorAll(".slide")];
    if (deck && typeof deck.show === "function") {
      deck.show(slideIndex, true, false);
      if (typeof deck.revealAll === "function") deck.revealAll();
    } else {
      slides.forEach((slide, i) => {
        slide.classList.toggle("active", i === slideIndex);
        slide.setAttribute("aria-hidden", i === slideIndex ? "false" : "true");
      });
      const slide = slides[slideIndex];
      if (slide) slide.querySelectorAll("[data-anim]").forEach((el) => el.classList.add("shown"));
    }
    await document.fonts?.ready;
  }, index);
  await page.waitForTimeout(80);
}

async function prepareSlideViewport(page, options) {
  await page.addStyleTag({
    content: `
      html, body {
        width: ${options.width}px !important;
        height: ${options.height}px !important;
        min-height: ${options.height}px !important;
        margin: 0 !important;
        padding: 0 !important;
        display: block !important;
        overflow: hidden !important;
      }
      #deck {
        transform: none !important;
        position: relative !important;
        left: 0 !important;
        top: 0 !important;
        margin: 0 !important;
      }
    `,
  });
}

async function disableMotion(page) {
  await page.addStyleTag({
    content: `
      *, *::before, *::after {
        transition-duration: 0s !important;
        transition-delay: 0s !important;
        animation-duration: 0s !important;
        animation-delay: 0s !important;
      }
    `,
  });
}

async function inspectSlide(page, index, options) {
  return await page.evaluate(({ slideIndex, minMargin, overlapTolerance }) => {
    const findings = [];
    const slides = [...document.querySelectorAll(".slide")];
    const slide = slides[slideIndex];
    if (!slide) return { findings: [{ type: "missing-slide", message: "slide not found" }] };

    const slideRect = slide.getBoundingClientRect();
    const isVisible = (el) => {
      const style = getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      return style.display !== "none" && style.visibility !== "hidden" &&
        Number(style.opacity) !== 0 && rect.width > 1 && rect.height > 1;
    };
    const relativeRect = (el) => {
      const r = el.getBoundingClientRect();
      return {
        x: Math.round(r.left - slideRect.left),
        y: Math.round(r.top - slideRect.top),
        width: Math.round(r.width),
        height: Math.round(r.height),
        right: Math.round(r.right - slideRect.left),
        bottom: Math.round(r.bottom - slideRect.top),
      };
    };
    const label = (el) => {
      const zone = el.dataset.zone ? `[data-zone="${el.dataset.zone}"]` : "";
      const cls = [...el.classList].slice(0, 3).map((c) => `.${c}`).join("");
      const text = (el.innerText || el.alt || "").trim().replace(/\s+/g, " ").slice(0, 48);
      return `${el.tagName.toLowerCase()}${zone}${cls}${text ? ` "${text}"` : ""}`;
    };
    const ignored = (el) => Boolean(el.closest("[data-overlap-ok], .bg, .background, .decor, .connector, .footer-zone, .page-number, .page-num, .source-note, .brand-badge"));
    const marginIgnored = (el) => Boolean(el.closest(".bg, .background, .decor, .footer-zone, .page-number, .page-num, .source-note, .brand-badge"));

    const allVisible = [...slide.querySelectorAll("*")].filter(isVisible);

    for (const el of allVisible) {
      const r = relativeRect(el);
      if (r.x < -1 || r.y < -1 || r.right > slideRect.width + 1 || r.bottom > slideRect.height + 1) {
        if (!ignored(el)) {
          findings.push({ type: "overflow-slide", element: label(el), rect: r, message: "要素がスライド境界からはみ出しています" });
        }
      }
    }

    const textCandidates = allVisible.filter((el) => {
      const tag = el.tagName.toLowerCase();
      return ["h1", "h2", "h3", "p", "li", "blockquote"].includes(tag) ||
        el.matches(".card, .conclusion-bar, .statement, [data-zone='title'], [data-zone='text'], [data-zone='conclusion']");
    });
    for (const el of textCandidates) {
      const style = getComputedStyle(el);
      const clipsX = style.overflowX !== "visible";
      const clipsY = style.overflowY !== "visible";
      const clippedX = clipsX && el.scrollWidth > el.clientWidth + 2;
      const clippedY = clipsY && el.scrollHeight > el.clientHeight + 4;
      if (clippedX || clippedY) {
        findings.push({ type: "text-clipped", element: label(el), rect: relativeRect(el), message: "テキストまたは内容が要素内で切れています" });
      }
    }

    const marginCandidates = allVisible.filter((el) => {
      if (marginIgnored(el)) return false;
      return el.matches("h1,h2,h3,p,li,img,.card,.conclusion-bar,.statement,[data-zone='title'],[data-zone='text'],[data-zone='visual'],[data-zone='conclusion'],[data-zone='qr']");
    });
    for (const el of marginCandidates) {
      const r = relativeRect(el);
      const near = [];
      if (r.x < minMargin) near.push("left");
      if (r.y < minMargin) near.push("top");
      if (slideRect.width - r.right < minMargin) near.push("right");
      if (slideRect.height - r.bottom < minMargin) near.push("bottom");
      if (near.length) {
        findings.push({ type: "tight-margin", element: label(el), rect: r, edge: near, message: `スライド端に近すぎます: ${near.join(", ")}` });
      }
    }

    const zones = [...slide.querySelectorAll(".zone[data-zone]:not([data-overlap-ok])")].filter((el) => isVisible(el) && !ignored(el));
    for (let i = 0; i < zones.length; i++) {
      for (let j = i + 1; j < zones.length; j++) {
        const a = zones[i];
        const b = zones[j];
        if (a.contains(b) || b.contains(a)) continue;
        const ar = a.getBoundingClientRect();
        const br = b.getBoundingClientRect();
        const ix = Math.min(ar.right, br.right) - Math.max(ar.left, br.left);
        const iy = Math.min(ar.bottom, br.bottom) - Math.max(ar.top, br.top);
        if (ix > overlapTolerance && iy > overlapTolerance) {
          findings.push({
            type: "overlap",
            element: `${label(a)} / ${label(b)}`,
            rect: { a: relativeRect(a), b: relativeRect(b), intersection: { width: Math.round(ix), height: Math.round(iy) } },
            message: "ゾーン同士が重なっています",
          });
        }
      }
    }

    for (const img of [...slide.querySelectorAll("img")].filter(isVisible)) {
      if (!img.naturalWidth || !img.naturalHeight) {
        findings.push({ type: "broken-image", element: label(img), rect: relativeRect(img), message: "画像が読み込めていません" });
      }
    }

    return { findings };
  }, { slideIndex: index, minMargin: options.minMargin, overlapTolerance: options.overlapTolerance });
}

async function collectActiveSlideStyles(page) {
  return await page.evaluate(() => {
    const slide = document.querySelector(".slide.active");
    if (!slide) return [];
    const elements = [slide, ...slide.querySelectorAll("*")];
    return elements.slice(0, 240).map((el) => {
      const style = getComputedStyle(el);
      const text = (el.innerText || el.alt || "").trim().replace(/\s+/g, " ").slice(0, 48);
      return {
        tag: el.tagName.toLowerCase(),
        classes: [...el.classList].slice(0, 4).join(" "),
        text,
        color: style.color,
        backgroundColor: style.backgroundColor,
        opacity: style.opacity,
        visibility: style.visibility,
        display: style.display,
        fontSize: style.fontSize,
        fontWeight: style.fontWeight,
      };
    });
  });
}

async function inspectPresenter(page, index, expectedCurrentHTML, expectedStyles) {
  return await page.evaluate(({ slideIndex, expectedHTML, expectedStyleSnapshot }) => {
    const findings = [];
    const root = document.getElementById("presenterConsole");
    const slideCount = document.querySelectorAll("body > .deck .slide").length || document.querySelectorAll(".slide").length;
    const normalize = (html) => String(html || "").replace(/\s+/g, " ").trim();
    const isVisible = (el) => {
      const style = getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      return style.display !== "none" && style.visibility !== "hidden" &&
        Number(style.opacity) !== 0 && rect.width > 1 && rect.height > 1;
    };
    const rectOf = (el) => {
      const r = el.getBoundingClientRect();
      return {
        x: Math.round(r.left),
        y: Math.round(r.top),
        width: Math.round(r.width),
        height: Math.round(r.height),
        right: Math.round(r.right),
        bottom: Math.round(r.bottom),
      };
    };
    const label = (el) => {
      const id = el.id ? `#${el.id}` : "";
      const cls = [...el.classList].slice(0, 3).map((c) => `.${c}`).join("");
      const text = (el.innerText || el.alt || "").trim().replace(/\s+/g, " ").slice(0, 48);
      return `${el.tagName.toLowerCase()}${id}${cls}${text ? ` "${text}"` : ""}`;
    };
    const labelFromSnapshot = (item) => {
      const cls = item.classes ? `.${item.classes.split(/\s+/).filter(Boolean).join(".")}` : "";
      return `${item.tag}${cls}${item.text ? ` "${item.text}"` : ""}`;
    };

    if (!document.body.classList.contains("presenter-mode")) {
      findings.push({ type: "presenter-mode-missing", message: "発表者ビューモードになっていません" });
    }
    if (!root || !isVisible(root)) {
      findings.push({ type: "presenter-console-missing", message: "発表者ビュー本体が表示されていません" });
      return { findings };
    }

    const shortcutPanel = root.querySelector(".presenter-shortcuts");
    if (!shortcutPanel || !isVisible(shortcutPanel)) {
      findings.push({ type: "presenter-shortcuts-missing", message: "ショートカット一覧が発表者ビューに表示されていません" });
    }

    const currentSlide = root.querySelector("#presenterCurrent .slide");
    if (!currentSlide || !isVisible(currentSlide)) {
      findings.push({ type: "presenter-current-missing", message: "現在スライドのプレビューが表示されていません" });
    } else if (expectedHTML && normalize(currentSlide.outerHTML) !== normalize(expectedHTML)) {
      findings.push({
        type: "presenter-current-mismatch",
        element: label(currentSlide),
        rect: rectOf(currentSlide),
        message: "現在プレビューのDOMが投影側の現在スライドDOMと一致していません",
      });
    }

    if (currentSlide && Array.isArray(expectedStyleSnapshot) && expectedStyleSnapshot.length) {
      const currentElements = [currentSlide, ...currentSlide.querySelectorAll("*")];
      let styleMismatchCount = 0;
      const comparableKeys = ["color", "backgroundColor", "opacity", "visibility", "display", "fontSize", "fontWeight"];
      for (let i = 0; i < Math.min(currentElements.length, expectedStyleSnapshot.length); i++) {
        const current = currentElements[i];
        const expected = expectedStyleSnapshot[i];
        const currentStyle = getComputedStyle(current);
        const mismatch = comparableKeys.filter((key) => currentStyle[key] !== expected[key]);
        if (mismatch.length) {
          findings.push({
            type: "presenter-style-mismatch",
            element: label(current),
            rect: rectOf(current),
            message: `投影側と発表者ビューでcomputed styleが異なります: ${labelFromSnapshot(expected)} / ${mismatch.join(", ")}`,
          });
          styleMismatchCount++;
          if (styleMismatchCount >= 5) break;
        }
      }
    }

    const nextSlide = root.querySelector("#presenterNext .slide");
    if (slideIndex < slideCount - 1 && (!nextSlide || !isVisible(nextSlide))) {
      findings.push({ type: "presenter-next-missing", message: "次スライドのプレビューが表示されていません" });
    }

    const visible = [...root.querySelectorAll("*")].filter(isVisible);
    for (const el of visible) {
      const r = rectOf(el);
      if (r.x < -1 || r.y < -1 || r.right > innerWidth + 1 || r.bottom > innerHeight + 1) {
        findings.push({ type: "presenter-overflow-window", element: label(el), rect: r, message: "発表者ビューの要素がウィンドウ外へはみ出しています" });
      }
    }

    const textCandidates = visible.filter((el) => {
      const tag = el.tagName.toLowerCase();
      return ["h1", "h2", "h3", "p", "li", "button", "kbd", "span"].includes(tag) ||
        el.matches(".presenter-label, .presenter-note, .presenter-position, .presenter-shortcut, .presenter-controls button");
    });
    for (const el of textCandidates) {
      const style = getComputedStyle(el);
      const clipsX = style.overflowX !== "visible";
      const clipsY = style.overflowY !== "visible";
      const clippedX = clipsX && el.scrollWidth > el.clientWidth + 2;
      const clippedY = clipsY && el.scrollHeight > el.clientHeight + 4;
      if (clippedX || clippedY) {
        findings.push({ type: "presenter-text-clipped", element: label(el), rect: rectOf(el), message: "発表者ビューのテキストまたは内容が切れています" });
      }
    }

    for (const img of [...root.querySelectorAll("img")].filter(isVisible)) {
      if (!img.naturalWidth || !img.naturalHeight) {
        findings.push({ type: "presenter-broken-image", element: label(img), rect: rectOf(img), message: "発表者ビュー内の画像が読み込めていません" });
      }
    }

    return { findings };
  }, { slideIndex: index, expectedHTML: expectedCurrentHTML, expectedStyleSnapshot: expectedStyles });
}

function buildMarkdown(report) {
  const lines = [];
  lines.push("# LTスライド視覚レビューレポート");
  lines.push("");
  lines.push(`- 対象: ${report.html}`);
  lines.push(`- スライド数: ${report.slideCount}`);
  lines.push(`- finding数: ${report.findingCount}`);
  lines.push(`- 通常表示finding数: ${report.audienceFindingCount}`);
  lines.push(`- 発表者ビューfinding数: ${report.presenterFindingCount}`);
  lines.push(`- viewport: ${report.viewport.width}x${report.viewport.height}`);
  lines.push(`- 最小余白: ${report.minMargin}px`);
  lines.push("");
  if (report.slides.length) {
    lines.push("## 通常表示");
    lines.push("");
  }
  for (const slide of report.slides) {
    lines.push(`### Slide ${slide.index + 1}`);
    lines.push("");
    lines.push(`- screenshot: ${slide.screenshot}`);
    if (!slide.findings.length) {
      lines.push("- findings: なし");
      lines.push("");
      continue;
    }
    lines.push("");
    lines.push("| type | element | message | rect |");
    lines.push("| --- | --- | --- | --- |");
    for (const finding of slide.findings) {
      lines.push(`| ${mdEscape(finding.type)} | ${mdEscape(finding.element || "")} | ${mdEscape(finding.message || "")} | ${mdEscape(JSON.stringify(finding.rect || {}))} |`);
    }
    lines.push("");
  }
  if (report.presenterSlides.length) {
    lines.push("## 発表者ビュー");
    lines.push("");
  }
  for (const slide of report.presenterSlides) {
    lines.push(`### Presenter Slide ${slide.index + 1}`);
    lines.push("");
    lines.push(`- screenshot: ${slide.screenshot}`);
    if (!slide.findings.length) {
      lines.push("- findings: なし");
      lines.push("");
      continue;
    }
    lines.push("");
    lines.push("| type | element | message | rect |");
    lines.push("| --- | --- | --- | --- |");
    for (const finding of slide.findings) {
      lines.push(`| ${mdEscape(finding.type)} | ${mdEscape(finding.element || "")} | ${mdEscape(finding.message || "")} | ${mdEscape(JSON.stringify(finding.rect || {}))} |`);
    }
    lines.push("");
  }
  return lines.join("\n");
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  ensureDir(args.out);
  const playwright = loadPlaywright();
  const browser = await launchBrowser(playwright);
  const audiencePage = await browser.newPage({ viewport: { width: args.width, height: args.height }, deviceScaleFactor: 1 });
  await audiencePage.goto(fileUrl(args.html, false), { waitUntil: "networkidle" });
  await disableMotion(audiencePage);
  await prepareSlideViewport(audiencePage, args);
  await audiencePage.waitForTimeout(200);

  const slideCount = await audiencePage.locator(".slide").count();
  const report = {
    html: path.resolve(args.html),
    slideCount,
    viewport: { width: args.width, height: args.height },
    minMargin: args.minMargin,
    overlapTolerance: args.overlapTolerance,
    slides: [],
    presenterSlides: [],
    audienceFindingCount: 0,
    presenterFindingCount: 0,
    findingCount: 0,
  };

  if (!args.presenterOnly) {
    for (let i = 0; i < slideCount; i++) {
      await revealSlide(audiencePage, i);
      const screenshot = path.join(args.out, `slide-${String(i + 1).padStart(2, "0")}.png`);
      await audiencePage.screenshot({ path: screenshot, fullPage: false });
      const result = await inspectSlide(audiencePage, i, args);
      report.audienceFindingCount += result.findings.length;
      report.slides.push({ index: i, screenshot, findings: result.findings });
    }
  }

  if (args.includePresenter) {
    const presenterPage = await browser.newPage({ viewport: { width: args.width, height: args.height }, deviceScaleFactor: 1 });
    await presenterPage.goto(fileUrl(args.html, true), { waitUntil: "networkidle" });
    await disableMotion(presenterPage);
    await presenterPage.waitForTimeout(300);

    for (let i = 0; i < slideCount; i++) {
      await revealSlide(audiencePage, i);
      const expectedCurrentHTML = await audiencePage.evaluate(() => document.querySelector(".slide.active")?.outerHTML || "");
      const expectedStyles = await collectActiveSlideStyles(audiencePage);
      const state = await audiencePage.evaluate(() => window.slideDeck && typeof window.slideDeck.state === "function" ? window.slideDeck.state() : null);
      if (state) await presenterPage.evaluate((message) => window.slideDeck?.receive?.(message), state);
      await presenterPage.waitForTimeout(120);
      const screenshot = path.join(args.out, `presenter-slide-${String(i + 1).padStart(2, "0")}.png`);
      await presenterPage.screenshot({ path: screenshot, fullPage: false });
      const result = await inspectPresenter(presenterPage, i, expectedCurrentHTML, expectedStyles);
      report.presenterFindingCount += result.findings.length;
      report.presenterSlides.push({ index: i, screenshot, findings: result.findings });
    }

    await presenterPage.close();
  }

  report.findingCount = report.audienceFindingCount + report.presenterFindingCount;
  await audiencePage.close();
  await browser.close();

  const jsonPath = path.join(args.out, "review-report.json");
  const mdPath = path.join(args.out, "review-report.md");
  fs.writeFileSync(jsonPath, JSON.stringify(report, null, 2), "utf8");
  fs.writeFileSync(mdPath, buildMarkdown(report), "utf8");

  console.log(`OK: reviewed ${slideCount} slides`);
  console.log(`Report: ${mdPath}`);
  console.log(`Findings: ${report.findingCount}`);
  if (report.findingCount > 0 && !args.noFail) process.exit(1);
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(2);
});

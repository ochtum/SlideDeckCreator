#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

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
    story: null,
    blueprint: null,
    python: process.env.PYTHON || null,
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
    else if (key === "--story") { args.story = value; i++; }
    else if (key === "--blueprint") { args.blueprint = value; i++; }
    else if (key === "--python") { args.python = value; i++; }
    else if (key === "--help" || key === "-h") {
      console.log("Usage: review_deck.js [html] [--story story.yaml] [--blueprint blueprint.yaml] [--out dir] [--min-margin px] [--skip-presenter] [--presenter] [--no-fail]");
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${key}`);
    }
  }
  return args;
}

function findWorkspaceRoot(htmlPath) {
  let current = path.dirname(path.resolve(htmlPath));
  while (true) {
    if (fs.existsSync(path.join(current, ".lt-slide-work"))) return current;
    const parent = path.dirname(current);
    if (parent === current) return null;
    current = parent;
  }
}

function resolveContractPaths(args) {
  const html = path.resolve(args.html);
  const root = findWorkspaceRoot(html);
  const result = {
    root,
    story: args.story ? path.resolve(args.story) : null,
    blueprint: args.blueprint ? path.resolve(args.blueprint) : null,
  };
  if (!root) return result;

  const relative = path.relative(path.join(root, "output"), html).split(path.sep);
  const partId = relative.length === 2 && relative[1] === "index.html" ? relative[0] : null;
  if (!result.story) {
    result.story = partId
      ? path.join(root, ".lt-slide-work", "parts", partId, "01-story.yaml")
      : path.join(root, ".lt-slide-work", "01-story.yaml");
  }
  if (!result.blueprint) {
    result.blueprint = partId
      ? path.join(root, ".lt-slide-work", "parts", partId, "02-blueprint.yaml")
      : path.join(root, ".lt-slide-work", "02-blueprint.yaml");
  }
  return result;
}

function runPythonCheck(python, script, args) {
  const result = spawnSync(python, [script, ...args], {
    encoding: "utf8",
    env: { ...process.env, PYTHONUTF8: "1" },
  });
  const output = `${result.stdout || ""}${result.stderr || ""}`.trim();
  return {
    script,
    args,
    exitCode: typeof result.status === "number" ? result.status : 2,
    output: output || (result.error ? result.error.message : "validator produced no output"),
  };
}

function readTopLevelYamlSection(filePath, sectionName) {
  const values = {};
  const lines = fs.readFileSync(filePath, "utf8").split(/\r?\n/);
  let inSection = false;
  for (const line of lines) {
    if (!inSection) {
      if (line === `${sectionName}:`) inSection = true;
      continue;
    }
    if (/^[^\s#]/.test(line)) break;
    const match = line.match(/^\s{2}([A-Za-z0-9_-]+):\s*(.*?)\s*$/);
    if (!match) continue;
    let value = match[2].replace(/\s+#.*$/, "").trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    values[match[1]] = value;
  }
  return values;
}

function validateContracts(args) {
  const paths = resolveContractPaths(args);
  const checks = [];
  const failures = [];
  if (!paths.root) {
    failures.push({ type: "contract-input-missing", message: "ワークスペースルートを特定できません。--story と --blueprint を指定してください。" });
    return { paths, checks, failures };
  }
  if (!paths.story || !fs.existsSync(paths.story)) {
    failures.push({ type: "contract-input-missing", message: `対応する01-story.yamlがありません: ${paths.story || "(未指定)"}` });
  }
  if (!paths.blueprint || !fs.existsSync(paths.blueprint)) {
    failures.push({ type: "contract-input-missing", message: `対応する02-blueprint.yamlがありません: ${paths.blueprint || "(未指定)"}` });
  }
  if (failures.length) return { paths, checks, failures };

  const python = args.python || (process.platform === "win32" ? "python" : "python3");
  const spoken = runPythonCheck(
    python,
    path.join(paths.root, ".codex", "skills", "01-lt-slide-story", "scripts", "validate_spoken_notes.py"),
    ["--story", paths.story, "--html", path.resolve(args.html)],
  );
  const talkability = runPythonCheck(
    python,
    path.join(paths.root, ".codex", "skills", "01-lt-slide-story", "scripts", "validate_talkability.py"),
    ["--story", paths.story, "--blueprint", paths.blueprint, "--html", path.resolve(args.html)],
  );
  const visual = runPythonCheck(
    python,
    path.join(paths.root, ".codex", "skills", "02-lt-slide-blueprint", "scripts", "validate_visual_plan.py"),
    ["--story", paths.story, "--blueprint", paths.blueprint],
  );
  const depth = runPythonCheck(
    python,
    path.join(paths.root, ".codex", "skills", "01-lt-slide-story", "scripts", "validate_explanation_depth.py"),
    ["--story", paths.story, "--blueprint", paths.blueprint, "--html", path.resolve(args.html)],
  );
  const roadmap = runPythonCheck(
    python,
    path.join(paths.root, ".codex", "skills", "01-lt-slide-story", "scripts", "validate_roadmap.py"),
    ["--story", paths.story, "--blueprint", paths.blueprint, "--html", path.resolve(args.html)],
  );
  const motion = runPythonCheck(
    python,
    path.join(paths.root, ".codex", "skills", "04-lt-slide-build", "scripts", "validate_animation_choreography.py"),
    ["--blueprint", paths.blueprint, "--html", path.resolve(args.html)],
  );
  const presenterSelection = readTopLevelYamlSection(paths.story, "presenter");
  const presenterIncluded = /^(true|yes|1)$/i.test(presenterSelection.include || "");
  const presenterBinding = presenterIncluded
    ? runPythonCheck(
        python,
        path.join(paths.root, ".codex", "skills", "04-lt-slide-build", "scripts", "validate_presenter_binding.py"),
        [
          "--presenter",
          path.resolve(path.dirname(paths.story), presenterSelection.data_file || "../config/presenter.json"),
          path.resolve(args.html),
        ],
      )
    : {
        script: null,
        args: [],
        exitCode: 0,
        output: "SKIPPED: Storyで自己紹介スライドを使用していません",
      };
  const designSystemSelection = readTopLevelYamlSection(paths.story, "design_system");
  let designSystem;
  if (designSystemSelection.registry) {
    const registryPath = path.resolve(path.dirname(paths.story), designSystemSelection.registry);
    designSystem = runPythonCheck(
      python,
      path.join(paths.root, ".codex", "skills", "07-lt-design-system-manager", "scripts", "manage_design_system.py"),
      ["validate-binding", "--root", path.dirname(registryPath), "--story", paths.story, "--blueprint", paths.blueprint, "--html", path.resolve(args.html)],
    );
  } else {
    designSystem = {
      script: null,
      args: [],
      exitCode: 0,
      output: `SKIPPED: Storyは内蔵デザインシステムを使用しています (${designSystemSelection.id || "未選択"})`,
    };
  }
  const rootStory = path.join(paths.root, ".lt-slide-work", "01-story.yaml");
  const sourceInventory = path.join(paths.root, ".lt-slide-work", "source-inventory.yaml");
  let contentEquivalence = null;
  if (fs.existsSync(rootStory) && fs.existsSync(sourceInventory)) {
    const outputRoot = path.join(paths.root, "output");
    const htmlFiles = [];
    const single = path.join(outputRoot, "index.html");
    if (fs.existsSync(single)) htmlFiles.push(single);
    if (fs.existsSync(outputRoot)) {
      for (const entry of fs.readdirSync(outputRoot, { withFileTypes: true })) {
        const candidate = entry.isDirectory() ? path.join(outputRoot, entry.name, "index.html") : null;
        if (candidate && fs.existsSync(candidate)) htmlFiles.push(candidate);
      }
    }
    const contentArgs = ["--inventory", sourceInventory, "--story", rootStory];
    for (const htmlFile of htmlFiles) contentArgs.push("--html", htmlFile);
    contentEquivalence = runPythonCheck(
      python,
      path.join(paths.root, ".codex", "skills", "01-lt-slide-story", "scripts", "audit_content_equivalence.py"),
      contentArgs,
    );
  }
  checks.push(
    { name: "spoken-notes", ...spoken },
    { name: "talkability", ...talkability },
    { name: "visual-plan", ...visual },
    { name: "explanation-depth", ...depth },
    { name: "roadmap", ...roadmap },
    { name: "animation-choreography", ...motion },
    { name: "presenter-binding", ...presenterBinding },
    { name: "design-system-binding", ...designSystem },
  );
  if (contentEquivalence) checks.push({ name: "content-equivalence", ...contentEquivalence });
  for (const check of checks) {
    if (check.exitCode !== 0) {
      failures.push({
        type: `contract-${check.name}-failed`,
        message: check.output,
      });
    }
  }
  return { paths, checks, failures };
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
      if (ignored(el)) return false;
      const tag = el.tagName.toLowerCase();
      return ["h1", "h2", "h3", "p", "li", "blockquote", "span", "td", "th", "pre", "code"].includes(tag) ||
        el.matches(".card, .conclusion-bar, .statement, [data-zone='title'], [data-zone='text'], [data-zone='conclusion']");
    });
    const clippedByAncestor = (el) => {
      let ancestor = el.parentElement;
      while (ancestor && ancestor !== slide) {
        if (ignored(ancestor)) return null;
        const style = getComputedStyle(ancestor);
        if (/(hidden|clip)/.test(`${style.overflow} ${style.overflowX} ${style.overflowY}`)) {
          const outer = ancestor.getBoundingClientRect();
          const inner = el.getBoundingClientRect();
          const clipped = inner.left < outer.left - 1 || inner.top < outer.top - 1 ||
            inner.right > outer.right + 1 || inner.bottom > outer.bottom + 1;
          if (clipped) return ancestor;
        }
        ancestor = ancestor.parentElement;
      }
      return null;
    };
    for (const el of textCandidates) {
      const style = getComputedStyle(el);
      const clipsX = style.overflowX !== "visible";
      const clipsY = style.overflowY !== "visible";
      const clippedX = clipsX && el.scrollWidth > el.clientWidth + 2;
      const clippedY = clipsY && el.scrollHeight > el.clientHeight + 4;
      const clippingAncestor = clippedByAncestor(el);
      if (clippedX || clippedY || clippingAncestor) {
        findings.push({
          type: "text-clipped",
          element: label(el),
          rect: relativeRect(el),
          message: clippingAncestor
            ? `テキストが祖先要素 ${label(clippingAncestor)} の境界で切れています`
            : "テキストまたは内容が要素内で切れています",
        });
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

    const genericPhrases = ["対象を確認する", "証拠を残す", "完了条件を確認する", "次の判断を確認する"];
    const slideText = (slide.innerText || "").replace(/\s+/g, " ");
    const genericHits = genericPhrases.filter((phrase) => slideText.includes(phrase));
    if (genericHits.length >= 2) {
      findings.push({
        type: "generic-explanation",
        message: `ページ固有の説明ではない汎用チェックが使われています: ${genericHits.join(" / ")}`,
      });
    }

    const estimatedSeconds = Number(slide.dataset.estimatedSeconds || 0);
    if (estimatedSeconds >= 60) {
      const detailTexts = [...slide.querySelectorAll("p,li,td,th,pre,code,.card,.flow-node,.check-item,[data-detail]")]
        .filter((el) => isVisible(el) && !el.closest("[data-zone='title'],.brand-badge,.footer-zone,.page-number,.page-num"))
        .map((el) => (el.innerText || "").trim().replace(/\s+/g, " "))
        .filter((text) => text.length >= 6);
      const uniqueDetails = new Set(detailTexts);
      const hasStructuredEvidence = Boolean(slide.querySelector("table,pre,code,img,svg"));
      if (uniqueDetails.size < 2 && !hasStructuredEvidence) {
        findings.push({
          type: "explanation-thin",
          message: `${estimatedSeconds}秒の説明に対して、投影面の具体的な説明要素が不足しています`,
        });
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

    const sourceSlide = [...document.querySelectorAll("body > .deck .slide")][slideIndex];
    const primaryScript = root.querySelector(".presenter-cue-primary .presenter-cue-body");
    const minimumPrimaryHeight = Math.round(Math.min(220, Math.max(160, innerHeight * .25)));
    if (!primaryScript || !isVisible(primaryScript)) {
      findings.push({ type: "presenter-primary-script-missing", message: "「話す内容」の主表示領域がありません" });
    } else {
      const primaryRect = rectOf(primaryScript);
      if (primaryRect.height < minimumPrimaryHeight) {
        findings.push({
          type: "presenter-primary-script-too-small",
          element: label(primaryScript),
          rect: primaryRect,
          message: `「話す内容」の表示高が不足しています: ${primaryRect.height}px < ${minimumPrimaryHeight}px`,
        });
      }
    }

    const contextPanel = root.querySelector("#presenterContext");
    const minimumContextHeight = Math.round(Math.min(160, Math.max(120, innerHeight * .18)));
    if (contextPanel && isVisible(contextPanel)) {
      const contextRect = rectOf(contextPanel);
      if (contextRect.height < minimumContextHeight) {
        findings.push({
          type: "presenter-context-too-small",
          element: label(contextPanel),
          rect: contextRect,
          message: `問い・文脈の表示高が不足しています: ${contextRect.height}px < ${minimumContextHeight}px`,
        });
      }
    }
    if (sourceSlide?.dataset.phaseQuestion) {
      const question = root.querySelector(".presenter-context-row.is-question .presenter-context-body");
      if (!question || !isVisible(question)) {
        findings.push({ type: "presenter-question-missing", message: "phaseの問いが独立した領域に表示されていません" });
      }
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
    const isClippedByScrollableAncestor = (el) => {
      let ancestor = el.parentElement;
      while (ancestor && ancestor !== root) {
        const style = getComputedStyle(ancestor);
        const scrollable = /(auto|scroll|hidden|clip)/.test(`${style.overflow} ${style.overflowX} ${style.overflowY}`);
        if (scrollable) {
          const a = ancestor.getBoundingClientRect();
          const r = el.getBoundingClientRect();
          const extendsBeyondAncestor =
            r.left < a.left - 1 || r.top < a.top - 1 || r.right > a.right + 1 || r.bottom > a.bottom + 1;
          const ancestorInsideWindow =
            a.left >= -1 && a.top >= -1 && a.right <= innerWidth + 1 && a.bottom <= innerHeight + 1;
          if (extendsBeyondAncestor && ancestorInsideWindow) return true;
        }
        ancestor = ancestor.parentElement;
      }
      return false;
    };
    for (const el of visible) {
      const r = rectOf(el);
      if (
        (r.x < -1 || r.y < -1 || r.right > innerWidth + 1 || r.bottom > innerHeight + 1) &&
        !isClippedByScrollableAncestor(el)
      ) {
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

async function inspectPresenterScrollStability(page) {
  return await page.evaluate(async () => {
    const primary = () => document.querySelector(".presenter-cue-primary .presenter-cue-body");
    const scroller = primary();
    if (!scroller || scroller.scrollHeight <= scroller.clientHeight + 4) {
      return { tested: false, findings: [] };
    }
    const maximum = Math.max(0, scroller.scrollHeight - scroller.clientHeight);
    scroller.scrollTop = Math.min(80, maximum);
    const before = {
      scrollTop: scroller.scrollTop,
      timer: document.getElementById("presenterTime")?.textContent || "",
    };
    await new Promise((resolve) => setTimeout(resolve, 1250));
    const current = primary();
    const after = {
      scrollTop: current?.scrollTop || 0,
      timer: document.getElementById("presenterTime")?.textContent || "",
    };
    const findings = [];
    if (Math.abs(after.scrollTop - before.scrollTop) > 2) {
      findings.push({
        type: "presenter-note-scroll-reset",
        message: `タイマー更新後に「話す内容」のスクロール位置が変化しました: ${before.scrollTop}px -> ${after.scrollTop}px`,
      });
    }
    if (after.timer === before.timer) {
      findings.push({
        type: "presenter-timer-stalled",
        message: `スクロール保持試験中にタイマーが進みませんでした: ${before.timer}`,
      });
    }
    current?.scrollTo?.({ top: 0 });
    return { tested: true, before, after, findings };
  });
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
  lines.push(`- 契約検証finding数: ${report.contractFindingCount}`);
  lines.push(`- viewport: ${report.viewport.width}x${report.viewport.height}`);
  lines.push(`- 最小余白: ${report.minMargin}px`);
  lines.push("");
  lines.push("## 契約検証");
  lines.push("");
  if (!report.contract.findings.length) {
    lines.push("- findings: なし");
  } else {
    for (const finding of report.contract.findings) {
      lines.push(`- ${finding.type}: ${finding.message}`);
    }
  }
  for (const check of report.contract.checks) {
    lines.push(`- ${check.name}: ${check.exitCode === 0 ? "OK" : "FAILED"}`);
  }
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
  const contract = validateContracts(args);
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
    contractFindingCount: contract.failures.length,
    findingCount: 0,
    contract: {
      story: contract.paths.story,
      blueprint: contract.paths.blueprint,
      checks: contract.checks,
      findings: contract.failures,
    },
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

    let scrollStabilityTested = false;
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
      if (!scrollStabilityTested) {
        const stability = await inspectPresenterScrollStability(presenterPage);
        if (stability.tested) {
          scrollStabilityTested = true;
          result.findings.push(...stability.findings);
        }
      }
      report.presenterFindingCount += result.findings.length;
      report.presenterSlides.push({ index: i, screenshot, findings: result.findings });
    }

    await presenterPage.close();
  }

  report.findingCount = report.audienceFindingCount + report.presenterFindingCount + report.contractFindingCount;
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

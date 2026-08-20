#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");

const EDITOR_STYLE_ID = "lt-slide-editor-style";
const EDITOR_SCRIPT_ID = "lt-slide-editor-runtime";

function usage() {
  console.error("Usage: node inject_editor.js <index.html> [--out <path>]");
  process.exit(2);
}

const args = process.argv.slice(2);
if (!args[0] || args.includes("--help") || args.includes("-h")) usage();

const inputPath = path.resolve(args[0]);
const outIndex = args.indexOf("--out");
const outputPath = outIndex >= 0 ? path.resolve(args[outIndex + 1] || "") : inputPath;
if (outIndex >= 0 && !args[outIndex + 1]) usage();

if (!fs.existsSync(inputPath)) {
  console.error(`[lt-editor] File not found: ${inputPath}`);
  process.exit(1);
}

let html = fs.readFileSync(inputPath, "utf8");
if (!html.includes("class=\"deck\"") && !html.includes("class='deck'")) {
  console.error("[lt-editor] Target does not look like an LT slide deck: missing .deck");
  process.exit(1);
}
if (!html.includes("class=\"slide") && !html.includes("class='slide")) {
  console.error("[lt-editor] Target does not look like an LT slide deck: missing .slide");
  process.exit(1);
}

html = removeBlock(html, "style", EDITOR_STYLE_ID);
html = removeBlock(html, "script", EDITOR_SCRIPT_ID);

const styleBlock = `<style id="${EDITOR_STYLE_ID}">
${editorCss()}
</style>`;
const scriptBlock = `<script id="${EDITOR_SCRIPT_ID}">
${editorRuntime()}
</script>`;

html = insertBefore(html, /<\/head>/i, `${styleBlock}\n`);
html = insertBefore(html, /<\/body>/i, `${scriptBlock}\n`);

if (outputPath === inputPath) {
  const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/T/, "-").slice(0, 15);
  const backup = `${inputPath}.bak-${stamp}`;
  fs.copyFileSync(inputPath, backup);
  console.log(`[lt-editor] Backup created: ${backup}`);
}

fs.writeFileSync(outputPath, html, "utf8");
console.log(`[lt-editor] Editor injected: ${outputPath}`);
console.log("[lt-editor] Open with ?edit=1 to edit slides, or press E in normal mode.");

function removeBlock(source, tag, id) {
  const re = new RegExp(`\\n?\\s*<${tag}[^>]*id=["']${escapeRe(id)}["'][\\s\\S]*?<\\/${tag}>\\s*`, "gi");
  return source.replace(re, "\n");
}

function insertBefore(source, re, addition) {
  if (!re.test(source)) {
    throw new Error(`Cannot insert editor runtime: missing ${re}`);
  }
  return source.replace(re, `${addition}$&`);
}

function escapeRe(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function editorCss() {
  return String.raw`
@media print {
  .lt-editor-root,
  .lt-editor-mode-badge,
  .lt-editor-selection,
  .lt-editor-tail-handle {
    display: none !important;
  }
  body.lt-editor-enabled {
    display: block !important;
    height: auto !important;
    overflow: visible !important;
    padding: 0 !important;
    background: #fff !important;
  }
  body.lt-editor-enabled > .deck {
    position: relative !important;
    left: auto !important;
    top: auto !important;
    z-index: auto !important;
    transform: none !important;
  }
}
body.lt-editor-enabled {
  --lt-editor-accent: #1d74e8;
  display: block;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  padding: 0;
  background: #0b1730;
}
body.lt-editor-enabled > .deck {
  position: fixed;
  z-index: 2147483000;
  transform-origin: top left !important;
}
body.lt-editor-enabled .pager,
body.lt-editor-enabled .presenter-console {
  display: none !important;
}
body.lt-editor-enabled.overview .pager {
  display: block !important;
}
body.lt-editor-enabled.overview > .deck {
  visibility: hidden;
}
body.lt-editor-enabled.overview .lt-editor-mode-badge {
  display: none !important;
}
body.lt-editor-view-mode .lt-editor-root,
body.lt-editor-view-mode .lt-editor-selection,
body.lt-editor-view-mode .lt-editor-tail-handle {
  display: none !important;
}
body.lt-editor-enabled.lt-editor-view-mode {
  display: grid;
  place-items: center;
  padding: var(--viewport-gutter, 48px);
  background: #edf4fb;
}
body.lt-editor-enabled.lt-editor-view-mode > .deck {
  position: relative;
  left: auto !important;
  top: auto !important;
  z-index: auto;
  transform-origin: center !important;
}
.lt-editor-root {
  position: fixed;
  z-index: 2147482000;
  inset: 16px;
  display: grid;
  grid-template-columns: minmax(0, 1.12fr) minmax(420px, .88fr);
  gap: 16px;
  color: #dce8ff;
  font-family: system-ui, -apple-system, "Segoe UI", "Noto Sans JP", sans-serif;
  pointer-events: none;
}
.lt-editor-root * {
  box-sizing: border-box;
}
.lt-editor-stage-shell,
.lt-editor-side-shell {
  min-width: 0;
  min-height: 0;
  border: 1px solid rgba(255, 255, 255, .14);
  border-radius: 18px;
  background: #111f3b;
  box-shadow: 0 20px 60px rgba(0, 0, 0, .28);
  overflow: hidden;
}
.lt-editor-stage-shell {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) minmax(230px, 34vh);
  gap: 10px;
  padding: 14px;
}
.lt-editor-stage-head,
.lt-editor-side-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #9fb5d8;
  font-size: 18px;
  line-height: 1.2;
  font-weight: 900;
}
.lt-editor-stage-viewport {
  min-width: 0;
  min-height: 0;
  border-radius: 12px;
  background: #fff;
  box-shadow: inset 0 0 0 1px rgba(0, 27, 77, .12);
  overflow: hidden;
}
.lt-editor-dock {
  position: relative;
  z-index: 2147483200;
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
  min-width: 0;
  min-height: 0;
  border: 1px solid rgba(255, 255, 255, .14);
  border-radius: 12px;
  background: #071326;
  overflow: hidden;
  pointer-events: auto;
}
.lt-editor-dock.is-floating {
  position: fixed;
  width: min(960px, calc(100vw - 32px));
  height: min(340px, calc(100vh - 32px));
  box-shadow: 0 24px 70px rgba(0, 0, 0, .42);
}
.lt-editor-dock-body {
  display: block;
  min-height: 0;
  overflow: hidden;
}
.lt-editor-tabs {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 4px;
  min-width: 0;
  padding: 6px;
  border-bottom: 1px solid rgba(159, 181, 216, .22);
  background: #0b1b33;
}
.lt-editor-tab {
  min-width: 0;
  min-height: 34px !important;
  padding: 4px 10px;
  border-color: transparent !important;
  background: transparent !important;
  color: #9fb5d8 !important;
}
.lt-editor-tab[aria-selected="true"] {
  border-color: rgba(91, 164, 255, .5) !important;
  background: #173b68 !important;
  color: #fff !important;
  box-shadow: inset 0 -3px 0 var(--lt-editor-accent);
}
.lt-editor-panel[hidden] {
  display: none !important;
}
.lt-editor-dock-body > .lt-editor-panel {
  height: 100%;
  border-bottom: 0;
}
.lt-editor-side-shell {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  gap: 10px;
  padding: 18px;
  pointer-events: auto;
}
.lt-editor-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px;
  border-bottom: 1px solid rgba(159, 181, 216, .22);
  background: #102644;
  color: #fff;
  font-size: 18px;
  font-weight: 900;
  cursor: grab;
  user-select: none;
}
.lt-editor-head:active {
  cursor: grabbing;
}
.lt-editor-root button,
.lt-editor-root input,
.lt-editor-root select,
.lt-editor-root textarea {
  min-height: 32px;
  border: 1px solid #c9d9ea;
  border-radius: 6px;
  background: #fff;
  color: #001b4d;
  font: inherit;
  font-size: 18px;
}
.lt-editor-root input,
.lt-editor-root select {
  width: 100%;
  min-width: 0;
}
.lt-editor-root textarea {
  width: 100%;
  min-height: 0;
  resize: none;
  line-height: 1.45;
}
.lt-editor-root button {
  cursor: pointer;
  font-weight: 800;
}
.lt-editor-root button[data-primary="true"] {
  border-color: var(--lt-editor-accent);
  background: var(--lt-editor-accent);
  color: #fff;
}
.lt-editor-dock button,
.lt-editor-dock input,
.lt-editor-dock select {
  min-height: 28px;
  font-size: 18px;
}
.lt-editor-section {
  min-width: 0;
  min-height: 0;
  padding: 10px;
  border-bottom: 1px solid rgba(159, 181, 216, .18);
  overflow: auto;
}
.lt-editor-section h2 {
  margin: 0 0 6px;
  color: #9fc8ff;
  font-size: 18px;
  line-height: 1.2;
  letter-spacing: 0;
}
.lt-editor-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(86px, 1fr));
  gap: 6px;
}
.lt-editor-wide {
  grid-column: 1 / -1;
}
.lt-editor-field {
  display: grid;
  gap: 3px;
  color: #b8cae4;
  font-size: 18px;
  font-weight: 800;
}
.lt-editor-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
}
.lt-editor-muted {
  margin-top: 6px;
  color: #9fb5d8;
  font-size: 18px;
  line-height: 1.35;
}
.lt-editor-note-status {
  margin: 8px 0 0;
  color: #ffb18e;
  font-size: 18px;
  font-weight: 800;
  line-height: 1.4;
}
.lt-editor-note-status.is-ok { color: #70e29d; }
.lt-editor-element-section {
  border-bottom: 0;
}
.lt-editor-element-section .lt-editor-grid {
  grid-template-columns: repeat(6, minmax(0, 1fr));
}
.lt-editor-element-section .lt-editor-actions {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}
.lt-editor-add-section,
.lt-editor-mode-section {
  padding: 8px;
}
.lt-editor-add-section .lt-editor-actions {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}
.lt-editor-mode-section .lt-editor-actions {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}
.lt-editor-note-section {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto auto;
  border: 0;
  border-radius: 14px;
  background: #f7faff;
  color: #001b4d;
  overflow: hidden;
}
.lt-editor-note-section h2 { color: #1761c3; }
.lt-editor-note-section textarea {
  padding: 12px;
  border: 2px solid #b9d7f4;
  background: #fff;
  font-size: 18px;
  line-height: 1.5;
  overflow: auto;
}
.lt-editor-note-section .lt-editor-muted { color: #5d6b82; }
.lt-editor-output-section {
  border: 1px solid rgba(159, 181, 216, .28);
  border-radius: 12px;
  background: #071326;
}
.lt-editor-status-line {
  min-height: 38px;
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(255, 255, 255, .07);
}
.lt-editor-dock-toggle {
  min-height: 28px !important;
  padding: 2px 10px;
  border-color: rgba(255, 255, 255, .32) !important;
  background: transparent !important;
  color: #dce8ff !important;
  font-size: 18px !important;
}
@media (max-width: 1120px) {
  .lt-editor-root { grid-template-columns: minmax(0, 1fr) minmax(360px, .72fr); }
  .lt-editor-stage-shell { grid-template-rows: auto minmax(0, 1fr) minmax(250px, 38vh); }
}
@media (max-height: 800px) {
  .lt-editor-stage-shell { grid-template-rows: auto minmax(0, 1fr) minmax(286px, 40vh); }
  .lt-editor-side-shell { padding: 14px; }
  .lt-editor-note-section textarea { font-size: 18px; line-height: 1.42; }
}
.lt-editor-mode-badge {
  display: none;
  position: fixed;
  z-index: 2147483647;
  left: 18px;
  bottom: 18px;
  padding: 8px 12px;
  border-radius: 6px;
  background: rgba(0, 27, 77, .92);
  color: #fff;
  font-family: system-ui, -apple-system, "Segoe UI", "Noto Sans JP", sans-serif;
  font-size: 18px;
  font-weight: 800;
  box-shadow: 0 14px 34px rgba(0, 27, 77, .22);
  pointer-events: none;
}
body.lt-editor-view-mode .lt-editor-mode-badge {
  display: block;
}
.lt-editor-selection {
  position: fixed;
  z-index: 2147483646;
  border: 2px solid var(--lt-editor-accent);
  pointer-events: none;
  box-shadow: 0 0 0 9999px rgba(29, 116, 232, .035);
}
.lt-editor-tail-handle {
  position: fixed;
  z-index: 2147483647;
  width: 18px;
  height: 18px;
  margin: -9px 0 0 -9px;
  border: 2px solid #135fbf;
  border-radius: 50%;
  background: #ffd12e;
  box-shadow: 0 2px 8px rgba(0, 27, 77, .28), 0 0 0 3px rgba(255, 255, 255, .92);
  cursor: crosshair;
  pointer-events: auto;
  touch-action: none;
}
.lt-editor-tail-handle[hidden] {
  display: none !important;
}
.lt-editor-tail-handle:focus-visible {
  outline: 3px solid rgba(29, 116, 232, .5);
  outline-offset: 4px;
}
.lt-editor-selected {
  outline: 2px solid var(--lt-editor-accent) !important;
  outline-offset: 2px !important;
}
body.lt-editor-edit-mode .zone {
  cursor: move;
}
body.lt-editor-edit-mode.lt-editor-dragging,
body.lt-editor-edit-mode.lt-editor-dragging * {
  user-select: none !important;
}
body.lt-editor-edit-mode [contenteditable="true"] {
  cursor: text;
  outline: 2px dashed rgba(29, 116, 232, .55);
  outline-offset: 3px;
}
.lt-editor-speech-bubble {
  --lt-bubble-bg: #fff;
  --lt-bubble-border: #1d74e8;
  --lt-bubble-tail-left: 34px;
  --lt-bubble-tail-width: 72px;
  --lt-bubble-tail-height: 30px;
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: visible !important;
  padding: 16px 24px;
  border: 3px solid var(--lt-bubble-border);
  border-radius: 24px;
  background: var(--lt-bubble-bg);
  color: #001b4d;
  font-size: 28px;
  line-height: 1.3;
  font-weight: 900;
  text-align: center;
  isolation: isolate;
}
.lt-editor-speech-text {
  position: relative;
  z-index: 3;
  min-width: 0;
}
.lt-editor-speech-bubble::before,
.lt-editor-speech-bubble::after {
  content: "";
  position: absolute;
  pointer-events: none;
}
.lt-editor-speech-bubble::before {
  z-index: 1;
  left: var(--lt-bubble-tail-outer-box-left, var(--lt-bubble-tail-left));
  top: var(--lt-bubble-tail-outer-box-top, calc(100% - 1px));
  width: var(--lt-bubble-tail-outer-box-width, var(--lt-bubble-tail-width));
  height: var(--lt-bubble-tail-outer-box-height, var(--lt-bubble-tail-height));
  background: var(--lt-bubble-border);
  clip-path: polygon(
    var(--lt-bubble-tail-outer-p1-x, 0%) var(--lt-bubble-tail-outer-p1-y, 0%),
    var(--lt-bubble-tail-outer-p2-x, 100%) var(--lt-bubble-tail-outer-p2-y, 0%),
    var(--lt-bubble-tail-outer-tip-x, 14%) var(--lt-bubble-tail-outer-tip-y, 100%)
  );
}
.lt-editor-speech-bubble::after {
  z-index: 2;
  left: var(--lt-bubble-tail-inner-box-left, calc(var(--lt-bubble-tail-left) + 2px));
  top: var(--lt-bubble-tail-inner-box-top, calc(100% - 2px));
  width: var(--lt-bubble-tail-inner-box-width, calc(var(--lt-bubble-tail-width) - 4px));
  height: var(--lt-bubble-tail-inner-box-height, calc(var(--lt-bubble-tail-height) - 3px));
  background: var(--lt-bubble-bg);
  clip-path: polygon(
    var(--lt-bubble-tail-inner-p1-x, 0%) var(--lt-bubble-tail-inner-p1-y, 0%),
    var(--lt-bubble-tail-inner-p2-x, 100%) var(--lt-bubble-tail-inner-p2-y, 0%),
    var(--lt-bubble-tail-inner-tip-x, 14%) var(--lt-bubble-tail-inner-tip-y, 100%)
  );
}
.lt-editor-speech-bubble[data-anim],
.lt-editor-speech-bubble[data-anim].shown {
  clip-path: none !important;
}
body.lt-editor-edit-mode .lt-editor-speech-bubble[data-anim] {
  visibility: visible !important;
  opacity: 1 !important;
  transform: none !important;
  filter: none !important;
}
@media screen and (prefers-reduced-motion: reduce) {
  body:not(.lt-editor-edit-mode) [data-anim]:not(.shown) {
    opacity: 0 !important;
  }
  body:not(.lt-editor-edit-mode) [data-anim].shown {
    opacity: 1 !important;
  }
}
`;
}

function editorRuntime() {
  return String.raw`
(function () {
  "use strict";

  const params = new URLSearchParams(location.search);
  const isPresenter = params.get("presenter") === "1";
  const isEditUrl = params.get("edit") === "1";
  if (isPresenter) return;

  const deck = document.querySelector(".deck");
  if (!deck) return;

  document.addEventListener("keydown", onEditUrlKeyDown, true);
  if (!isEditUrl) return;

  document.body.classList.add("lt-editor-enabled");

  const TEXT_DRAG_THRESHOLD = 5;

  let selected = null;
  let drag = null;
  let pendingDrag = null;
  let tailDrag = null;
  let panelDrag = null;
  let editorMode = true;
  let noteSlide = null;
  let overviewReturnEditorMode = null;
  let overviewSelected = null;

  const root = document.createElement("aside");
  root.className = "lt-editor-root";
  root.innerHTML = [
    '<section class="lt-editor-stage-shell">',
    '<div class="lt-editor-stage-head"><span>編集中のスライド</span><span data-editor-position></span></div>',
    '<div class="lt-editor-stage-viewport" data-editor-stage-viewport aria-label="編集対象スライド領域"></div>',
    '<div class="lt-editor-dock" data-editor-dock>',
    '<div class="lt-editor-head"><span>Slide Editor</span><button type="button" class="lt-editor-dock-toggle" data-action="dock" data-dock-toggle>フロート</button></div>',
    '<div class="lt-editor-tabs" role="tablist" aria-label="編集ツール">',
    '<button type="button" class="lt-editor-tab" role="tab" aria-selected="true" data-editor-tab="element">選択要素</button>',
    '<button type="button" class="lt-editor-tab" role="tab" aria-selected="false" data-editor-tab="add">追加</button>',
    '<button type="button" class="lt-editor-tab" role="tab" aria-selected="false" data-editor-tab="mode">表示・移動</button>',
    '</div>',
    '<div class="lt-editor-dock-body">',
    '<section class="lt-editor-section lt-editor-panel lt-editor-element-section" data-editor-panel="element">',
    '<div class="lt-editor-grid">',
    field("X", "x", "number"), field("Y", "y", "number"), field("W", "w", "number"), field("H", "h", "number"),
    field("Font", "fontSize", "number", 'min="1" step="1"'), field("Step", "step", "number", 'min="0" step="1"'), field("Text", "color", "color"),
    field("Bg", "background", "color"),
    '<label class="lt-editor-field">Align<select data-field="textAlign"><option value="">auto</option><option value="left">left</option><option value="center">center</option><option value="right">right</option></select></label>',
    '<label class="lt-editor-field">Anim<select data-field="anim"><option value="">none</option><option value="rise">rise</option><option value="fade">fade</option><option value="pop">pop</option><option value="wipe">wipe</option><option value="draw">draw</option><option value="stamp">stamp</option><option value="marker">marker</option><option value="stomp">stomp</option></select></label>',
    '<label class="lt-editor-field">Zone<select data-field="zone"><option value="text">text</option><option value="visual">visual</option><option value="content">content</option><option value="callout">callout</option><option value="title">title</option><option value="conclusion">conclusion</option><option value="qr">qr</option></select></label>',
    '</div>',
    '<div class="lt-editor-actions" style="margin-top:6px">',
    '<button type="button" data-action="bold">Bold</button>',
    '<button type="button" data-action="card">Card</button>',
    '<button type="button" data-action="front">Front</button>',
    '<button type="button" data-action="stepLast">最後に表示</button>',
    '<button type="button" data-action="delete">Delete</button>',
    '</div>',
    '<p class="lt-editor-muted lt-editor-status-line" data-status>Select a slide element.</p>',
    '</section>',
    '<section class="lt-editor-section lt-editor-panel lt-editor-add-section" data-editor-panel="add" hidden>',
    '<div class="lt-editor-actions">',
    '<button type="button" data-action="addText">Text</button>',
    '<button type="button" data-action="addImage">Image</button>',
    '<button type="button" data-action="addSpeechBubble">吹き出し</button>',
    '<button type="button" data-action="duplicateSlide">Duplicate</button>',
    '<button type="button" data-action="addSlide">Blank page</button>',
    '</div>',
    '<input type="file" accept="image/*" data-image-picker hidden>',
    '</section>',
    '<section class="lt-editor-section lt-editor-panel lt-editor-mode-section" data-editor-panel="mode" hidden>',
    '<div class="lt-editor-actions">',
    '<button type="button" data-action="toggleMode" data-mode-toggle>View mode</button>',
    '<button type="button" data-action="previewAnimation">アニメ確認</button>',
    '<button type="button" data-action="prev">Prev</button>',
    '<button type="button" data-action="next">Next</button>',
    '</div>',
    '<p class="lt-editor-muted"><strong>P</strong>: ページ一覧 / <strong>E</strong>: 終了 / <strong>V</strong>: UI表示切替</p>',
    '</section>',
    '</div>',
    '</div>',
    '</section>',
    '<section class="lt-editor-side-shell">',
    '<div class="lt-editor-side-head"><span>台本・出力</span><span>P: ページ一覧 / E: 終了 / V: 表示切替</span></div>',
    '<section class="lt-editor-section lt-editor-note-section">',
    '<h2>Spoken Note</h2>',
    '<textarea data-spoken-note rows="8" spellcheck="false" placeholder="橋渡し: 前ページから進む理由&#10;話す内容: 実際に口にする説明&#10;指差し: 画面にあるラベル&#10;次の一言: 次へ渡す発話"></textarea>',
    '<p class="lt-editor-note-status" data-note-status>台本形式を確認中</p>',
    '<p class="lt-editor-muted">Storyの台本と同じ四区画を保ちます。</p>',
    '</section>',
    '<section class="lt-editor-section lt-editor-output-section">',
    '<h2>Output</h2>',
    '<div class="lt-editor-actions">',
    '<button type="button" data-action="save" data-primary="true">Save HTML</button>',
    '<button type="button" data-action="exportPdf">Export PDF</button>',
    '</div>',
    '<p class="lt-editor-muted">serve_editor.js ではHTMLとPDFを同名で上書きします。</p>',
    '</section>',
    '</section>'
  ].join("");
  document.body.appendChild(root);

  const stageViewport = root.querySelector("[data-editor-stage-viewport]");
  const editorDock = root.querySelector("[data-editor-dock]");
  const editorPosition = root.querySelector("[data-editor-position]");
  const dockToggle = root.querySelector("[data-dock-toggle]");
  restorePanelPosition();

  const modeBadge = document.createElement("div");
  modeBadge.className = "lt-editor-mode-badge";
  modeBadge.textContent = "View mode - press V to edit";
  document.body.appendChild(modeBadge);

  const selectionBox = document.createElement("div");
  selectionBox.className = "lt-editor-selection";
  selectionBox.hidden = true;
  document.body.appendChild(selectionBox);

  const tailHandle = document.createElement("div");
  tailHandle.className = "lt-editor-tail-handle";
  tailHandle.hidden = true;
  tailHandle.tabIndex = 0;
  tailHandle.setAttribute("role", "button");
  tailHandle.setAttribute("aria-label", "吹き出しの尻尾の頂点を移動");
  tailHandle.title = "ドラッグして吹き出しの尻尾の頂点を移動";
  document.body.appendChild(tailHandle);

  const imagePicker = root.querySelector("[data-image-picker]");
  const spokenNoteInput = root.querySelector("[data-spoken-note]");
  const noteStatus = root.querySelector("[data-note-status]");
  const status = root.querySelector("[data-status]");
  const fields = Object.fromEntries([...root.querySelectorAll("[data-field]")].map((el) => [el.dataset.field, el]));
  const editorTabs = [...root.querySelectorAll("[data-editor-tab]")];
  const editorPanels = [...root.querySelectorAll("[data-editor-panel]")];

  root.querySelector(".lt-editor-head").addEventListener("pointerdown", onPanelPointerDown);
  root.addEventListener("input", onFieldInput);
  root.addEventListener("change", onFieldInput);
  root.addEventListener("click", onToolbarClick);
  imagePicker.addEventListener("change", onImagePicked);
  spokenNoteInput.addEventListener("input", onSpokenNoteInput);

  document.addEventListener("pointerdown", onPointerDown, true);
  document.addEventListener("pointermove", onPointerMove, true);
  document.addEventListener("pointerup", onPointerUp, true);
  document.addEventListener("keydown", onKeyDown, true);
  document.addEventListener("keyup", syncSlideContextSoon, true);
  window.addEventListener("resize", onEditorResize);
  document.addEventListener("selectionchange", updateSelectionBox);
  document.getElementById("pagerGrid")?.addEventListener("click", onOverviewGridClick);

  setEditorPanel("element");
  renumberSlides();
  setEditorMode(true, false);
  syncSlideContext(true);
  setStatus("Select a .zone element, then drag or edit it.");

  function field(label, name, type, attrs = "") {
    return '<label class="lt-editor-field">' + label + '<input data-field="' + name + '" type="' + type + '"' + (attrs ? " " + attrs : "") + '></label>';
  }

  function activeSlide() {
    return deck.querySelector(".slide.active") || deck.querySelector(".slide");
  }

  function onEditorResize() {
    layoutEditorStage();
    updateSelectionBox();
  }

  function layoutEditorStage() {
    if (!editorMode) {
      deck.style.left = "";
      deck.style.top = "";
      window.slideDeck?.fit?.();
      return;
    }
    const rect = stageViewport.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    const scale = Math.min(rect.width / 1280, rect.height / 720);
    const renderedWidth = 1280 * scale;
    const renderedHeight = 720 * scale;
    deck.style.left = Math.round(rect.left + (rect.width - renderedWidth) / 2) + "px";
    deck.style.top = Math.round(rect.top + (rect.height - renderedHeight) / 2) + "px";
    deck.style.transform = "scale(" + scale + ")";
  }

  function slideScale() {
    const slide = activeSlide();
    if (!slide) return { x: 1, y: 1 };
    const rect = slide.getBoundingClientRect();
    return {
      x: rect.width ? 1280 / rect.width : 1,
      y: rect.height ? 720 / rect.height : 1
    };
  }

  function onPointerDown(event) {
    if (!editorMode) return;
    if (event.target === tailHandle) {
      if (!isSpeechBubble(selected)) return;
      tailDrag = { el: selected, pointerId: event.pointerId };
      document.body.classList.add("lt-editor-tail-dragging");
      tailHandle.focus({ preventScroll: true });
      try { tailHandle.setPointerCapture(event.pointerId); } catch (error) {}
      event.preventDefault();
      event.stopPropagation();
      return;
    }
    if (root.contains(event.target)) return;
    const target = event.target.closest(".zone");
    if (!target || !activeSlide() || !activeSlide().contains(target)) return;

    select(target);
    if (event.target.closest('input, textarea, select')) return;

    const style = getBoxStyle(target);
    const scale = slideScale();
    const nextDrag = {
      el: target,
      startClientX: event.clientX,
      startClientY: event.clientY,
      startLeft: style.left,
      startTop: style.top,
      scaleX: scale.x,
      scaleY: scale.y
    };
    if (event.target.closest('[contenteditable="true"]')) {
      pendingDrag = nextDrag;
      return;
    }
    startElementDrag(nextDrag);
    event.preventDefault();
    event.stopPropagation();
  }

  function onPointerMove(event) {
    if (tailDrag) {
      setTailTipFromPointer(tailDrag.el, event.clientX, event.clientY);
      updateSelectionBox();
      setStatus("吹き出しの尻尾の頂点を移動中（付け根は最寄りの辺へ追従）");
      event.preventDefault();
      event.stopPropagation();
      return;
    }
    if (panelDrag) {
      const nextLeft = clamp(panelDrag.startLeft + event.clientX - panelDrag.startClientX, 0, Math.max(0, innerWidth - editorDock.offsetWidth));
      const nextTop = clamp(panelDrag.startTop + event.clientY - panelDrag.startClientY, 0, Math.max(0, innerHeight - Math.min(editorDock.offsetHeight, innerHeight)));
      editorDock.style.left = Math.round(nextLeft) + "px";
      editorDock.style.top = Math.round(nextTop) + "px";
      event.preventDefault();
      event.stopPropagation();
      return;
    }
    if (pendingDrag) {
      const dx = event.clientX - pendingDrag.startClientX;
      const dy = event.clientY - pendingDrag.startClientY;
      if (Math.hypot(dx, dy) < TEXT_DRAG_THRESHOLD) return;
      startElementDrag(pendingDrag);
      pendingDrag = null;
    }
    if (!drag) return;
    const left = clamp(Math.round(drag.startLeft + (event.clientX - drag.startClientX) * drag.scaleX), -200, 1480);
    const top = clamp(Math.round(drag.startTop + (event.clientY - drag.startClientY) * drag.scaleY), -200, 920);
    drag.el.style.left = left + "px";
    drag.el.style.top = top + "px";
    refreshFields();
    updateSelectionBox();
    event.preventDefault();
    event.stopPropagation();
  }

  function onPointerUp(event) {
    if (tailDrag) {
      try { tailHandle.releasePointerCapture(tailDrag.pointerId); } catch (error) {}
      tailDrag = null;
      document.body.classList.remove("lt-editor-tail-dragging");
      setStatus("尻尾の頂点位置を保存しました。黄色いハンドルで再調整できます。");
      event.preventDefault();
      event.stopPropagation();
      return;
    }
    if (panelDrag) {
      savePanelPosition();
      panelDrag = null;
      event.preventDefault();
      event.stopPropagation();
      return;
    }
    if (pendingDrag) {
      pendingDrag = null;
      return;
    }
    if (!drag) return;
    drag = null;
    document.body.classList.remove("lt-editor-dragging");
    event.preventDefault();
    event.stopPropagation();
  }

  function startElementDrag(nextDrag) {
    drag = nextDrag;
    document.body.classList.add("lt-editor-dragging");
    window.getSelection()?.removeAllRanges();
    if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
  }

  function onPanelPointerDown(event) {
    if (!editorMode) return;
    if (event.target.closest("button, input, textarea, select, a")) return;
    const rect = editorDock.getBoundingClientRect();
    if (!editorDock.classList.contains("is-floating")) setDocked(false, rect);
    panelDrag = {
      startClientX: event.clientX,
      startClientY: event.clientY,
      startLeft: rect.left,
      startTop: rect.top
    };
    event.preventDefault();
    event.stopPropagation();
  }

  function setDocked(docked, sourceRect = null) {
    if (docked) {
      editorDock.classList.remove("is-floating");
      editorDock.style.left = "";
      editorDock.style.top = "";
      editorDock.style.width = "";
      editorDock.style.height = "";
      dockToggle.textContent = "フロート";
      try { localStorage.removeItem("lt-slide-editor-dock-position-v2"); } catch (error) {}
      return;
    }
    const rect = sourceRect || editorDock.getBoundingClientRect();
    editorDock.classList.add("is-floating");
    editorDock.style.left = Math.round(clamp(rect.left, 0, Math.max(0, innerWidth - rect.width))) + "px";
    editorDock.style.top = Math.round(clamp(rect.top, 0, Math.max(0, innerHeight - rect.height))) + "px";
    editorDock.style.width = Math.round(Math.min(rect.width || 960, innerWidth - 32)) + "px";
    editorDock.style.height = Math.round(Math.min(Math.max(rect.height || 300, 260), innerHeight - 32)) + "px";
    dockToggle.textContent = "ドックへ戻す";
  }

  function onKeyDown(event) {
    if (!document.body.classList.contains("lt-editor-enabled")) return;
    if (event.defaultPrevented) return;
    if (isEditorTextEntryTarget(event.target)) {
      event.stopPropagation();
      return;
    }
    if (isPageOverviewShortcut(event)) {
      toggleEditorOverview();
      event.preventDefault();
      event.stopPropagation();
      return;
    }
    if (overviewReturnEditorMode !== null && event.key === "Escape") {
      toggleEditorOverview(false);
      event.preventDefault();
      event.stopPropagation();
      return;
    }
    if (isViewModeShortcut(event)) {
      setEditorMode(!editorMode);
      event.preventDefault();
      event.stopPropagation();
      return;
    }
    if (!editorMode) return;
    if (root.contains(event.target)) {
      event.stopPropagation();
      return;
    }
    if (event.target === tailHandle && isSpeechBubble(selected)) {
      const point = tailPoint(selected);
      const step = event.shiftKey ? 10 : 1;
      if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(event.key)) {
        const dx = event.key === "ArrowLeft" ? -step : event.key === "ArrowRight" ? step : 0;
        const dy = event.key === "ArrowUp" ? -step : event.key === "ArrowDown" ? step : 0;
        renderTailGeometry(selected, point.x + dx, point.y + dy, true);
        updateSelectionBox();
        event.preventDefault();
        event.stopPropagation();
        return;
      }
    }
    if (event.key === "Escape") {
      select(null);
      event.preventDefault();
      event.stopPropagation();
      return;
    }
    if (!selected) return;
    if (event.target.closest('[contenteditable="true"]')) {
      event.stopPropagation();
      return;
    }
    const step = event.shiftKey ? 10 : 1;
    if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Delete", "Backspace"].includes(event.key)) {
      event.preventDefault();
      event.stopPropagation();
    }
    if (event.key === "ArrowUp") selected.style.top = (getBoxStyle(selected).top - step) + "px";
    if (event.key === "ArrowDown") selected.style.top = (getBoxStyle(selected).top + step) + "px";
    if (event.key === "ArrowLeft") selected.style.left = (getBoxStyle(selected).left - step) + "px";
    if (event.key === "ArrowRight") selected.style.left = (getBoxStyle(selected).left + step) + "px";
    if (event.key === "Delete" || event.key === "Backspace") {
      selected.remove();
      select(null);
      return;
    }
    refreshFields();
    updateSelectionBox();
  }

  function onFieldInput(event) {
    const field = event.target.closest("[data-field]");
    if (!field || !selected) return;
    const name = field.dataset.field;
    const value = field.value;
    if (["x", "y", "w", "h"].includes(name)) {
      const map = { x: "left", y: "top", w: "width", h: "height" };
      selected.style[map[name]] = (Number(value) || 0) + "px";
    }
    if (name === "fontSize") applyFontSize(selected, value);
    if (name === "step") setAnimationStep(animationTarget(selected), value);
    if (name === "color") selected.style.color = value || "";
    if (name === "background") {
      selected.style.background = value || "";
      if (selected.classList.contains("lt-editor-speech-bubble")) {
        selected.style.setProperty("--lt-bubble-bg", value || "#ffffff");
      }
    }
    if (name === "textAlign") selected.style.textAlign = value || "";
    if (name === "zone") selected.dataset.zone = value || "text";
    if (name === "anim") setAnimation(animationTarget(selected), value);
    updateSelectionBox();
  }

  function onToolbarClick(event) {
    const tab = event.target.closest("[data-editor-tab]");
    if (tab) {
      event.preventDefault();
      event.stopPropagation();
      setEditorPanel(tab.dataset.editorTab);
      return;
    }
    const action = event.target.closest("[data-action]")?.dataset.action;
    if (!action) return;
    event.preventDefault();
    event.stopPropagation();

    if (action === "save") {
      saveHtml();
      return;
    }
    if (action === "exportPdf") {
      exportPdf();
      return;
    }
    if (action === "dock") {
      if (editorDock.classList.contains("is-floating")) setDocked(true);
      else setDocked(false);
      return;
    }
    if (action === "toggleMode") setEditorMode(!editorMode);
    if (action === "previewAnimation") {
      const index = slideIndex(activeSlide());
      setEditorMode(false);
      window.slideDeck?.show?.(index, false);
      return;
    }
    if (action === "bold" && selected) selected.style.fontWeight = selected.style.fontWeight === "900" ? "" : "900";
    if (action === "card" && selected) selected.classList.toggle("card");
    if (action === "front" && selected) bringForward(selected);
    if (action === "stepLast" && selected) setAnimationLast(animationTarget(selected));
    if (action === "delete" && selected) {
      selected.remove();
      select(null);
    }
    if (action === "addText") addText();
    if (action === "addImage") imagePicker.click();
    if (action === "addSpeechBubble") addSpeechBubble();
    if (action === "duplicateSlide") duplicateSlide();
    if (action === "addSlide") addBlankSlide();
    if (action === "prev") window.slideDeck?.previous?.();
    if (action === "next") window.slideDeck?.next?.();

    exposeTextEditing();
    renumberSlides();
    syncSlideContextSoon();
    refreshFields();
    updateSelectionBox();
  }

  function onSpokenNoteInput() {
    const slide = activeSlide();
    if (!slide) return;
    slide.dataset.spokenNote = spokenNoteInput.value;
    noteSlide = slide;
    updateSpokenNoteStatus();
  }

  function updateSpokenNoteStatus() {
    const labels = ["橋渡し", "話す内容", "指差し", "次の一言"];
    const missing = labels.filter((label) => {
      const pattern = new RegExp("^\\s*" + label + "\\s*[:：]\\s*\\S.+$", "m");
      return !pattern.test(spokenNoteInput.value);
    });
    noteStatus.classList.toggle("is-ok", missing.length === 0);
    noteStatus.textContent = missing.length ? "未入力: " + missing.join(" / ") : "台本形式OK（四区画入力済み）";
  }

  function onImagePicked(event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => addImage(String(reader.result || ""), file.name || "image");
    reader.readAsDataURL(file);
    event.target.value = "";
  }

  function select(el) {
    if (selected) selected.classList.remove("lt-editor-selected");
    selected = el;
    if (selected) {
      selected.classList.add("lt-editor-selected");
      setEditorPanel("element");
    }
    refreshFields();
    updateSelectionBox();
    setStatus(selected ? describe(selected) : "Select a .zone element.");
  }

  function setEditorPanel(name) {
    const next = editorPanels.some((panel) => panel.dataset.editorPanel === name) ? name : "element";
    editorTabs.forEach((tab) => {
      const active = tab.dataset.editorTab === next;
      tab.setAttribute("aria-selected", active ? "true" : "false");
      tab.tabIndex = active ? 0 : -1;
    });
    editorPanels.forEach((panel) => {
      panel.hidden = panel.dataset.editorPanel !== next;
    });
  }

  function toggleEditorOverview(force) {
    const open = document.body.classList.contains("overview");
    const next = typeof force === "boolean" ? force : !open;
    if (next) {
      overviewReturnEditorMode = editorMode;
      overviewSelected = selected;
      if (editorMode) setEditorMode(false, false);
      window.slideDeck?.toggleOverview?.(true);
      return;
    }
    window.slideDeck?.toggleOverview?.(false);
    restoreEditorAfterOverview();
  }

  function onOverviewGridClick(event) {
    if (overviewReturnEditorMode === null || !event.target.closest(".pager-thumb")) return;
    requestAnimationFrame(restoreEditorAfterOverview);
  }

  function restoreEditorAfterOverview() {
    if (overviewReturnEditorMode === null) return;
    const restoreEditMode = overviewReturnEditorMode;
    const restoreSelection = overviewSelected;
    overviewReturnEditorMode = null;
    overviewSelected = null;
    if (restoreEditMode) {
      setEditorMode(true, false);
      if (restoreSelection && activeSlide()?.contains(restoreSelection)) select(restoreSelection);
      else select(null);
    }
    syncSlideContextSoon();
  }

  function getBoxStyle(el) {
    const style = getComputedStyle(el);
    return {
      left: px(style.left),
      top: px(style.top),
      width: px(style.width),
      height: px(style.height)
    };
  }

  function refreshFields() {
    if (!selected) {
      Object.values(fields).forEach((field) => { field.value = ""; });
      return;
    }
    const box = getBoxStyle(selected);
    const animated = animationTarget(selected);
    fields.x.value = Math.round(box.left);
    fields.y.value = Math.round(box.top);
    fields.w.value = Math.round(box.width);
    fields.h.value = Math.round(box.height);
    fields.fontSize.value = Math.round(px(getComputedStyle(primaryTextTarget(selected)).fontSize)) || "";
    fields.step.value = animated?.hasAttribute("data-anim") ? String(Math.max(0, Math.round(Number(animated.dataset.step) || 0))) : "";
    fields.color.value = rgbToHex(getComputedStyle(selected).color);
    fields.background.value = rgbToHex(getComputedStyle(selected).backgroundColor);
    fields.textAlign.value = selected.style.textAlign || "";
    fields.zone.value = selected.dataset.zone || "text";
    fields.anim.value = animated?.dataset.anim || "";
  }

  function updateSelectionBox() {
    if (!editorMode || !selected || !document.body.contains(selected)) {
      selectionBox.hidden = true;
      tailHandle.hidden = true;
      return;
    }
    const rect = selected.getBoundingClientRect();
    selectionBox.hidden = false;
    selectionBox.style.left = rect.left + "px";
    selectionBox.style.top = rect.top + "px";
    selectionBox.style.width = rect.width + "px";
    selectionBox.style.height = rect.height + "px";
    updateTailHandle();
  }

  function updateTailHandle() {
    if (!editorMode || !isSpeechBubble(selected) || !document.body.contains(selected)) {
      tailHandle.hidden = true;
      return;
    }
    const rect = selected.getBoundingClientRect();
    const scale = slideScale();
    const point = tailPoint(selected);
    tailHandle.hidden = false;
    tailHandle.style.left = (rect.left + point.x / scale.x) + "px";
    tailHandle.style.top = (rect.top + point.y / scale.y) + "px";
  }

  function isSpeechBubble(el) {
    return Boolean(el?.classList?.contains("lt-editor-speech-bubble"));
  }

  function setTailTipFromPointer(el, clientX, clientY) {
    const rect = el.getBoundingClientRect();
    const scale = slideScale();
    renderTailGeometry(el, (clientX - rect.left) * scale.x, (clientY - rect.top) * scale.y, true);
  }

  function tailPoint(el) {
    const storedX = Number.parseFloat(el.dataset.tailTipX);
    const storedY = Number.parseFloat(el.dataset.tailTipY);
    if (Number.isFinite(storedX) && Number.isFinite(storedY)) return { x: storedX, y: storedY };
    const style = getComputedStyle(el);
    const left = px(style.getPropertyValue("--lt-bubble-tail-left")) || 34;
    const width = px(style.getPropertyValue("--lt-bubble-tail-width")) || 72;
    const height = px(style.getPropertyValue("--lt-bubble-tail-height")) || 30;
    return { x: left + width * .14, y: (el.offsetHeight || getBoxStyle(el).height) - 1 + height };
  }

  function renderTailGeometry(el, rawX, rawY, persist) {
    const width = Math.max(1, el.offsetWidth || getBoxStyle(el).width);
    const height = Math.max(1, el.offsetHeight || getBoxStyle(el).height);
    const elementBox = getBoxStyle(el);
    const slidePadding = 8;
    let x = clamp(Number(rawX) || 0, slidePadding - elementBox.left, 1280 - slidePadding - elementBox.left);
    let y = clamp(Number(rawY) || 0, slidePadding - elementBox.top, 720 - slidePadding - elementBox.top);
    const side = tailSide(width, height, x, y);
    const minimumLength = 8;
    if (side === "bottom") y = Math.max(y, height + minimumLength);
    if (side === "top") y = Math.min(y, -minimumLength);
    if (side === "left") x = Math.min(x, -minimumLength);
    if (side === "right") x = Math.max(x, width + minimumLength);

    const style = getComputedStyle(el);
    const requestedBaseWidth = px(style.getPropertyValue("--lt-bubble-tail-width")) || 72;
    const edgeLength = side === "top" || side === "bottom" ? width : height;
    const baseHalf = Math.min(requestedBaseWidth / 2, Math.max(10, (edgeLength - 8) / 2));
    const outline = 2;
    const tipInset = 3;
    let p1;
    let p2;
    let tip = { x, y };
    let innerP1;
    let innerP2;
    let baseCenter;

    if (side === "top" || side === "bottom") {
      baseCenter = clamp(x, baseHalf + 4, Math.max(baseHalf + 4, width - baseHalf - 4));
      const baseY = side === "bottom" ? height - 1 : 1;
      p1 = { x: baseCenter - baseHalf, y: baseY };
      p2 = { x: baseCenter + baseHalf, y: baseY };
      innerP1 = { x: p1.x + outline, y: baseY + (side === "bottom" ? outline : -outline) };
      innerP2 = { x: p2.x - outline, y: baseY + (side === "bottom" ? outline : -outline) };
    } else {
      baseCenter = clamp(y, baseHalf + 4, Math.max(baseHalf + 4, height - baseHalf - 4));
      const baseX = side === "right" ? width - 1 : 1;
      p1 = { x: baseX, y: baseCenter - baseHalf };
      p2 = { x: baseX, y: baseCenter + baseHalf };
      innerP1 = { x: baseX + (side === "right" ? outline : -outline), y: p1.y + outline };
      innerP2 = { x: baseX + (side === "right" ? outline : -outline), y: p2.y - outline };
    }

    const baseMid = { x: (p1.x + p2.x) / 2, y: (p1.y + p2.y) / 2 };
    const tailLength = Math.max(1, Math.hypot(tip.x - baseMid.x, tip.y - baseMid.y));
    const ratio = Math.min(.45, tipInset / tailLength);
    const innerTip = {
      x: tip.x + (baseMid.x - tip.x) * ratio,
      y: tip.y + (baseMid.y - tip.y) * ratio
    };
    const all = [p1, p2, tip];
    const boxLeft = Math.min(...all.map((point) => point.x));
    const boxTop = Math.min(...all.map((point) => point.y));
    const boxRight = Math.max(...all.map((point) => point.x));
    const boxBottom = Math.max(...all.map((point) => point.y));
    const boxWidth = Math.max(1, boxRight - boxLeft);
    const boxHeight = Math.max(1, boxBottom - boxTop);
    const local = (point) => ({ x: point.x - boxLeft, y: point.y - boxTop });
    const outerP1 = local(p1);
    const outerP2 = local(p2);
    const outerTip = local(tip);
    const localInnerP1 = local(innerP1);
    const localInnerP2 = local(innerP2);
    const localInnerTip = local(innerTip);

    setTailBox(el, "outer", boxLeft, boxTop, boxWidth, boxHeight);
    setTailBox(el, "inner", boxLeft, boxTop, boxWidth, boxHeight);
    setTailPointVariables(el, "outer", outerP1, outerP2, outerTip);
    setTailPointVariables(el, "inner", localInnerP1, localInnerP2, localInnerTip);
    el.style.setProperty("--lt-bubble-tail-tip-x", tailPx(x));
    el.style.setProperty("--lt-bubble-tail-tip-y", tailPx(y));
    if (persist) {
      el.dataset.tailTipX = tailNumber(x);
      el.dataset.tailTipY = tailNumber(y);
      el.dataset.tailSide = side;
    }
    return { x, y, side };
  }

  function tailSide(width, height, x, y) {
    const outside = [];
    if (x < 0) outside.push({ side: "left", distance: -x });
    if (x > width) outside.push({ side: "right", distance: x - width });
    if (y < 0) outside.push({ side: "top", distance: -y });
    if (y > height) outside.push({ side: "bottom", distance: y - height });
    if (outside.length) return outside.sort((a, b) => b.distance - a.distance)[0].side;
    return [
      { side: "left", distance: x },
      { side: "right", distance: width - x },
      { side: "top", distance: y },
      { side: "bottom", distance: height - y }
    ].sort((a, b) => a.distance - b.distance)[0].side;
  }

  function setTailBox(el, layer, left, top, width, height) {
    el.style.setProperty("--lt-bubble-tail-" + layer + "-box-left", tailPx(left));
    el.style.setProperty("--lt-bubble-tail-" + layer + "-box-top", tailPx(top));
    el.style.setProperty("--lt-bubble-tail-" + layer + "-box-width", tailPx(width));
    el.style.setProperty("--lt-bubble-tail-" + layer + "-box-height", tailPx(height));
  }

  function setTailPointVariables(el, layer, p1, p2, tip) {
    [["p1", p1], ["p2", p2], ["tip", tip]].forEach(([name, point]) => {
      el.style.setProperty("--lt-bubble-tail-" + layer + "-" + name + "-x", tailPx(point.x));
      el.style.setProperty("--lt-bubble-tail-" + layer + "-" + name + "-y", tailPx(point.y));
    });
  }

  function tailPx(value) {
    return tailNumber(value) + "px";
  }

  function tailNumber(value) {
    return String(Math.round(Number(value) * 10) / 10);
  }

  function exposeTextEditing() {
    deck.querySelectorAll(".zone").forEach((zone) => {
      const bubbleText = zone.querySelector(":scope > .lt-editor-speech-text");
      const editable = bubbleText || (zone.matches("h1,h2,h3,p,li,span,div") ? zone : zone.querySelector("h1,h2,h3,p,li,span,div"));
      if (editable && !editable.querySelector("img,svg")) {
        editable.setAttribute("contenteditable", "true");
        editable.setAttribute("spellcheck", "false");
      }
    });
  }

  function disableTextEditing() {
    deck.querySelectorAll('[contenteditable="true"]').forEach((el) => {
      el.removeAttribute("contenteditable");
      el.removeAttribute("spellcheck");
    });
  }

  function setEditorMode(enabled, announce = true) {
    editorMode = Boolean(enabled);
    document.body.classList.toggle("lt-editor-edit-mode", editorMode);
    document.body.classList.toggle("lt-editor-view-mode", !editorMode);
    const toggle = root.querySelector("[data-mode-toggle]");
    if (toggle) toggle.textContent = editorMode ? "View mode" : "Edit mode";
    if (editorMode) {
      exposeTextEditing();
      if (announce) setStatus("Editor mode. Press V for view mode, or E for normal URL.");
    } else {
      drag = null;
      pendingDrag = null;
      tailDrag = null;
      panelDrag = null;
      document.body.classList.remove("lt-editor-dragging", "lt-editor-tail-dragging");
      select(null);
      disableTextEditing();
      if (announce) setStatus("View mode. Press V for editor mode, or E for normal URL.");
    }
    requestAnimationFrame(() => {
      layoutEditorStage();
      updateSelectionBox();
    });
    syncSlideContextSoon();
  }

  function onEditUrlKeyDown(event) {
    if (!isEditUrlShortcut(event)) return;
    const nextUrl = new URL(location.href);
    if (nextUrl.searchParams.get("edit") === "1") nextUrl.searchParams.delete("edit");
    else nextUrl.searchParams.set("edit", "1");
    event.preventDefault();
    event.stopImmediatePropagation();
    location.assign(nextUrl.toString());
  }

  function isEditUrlShortcut(event) {
    if (event.key.toLowerCase() !== "e") return false;
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return false;
    if (event.target.closest('input, textarea, select, [contenteditable="true"]')) return false;
    return true;
  }

  function isViewModeShortcut(event) {
    if (event.key.toLowerCase() !== "v") return false;
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return false;
    if (root.contains(event.target)) return false;
    if (event.target.closest('input, textarea, select, [contenteditable="true"]')) return false;
    return true;
  }

  function isPageOverviewShortcut(event) {
    if (event.key.toLowerCase() !== "p") return false;
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return false;
    return !isEditorTextEntryTarget(event.target);
  }

  function isEditorTextEntryTarget(target) {
    return target instanceof Element && Boolean(target.closest('input, textarea, select, [contenteditable="true"]'));
  }

  function applyFontSize(el, value) {
    const size = Number(value);
    const next = value && Number.isFinite(size) && size > 0 ? Math.round(size) + "px" : "";
    textStyleTargets(el).forEach((target) => {
      target.style.fontSize = next;
    });
  }

  function primaryTextTarget(el) {
    if (isTextStyleElement(el) && !containsMedia(el)) return el;
    return [...el.querySelectorAll(textStyleSelector())].find((candidate) => !containsMedia(candidate)) || el;
  }

  function textStyleTargets(el) {
    const targets = new Set([el]);
    el.querySelectorAll(textStyleSelector()).forEach((candidate) => {
      if (!containsMedia(candidate)) targets.add(candidate);
    });
    return [...targets];
  }

  function isTextStyleElement(el) {
    return el.matches(textStyleSelector());
  }

  function textStyleSelector() {
    return "h1,h2,h3,h4,h5,h6,p,li,span,strong,em,b,i,small,blockquote";
  }

  function containsMedia(el) {
    return Boolean(el.querySelector("img,svg,canvas,video"));
  }

  function addText() {
    const slide = activeSlide();
    if (!slide) return;
    const zone = document.createElement("div");
    zone.className = "zone body";
    zone.dataset.zone = "text";
    zone.dataset.anim = "rise";
    zone.style.cssText = "left:96px;top:190px;width:520px;height:120px;font-size:30px;";
    zone.textContent = "新しいテキスト";
    zone.setAttribute("contenteditable", "true");
    slide.appendChild(zone);
    select(zone);
  }

  function addSpeechBubble() {
    const slide = activeSlide();
    if (!slide) return;
    const index = slide.querySelectorAll('[data-editor-element="speech-bubble"]').length + 1;
    const zone = document.createElement("div");
    zone.className = "zone lt-editor-speech-bubble";
    zone.dataset.zone = "callout";
    zone.dataset.editorElement = "speech-bubble";
    zone.dataset.overlapOk = "true";
    zone.dataset.anim = "pop";
    zone.dataset.step = String(nextAnimationStep(slide));
    zone.dataset.motionTarget = "speech-bubble-" + index;
    zone.dataset.motionTargets = zone.dataset.motionTarget;
    zone.dataset.motionReason = "追加した吹き出しを表示する";
    zone.style.cssText = "left:420px;top:160px;width:440px;height:96px;";
    const bubbleText = document.createElement("span");
    bubbleText.className = "lt-editor-speech-text";
    bubbleText.textContent = "新しい吹き出し";
    bubbleText.setAttribute("contenteditable", "true");
    bubbleText.setAttribute("spellcheck", "false");
    zone.appendChild(bubbleText);
    slide.appendChild(zone);
    select(zone);
  }

  function nextAnimationStep(slide) {
    const steps = [...slide.querySelectorAll("[data-step]")]
      .map((el) => Number(el.dataset.step))
      .filter((value) => Number.isFinite(value));
    return Math.max(0, ...steps) + 1;
  }

  function addImage(src, alt) {
    const slide = activeSlide();
    if (!slide) return;
    const zone = document.createElement("div");
    zone.className = "zone";
    zone.dataset.zone = "visual";
    zone.dataset.anim = "pop";
    zone.style.cssText = "left:720px;top:180px;width:420px;height:280px;";
    const img = document.createElement("img");
    img.src = src;
    img.alt = alt || "added image";
    img.style.cssText = "width:100%;height:100%;object-fit:contain;display:block;";
    zone.appendChild(img);
    slide.appendChild(zone);
    select(zone);
  }

  function duplicateSlide() {
    const slide = activeSlide();
    if (!slide) return;
    const clone = cleanSlideClone(slide.cloneNode(true));
    markSlideDraft(clone, "duplicate");
    clone.classList.remove("active");
    slide.after(clone);
    refreshDeckSlides();
    window.slideDeck?.show?.(slideIndex(clone), true);
    select(null);
  }

  function addBlankSlide() {
    const slides = [...deck.querySelectorAll(".slide")];
    const source = activeSlide() || slides[0];
    const slide = document.createElement("section");
    slide.className = "slide";
    slide.dataset.role = "editor-added";
    markSlideDraft(slide, "blank");
    const badge = source?.querySelector(".brand-badge")?.cloneNode(true);
    if (badge) slide.appendChild(cleanElement(badge));
    const title = document.createElement("div");
    title.className = "zone";
    title.dataset.zone = "title";
    title.style.cssText = "left:64px;top:92px;width:1152px;height:100px;";
    title.innerHTML = '<h2 contenteditable="true">新しいページ</h2>';
    const body = document.createElement("div");
    body.className = "zone card body";
    body.dataset.zone = "text";
    body.style.cssText = "left:64px;top:220px;width:1152px;height:300px;";
    body.textContent = "本文を入力";
    body.setAttribute("contenteditable", "true");
    const page = document.createElement("span");
    page.className = "zone page-number";
    page.dataset.overlapOk = "";
    page.textContent = String(slides.length + 1);
    slide.append(title, body, page);

    const thanks = deck.querySelector('.slide[data-role="thanks"]');
    if (thanks) thanks.before(slide);
    else deck.appendChild(slide);

    refreshDeckSlides();
    renumberSlides();
    window.slideDeck?.show?.(slideIndex(slide), true);
    select(body);
  }

  function refreshDeckSlides() {
    if (window.slideDeck) {
      window.slideDeck.slides = [...document.querySelectorAll(".slide")];
      window.slideDeck.applyZFlow?.();
    }
  }

  function renumberSlides() {
    const slides = [...deck.querySelectorAll(".slide")];
    const showTotal = slides.some((slide) => /\/\s*\d+\s*$/.test(slide.querySelector(".page-number")?.textContent || ""));
    slides.forEach((slide, index) => {
      let number = slide.querySelector(".page-number");
      if (!number) {
        number = document.createElement("span");
        number.className = "zone page-number";
        number.dataset.overlapOk = "";
        slide.appendChild(number);
      }
      number.textContent = showTotal ? (index + 1) + " / " + slides.length : String(index + 1);
    });
  }

  function markSlideDraft(slide, kind) {
    slide.dataset.editorDraft = kind;
    slide.dataset.deliveryMode = "draft";
    slide.dataset.estimatedSeconds = "0";
    slide.dataset.contentModelType = "draft";
    slide.dataset.evidenceArtifactIds = "draft";
    slide.dataset.sourceUnitIds = "draft";
    slide.dataset.flowPhase = "draft";
    slide.dataset.phaseQuestion = "";
    slide.dataset.speakerPurpose = "";
    slide.dataset.spokenNote = "";
  }

  function cleanSlideClone(slide) {
    cleanElement(slide);
    slide.querySelectorAll("[contenteditable]").forEach((el) => el.setAttribute("contenteditable", "true"));
    return slide;
  }

  function cleanElement(el) {
    el.classList.remove("active", "lt-editor-selected");
    el.removeAttribute("aria-hidden");
    return el;
  }

  function setAnimation(el, value) {
    if (!el) return;
    if (value) {
      el.dataset.anim = value;
      if (!el.hasAttribute("data-step")) el.dataset.step = String(nextAnimationStep(activeSlide()));
      normalizeAnimationSteps(activeSlide());
    } else {
      el.removeAttribute("data-anim");
      el.removeAttribute("data-step");
      el.classList.remove("shown");
      normalizeAnimationSteps(activeSlide());
    }
    refreshFields();
  }

  function setAnimationStep(el, value) {
    if (!el) return;
    if (value === "") return;
    if (!el.hasAttribute("data-anim")) {
      el.dataset.anim = "fade";
      fields.anim.value = "fade";
    }
    el.dataset.step = String(Math.max(0, Math.round(Number(value) || 0)));
    normalizeAnimationSteps(activeSlide());
    refreshFields();
    setStatus(animationStatus(el));
  }

  function setAnimationLast(el) {
    if (!el) return;
    const slide = el.closest(".slide") || activeSlide();
    if (!slide) return;
    if (!el.hasAttribute("data-anim")) el.dataset.anim = "fade";
    const otherSteps = [...slide.querySelectorAll("[data-anim][data-step]")]
      .filter((item) => item !== el)
      .map((item) => Number(item.dataset.step))
      .filter(Number.isFinite);
    el.dataset.step = String(Math.max(0, ...otherSteps) + 1);
    normalizeAnimationSteps(slide);
    refreshFields();
    setStatus(animationStatus(el) + "（最後に表示）");
  }

  function normalizeAnimationSteps(slide) {
    if (!slide) return;
    const items = [...slide.querySelectorAll("[data-anim][data-step]")];
    const uniqueSteps = [...new Set(items.map((item) => Math.max(0, Math.round(Number(item.dataset.step) || 0))))].sort((a, b) => a - b);
    const normalized = new Map(uniqueSteps.map((step, index) => [step, index]));
    items.forEach((item) => {
      const step = normalized.get(Math.max(0, Math.round(Number(item.dataset.step) || 0))) || 0;
      item.dataset.step = String(step);
      if (item.hasAttribute("data-reading-order")) item.dataset.readingOrder = String(step);
    });
  }

  function animationStatus(el) {
    const slide = el.closest(".slide") || activeSlide();
    const step = Math.max(0, Math.round(Number(el.dataset.step) || 0));
    const max = slide ? Math.max(0, ...[...slide.querySelectorAll("[data-anim][data-step]")].map((item) => Number(item.dataset.step)).filter(Number.isFinite)) : step;
    return "表示step " + step + " / 最終step " + max;
  }

  function animationTarget(el) {
    if (!el) return null;
    if (el.hasAttribute("data-anim")) return el;
    const nested = [...el.querySelectorAll("[data-anim]")];
    return nested.length === 1 ? nested[0] : el;
  }

  function bringForward(el) {
    const current = Number(getComputedStyle(el).zIndex);
    el.style.zIndex = String(Number.isFinite(current) ? current + 1 : 5);
  }

  async function saveHtml() {
    try {
      setStatus("Saving HTML...");
      const result = await postCleanHtml("/__lt_editor_save");
      setStatus("Overwritten HTML" + pathSuffix(result.htmlPath) + ".");
    } catch (error) {
      console.error("LT editor overwrite save failed", error);
      if (isFileUrl()) {
        await saveHtmlFromFileUrl(error);
        return;
      }
      setStatus("Overwrite unavailable. Start serve_editor.js and open its ?edit=1 URL. " + error.message);
    }
  }

  async function exportPdf() {
    prepareForPdfOutput();
    try {
      setStatus("Saving HTML and exporting PDF...");
      const result = await postCleanHtml("/__lt_editor_export_pdf");
      setStatus("PDF exported" + pathSuffix(result.pdfPath) + ".");
    } catch (error) {
      console.error("LT editor PDF export failed", error);
      if (isFileUrl()) {
        printPdfFromFileUrl(error);
        return;
      }
      setStatus("PDF export unavailable. Start serve_editor.js with bundled Node.js. " + error.message);
    }
  }

  async function saveHtmlFromFileUrl(originalError) {
    if (!window.showSaveFilePicker) {
      downloadHtmlFallback();
      setStatus("Direct overwrite is unavailable from file://. Downloaded edited HTML instead. For direct overwrite, start serve_editor.js. " + originalError.message);
      return;
    }
    try {
      const handle = await window.showSaveFilePicker({
        suggestedName: currentHtmlFilename(),
        types: [{ description: "HTML", accept: { "text/html": [".html"] } }]
      });
      const writable = await handle.createWritable();
      await writable.write(cleanDocumentHtml());
      await writable.close();
      setStatus("Saved HTML with browser file picker.");
    } catch (error) {
      if (error && error.name === "AbortError") {
        setStatus("Save canceled. Start serve_editor.js for one-click overwrite.");
      } else {
        downloadHtmlFallback();
        setStatus("File picker save failed; downloaded edited HTML instead. " + (error?.message || originalError.message));
      }
    }
  }

  function printPdfFromFileUrl(originalError) {
    prepareForPdfOutput();
    setStatus("Switched to view mode. Opening print dialog; choose Save as PDF. " + originalError.message);
    setTimeout(() => window.print(), 80);
  }

  function prepareForPdfOutput() {
    if (editorMode) {
      setEditorMode(false, false);
    } else {
      drag = null;
      pendingDrag = null;
      panelDrag = null;
      document.body.classList.remove("lt-editor-dragging");
      select(null);
      disableTextEditing();
      updateSelectionBox();
    }
    if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
  }

  function downloadHtmlFallback() {
    const blob = new Blob([cleanDocumentHtml()], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = currentHtmlFilename();
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function currentHtmlFilename() {
    const path = decodeURIComponent(location.pathname.split("/").pop() || "index.html");
    return path.toLowerCase().endsWith(".html") ? path : "index.html";
  }

  function isFileUrl() {
    return location.protocol === "file:";
  }

  async function postCleanHtml(endpoint) {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "content-type": "text/html;charset=utf-8", "accept": "application/json" },
      body: cleanDocumentHtml(),
      cache: "no-store"
    });
    if (!response.ok) {
      throw new Error(await responseErrorText(response));
    }
    return await response.json().catch(() => ({}));
  }

  async function responseErrorText(response) {
    const text = await response.text().catch(() => "");
    return text || response.statusText || "request failed";
  }

  function pathSuffix(value) {
    return value ? ": " + value : "";
  }

  function cleanDocumentHtml() {
    const clone = document.documentElement.cloneNode(true);
    clone.querySelector(".lt-editor-root")?.remove();
    clone.querySelector(".lt-editor-mode-badge")?.remove();
    clone.querySelector(".lt-editor-selection")?.remove();
    clone.querySelector(".lt-editor-tail-handle")?.remove();
    clone.querySelectorAll(".lt-editor-selected").forEach((el) => el.classList.remove("lt-editor-selected"));
    clone.querySelectorAll("[contenteditable]").forEach((el) => el.removeAttribute("contenteditable"));
    clone.querySelectorAll("[spellcheck]").forEach((el) => el.removeAttribute("spellcheck"));
    clone.querySelector("body")?.classList.remove("lt-editor-enabled", "lt-editor-edit-mode", "lt-editor-view-mode", "lt-editor-dragging", "lt-editor-tail-dragging");
    const cleanDeck = clone.querySelector(".deck");
    cleanDeck?.style.removeProperty("left");
    cleanDeck?.style.removeProperty("top");
    cleanDeck?.style.removeProperty("transform");
    cleanDeck?.style.removeProperty("transform-origin");
    const doctype = document.doctype ? "<!doctype html>\n" : "";
    return doctype + clone.outerHTML + "\n";
  }

  function describe(el) {
    const position = (el.dataset.zone || "zone") + " " + Math.round(getBoxStyle(el).left) + "," + Math.round(getBoxStyle(el).top);
    const animated = animationTarget(el);
    const animation = animated?.hasAttribute("data-anim") ? " / " + animationStatus(animated) : "";
    return isSpeechBubble(el) ? position + animation + " / 黄色いハンドルで尻尾の頂点を移動" : position + animation;
  }

  function setStatus(text) {
    status.textContent = text;
  }

  function syncSlideContextSoon() {
    setTimeout(() => syncSlideContext(false), 0);
  }

  function syncSlideContext(force) {
    const slide = activeSlide();
    if (!slide) return;
    if (selected && !slide.contains(selected)) select(null);
    const slides = [...deck.querySelectorAll(".slide")];
    const index = slides.indexOf(slide);
    editorPosition.textContent = (index + 1) + " / " + slides.length;
    if (!force && slide === noteSlide) return;
    if (document.activeElement === spokenNoteInput) return;
    noteSlide = slide;
    spokenNoteInput.value = slide.dataset.spokenNote || "";
    updateSpokenNoteStatus();
  }

  function restorePanelPosition() {
    try {
      const saved = JSON.parse(localStorage.getItem("lt-slide-editor-dock-position-v2") || "null");
      if (!saved?.floating) return;
      setDocked(false, {
        left: Number(saved.left) || 16,
        top: Number(saved.top) || 16,
        width: Number(saved.width) || 960,
        height: Number(saved.height) || 320
      });
    } catch (error) {
      localStorage.removeItem("lt-slide-editor-dock-position-v2");
    }
  }

  function savePanelPosition() {
    if (!editorDock.classList.contains("is-floating")) return;
    try {
      const rect = editorDock.getBoundingClientRect();
      localStorage.setItem("lt-slide-editor-dock-position-v2", JSON.stringify({
        floating: true,
        left: Math.round(rect.left),
        top: Math.round(rect.top),
        width: Math.round(rect.width),
        height: Math.round(rect.height)
      }));
    } catch (error) {
      // Position persistence is optional; keep the editor usable when storage is unavailable.
    }
  }

  function slideIndex(slide) {
    return [...deck.querySelectorAll(".slide")].indexOf(slide);
  }

  function px(value) {
    const number = Number.parseFloat(value);
    return Number.isFinite(number) ? number : 0;
  }

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function rgbToHex(value) {
    const match = String(value).match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
    if (!match) return "#ffffff";
    return "#" + [match[1], match[2], match[3]].map((part) => Number(part).toString(16).padStart(2, "0")).join("");
  }
})();
`;
}

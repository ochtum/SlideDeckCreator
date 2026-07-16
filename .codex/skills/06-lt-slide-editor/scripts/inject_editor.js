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
  .lt-editor-selection {
    display: none !important;
  }
}
body.lt-editor-enabled {
  --lt-editor-accent: #1d74e8;
}
body.lt-editor-view-mode .lt-editor-root,
body.lt-editor-view-mode .lt-editor-selection {
  display: none !important;
}
.lt-editor-root {
  position: fixed;
  z-index: 2147483647;
  left: 18px;
  top: 18px;
  width: 330px;
  max-height: calc(100vh - 36px);
  overflow: auto;
  border: 1px solid rgba(0, 27, 77, .18);
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 22px 60px rgba(0, 27, 77, .24);
  color: #001b4d;
  font-family: system-ui, -apple-system, "Segoe UI", "Noto Sans JP", sans-serif;
}
.lt-editor-root * {
  box-sizing: border-box;
}
.lt-editor-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 12px;
  border-bottom: 1px solid #d8e6f3;
  background: #f7faff;
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
.lt-editor-root textarea {
  width: 100%;
  min-height: 110px;
  resize: vertical;
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
.lt-editor-section {
  padding: 12px;
  border-bottom: 1px solid #e8f0f8;
}
.lt-editor-section h2 {
  margin: 0 0 8px;
  font-size: 18px;
  line-height: 1.2;
  letter-spacing: 0;
}
.lt-editor-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.lt-editor-wide {
  grid-column: 1 / -1;
}
.lt-editor-field {
  display: grid;
  gap: 4px;
  font-size: 18px;
  font-weight: 800;
  color: #385170;
}
.lt-editor-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.lt-editor-muted {
  margin-top: 8px;
  color: #5d6b82;
  font-size: 18px;
  line-height: 1.45;
}
.lt-editor-note-status {
  margin: 8px 0 0;
  color: #a33a12;
  font-size: 18px;
  font-weight: 800;
  line-height: 1.4;
}
.lt-editor-note-status.is-ok { color: #087a35; }
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
  let panelDrag = null;
  let editorMode = true;
  let noteSlide = null;

  const root = document.createElement("aside");
  root.className = "lt-editor-root";
  root.innerHTML = [
    '<div class="lt-editor-head"><span>Slide Editor</span></div>',
    '<section class="lt-editor-section">',
    '<h2>Element</h2>',
    '<div class="lt-editor-grid">',
    field("X", "x", "number"), field("Y", "y", "number"), field("W", "w", "number"), field("H", "h", "number"),
    field("Font", "fontSize", "number", 'min="1" step="1"'), field("Text", "color", "color"),
    field("Bg", "background", "color"),
    '<label class="lt-editor-field">Align<select data-field="textAlign"><option value="">auto</option><option value="left">left</option><option value="center">center</option><option value="right">right</option></select></label>',
    '<label class="lt-editor-field">Anim<select data-field="anim"><option value="">none</option><option value="rise">rise</option><option value="fade">fade</option><option value="pop">pop</option><option value="wipe">wipe</option><option value="draw">draw</option><option value="stamp">stamp</option><option value="marker">marker</option><option value="stomp">stomp</option></select></label>',
    '<label class="lt-editor-field">Zone<select data-field="zone"><option value="text">text</option><option value="visual">visual</option><option value="content">content</option><option value="title">title</option><option value="conclusion">conclusion</option><option value="qr">qr</option></select></label>',
    '</div>',
    '<div class="lt-editor-actions" style="margin-top:8px">',
    '<button type="button" data-action="bold">Bold</button>',
    '<button type="button" data-action="card">Card</button>',
    '<button type="button" data-action="front">Front</button>',
    '<button type="button" data-action="delete">Delete</button>',
    '</div>',
    '<p class="lt-editor-muted" data-status>Select a slide element.</p>',
    '</section>',
    '<section class="lt-editor-section">',
    '<h2>Add</h2>',
    '<div class="lt-editor-actions">',
    '<button type="button" data-action="addText">Text</button>',
    '<button type="button" data-action="addImage">Image</button>',
    '<button type="button" data-action="duplicateSlide">Duplicate page</button>',
    '<button type="button" data-action="addSlide">Blank page</button>',
    '</div>',
    '<input type="file" accept="image/*" data-image-picker hidden>',
    '</section>',
    '<section class="lt-editor-section">',
    '<h2>Spoken Note</h2>',
    '<textarea data-spoken-note rows="8" spellcheck="false" placeholder="橋渡し: 前ページから進む理由&#10;話す内容: 実際に口にする説明&#10;指差し: 画面にあるラベル&#10;次の一言: 次へ渡す発話"></textarea>',
    '<p class="lt-editor-note-status" data-note-status>台本形式を確認中</p>',
    '<p class="lt-editor-muted">Storyの台本と同じ四区画を保ちます。</p>',
    '</section>',
    '<section class="lt-editor-section">',
    '<h2>Output</h2>',
    '<div class="lt-editor-actions">',
    '<button type="button" data-action="save" data-primary="true">Save HTML</button>',
    '<button type="button" data-action="exportPdf">Export PDF</button>',
    '</div>',
    '<p class="lt-editor-muted">Server mode overwrites files directly. File mode uses a save picker and print dialog.</p>',
    '</section>',
    '<section class="lt-editor-section">',
    '<h2>Mode</h2>',
    '<div class="lt-editor-actions">',
    '<button type="button" data-action="toggleMode" data-mode-toggle>Edit mode</button>',
    '<button type="button" data-action="prev">Prev</button>',
    '<button type="button" data-action="next">Next</button>',
    '</div>',
    '<p class="lt-editor-muted">Press <strong>E</strong> to leave edit mode. Press <strong>V</strong> to show/hide editing controls.</p>',
    '</section>'
  ].join("");
  document.body.appendChild(root);
  restorePanelPosition();

  const modeBadge = document.createElement("div");
  modeBadge.className = "lt-editor-mode-badge";
  modeBadge.textContent = "View mode - press V to edit";
  document.body.appendChild(modeBadge);

  const selectionBox = document.createElement("div");
  selectionBox.className = "lt-editor-selection";
  selectionBox.hidden = true;
  document.body.appendChild(selectionBox);

  const imagePicker = root.querySelector("[data-image-picker]");
  const spokenNoteInput = root.querySelector("[data-spoken-note]");
  const noteStatus = root.querySelector("[data-note-status]");
  const status = root.querySelector("[data-status]");
  const fields = Object.fromEntries([...root.querySelectorAll("[data-field]")].map((el) => [el.dataset.field, el]));

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
  window.addEventListener("resize", updateSelectionBox);
  document.addEventListener("selectionchange", updateSelectionBox);

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
    if (panelDrag) {
      const nextLeft = clamp(panelDrag.startLeft + event.clientX - panelDrag.startClientX, 0, Math.max(0, innerWidth - root.offsetWidth));
      const nextTop = clamp(panelDrag.startTop + event.clientY - panelDrag.startClientY, 0, Math.max(0, innerHeight - Math.min(root.offsetHeight, innerHeight)));
      root.style.left = Math.round(nextLeft) + "px";
      root.style.top = Math.round(nextTop) + "px";
      root.style.right = "auto";
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
    const rect = root.getBoundingClientRect();
    panelDrag = {
      startClientX: event.clientX,
      startClientY: event.clientY,
      startLeft: rect.left,
      startTop: rect.top
    };
    event.preventDefault();
    event.stopPropagation();
  }

  function onKeyDown(event) {
    if (!document.body.classList.contains("lt-editor-enabled")) return;
    if (event.defaultPrevented) return;
    if (isViewModeShortcut(event)) {
      setEditorMode(!editorMode);
      event.preventDefault();
      event.stopPropagation();
      return;
    }
    if (!editorMode) return;
    if (root.contains(event.target)) return;
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
    if (name === "color") selected.style.color = value || "";
    if (name === "background") selected.style.background = value || "";
    if (name === "textAlign") selected.style.textAlign = value || "";
    if (name === "zone") selected.dataset.zone = value || "text";
    if (name === "anim") setAnimation(selected, value);
    updateSelectionBox();
  }

  function onToolbarClick(event) {
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
    if (action === "toggleMode") setEditorMode(!editorMode);
    if (action === "bold" && selected) selected.style.fontWeight = selected.style.fontWeight === "900" ? "" : "900";
    if (action === "card" && selected) selected.classList.toggle("card");
    if (action === "front" && selected) bringForward(selected);
    if (action === "delete" && selected) {
      selected.remove();
      select(null);
    }
    if (action === "addText") addText();
    if (action === "addImage") imagePicker.click();
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
    if (selected) selected.classList.add("lt-editor-selected");
    refreshFields();
    updateSelectionBox();
    setStatus(selected ? describe(selected) : "Select a .zone element.");
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
    fields.x.value = Math.round(box.left);
    fields.y.value = Math.round(box.top);
    fields.w.value = Math.round(box.width);
    fields.h.value = Math.round(box.height);
    fields.fontSize.value = Math.round(px(getComputedStyle(primaryTextTarget(selected)).fontSize)) || "";
    fields.color.value = rgbToHex(getComputedStyle(selected).color);
    fields.background.value = rgbToHex(getComputedStyle(selected).backgroundColor);
    fields.textAlign.value = selected.style.textAlign || "";
    fields.zone.value = selected.dataset.zone || "text";
    fields.anim.value = selected.dataset.anim || selected.querySelector("[data-anim]")?.dataset.anim || "";
  }

  function updateSelectionBox() {
    if (!editorMode || !selected || !document.body.contains(selected)) {
      selectionBox.hidden = true;
      return;
    }
    const rect = selected.getBoundingClientRect();
    selectionBox.hidden = false;
    selectionBox.style.left = rect.left + "px";
    selectionBox.style.top = rect.top + "px";
    selectionBox.style.width = rect.width + "px";
    selectionBox.style.height = rect.height + "px";
  }

  function exposeTextEditing() {
    deck.querySelectorAll(".zone").forEach((zone) => {
      const editable = zone.matches("h1,h2,h3,p,li,span,div") ? zone : zone.querySelector("h1,h2,h3,p,li,span,div");
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
      panelDrag = null;
      document.body.classList.remove("lt-editor-dragging");
      select(null);
      disableTextEditing();
      if (announce) setStatus("View mode. Press V for editor mode, or E for normal URL.");
    }
    updateSelectionBox();
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
    slide.dataset.spokenNote = "";
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
    slides.forEach((slide, index) => {
      let number = slide.querySelector(".page-number");
      if (!number) {
        number = document.createElement("span");
        number.className = "zone page-number";
        number.dataset.overlapOk = "";
        slide.appendChild(number);
      }
      number.textContent = String(index + 1);
    });
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
    if (value) el.dataset.anim = value;
    else el.removeAttribute("data-anim");
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
    clone.querySelectorAll(".lt-editor-selected").forEach((el) => el.classList.remove("lt-editor-selected"));
    clone.querySelectorAll("[contenteditable]").forEach((el) => el.removeAttribute("contenteditable"));
    clone.querySelectorAll("[spellcheck]").forEach((el) => el.removeAttribute("spellcheck"));
    clone.querySelector("body")?.classList.remove("lt-editor-enabled", "lt-editor-edit-mode", "lt-editor-view-mode", "lt-editor-dragging");
    const doctype = document.doctype ? "<!doctype html>\n" : "";
    return doctype + clone.outerHTML + "\n";
  }

  function describe(el) {
    return (el.dataset.zone || "zone") + " " + Math.round(getBoxStyle(el).left) + "," + Math.round(getBoxStyle(el).top);
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
    if (!force && slide === noteSlide) return;
    if (document.activeElement === spokenNoteInput) return;
    noteSlide = slide;
    spokenNoteInput.value = slide.dataset.spokenNote || "";
    updateSpokenNoteStatus();
  }

  function restorePanelPosition() {
    try {
      const saved = JSON.parse(localStorage.getItem("lt-slide-editor-position") || "null");
      if (!saved) return;
      root.style.left = clamp(Number(saved.left) || 18, 0, Math.max(0, innerWidth - root.offsetWidth)) + "px";
      root.style.top = clamp(Number(saved.top) || 18, 0, Math.max(0, innerHeight - Math.min(root.offsetHeight, innerHeight))) + "px";
    } catch (error) {
      localStorage.removeItem("lt-slide-editor-position");
    }
  }

  function savePanelPosition() {
    try {
      localStorage.setItem("lt-slide-editor-position", JSON.stringify({
        left: Math.round(root.getBoundingClientRect().left),
        top: Math.round(root.getBoundingClientRect().top)
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

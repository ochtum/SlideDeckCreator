#!/usr/bin/env node
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { execFileSync } = require("node:child_process");
const { chromium } = require("playwright");
const { prepareSlideViewport, inspectSlide } = require("./review_deck.js");

async function main() {
  const skills = path.resolve(__dirname, "../..");
  const tempRoot = fs.realpathSync(os.tmpdir());
  const folder = fs.mkdtempSync(path.join(tempRoot, "lt-speaking-"));
  const html = path.join(folder, "index.html");
  fs.copyFileSync(path.join(skills, "04-lt-slide-build/assets/deck-shell.html"), html);
  execFileSync(process.execPath, [path.join(skills, "06-lt-slide-editor/scripts/inject_editor.js"), html]);
  const browser = await chromium.launch({ channel: "chrome", headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
    await page.goto(pathToFileURL(html).href + "?presenter=1");
    const note = "形式: hybrid\n要点: 読む順序と共通ルールに絞る\n話す内容: 全部入れると最初に読む情報が埋もれます。\n指差し: AGENTS.md";
    await page.evaluate(note => { window.slideDeck.slides[0].dataset.spokenNote = note; window.slideDeck.renderPresenter(); }, note);
    assert.equal(await page.locator(".presenter-cue-primary li").textContent(), "読む順序と共通ルールに絞る");
    assert.equal(await page.locator(".presenter-cue-primary details").evaluate(el => el.open), false);
    await page.locator(".presenter-cue-primary summary").click();
    await page.evaluate(() => window.slideDeck.renderPresenter());
    assert.equal(await page.locator(".presenter-cue-primary details").evaluate(el => el.open), true, "same-note rerender must preserve expanded script");
    await page.evaluate(() => window.slideDeck.renderPresenterNote(document.getElementById("presenterNote"), "形式: cue\n指差し: 差分グラフ\n話さない理由: 二つの値を見比べる時間を取る"));
    assert.equal(await page.locator(".presenter-cue-primary .presenter-cue-label").textContent(), "見る時間");
    await page.evaluate(() => window.slideDeck.renderPresenterNote(document.getElementById("presenterNote"), "橋渡し: 前の説明から進みます\n話す内容: 旧形式の台本も表示できます\n指差し: 値\n次の一言: 次を見ます"));
    assert.equal(await page.locator(".presenter-cue-primary .presenter-cue-body").textContent(), "旧形式の台本も表示できます");

    await page.goto(pathToFileURL(html).href);
    await prepareSlideViewport(page, { width: 1280, height: 720 });
    const rect = await page.locator("#deck").boundingBox();
    assert.ok(Math.abs(rect.x) < 1 && Math.abs(rect.y) < 1 && Math.abs(rect.width - 1280) < 1, JSON.stringify(rect));
    await page.locator("#deck").evaluate(el => el.style.setProperty("translate", "-50% -50%", "important"));
    const clipped = await inspectSlide(page, 0, { minMargin: 40, brandMinMargin: 16, overlapTolerance: 8 });
    assert.ok(clipped.findings.some(f => f.type === "slide-outside-viewport"), "capture clipping must be reported");

    await page.goto(pathToFileURL(html).href);
    await page.emulateMedia({ reducedMotion: "reduce" });
    const future = await page.evaluate(() => {
      const el = document.createElement("p"); el.id = "future-step"; el.dataset.anim = "rise"; el.dataset.step = "1"; el.textContent = "次の判断";
      window.slideDeck.slides[0].appendChild(el);
      return getComputedStyle(el).opacity;
    });
    assert.equal(future, "0", "reduced motion must preserve unreached steps");
    await page.emulateMedia({ media: "print", reducedMotion: "reduce" });
    assert.equal(await page.locator("#future-step").evaluate(el => getComputedStyle(el).opacity), "1", "print must reveal all steps even with reduced motion");

    await page.emulateMedia({ media: "screen", reducedMotion: "no-preference" });
    await page.goto(pathToFileURL(html).href + "?edit=1");
    const input = page.locator("textarea[data-spoken-note]");
    const before = await input.inputValue();
    await input.fill(note);
    await input.fill(note.replace("絞る", "まとめる"));
    const data = await page.evaluate(() => ({ baseline: window.slideDeck.slides[0].dataset.originalSpokenNote, status: window.slideDeck.slides[0].dataset.noteReview, note: window.slideDeck.slides[0].dataset.spokenNote }));
    assert.equal(data.baseline, before, "first edit baseline must survive subsequent changes");
    assert.equal(data.status, "pending");
    assert.ok(data.note.includes("まとめる"));
    console.log("OK: cue/hybrid/legacy presenter, edit baseline, viewport, reduced motion and print");
  } finally {
    await browser.close();
    if (path.dirname(fs.realpathSync(folder)) === tempRoot) fs.rmSync(folder, { recursive: true });
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });

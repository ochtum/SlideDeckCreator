# Build contract

## Project directories

- Intermediate files: `.lt-slide-work/`
- Persistent presenter configuration: `config/presenter.json`
- Final deliverables: `output/`
- Final local assets: `output/assets/`

Recommended `.gitignore` entry:

```gitignore
# LT slide generation intermediates
.lt-slide-work/
```

## Presenter profile binding

`config/presenter.json` は自己紹介スライドの唯一のデータソースとする。Storyで `presenter.include: true` の場合、各出力デッキの `data-role="profile"` は次を満たす。

- `display_name`、`bio`、全リンクの platform と account を可視テキストとして持つ。
- `qr.use: true` なら、JSONと完全一致する `qr.label` と、`qr.path` からコピーしたQR画像を持つ。
- `avatar.use: true` なら、`avatar.path` からコピーした画像を持つ。
- `use: false` の画像を出力しない。作業用の `visuals/` や `visuals-manifest.yaml` に残った古いコピーを使わない。
- 構造ラベルの「自己紹介」「PROFILE」、章フッター、ページ番号を除き、JSONにない可視テキストを持たない。テーマ固有の結論帯、補足コピー、実績、意気込みを追加せず、`conclusion_zone` / `.conclusion-bar` を持たない。

ビルド後、`scripts/validate_presenter_binding.py --presenter config/presenter.json <part-output>/index.html` を実行する。値の欠落、固定文言、asset不一致はビルド失敗とする。

## Design system binding

Storyに `design_system` がある場合、`config/design-systems/registry.yaml` から同じID/versionのspecを解決し、Blueprintへ参照をそのまま引き継ぐ。最終HTMLの `body` または `.deck` に `data-design-system-id` と `data-design-system-version` を置く。選択済みIDが存在しない、versionが違う、HTML属性が違う場合は内蔵テーマへfallbackせずビルド失敗とする。Storyに選択がない場合だけ `references/design-system.md` を内蔵fallbackとして使う。

## Required behavior

- Right Arrow, Space, PageDown: next step or next slide
- Left Arrow, PageUp: previous step or previous slide
- Home and End: first and last slide
- F: fullscreen
- R: replay current slide
- P: pager and overview mode
- S: open the synchronized presenter view in a separate window
- A: reveal every animation step on the current slide without advancing
- Hash links: `#1`, `#2`, ...

## Visible metadata

- Preserve each internal identifier in `.slide[data-slide-id]`, but never render `s01` / `sXX` as audience-visible text.
- The footer may show a left section/phase label and a right page number. Do not add a center system title, deck title, source filename, or source note.
- Preserve provenance in `data-source-note`, `data-source-unit-ids`, and evidence attributes instead of consuming slide space.
- A long-form roadmap renders the exact Story/Blueprint `roadmap.items`: concrete label, summary, physical page range, and `data-roadmap-slide-ids` for every node.

## Animation Order

- Animation steps follow semantic order first: explicit number, cause/effect, dependency, operation, and speaker explanation order. DOM order must match the visual order. Z-shaped position is only the fallback for independent elements with no semantic order.
- Runtime preserves explicit `[data-step]` values, including `data-step="0"`. Zone positionからのZ-flow補完は属性自体がない要素だけに行い、0を未指定として扱わない。
- Per-slide step numbers are compressed so navigation has no empty intermediate step.
- The default maximum step count is 6. An explicit item-by-item sequence may use up to 9 steps; 10 or more must be regrouped by meaning.
- The title and required context are visible at step 0. Ordered content starts at step 1. Output, completion criteria, and the conclusion appear after the content; the conclusion is last. A `data-role="profile"` slide has no conclusion unless it is explicit presenter data, and the standard profile contract forbids that extra region.
- Every meaningful sibling in a progressive table, card group, checklist, or numbered process must be either animated or explicitly marked `data-static-intentional`. Partial coverage is a build error.
- Current and presenter previews use the same normalized DOM state.

## Presenter view

- Keep the original window as the audience display and open the presenter view with `?presenter=1`.
- Synchronize slide index and animation step in both directions.
- Show the current slide, next slide, current `spoken_note`, elapsed time, page number, and step.
- For talkability v2, parse the four note lines into visible `橋渡し`、`話す内容`、`指差し`、`次の一言` sections. Do not collapse them into an undifferentiated paragraph.
- Treat `話す内容` as the primary reading area. Place `橋渡し`、`指差し`、`次の一言` in a subordinate support area so a long bridge cannot consume the script height.
- Show the current phase question and speaker purpose near the note when present.
- Show the phase question as a distinct, readable row. Do not compress question, purpose, reader context, and bridge into a 1–3 line strip.
- Update elapsed time without rebuilding the note or context DOM. Scrolling `話す内容` must keep the same position while the timer advances and while animation steps change on the same slide.
- Rebuild the note only when `data-spoken-note` changes, and rebuild the context only when its values change. Reset their scroll positions when moving to a different note, not on timer ticks.
- Show the embedded keyboard shortcut list in the presenter view, near the next-slide preview.
- Clone the current audience slide exactly as rendered. Preserve its runtime classes, attributes, inline styles, SVG state, and deck-specific reveal markers.
- Include the audience slide's current DOM snapshot in synchronization messages; index and step alone are insufficient for deck-specific reveal state.
- When navigation originates in the presenter window, apply it on the audience window first, then return the audience DOM snapshot to the presenter.
- Do not reconstruct the current preview's visibility solely from `data-step` or `data-anim`; generated decks may use additional state classes.
- Render only the next-slide preview in its animation-complete final state. Keep current-preview and next-preview rendering paths separate.
- At every step, the current presenter preview must contain the same visible slide content as the audience display.
- Provide previous, next, and timer reset controls in the presenter view.
- Embed every slide note locally in `index.html`; do not fetch notes from `.lt-slide-work/` at runtime.
- Use same-page browser APIs such as `BroadcastChannel` and `postMessage`, with graceful behavior when one channel or window is unavailable.
- Never show presenter notes in print output or the audience display.

## Accessibility

- Semantic headings and sections
- Meaningful image alt text
- Decorative SVG uses `aria-hidden="true"`
- Focus is not trapped
- Reduced motion reveals all content
- Print reveals all content

## Long-form explanation traceability

For decks of 20 minutes or longer:

- Copy `delivery.mode` and `delivery.estimated_seconds` to `data-delivery-mode` and `data-estimated-seconds` on each body slide.
- Render every `delivery.visible_anchors` value as visible audience text.
- Add `data-content-model-type` and comma-separated `data-evidence-artifact-ids` when a blueprint content model exists.
- `full-equivalence` では各 `.slide` に空白区切りの `data-source-unit-ids` を置き、StoryとBlueprintの同じIDを保持する。
- Render the actual content-model data. A generic checklist, stock icon, or repeated diagram is not an implementation of different source artifacts.
- When the same artifact is shown again, render the blueprint's page-specific focus and highlight so the new reading is visible.
- Copy `flow_phase`, the matching phase question, and `speaker_cue.purpose` to `data-flow-phase`, `data-phase-question`, and `data-speaker-purpose`.
- Preserve `speaker_cue.point_at` as visible HTML/SVG anchors. A generated image with approximate text does not satisfy this requirement.

## PDF print

- Define `@page { size: 13.333333in 7.5in; margin: 0; }`.
- This custom 16:9 page is the PDF source of truth. Do not use A4, Letter, or a printer-specific paper size.
- In print CSS, set each slide to `13.333333in` by `7.5in`, remove transforms and transitions, and emit exactly one slide per page.
- Set `print-color-adjust: exact` and `-webkit-print-color-adjust: exact`.
- Reveal every animation step and hide presenter UI, speaker notes, and navigation controls.
- Export `output/index.pdf` with browser headers and footers disabled.
- Validate that PDF page count equals slide count and every page is 960 by 540 points within a small rounding tolerance.
- Render the PDF to PNG and visually inspect every page before delivery.

## Packaging

`index.html` must be self-contained except local files under `assets/`. ZIP root contains `index.html` and `assets/`, not an extra parent directory.

## Visual QA

Review every slide at 1280x720:

- initial entrance state
- every step revealed
- every intermediate step follows semantic order; Z flow is checked only for independent items without a semantic sequence
- normal browser projection with visible outer viewport gutter on all sides
- previous navigation
- overview mode
- presenter view and bidirectional navigation
- shortcut list is visible in the presenter view and absent from the audience display
- audience/current-preview parity at the initial state, every intermediate step, and reveal-all state
- print preview
- exported PDF page count and 16:9 page dimensions
- presenter note scroll position after at least one timer tick
- presenter usability at both 1280x720 and a taller 1280x860 viewport, including minimum readable areas for `話す内容` and the phase question

Reject the deck when text is clipped, the deck is flush against the browser viewport edge, any content zone intersects another, body text falls below 28px, a visual uses cover cropping, a QR is too small, or a conclusion obscures the main diagram.

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

ビルド後、`scripts/validate_presenter_binding.py --presenter config/presenter.json <part-output>/index.html` を実行する。値の欠落、固定文言、asset不一致はビルド失敗とする。

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

## Animation Order

- Animation steps follow a Z-shaped reading path: top-left, top-right, center-left, center, bottom-left, bottom-right.
- Runtime normalizes `[data-step]` from element zone positions before the first slide is shown.
- Per-slide step numbers are compressed so navigation has no empty intermediate step.
- The maximum step count is 6. Fewer steps are preferred when the slide has fewer visual groups.
- Current and presenter previews use the same normalized DOM state.

## Presenter view

- Keep the original window as the audience display and open the presenter view with `?presenter=1`.
- Synchronize slide index and animation step in both directions.
- Show the current slide, next slide, current `spoken_note`, elapsed time, page number, and step.
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
- step-by-step Z flow from top-left to top-right, center-left, center, bottom-left, then bottom-right
- normal browser projection with visible outer viewport gutter on all sides
- previous navigation
- overview mode
- presenter view and bidirectional navigation
- shortcut list is visible in the presenter view and absent from the audience display
- audience/current-preview parity at the initial state, every intermediate step, and reveal-all state
- print preview
- exported PDF page count and 16:9 page dimensions

Reject the deck when text is clipped, the deck is flush against the browser viewport edge, any content zone intersects another, body text falls below 28px, a visual uses cover cropping, a QR is too small, or a conclusion obscures the main diagram.

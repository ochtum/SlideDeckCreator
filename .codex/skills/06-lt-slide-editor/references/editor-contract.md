# Editor contract

## Scope

The editor augments a finished HTML deck. It is not a replacement for the story, blueprint, visual generation, or PDF build skills.

## Activation

- Start only when the URL contains `edit=1`.
- Do not start in presenter mode.
- Do not alter normal presentation behavior when `edit=1` is absent.
- Keep all editor UI outside `.deck` so it cannot be printed or captured as slide content.
- Use a presenter-style workspace in edit mode: the real editable slide in the upper-left stage, the element editor docked below it, and spoken notes/output in the right column.
- Keep the lower-left editor dock separate from the slide. Allow its header to undock and drag the panel, and provide an explicit action to return it to the default dock.
- Support `E` as a keyboard shortcut that toggles between the normal URL and the `?edit=1` editor URL.
- Support `V` as a keyboard shortcut for switching between editor mode and view mode while `edit=1` is active.

## Required capabilities

- Select `.zone` elements on the active slide.
- Move selected elements by dragging.
- Edit text in place.
- Edit the active slide's `data-spoken-note`.
- Show whether the note contains non-empty `橋渡し`, `話す内容`, `指差し`, and `次の一言` sections while editing.
- Add text zones.
- Add image zones from a local file or pasted asset.
- Apply common styles: font size, text color, background color, bold, alignment, card style, animation type, geometry.
- Add a blank slide.
- Duplicate the current slide.
- Recalculate page numbers after page changes.
- Preserve the deck's existing page-number format. A deck using `1 / 28` must remain in the `current / total` format after editing, duplication, or page insertion.
- Save a clean edited HTML file without editor selection state.
- Overwrite the source HTML through the bundled local save server. Do not make download-only save the standard behavior.
- Export a PDF through the bundled local save server after first writing the clean edited HTML.
- Move the editor panel without moving selected slide elements.
- Keep the editable `.deck` inside the upper-left stage bounds at both 1280x720 and a large desktop viewport; do not edit a presenter-preview clone.
- Toggle normal/editor URLs with `E` when focus is not inside editable text or a form control.
- Toggle editor/view mode with `V` when focus is not inside editable text or a form control.

## Preservation rules

- Preserve every slide's `data-spoken-note`.
- Preserve `data-delivery-mode`, `data-estimated-seconds`, `data-content-model-type`, `data-evidence-artifact-ids`, `data-source-unit-ids`, `data-flow-phase`, `data-phase-question`, and `data-speaker-purpose` on existing slides.
- Preserve deck-level `data-design-system-id` and `data-design-system-version`. Per-slide edits must not rewrite the registry design-system spec.
- Save edited `data-spoken-note` values as slide attributes.
- Preserve presentation keyboard shortcuts in normal mode.
- Preserve presenter view behavior.
- Preserve normal slide navigation shortcuts while editor view mode is active.
- Preserve print CSS and 16:9 page sizing.
- Preserve local `output/assets/` references.
- Avoid rewriting unrelated deck markup.
- Treat duplicated and blank slides as content drafts until their timing, visible anchors, evidence traceability, and spoken notes are made page-specific.
- Mark duplicated and blank slides with `data-editor-draft`, and clear inherited timing, evidence, source-unit, question, speaker-purpose, and spoken-note values instead of presenting them as reviewed content.
- Keep save-server writes scoped to the explicit HTML file passed to `serve_editor.js`.
- Keep PDF export scoped to the same directory and basename as the explicit HTML file passed to `serve_editor.js`.

## Safety checks

Before delivery, verify:

- `output/index.html?edit=1` shows the editor toolbar.
- Pressing `E` on `output/index.html` navigates to `output/index.html?edit=1`.
- Pressing `E` on `output/index.html?edit=1` navigates back to the normal URL without `edit=1`.
- The editor panel can be dragged from its header and remains within the viewport.
- The editor starts docked below the real editable slide, does not overlap it, and can return to that dock after floating.
- The spoken-note field and Save/PDF actions appear in the right column and remain readable at 1280x720.
- Pressing `V` switches from editor mode to view mode, hiding edit controls and allowing normal slide navigation.
- Pressing `V` again returns to editor mode.
- A selected zone can be dragged and the inline `left` and `top` values update.
- A selected text zone's font size can be changed even when the visible text is inside nested heading or paragraph elements.
- Text can be changed and remains after saving and reopening the saved HTML.
- The Spoken Note field follows the active slide and updates that slide's `data-spoken-note`.
- The Spoken Note field warns when any talkability v2 section is missing and reports ready only when all four sections are non-empty.
- Edited spoken notes remain after saving and reopening the saved HTML.
- `Save HTML` overwrites the original target file when opened from `serve_editor.js`.
- `Save HTML` reports the saved path or a concrete failure reason in the editor status.
- `Export PDF` switches the active editor UI to view mode before exporting or opening print.
- `Export PDF` overwrites the target HTML first, then writes a same-basename PDF such as `output/index.pdf`.
- If Playwright is not available, `Export PDF` reports a concrete failure reason in the editor status.
- If the deck is opened as `file://`, `Save HTML` uses the browser file save picker when available, otherwise downloads the edited HTML.
- If the deck is opened as `file://`, `Export PDF` opens the browser print dialog so the user can choose Save as PDF.
- If the deck is opened from a normal static server without the bundled save server, `Save HTML` reports that overwrite save is unavailable.
- If the deck is opened from a normal static server without the bundled save server, `Export PDF` reports that PDF export is unavailable.
- A text zone and an image zone can be added.
- A slide can be duplicated.
- A blank slide can be added.
- `?edit=1` absent keeps the normal presentation view clean.
- `?presenter=1` does not show editor UI.
- Print preview does not show editor UI.
- After content edits in a 20+ minute deck, the explanation-depth and talkability reviews pass and no duplicated slide keeps another page's timing/evidence/speaker purpose without a new focus.

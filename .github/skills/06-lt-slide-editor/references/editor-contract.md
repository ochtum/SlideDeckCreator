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
- Organize the lower-left dock into Element, Add, and View/Navigation tabs. Show one task surface at a time, switch back to Element when a slide zone is selected, and avoid horizontal scrolling in the active panel.
- Support `E` as a keyboard shortcut that toggles between the normal URL and the `?edit=1` editor URL.
- Support `V` as a keyboard shortcut for switching between editor mode and view mode while `edit=1` is active.
- Support `P` as a keyboard shortcut for opening the existing page overview while editing. Choosing a thumbnail or closing the overview must return to the prior editor/view state.

## Required capabilities

- Select `.zone` elements on the active slide.
- Move selected elements by dragging.
- Edit text in place.
- Edit the active slide's `data-spoken-note`.
- Show whether the note contains non-empty `橋渡し`, `話す内容`, `指差し`, and `次の一言` sections while editing.
- Add text zones.
- Add image zones from a local file or pasted asset.
- Add speech-bubble zones with a two-layer CSS pseudo-element tail that protrudes about 30px beyond the bubble body, editable text, movable geometry, and an animation step after the current maximum step. When a bubble is selected, show a draggable tail-tip handle; moving it must recompute the two triangle layers and automatically attach the base to the nearest bubble edge.
- Apply common styles: font size, text color, background color, bold, alignment, card style, animation type, animation step, geometry. Provide an explicit action that moves the selected animated element to the final step and a preview action that resets the current slide to step 0 in clean view mode.
- Add a blank slide.
- Duplicate the current slide.
- Recalculate page numbers after page changes.
- Preserve the deck's existing page-number format. A deck using `1 / 28` must remain in the `current / total` format after editing, duplication, or page insertion.
- Save a clean edited HTML file without editor selection state.
- Overwrite the source HTML through the bundled local save server. Do not make download-only save the standard behavior.
- Export a PDF through the bundled local save server after first writing the clean edited HTML.
- Move the editor panel without moving selected slide elements.
- Keep editor labels readable against the dark dock background and keep all controls in the active tab within the dock width.
- Keep the editable `.deck` inside the upper-left stage bounds at both 1280x720 and a large desktop viewport; do not edit a presenter-preview clone.
- Toggle normal/editor URLs with `E` when focus is not inside editable text or a form control.
- Toggle editor/view mode with `V` when focus is not inside editable text or a form control.
- Open the page overview with `P`, move to a selected thumbnail, and restore editor mode without treating `P` as a shortcut while text, notes, or form fields have focus.

## Preservation rules

- Preserve every slide's `data-spoken-note`.
- Preserve `data-delivery-mode`, `data-estimated-seconds`, `data-content-model-type`, `data-evidence-artifact-ids`, `data-source-unit-ids`, `data-flow-phase`, `data-phase-question`, and `data-speaker-purpose` on existing slides.
- Preserve deck-level `data-design-system-id` and `data-design-system-version`. Per-slide edits must not rewrite the registry design-system spec.
- Save edited `data-spoken-note` values as slide attributes.
- Persist an edited speech-bubble tip as `data-tail-tip-x`, `data-tail-tip-y`, `data-tail-side`, and the CSS variables required to reproduce both pseudo-element polygons. Do not serialize the editor-only tip handle.
- Preserve presentation keyboard shortcuts in normal mode.
- Preserve presenter view behavior.
- Preserve normal slide navigation shortcuts while editor view mode is active.
- Preserve print CSS and 16:9 page sizing.
- Preserve staged disclosure when `prefers-reduced-motion: reduce`: disable motion but keep future-step elements hidden until their step. Print output still reveals all elements.
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
- Pressing `P` opens a visible page overview, selecting a thumbnail changes the active slide and returns to editor mode, and `P` / `Escape` can close the overview without losing the edit URL.
- Typing `P` in slide text, Spoken Note, or an editor form does not open the page overview.
- A selected zone can be dragged and the inline `left` and `top` values update.
- A selected text zone's font size can be changed even when the visible text is inside nested heading or paragraph elements.
- A selected animated element exposes its numeric step, accepts a new step, can be moved to the final step, and remains hidden until that step in both normal and reduced-motion presentation settings. If the selected zone has exactly one animated descendant, edit that descendant instead of adding a duplicate animation to the zone wrapper.
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
- A speech-bubble zone can be added, selected, moved, edited, and saved; selection shows a draggable yellow tail-tip handle, dragging or arrow-key movement updates the saved tip coordinates, the base follows the nearest top/right/bottom/left edge, and both CSS pseudo-element layers redraw. The tail remains visibly connected, uses an outline close to the bubble body's approximately 2px border, protrudes about 30px beyond the body on a white slide, leaves at least 5px before its target text, and is not clipped by animation-state styles.
- A slide can be duplicated.
- A blank slide can be added.
- `?edit=1` absent keeps the normal presentation view clean.
- `?presenter=1` does not show editor UI.
- Print preview does not show editor UI.
- After content edits in a 20+ minute deck, the explanation-depth and talkability reviews pass and no duplicated slide keeps another page's timing/evidence/speaker purpose without a new focus.

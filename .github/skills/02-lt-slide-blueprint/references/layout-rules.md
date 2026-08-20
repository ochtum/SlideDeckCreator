# Layout rules

## Reserved areas

- Canvas: 1280x720
- Safe content: x=48..1232, y=72..648
- Badge: x=48..220, y=24..64
- Footer: x=48..1232, y=660..704
- Page number: x=1160..1232, y=660..704
- Optional visible citation: x=64..1120, y=620..648. Use only when the slide cites an external claim.

## Zone gaps

- Independent zones need at least 24px.
- Text and image columns need at least 40px.
- Card gaps are 20 to 28px.
- Conclusion bars need 24px above and below.
- QR quiet space must be at least 12px.

## Capacity

- One card: heading plus at most 3 short lines.
- Three-column cards: heading plus at most 2 short lines each.
- Four-column cards: heading plus 1 short line each.
- One slide: at most 3 bullets, except recap with 4.
- One line: aim for 13 to 22 Japanese characters at 30px.

### 20 minutes or longer

- Slide title: 44 to 56px. Do not consume the upper third with a 70px title on every page.
- Explanatory body: 24 to 30px.
- Table, code, config, and annotations: 18 to 22px with short representative data.
- A substantive slide should use roughly 60 to 85 percent of the safe content area for meaningful text, data, diagram, or evidence.
- Allow 4 to 7 short table cells, code lines, annotations, or checklist rows when they belong to one concrete artifact. The three-bullet limit does not apply to structured evidence.
- Low-density statement layouts are limited to transitions and conclusions; they do not define the default capacity of a long-form deck.

## Collision handling order

1. Remove redundant words.
2. Move detail to `spoken_note`.
3. Reduce cards or bullets.
4. Change layout.
5. Split the slide.

Never solve collision by shrinking body text below 28px or by overlapping a conclusion over a diagram.

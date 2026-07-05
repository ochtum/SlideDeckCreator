# Layout rules

## Reserved areas

- Canvas: 1280x720
- Safe content: x=48..1232, y=72..648
- Badge: x=48..220, y=24..64
- Footer: x=48..1232, y=660..704
- Page number: x=1160..1232, y=660..704

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

## Collision handling order

1. Remove redundant words.
2. Move detail to `spoken_note`.
3. Reduce cards or bullets.
4. Change layout.
5. Split the slide.

Never solve collision by shrinking body text below 28px or by overlapping a conclusion over a diagram.


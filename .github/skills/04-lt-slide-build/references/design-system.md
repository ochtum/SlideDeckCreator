# Design system

これはStoryでデザインシステムが選択されていない場合だけ使う内蔵fallbackである。`config/design-systems/registry.yaml` のID/versionが選択されている場合は、そのspecを優先し、この値へ暗黙に戻さない。追加・変更・削除は `07-lt-design-system-manager` を使う。

## Tokens

```css
:root {
  --bg: #ffffff;
  --navy: #001b4d;
  --green: #00a83b;
  --deep-green: #008f32;
  --blue: #1d74e8;
  --cyan: #17b8c8;
  --green-soft: #eaf8ef;
  --blue-soft: #eef6ff;
  --line: #d8e6f3;
  --muted: #5d6b82;
  --shadow: 0 22px 50px rgba(0, 27, 77, .12);
}
```

## Typography

- Cover: 88 to 120px, weight 900
- Slide title: 56 to 76px, weight 900
- Strong statement: 42 to 60px, weight 850 to 900
- Card heading: 30 to 38px, weight 800 to 900
- Body: 28 to 34px, weight 600 to 750
- Supporting text: 22 to 26px
- Source and page: 18 to 22px

For 20+ minute explanatory decks, use a denser technical mode:

- Slide title: 44 to 56px
- Body: 24 to 30px
- Table, code, config, and diagram annotations: 18 to 22px
- Statement layouts may keep larger type, but they are transitions rather than the default page template

Technical mode is not permission to paste long prose. It exists so a concrete table, code/config excerpt, annotated screenshot, or decision flow can occupy 60 to 85 percent of the safe content area at a readable size.

Use system fonts only. Keep Japanese line-height between 1.3 and 1.55.

## Components

- `brand-badge`: top-left, outside title zone
- `gradient-line`: 180 to 240px wide, 7 to 9px high
- `card`: 18 to 24px radius, 2px border, soft shadow
- `icon-disc`: 64 to 80px square with inline SVG
- `conclusion-bar`: dedicated rounded zone, never overlay the visual
- `page-number`: bottom-right
- `section-label`: bottom-left when useful
- `source-note`: non-visual `data-source-note`; do not reserve a center footer column for it

Do not render internal slide IDs such as `s01` / `sXX`. Keep them only in `data-slide-id`. The routine footer has at most a left section label and a right page number; a center system title, source filename, or document title is forbidden.

## Spatial Safety

- Browser projection keeps an outer viewport gutter: minimum 32px, recommended 48px on all sides.
- The runtime `fit()` calculation subtracts this gutter before computing `scale()`.
- The gutter is for screen display only. Print/PDF resets body padding to 0 and uses the exact 16:9 page.
- Readable slide text should stay inside `x=64..1216` and `y=88..636` whenever possible.
- The only routine exceptions are `brand-badge`, footer, page number, and background decoration.
- If a large heading feels too close to an edge, reduce words, move the zone inward, or change layout. Do not rely on browser clipping or hidden overflow.

## Background

Use a faint 40px grid and one or two translucent circles or curves. Background decorations must use `pointer-events:none`, stay below content, and never reduce text contrast.

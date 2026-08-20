# LT design-system.yaml schema

```yaml
schema_version: 1
kind: lt-design-system
id: trustworthy-blue
name: Trustworthy Blue
version: 1.0.0
description: "技術発表向けの明るく信頼感のあるテーマ"
personality: [trustworthy, technical]
tokens:
  canvas: {width: 1280, height: 720, safe_margin: 48}
  colors:
    background: "#FFFFFF"
    surface: "#F5F9FF"
    text: "#08224A"
    muted_text: "#52637A"
    primary: "#135FCA"
    secondary: "#007F74"
    accent: "#B64700"
    border: "#C9D7EA"
    success: "#08783E"
    warning: "#9A5B00"
    danger: "#B42318"
  typography:
    family: "system-ui, -apple-system, Segoe UI, Noto Sans JP, sans-serif"
    mono_family: "ui-monospace, SFMono-Regular, Consolas, monospace"
    title_px: 68
    heading_px: 48
    body_px: 30
    detail_px: 24
    source_px: 18
    title_weight: 900
    body_weight: 600
  spacing: {xs: 8, sm: 16, md: 24, lg: 40, xl: 64}
  shape: {radius_small: 10, radius_card: 22, border_px: 2}
  shadow: {card: "0 20px 48px rgba(8,34,74,.14)"}
layouts:
  density: standard
  preferred: [visual-right, comparison, flow, evidence]
  max_columns: 3
components:
  card: {surface_token: surface, border_token: border}
  table: {header_token: primary, stripe: true}
  code: {background: "#07162C", text: "#ECF4FF"}
  conclusion: {background_token: primary, text: "#FFFFFF"}
motion:
  energy: standard
  preferred_families: [quiet-reveal, direction, structure, focus]
  strong_moment_limit_percent: 20
  duration_ms: {fast: 280, standard: 520, emphasis: 720}
  easing: "cubic-bezier(.2,.75,.25,1)"
accessibility:
  body_contrast_min: 4.5
  large_text_contrast_min: 3.0
  reduced_motion: true
  color_only_meaning: false
usage:
  do: ["表とコードの具体物を主役にする"]
  dont: ["低コントラストの細字を使わない"]
```

`id` は小文字英数字とハイフン、`version` はmajor.minor.patch。canvasは1280x720、safe marginは40以上。body 24px以上、source 16px以上。background/text、surface/text、primary上の結論文字、code背景/code文字をcontrast検証する。reduced motionはtrue、color-only meaningはfalse。motionの強い演出上限は0〜25%。

registryの各entryは `id`, `name`, `version`, `status`, `path`, `description`, `tags`, `created_at`, `updated_at` を持つ。statusは `active`, `draft`, `deprecated` のいずれか。

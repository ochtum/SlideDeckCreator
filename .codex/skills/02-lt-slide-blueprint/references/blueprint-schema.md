# .lt-slide-work/02-blueprint.yaml schema

座標は1280x720の左上原点。ゾーンは `{x, y, w, h}` で表す。

```yaml
schema_version: 1
source_story: "./01-story.yaml"
canvas:
  width: 1280
  height: 720
  safe_margin: 48
theme:
  style: business-tech
  colors:
    navy: "#001B4D"
    green: "#00A83B"
    blue: "#1D74E8"
    cyan: "#17B8C8"
    background: "#FFFFFF"
  typography:
    family: "system-ui, -apple-system, Segoe UI, Noto Sans JP, sans-serif"
    title_px: 66
    body_px: 30
slides:
  - id: s03
    role: conclusion
    reader_context: "このページだけを読む人のための前提"
    narrative_continuity:
      prior_state: "直前までに分かっていること"
      bridge: "このページが必要になる理由"
      next_question: "次ページが答える問い"
    spoken_note: "このスライドで口頭説明する内容。投影面には表示しない"
    layout: visual-right
    title: "今日の結論"
    message: "短い主張"
    text:
      bullets: []
      source_note: ""
    zones:
      title_zone: {x: 64, y: 78, w: 1152, h: 96}
      text_zone: {x: 64, y: 202, w: 500, h: 340}
      visual_zone: {x: 620, y: 190, w: 560, h: 350}
      conclusion_zone: {x: 160, y: 568, w: 960, h: 70}
      footer_zone: {x: 48, y: 660, w: 1184, h: 44}
    typography:
      title_px: 66
      message_px: 44
      body_px: 30
      source_px: 18
    visual:
      kind: generated-image
      pattern: transformation
      asset_id: visual-s03
      visual_plan_id: plan-s04-impact
      source_asset_ids: [source-fig-01]
      aspect_ratio: "8:5"
      transparent_background: true
      embedded_text: false
      alt: "変化を示す抽象的な図解"
    animation:
      entrance:
        - target: title
          preset: rise
          delay_ms: 0
      steps:
        - step: 1
          targets: [visual]
          preset: pop
        - step: 2
          targets: [conclusion]
          preset: stomp
    text_budget:
      title_max_chars: 24
      message_max_chars: 42
      bullets_max: 3
      bullet_max_chars: 24
    notes: "実装上の注意"
    content_model:
      type: implementation-playbook # table, flow, implementation-playbook, checklist, code, config, comparison, file-map
      source_artifacts: [artifact-1]
      data:
        steps:
          - label: "題材選定"
            artifact: "変更候補リスト"
            owner: "人"
            done_when: "影響範囲を限定できる"
visual_assets:
  - asset_id: visual-s03
    slide_id: s03
    required: true
    output: "visuals/visual-s03.png"
```

`visual.kind` は `none`, `css-component`, `inline-svg`, `generated-image`, `provided-image` から選ぶ。`generated-image` と `provided-image` は必ず `visual_assets` に列挙する。

全スライドに `spoken_note` を置き、`01-story.yaml` の同じIDから内容を変更せず引き継ぐ。ノートがない場合も空文字でキーを残す。

`reader_context` と `narrative_continuity` は `01-story.yaml` の同じIDから引き継ぐ。初見者に必要な定義・具体例は、`text` または非空の `content_model` に置く。`bridge` は投影面に常設する必要はないが、発表者ノートと発表者ビューで失われないようにする。

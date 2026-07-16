# .lt-slide-work/02-blueprint.yaml schema

座標は1280x720の左上原点。ゾーンは `{x, y, w, h}` で表す。

```yaml
schema_version: 1
source_story: "./01-story.yaml"
design_system:
  id: trustworthy-blue
  version: 1.0.0
  registry: "../config/design-systems/registry.yaml"
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
    source_unit_ids: ["implementation-section-001"]
    role: conclusion
    reader_context: "このページだけを読む人のための前提"
    narrative_continuity:
      prior_state: "直前までに分かっていること"
      bridge: "このページが必要になる理由"
      next_question: "次ページが答える問い"
    phase_context:
      audience_question: "このphaseで聴衆が抱く問い"
      answer: "このphaseの一文回答"
      transition_to_next: "次phaseへ渡す一言"
    speaker_cue:
      purpose: "このページが発表全体で果たす役割"
      audience_state_before: "表示前の聴衆の理解・疑問"
      audience_state_after: "説明後に聴衆が言えること"
      script: "Storyから変更せず引き継ぐ台本"
      point_at: ["App.DefaultPageSize", "ProductService"]
      transition: "Storyから変更せず引き継ぐ次の一言"
    spoken_note: |-
      橋渡し: Storyから変更せず引き継ぐ
      話す内容: Storyから変更せず引き継ぐ
      指差し: App.DefaultPageSize / ProductService
      次の一言: Storyから変更せず引き継ぐ
    delivery:
      mode: explain
      estimated_seconds: 75
      talking_points: ["設定値の読み取り経路", "変更前に確認する条件"]
      visible_anchors: ["App.DefaultPageSize", "ProductService"]
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
      intent: "構造を先に見せ、最後に判断へ注目させる"
      family: structure # quiet-reveal, direction, structure, focus, decision
      selection:
        rule_id: content:implementation-playbook
        role: conclusion
        content_type: implementation-playbook
        phase_entry: false
        rationale: "作業対象を順に切り替え、最後の行動へ焦点を移す"
      entrance:
        - target: title
          preset: rise
          reason: "本文より先にタイトルを表示する"
          delay_ms: 0
      steps:
        - step: 1
          targets: [visual]
          preset: pop
          reason: "主役の具体物へ焦点を移す"
          target_presets: {visual: pop}
          target_reasons: {visual: "主役の具体物"}
        - step: 2
          targets: [conclusion]
          preset: stomp
          reason: "最終行動を確定する"
          target_presets: {conclusion: stomp}
          target_reasons: {conclusion: "最終行動"}
      sequence:
        mode: staged
        initial_targets: [title, message]
        ordered_targets: [visual, conclusion]
        completion_targets: [conclusion]
        order_basis: narrative
        spatial_fallback: z-flow
        coverage: all-meaningful-siblings
        max_steps: 2
    text_budget:
      title_max_chars: 24
      message_max_chars: 42
      bullets_max: 3
      bullet_max_chars: 24
    notes: "実装上の注意"
    content_model:
      type: implementation-playbook # table, flow, implementation-playbook, checklist, code, config, comparison, file-map
      source_artifacts: [artifact-1]
      focus: "App.DefaultPageSize がどこで読まれるか"
      highlight: ["App.DefaultPageSize", "ProductService"]
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

全スライドに `speaker_cue` と `spoken_note` を置き、`01-story.yaml` の同じIDから内容を変更せず引き継ぐ。talkability v2では空文字を許可しない。

`flow_phase` を持つページは、`narrative.question_spine` の同じphaseから `audience_question`、`answer`、`transition_to_next` を `phase_context` へ変更せず引き継ぐ。

20分以上では `delivery` も同じIDのStoryから変更せず引き継ぐ。`visible_anchors` は `text`、`content_model`、`visual.annotations` のいずれかへ実際に配置する。同一の `content_model.data` を再利用するときは、ページごとに異なる `focus` と `highlight` を持たせる。

`reader_context` と `narrative_continuity` は `01-story.yaml` の同じIDから引き継ぐ。初見者に必要な定義・具体例は、`text` または非空の `content_model` に置く。`bridge` は投影面に常設する必要はないが、発表者ノートと発表者ビューで失われないようにする。

`speaker_cue.point_at` は `delivery.visible_anchors`、`text`、`content_model`、`visual.annotations` のいずれかに読める文字列として存在させる。生成画像内の不確かな文字、座標だけの「ここ」、実装されていないラベルは不可。

`animation` の正本は `motion-choreography.md` とする。最終HTMLへ `preset` を同名の `data-anim` として引き継ぎ、一律 `rise` へ正規化しない。本編20枚以上ではデッキ全体のpreset、family、step数、連続signatureの分布を検査する。

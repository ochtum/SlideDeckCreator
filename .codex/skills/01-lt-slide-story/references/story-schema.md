# .lt-slide-work/01-story.yaml schema

次のキーをこの順で使う。YAML文字列は必要に応じて引用する。

```yaml
schema_version: 1
project:
  title: "発表タイトル"
  subtitle: "任意"
  language: ja
  duration_minutes: 5
  target_slide_count: 10
  work_dir: "../.lt-slide-work"
  output_dir: "../output"
source:
  mode: markdown
  title: "元資料タイトル"
  refs:
    - url: "https://example.com"
      checked_at: "YYYY-MM-DD"
      purpose: "数値の根拠"
content_inventory:
  facts:
    - id: fact-1
      text: "入力から抽出した事実"
      evidence_refs: []
  claims:
    - id: claim-1
      text: "入力から抽出した主張"
      evidence_refs: []
  procedures:
    - id: step-1
      text: "入力から抽出した手順"
      evidence_refs: []
  demo_candidates:
    - id: demo-1
      text: "実演できる内容"
      evidence_refs: []
  cautions:
    - id: caution-1
      text: "注意点や制約"
      evidence_refs: []
audience:
  profile: "想定聴衆"
  prior_knowledge: "前提知識"
  desired_action: "発表後の最初の一手"
story:
  core_claim: "全体の主張を一文で"
  tension: "聴衆が抱える問題"
  resolution: "発表が示す解決"
  tone: business-tech
narrative:
  goal: "聴衆が何を理解し、何を試せる状態になるか"
  omitted_phases: []
  flow:
    - phase: why
      purpose: "なぜこの話を聞く必要があるか"
      key_message: "Whyの中心メッセージ"
      source_items:
        - fact-1
      reason: ""
    - phase: what
      purpose: "それは何か"
      key_message: "Whatの中心メッセージ"
      source_items:
        - claim-1
      reason: ""
    - phase: how
      purpose: "どう使うか"
      key_message: "Howの中心メッセージ"
      source_items:
        - step-1
      reason: ""
    - phase: demo
      purpose: "実際に見せる"
      key_message: "Demoの中心メッセージ"
      source_items:
        - demo-1
      reason: ""
    - phase: takeaway
      purpose: "明日から何をするか"
      key_message: "Takeawayの中心メッセージ"
      source_items:
        - caution-1
      reason: ""
presenter:
  include: true
  data_file: "../config/presenter.json"
slides:
  - id: s01
    role: cover
    flow_phase: ""
    title: "短いタイトル"
    message: "この1枚で伝える唯一のこと"
    support:
      - "補助点は最大3つ"
    evidence_refs: []
    spoken_note: "画面には置かない口頭説明"
  - id: s02
    role: profile
    flow_phase: ""
    title: "自己紹介"
    message: "誰がなぜ話すのか"
    support: []
    evidence_refs: []
    spoken_note: ""
  - id: s03
    role: goal
    flow_phase: ""
    title: "今日のゴール"
    message: "聴衆への約束"
    support: []
    evidence_refs: []
    spoken_note: ""
  - id: s04
    role: problem
    flow_phase: why
    title: "なぜ必要か"
    message: "Whyの中心メッセージ"
    support: []
    evidence_refs: []
    spoken_note: ""
  - id: s99
    role: recap
    flow_phase: takeaway
    title: "まとめ"
    message: "今日のゴールとTakeawayを回収する"
    support:
      - "要点1"
      - "要点2"
      - "要点3"
    evidence_refs: []
    spoken_note: ""
  - id: s100
    role: thanks
    flow_phase: ""
    title: "Thank you"
    message: "終了"
    support: []
    evidence_refs: []
    spoken_note: ""
open_questions: []
```

`role` は `cover`, `profile`, `goal`, `conclusion`, `problem`, `comparison`, `list`, `flow`, `matrix`, `evidence`, `action`, `demo`, `recap`, `thanks` から選ぶ。自己紹介なしの場合は `profile` を省く。

`flow_phase` は `why`, `what`, `how`, `demo`, `takeaway` から選ぶ。表紙、自己紹介、今日のゴール、サンクスなど話法上のphaseに属さないスライドは空文字にする。`recap` は新情報を持たず、原則として `takeaway` を回収する。

`omitted_phases` は標準phaseを省略した場合だけ `{phase, reason}` で記録する。省略がなければ空配列にする。

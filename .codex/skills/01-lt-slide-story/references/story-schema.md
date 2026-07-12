# .lt-slide-work/01-story.yaml schema

これは単発デッキ、またはシリーズの各パート用の schema version 1 である。シリーズ全体を判定・分割する場合は、先に `series-schema.md` の schema version 2 マニフェストをルートの `01-story.yaml` に置き、ここで定義する形式を各 `parts/<part-id>/01-story.yaml` に使う。

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
source_asset_inventory:
  - asset_id: source-fig-01
    kind: provided-image # provided-image, table, code, config, flow
    source_ref: "input/diagram.png"
    meaning: "変更範囲の関係"
    usage_rights: reference-only # provided-for-reuse, reference-only, unknown
    decision: adopt # adopt, replace, omit
    decision_reason: "関係性を説明する主役なのでSVGへ再構成する"
visual_plan:
  - plan_id: plan-s04-impact
    slide_id: s04
    need: required # required, optional, none
    purpose: "変更範囲の関係を一目で示す"
    source_asset_ids: [source-fig-01]
    implementation: inline-svg # provided-image, inline-svg, html-table, html-code, generated-image, none
    decision_reason: "文字と矢印の正確さを保つため"
    status: planned # planned, resolved, blocked
content_inventory:
  evidence_artifacts:
    - id: artifact-1
      type: table # table, flow, checklist, code, config, comparison, file-map
      title: "設定キー対応表"
      source_items: [fact-1, step-1]
      evidence_refs: []
      payload:
        columns: ["設定キー", "使用箇所", "変更条件"]
        rows:
          - ["App.DefaultPageSize", "ProductService", "影響確認後に変更"]
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
  first_time_listener: "初見者が置かれた具体的な状況"
  known_terms: ["既知としてよい用語"]
  terms_to_define:
    - term: "初出の用語"
      plain_definition: "平易な一言の定義"
      example: "身近な具体例"
  misconceptions: ["避けるべき誤解"]
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
    evidence_artifact_ids: [artifact-1]
    reader_context: "このページだけを読む人のための前提"
    connection_from_previous:
      prior_state: "直前までに分かっていること"
      bridge: "このページが次に必要になる理由"
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

`project.target_slide_count` は本編だけを数える。`cover`、`profile`、`thanks` は除き、`recap` は含める。指定時間の下限は5分: 8枚、10分: 12枚、15分: 18枚、16〜29分: 23枚、30分以上: 28枚である。`scripts/validate_duration_floor.py --story <01-story.yaml>` が成功するまで、この正本を後工程へ渡してはならない。

`flow_phase` は `why`, `what`, `how`, `demo`, `takeaway` から選ぶ。表紙、自己紹介、今日のゴール、サンクスなど話法上のphaseに属さないスライドは空文字にする。`recap` は新情報を持たず、原則として `takeaway` を回収する。

`reader_context` は後から一枚だけを読む人に必要な前提または現在地を短く記録する。`connection_from_previous.prior_state` と `bridge` は前ページからの論理的接続を記録する。表紙、自己紹介、Thanksは空文字または省略してよいが、その他のスライドでは両方を必須とする。

`omitted_phases` は標準phaseを省略した場合だけ `{phase, reason}` で記録する。省略がなければ空配列にする。

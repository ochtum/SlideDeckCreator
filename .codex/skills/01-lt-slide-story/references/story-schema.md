# .lt-slide-work/01-story.yaml schema

これは単発デッキ、またはシリーズの各パート用の schema version 1 である。シリーズ全体を判定・分割する場合は、先に `series-schema.md` の schema version 2 マニフェストをルートの `01-story.yaml` に置き、ここで定義する形式を各 `parts/<part-id>/01-story.yaml` に使う。

次のキーをこの順で使う。YAML文字列は必要に応じて引用する。

```yaml
schema_version: 1
project:
  title: "発表タイトル"
  subtitle: "任意"
  language: ja
  duration_minutes: 30
  content_fidelity: full-equivalence # overview, representative, full-equivalence
  talkability_version: 2 # 20分以上で必須
  target_slide_count: 20
  time_budget: # 20分以上で必須
    content_seconds: 1260
    demo_seconds: 300
    interaction_seconds: 120
    buffer_seconds: 120
  work_dir: "../.lt-slide-work"
  output_dir: "../output"
source:
  mode: markdown
  title: "元資料タイトル"
  refs:
    - url: "https://example.com"
      checked_at: "YYYY-MM-DD"
      purpose: "数値の根拠"
source_inventory: "./source-inventory.yaml"
coverage_matrix:
  - unit_id: "implementation-section-001"
    parts: ["part-01"]
    slide_ids: ["s04", "s05"]
    delivery_surfaces: [visible, spoken]
    preservation: explain # explain, example-preserved, structure-preserved, exact, reconstructed
    artifact_ids: []
    status: covered
approved_omissions: [] # ユーザーが範囲縮小を明示承認した場合だけ使用する
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
roadmap: # 30分以上または本編20枚超で必須。slides確定後に生成する
  source: generated-from-slides
  slide_id: s04
  items:
    - phase: why # 内部分類。これだけを可視ラベルにしない
      label: "判断できない理由"
      summary: "コード外の知識と人・AIの境界"
      slide_ids: [s05, s06, s07, s08]
      page_start: 5
      page_end: 8
      start_title: "コードだけでは変更可否が分からない"
      end_title: "人とAIの担当境界を決める"
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
  central_example: "最初から最後まで追う一つの具体例"
  opening_problem: "冒頭で聴衆が自分事として認識する困りごと"
  final_change: "終了時に聴衆ができるようになる変化"
  framing_seconds: 120
  omitted_phases: []
  question_spine:
    - phase: why
      audience_question: "なぜ必要なのか？"
      answer: "Whyを聞き終えた時の一文回答"
      transition_to_next: "では、解決策の正体を見ます。"
      time_seconds: 240
      source_items: [fact-1]
    - phase: what
      audience_question: "解決策は何なのか？"
      answer: "Whatを聞き終えた時の一文回答"
      transition_to_next: "正体が分かったので、使い方へ進みます。"
      time_seconds: 300
      source_items: [claim-1]
    - phase: how
      audience_question: "どう使い始めるのか？"
      answer: "Howを聞き終えた時の一文回答"
      transition_to_next: "手順が本当に動くか、同じ例で実演します。"
      time_seconds: 480
      source_items: [step-1]
    - phase: demo
      audience_question: "実際に何が起きるのか？"
      answer: "観測できる結果を含む一文回答"
      transition_to_next: "見えた変化を、明日の一手へ縮めます。"
      time_seconds: 360
      source_items: [demo-1]
    - phase: takeaway
      audience_question: "明日、最初に何をするのか？"
      answer: "時間・成果物・完了条件を含む一文回答"
      transition_to_next: "この一手から始めてください。"
      time_seconds: 180
      source_items: [caution-1]
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
demo_runbook:
  starting_state: "対象ファイルと実行前の値が画面に見えている"
  steps:
    - action: "対象ファイルの設定値を一つ変更する"
      visible_result: "差分表示に変更前後の値が一行ずつ現れる"
      talk_line: "変更は一か所だけです。まず差分を見てください。"
    - action: "検証コマンドを実行する"
      visible_result: "対象テスト名と成功件数が端末に表示される"
      talk_line: "次に、この変更へ直接関係する検証だけを実行します。"
    - action: "完了条件と実行結果を照合する"
      visible_result: "チェック項目が未完了から完了へ変わる"
      talk_line: "出力があるだけでなく、最初に決めた完了条件へ戻ります。"
  end_state: "差分、検証結果、完了条件の三つが同じ画面で追える"
  fallback: "同じ操作の差分画像と実行ログを順に表示する"
  source_items: [demo-1]
tomorrow_action:
  timebox: "15分"
  action: "自分の題材で最小の変更候補を一件書き出す"
  artifact: "変更候補、確認方法、完了条件を持つ一枚のメモ"
  done_when: "別の人がメモだけで実行前の判断を説明できる"
  first_step: "作業中のリポジトリで最近触ったファイルを一つ開く"
presenter:
  include: true
  data_file: "../config/presenter.json"
design_system:
  id: trustworthy-blue
  version: 1.0.0
  registry: "../config/design-systems/registry.yaml"
style_profile:
  data_file: "../config/slide-style-profile.md"
  status: applied # applied, absent
  applied_rule_ids: [experiment-turn]
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
    source_unit_ids: ["implementation-section-001"]
    reader_context: "このページだけを読む人のための前提"
    connection_from_previous:
      prior_state: "直前までに分かっていること"
      bridge: "このページが次に必要になる理由"
    delivery: # 20分以上で必須
      mode: explain # explain, demo, interaction, transition, recap
      estimated_seconds: 60
      talking_points:
        - "画面には収めないが、このページで必ず説明する仕組み"
        - "代表例のどこを見て何を判断するか"
      visible_anchors:
        - "App.DefaultPageSize"
        - "影響確認後に変更"
    speaker_cue:
      purpose: "このページが発表全体で果たす役割"
      audience_state_before: "表示前に聴衆が分からないこと"
      audience_state_after: "説明後に聴衆が言えること"
      script: "そのまま話せる自然な複数文の説明。理由、具体例、判断を含める。"
      point_at: ["App.DefaultPageSize", "影響確認後に変更"]
      transition: "このページの最後に言って次へ渡す一文"
    spoken_note: |-
      橋渡し: このページが次に必要になる理由
      話す内容: そのまま話せる自然な複数文の説明。理由、具体例、判断を含める。
      指差し: App.DefaultPageSize / 影響確認後に変更
      次の一言: このページの最後に言って次へ渡す一文
  - id: s02
    role: profile
    flow_phase: ""
    title: "自己紹介"
    message: "presenter.jsonのbioと同じ文字列"
    support: ["presenter.jsonのdisplay_name", "presenter.jsonのbio", "presenter.jsonのlinks"]
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

`roadmap.items` は後続のphase付きスライドを順序どおり、重複も欠落もなく覆う。各項目の `slide_ids` は連続していなければならず、`page_start` / `page_end` は `slides` の物理位置、`start_title` / `end_title` は範囲の実タイトルと一致させる。道筋スライド自身の `content_model.data.steps` には同じitemsをそのまま置く。ページ追加・削除・並べ替え後は手修正ではなく `slides` から再生成する。

`narrative` の直後に `demo_runbook` と `tomorrow_action` を置く。形式と記述基準は `talkability.md` を正本とする。20分以上では両方必須である。

`role` は `cover`, `profile`, `goal`, `conclusion`, `problem`, `comparison`, `list`, `flow`, `matrix`, `evidence`, `action`, `demo`, `recap`, `thanks` から選ぶ。自己紹介なしの場合は `profile` を省く。

`role: profile` の投影面は `presenter.data_file` の `display_name`、`bio`、全 `links`、QRラベル、使用を許可された画像だけを表示する。発表テーマに合わせた結論帯、補足コピー、実績、意気込みをStoryから追加しない。テーマへの橋渡しは `speaker_cue.script` と `spoken_note` にだけ置く。

`project.target_slide_count` は本編だけを数える。`cover`、`profile`、`thanks` は除き、`recap` は含める。安全下限は5分: 6枚、10分: 8枚、15分: 10枚、16〜29分: 14枚、30分以上: 16枚である。30分は18〜24枚を標準範囲とするが、問い・例・実演・完了条件から見積もり、枚数自体を目標にしない。`scripts/validate_duration_floor.py --story <01-story.yaml>` が成功するまで、この正本を後工程へ渡してはならない。

20分以上では `project.time_budget` と各本編スライドの `delivery` を必須とする。time budgetは発表時間と一致し、スライドの `estimated_seconds` 合計はbufferを除いた秒数と一致させる。通常ページは具体的な `talking_points` と、最終HTMLで読める `visible_anchors` を各2件以上持つ。詳細は `explanation-depth.md` に従い、`scripts/validate_explanation_depth.py --story <01-story.yaml>` が成功するまで次工程へ渡さない。

20分以上では `project.talkability_version: 2`、`narrative.question_spine`、`demo_runbook`、`tomorrow_action`、全スライドの `speaker_cue` と四行 `spoken_note` を必須とする。詳細は `talkability.md` に従い、`scripts/validate_talkability.py --story <01-story.yaml>` が成功するまで次工程へ渡さない。

`flow_phase` は `why`, `what`, `how`, `demo`, `takeaway` から選ぶ。表紙、自己紹介、今日のゴール、サンクスなど話法上のphaseに属さないスライドは空文字にする。`recap` は新情報を持たず、原則として `takeaway` を回収する。

`reader_context` は後から一枚だけを読む人に必要な前提または現在地を短く記録する。`connection_from_previous.prior_state` と `bridge` は前ページからの論理的接続を記録する。表紙、自己紹介、Thanksは空文字または省略してよいが、その他のスライドでは両方を必須とする。

`omitted_phases` は標準phaseを省略した場合だけ `{phase, reason}` で記録する。省略がなければ空配列にする。

`style_profile` は `config/slide-style-profile.md` がある場合だけそのルールを参照したことを記録する。スタイルを理由に入力にない体験を追加しない。ファイルがない場合は `data_file` を残して `status: absent`、`applied_rule_ids: []` とする。

`full-equivalence` では `source_inventory`、`coverage_matrix`、`approved_omissions`、各スライドの `source_unit_ids` が必須である。正本は `content-equivalence.md` とし、表・コード・設定・図などの構造化unitには `artifact_ids` と構造保存方法を必ず指定する。

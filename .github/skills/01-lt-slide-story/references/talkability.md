# Talkability contract

この契約は、スライドを見てもノートを見ても話し方が浮かばない状態を防ぐ。投影面の文字量を増やす契約ではない。発表全体の問い、各phaseの答え、実演で見える変化、各ページの口頭説明を、後工程が失わないデータにする。

## 1. 発表全体の問いの背骨

20分以上では `project.talkability_version: 2` を置き、`narrative.phase_order` と同じ順序の `question_spine` を必須とする。以下はfallbackの一例であり、記事入力では `knowledge-structure.md` のarchetypeを優先する。

```yaml
narrative:
  central_example: "最初から最後まで追う一つの具体例"
  opening_problem: "冒頭で聴衆が自分事として認識する困りごと"
  final_change: "終了時に聴衆が理解・実行できるようになる変化"
  framing_seconds: 120
  question_spine:
    - phase: why
      audience_question: "なぜ今までのやり方では困るのか？"
      answer: "このphaseを聞き終えた時の一文回答"
      transition_to_next: "では、解決策の正体は何かを見ます。"
      time_seconds: 240
      source_items: [fact-1]
    - phase: what
      audience_question: "それは何なのか？"
      answer: "一文回答"
      transition_to_next: "正体が分かったので、作り方へ進みます。"
      time_seconds: 300
      source_items: [claim-1]
    - phase: how
      audience_question: "どう使い始めるのか？"
      answer: "一文回答"
      transition_to_next: "手順が本当に動くか、同じ例で実演します。"
      time_seconds: 480
      source_items: [step-1]
    - phase: demo
      audience_question: "実際に何が起きるのか？"
      answer: "観測できる変化を含む一文回答"
      transition_to_next: "見えた変化を、明日の一手へ縮めます。"
      time_seconds: 360
      source_items: [demo-1]
    - phase: takeaway
      audience_question: "明日、最初に何をするのか？"
      answer: "時間・成果物・完了条件を含む一文回答"
      transition_to_next: "この一手から始めてください。"
      time_seconds: 180
      source_items: [caution-1]
```

- `phase_order` がない旧Storyだけ Why / What / How / Demo / Takeaway を使う。記事種別に存在しないDemoや手順を捏造しない。
- `audience_question` は聴衆がその時点で抱く問い、`answer` はそのphaseを聞いた後に言える答えにする。
- `transition_to_next` は、前の答えから次の問いが必要になる理由を実際に口にできる文にする。
- `central_example` は可能な限り全phaseで同じ対象を追う。例を切り替える場合は、切り替える理由をページの橋渡しで明示する。
- `framing_seconds + question_spine.time_seconds` は、`project.time_budget` のQ&Aとbuffer以外と一致させる。各phaseの秒数は、そのphaseに属するlive本編スライドの `delivery.estimated_seconds` 合計と一致させる。
- すべてを均等な60秒ページにしない。定義は短く、比較・手順・実演は長くするなど、説明上の役割で配分する。

## 2. Demoは操作と観測で設計する

Demoを「構成を説明するページ」にしない。開始状態、操作、画面で確認できる結果、失敗時の代替を持つ。

```yaml
demo_runbook:
  starting_state: "実演開始時に開いているものと準備済みの状態"
  steps:
    - action: "話者が行う具体的な操作"
      visible_result: "聴衆が画面上で確認できる結果"
      talk_line: "操作中に実際に話す一言"
  end_state: "Demoが成功したと判断できる最終状態"
  fallback: "実演失敗時に見せるスクリーンショット、ログ、録画など"
  source_items: [demo-1]
```

Demo phaseを採用した20分以上の発表では3手順以上を原則とする。`visible_result` が「確認する」「理解する」だけの手順は不可。ファイル名、表示値、状態変化、出力、差分などを観測できるようにする。

## 3. Takeawayは明日の一手まで縮める

```yaml
tomorrow_action:
  timebox: "15分"
  action: "最初に行う具体的な操作"
  artifact: "終わった時に残るファイル、表、Issue、ログなど"
  done_when: "完了を判定できる条件"
  first_step: "PCを開いて最初に行う一操作"
```

「試してみる」「検討する」だけでは不可。時間枠、残る成果物、完了条件を必ず含める。

## 4. ページ単位の話者キュー

全スライドに `speaker_cue` を置く。これは説明の設計図であり、投影面にそのまま載せる文章ではない。appendix/referenceの台本は短くてよいが、そのページを開く条件と読み方を固有に書く。

```yaml
speaker_cue:
  purpose: "このページが発表全体で果たす役割"
  audience_state_before: "表示前の聴衆の理解・疑問"
  audience_state_after: "説明後に聴衆が言えること"
  script: "話者がそのまま話せる自然な説明。理由、具体例、判断を含める。"
  point_at: ["画面に実在するラベル", "具体的な値"]
  transition: "このページの最後に実際に言う一文"
spoken_note: |-
  橋渡し: 前ページからこのページが必要になる理由
  話す内容: speaker_cue.script と同じ文章
  指差し: 画面に実在するラベル / 具体的な値
  次の一言: speaker_cue.transition と同じ文章
```

- `script` はスライドの説明方法ではなく、発表で実際に口にする文章にする。「このページでは」「タイトルの通り」「表示内容を確認します」のようなメタ説明は禁止する。
- 45秒以上の本編ページは、理由・例・判断のうち二つ以上を含む複数文にする。目安は1分あたり90〜220字。長文を一息で読むのではなく、画面を指す位置と間を設計する。
- `point_at` は `delivery.visible_anchors` と対応させ、02で実在する文字・表セル・コード行・図のラベルにする。生成画像の中に埋め込んだ読めない文字を指差し対象にしない。
- cover / profile / thanks または真のtransitionだけは `point_at: [none]` を許可する。
- `audience_state_before` と `audience_state_after` が同じなら、そのページは不要か、説明目的が未設計である。
- `spoken_note` は上記4行を正本とし、01から06まで文字列を保持する。

## 5. 合格条件

`scripts/validate_talkability.py` は少なくとも次を機械判定する。

- 20分以上にarchetypeと問いの背骨がある。Demo phaseを採用した場合はDemo runbook、Takeaway phaseを採用した場合は明日の一手がある。
- phase時間、framing時間、ページ時間がtime budgetと一致する。
- 全ページに具体的で固有の話者キューと4行ノートがある。
- 指差し対象がStory、Blueprint、HTMLで失われていない。
- Blueprintが `speaker_cue` を変更していない。
- HTMLが `data-flow-phase`、`data-phase-question`、`data-speaker-purpose`、`data-spoken-note` を持つ。
- メタ説明テンプレート、完全重複ノート、観測不能なDemo、成果物のないTakeawayを不合格にする。

機械判定の合格は必要条件である。05ではノートだけを上から読み、発表の問い・答え・接続・実演・結論を再現できるかを人間の意味判断でも確認する。

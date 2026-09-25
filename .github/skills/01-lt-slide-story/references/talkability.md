# Talkability contract

この契約は、スライドを見てもノートを見ても話し方が浮かばない状態を防ぐ。投影面の文字量を増やす契約ではない。発表全体の問い、各phaseの答え、実演で見える変化、各ページの口頭説明を、後工程が失わないデータにする。

## 1. 発表全体の問いの背骨

新規作成では `project.talkability_version: 3` を使う。既存v1/v2は明示的に移行するまで維持する。20分以上では`narrative.phase_order` と同じ順序の `question_spine` を必須とする。以下はfallbackの一例であり、記事入力では `knowledge-structure.md` のarchetypeを優先する。

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
      transition_to_next: "実演で見えた変化を含めて、今日の要点を振り返ります。"
      time_seconds: 360
      source_items: [demo-1]
    - phase: takeaway
      audience_question: "今日の説明から何が分かったのか？"
      answer: "本文で説明した要点と結論を結び直す一文回答"
      transition_to_next: "最後に、発表全体で伝えたかった結論へ戻ります。"
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

## 3. 発表内容のまとめと任意の行動提案を分ける

まとめでは、発表済みの主要な内容・関係・結論を振り返る。各要点がどの本文ページの説明に対応するか確認する。`speaker_cue.recap_of` と `recap_reason` は、この対応と振り返る目的を記録するために使える。新しい課題や「明日15分」の作業を、まとめの代わりに追加しない。

`takeaway` は持ち帰る理解・判断を含み、行動提案を意味するとは限らない。ユーザーの希望や発表の目的に合って行動提案を採用する場合だけ、次の任意フィールドを設定する。設定した場合は、操作・成果物・完了条件を具体化する。

```yaml
tomorrow_action:
  timebox: "15分"
  action: "最初に行う具体的な操作"
  artifact: "終わった時に残るファイル、表、Issue、ログなど"
  done_when: "完了を判定できる条件"
  first_step: "PCを開いて最初に行う一操作"
```

行動提案を設定した場合は「試してみる」「検討する」だけでは不可。時間枠、残る成果物、完了条件を含める。設定しないまとめに、これらを捏造して埋めてはならない。

## 4. 短いメモを基本にする（v3）

`speaker_cue` のpurpose、audience_state_before/afterは設計用。発表者が読むノートには、そのページで補う説明だけを残す。`mode` は `cue`（既定）、`script`（台詞が必要）、`hybrid`（要点＋任意に開く発話例）。短いメモに最低文字数を設けず、時間から台詞を水増ししない。秒数は図を見る時間、操作、間、質問も含めて見積もる。

```yaml
project:
  talkability_version: 3
slides:
  - id: s15
    speaker_cue:
      mode: hybrid
      purpose: "資料一覧を見て、AGENTS.mdへ何を書くかを判断できるようにする"
      audience_state_before: "設計内容を全部AGENTS.mdへ入れるか迷っている"
      audience_state_after: "読む順序と共通ルールをAGENTS.mdに残すと説明できる"
      cues:
        - "全部入れると、最初に読む情報が埋もれる"
        - "読む順序と共通ルールに絞る"
      script: "全部入れると、最初に読む情報が埋もれるんですよね。ここには読む順序と共通ルールに絞って書きます。"
      point_at: ["AGENTS.md"]
    spoken_note: |-
      形式: hybrid
      要点: 全部入れると、最初に読む情報が埋もれる
      要点: 読む順序と共通ルールに絞る
      話す内容: 全部入れると、最初に読む情報が埋もれるんですよね。ここには読む順序と共通ルールに絞って書きます。
      指差し: AGENTS.md
```

この発話例は作成例であり、発表者の実際の発話ではない。

- `cues` は一つの思考または補足につき一項目。画面の表を全行読むリストにしない。要点は通常1〜3件を目安とし、内容に応じて調整する。
- `script` は実際に口に出す文。cueでは省略、script/hybridでは指定する。列挙を一文に連結しない。
- `point_at` は実在する `delivery.visible_anchors` を指定する。03/04で対応する文字・表セル・コード行が読める状態にする。
- `connection_from_previous.bridge` と `speaker_cue.transition` は必要な場合だけ指定する。transitionを指定したら `next_slide_id` も付け、実際の次ページIDに合わせる。最終ページに次の予告を置かない。設計用の前提 `prior_state` と、口に出すbridgeは分ける。
- 画面を読む時間だけ取るページは `mode: cue`、具体的な `silence_reason` と `point_at` を指定し、cues/script/bridge/transitionを省略する。空欄を放置したノートとは区別する。既存の `delivery.mode` はexplain等を使い、推定秒数に見る時間を含める。
- `spoken_note` は `scripts/speaker_notes.py` の `render_note(slide)` で生成する。`形式`、複数の `要点`、任意の `話す内容`、`指差し`、`橋渡し`、`次の一言`、`次のスライド`、`話さない理由` を1項目1行で保存する。値の中に改行を入れない。指差しが複数なら ` / ` で区切る。
- section-faithfulではbeatの `delivery: spoken` だけをcues/scriptへ含める。`delivery: visual` はvisible_textを必須にしてspoken_textは空にする。補足・出典はスライドの `delivery_scope` を使う。全内容の保持は、全内容の読み上げを意味しない。
- 同じ説明を意図的に振り返る場合だけ、任意の `speaker_cue.recap_of: [s01]` と `recap_reason` に、何を思い出してほしいかを残せる。自動チェックの警告を消すためだけに付けない。

## 5. 画面を見てノートを調整する

01で説明意図を作り、02で配置と表示内容を決めたら、画面とノートを同時に確認する。画面だけで伝わる説明を削り、追加する理由・判断を残す。変更はStoryのcue、該当beat、spoken_noteへ戻し、同じ変更をBlueprintへ反映してから再検証する。以後の工程は、この更新後のデータを一致させる。「最初の台本を永久に変更しない」という意味ではない。

機械検証は `validate_talkability.py` と `validate_spoken_notes.py`。時間、指す対象、次ページID、データ一致、未記入を確認する。v3のノートにv2の文字数下限・四区画の必須条件を適用しない。

05では `review_speaking.py` で語彙・長文・反復の確認候補を出し、スライドとメモを一緒に通して意味を確認する。自動チェック、エージェントによる意味確認、本人の通し練習を別々に報告する。短いメモから本人が自然に話せるかは、文字数や文字列一致では保証できない。

## 6. 旧形式の互換性

既存v1は「橋渡し／読み方／次の判断」、v2は「橋渡し／話す内容／指差し／次の一言」と既存のspeaker_cueを保持する。上位バージョン番号だけを付け替えない。移行する場合は全ページのcueとノートを作り直し、section-faithfulのbeatsに伝達方法を付け、Story・Blueprint・HTMLを同時に更新する。

# LT Slide Style Profile

## Metadata

- profile_version: 2
- updated_at: 2026-07-14
- evidence_count: 4
- independent_evidence_count: 3
- distinct_topic_count: 3
- oldest_evidence_date: 2025-09
- newest_evidence_date: 2026-06
- status: confirmed

## Presenter Stance

- 実際に試した人として、結論だけでなく検証過程と判断理由を共有する。
- 完成した答えを一方的に教えるより、初見者が追える実験・発見の流れを優先する。
- 実務評価では、使えた点だけでなく制約や人間が判断した箇所も残す。

## Narrative Patterns

- 実際の検証過程がある場合は、疑問、条件、試行、結果、実務判断の順を優先する。
- 失敗が学びに寄与する場合は、失敗、原因、再試行を分断せずにつなげる。
- 機能一覧から始めるより、なぜ試したか、何を確かめたかったかを先に示す。

## Heading And Voice

- 通常見出しは短くし、詳細解説へ移る場面だけ会話的な問いや転換を許可する。
- 感嘆符や三点リーダーは、実際の転換点がある場合だけ使用する。
- 技術説明の本文は、会話的な口調より正確性と具体性を優先する。

## Emotional Beats

- 感情の転換は、前後の具体的な情報と結び付くときだけ使う。
- 驚き、失敗、成功を示すページの直後には、原因、結果、次の操作のいずれかを置く。
- 内容がない場面で、期待を作るためだけの感情スライドを追加しない。

## Failure And Success

- 失敗は原因または次の操作とセットで扱う。
- AIだけで解決できず、人間が確認・判断した場合はその境界を明示する。
- 未解決の問題を成功したように見せない。

## Evidence And Specificity

- 技術説明では、入力、制約、数値、ファイル名、エラー、出力、成果物のうち少なくとも一つを残す。
- 「便利だった」「使えそう」で終わらず、何をして何が起きたかを示す。
- 検証条件と結果を混同せず、Before、操作、Afterを区別する。

## Visual Composition

- `composition`: 検証条件や比較は左右分割、手順はフロー、結果は実物または強い短文を優先する。
- `density`: 説明量の多いページの後に、問い、結果、転換など低密度ページを置く場合がある。
- `hierarchy`: 結論、実物、エラー、判断基準のいずれかを視覚的主役にする。
- `emphasis`: 強い短文や大きな文字は、実際の転換点または結論に限定する。
- `asset_usage`: スクリーンショット、コード、表、ファイル構成など、検証対象の具体物を優先する。
- `transition_slide`: 章区切り、問題発生、最終結果に限定する。
- `repetition`: 同一レイアウトや会話的見出しを連続させない。
- `pacing`: 説明、問い、実物、問題、原因、結果の密度差を使って流れを作る。
- `reader_flow`: 転換スライドの次には、具体的な条件、原因、操作、結果を置く。

## Speaker Notes

- 前ページからの橋渡しと、次に判断することをノートで補う。
- 投影面に載せない実体験、迷った理由、人間が判断した箇所を残す。
- 話者ノートの会話的な文章を、そのまま投影面の長文へ転用しない。

## Title And Surface Rules

- 発表タイトルは、検証対象または得られる学びが第三者に伝わることを優先する。
- 章タイトルは現在地が分かる表現にする。
- 通常見出しは、必要に応じて疑問、判断、気づきを短く示す。
- 転換スライドは、実際の問題、発見、成功、章切替がある場合に限定する。
- 投影面は短く具体的にし、補足や判断理由は話者ノートへ分離する。

## Negative Patterns

```yaml
- id: generic-corporate-summary
  applies_when: 結論、まとめ、価値説明を作成するとき
  avoid:
    - 革新的なソリューション
    - 生産性を最大化
    - 新たな価値を創出
  prefer: 実際に確認できた効果、制約、使える場面を具体的に示す
  reason: 発表者の実測・検証中心の表現と合わない
  evidence_basis:
    type: quality-policy

- id: generic-three-card-reduction
  applies_when: 表、フロー、設定、実装手順を説明するとき
  avoid:
    - 内容を抽象的な3枚のカードだけへ還元する
  prefer: 実際の列、工程、ファイル名、入力、出力、判断ゲートを示す
  reason: 再現性に必要な具体物が失われる
  evidence_basis:
    type: quality-policy
```

## Profile Evolution

- `test-arc` と `concrete-evidence` は、複数テーマ・複数時期で確認できるため `stable` とする。
- `failure-transition-slide` は検証型LTでのみ有効なため `contextual` とする。
- 顔文字は過去資料で確認できるが、最近の資料で継続性が不足するため恒常ルールへ昇格させない。
- 新しい資料1件だけで、既存の `stable` ルールを変更しない。

## Reusable Patterns

```yaml
- id: test-arc
  scope: shared
  status: stable

  observation:
    description: 実際の検証過程がある資料では、試した理由、条件、操作、結果、判断を順に示す
    occurrences: 4
    distinct_topics: 3
    distinct_periods: 3
    confidence: high

  interpretation:
    role: experiment-narrative
    purpose: 機能紹介ではなく、検証から得た学びとして伝える

  application:
    strength: MUST
    applies_when: 入力に実際の検証過程がある
    guidance: 試した理由、条件、最初の操作、結果、実務判断を時系列でつなげる
    next_slide: 実行結果、次に試した操作、または実務上の判断
    limits:
      fabricate_steps: false
      omit_important_failure: false

  evidence_basis:
    type: observed-pattern

  evidence:
    - deck-a
    - deck-b
    - deck-c
    - deck-d

- id: transition-heading
  scope: shared
  status: stable

  observation:
    description: 詳細解説へ移る前に、短い会話的見出しで次の問いを示す
    occurrences: 3
    distinct_topics: 3
    distinct_periods: 2
    confidence: high

  interpretation:
    role: explanation-transition
    purpose: 説明の切替を明確にし、次に見る具体物へ注意を向ける

  application:
    strength: SHOULD
    applies_when: 抽象説明から表、フロー、設定、コードなどの具体物へ移る
    guidance: 短い会話的見出しで次の問いを示す
    next_slide: 表、フロー、設定、コード、またはスクリーンショット
    limits:
      max_ratio_of_main_slides: 0.25
      max_consecutive_usage: 1
      min_distance_between_uses: 2

  evidence_basis:
    type: observed-pattern

  evidence:
    - deck-a
    - deck-b
    - deck-d

- id: failure-transition-slide
  scope: candidate
  status: contextual

  observation:
    description: 検証中の重要な失敗を短い独立スライドで示す
    occurrences: 2
    distinct_topics: 2
    distinct_periods: 2
    confidence: medium

  interpretation:
    role: failure-transition
    purpose: 問題の発生を明確にし、原因調査へ切り替える

  application:
    strength: MAY
    applies_when: 実際の失敗が発表の学びに直接つながる
    guidance: 問題の存在を短く示し、直後に原因、エラー、次の操作のいずれかを示す
    next_slide: 原因、エラー、または再試行
    limits:
      max_occurrences: 1
      max_consecutive_usage: 1
      fabricate_failure: false

  evidence_basis:
    type: observed-pattern

  evidence:
    - deck-a
    - deck-b

- id: concrete-evidence
  scope: shared
  status: stable

  observation:
    description: 技術説明で数値、制約、ファイル名、エラー、成果物などの具体物を示す
    occurrences: 4
    distinct_topics: 3
    distinct_periods: 3
    confidence: high

  interpretation:
    role: reproducibility-anchor
    purpose: 聴衆が試した条件と結果を再現・評価できるようにする

  application:
    strength: MUST
    applies_when: How、Demo、結果、実務評価を説明する
    guidance: 入力、制約、数値、ファイル名、エラー、成果物のうち少なくとも一つを画面上に残す
    next_slide: 結果、比較、完了条件、または実務評価
    limits:
      abstract_summary_only: false

  evidence_basis:
    type: observed-pattern

  evidence:
    - deck-a
    - deck-b
    - deck-c
    - deck-d

- id: avoid-performative-drama
  scope: shared
  status: stable

  observation:
    description: 感情表現は、実際の失敗、発見、成功がある場面に限定されている
    occurrences: 4
    distinct_topics: 3
    distinct_periods: 3
    confidence: high

  interpretation:
    role: anti-overapplication
    purpose: 実体験の捏造と過剰演出を防ぐ

  application:
    strength: MUST NOT
    applies_when: 失敗、驚き、成功が入力で確認できない
    guidance: 感情スライドを追加せず、事実と具体物を優先する
    next_slide: 実際の根拠、操作、結果、または結論
    limits:
      fabricate_experience: false
      fabricate_emotion: false
      unsupported_exaggeration: false

  evidence_basis:
    type: safety

  evidence:
    - deck-a
    - deck-b
    - deck-c
    - deck-d
```

## Application Limits

- 5分LTでは、感情や転換だけを担う独立スライドは原則0〜1枚とする。
- 10〜15分では1〜2枚を目安とする。
- 30分以上では、章の切替、重要な失敗、重要な発見に限定する。
- 会話的な転換、感嘆符、顔文字、statementを連続させない。
- ページ数を増やす目的でスタイル表現を追加しない。
- 発表時間が短いほど、雰囲気だけのページより、具体例、結果、判断基準を優先する。

```yaml
duration_limits:
  five_minutes:
    emotional_transition_slides: 0-1
    statement_slides_max_ratio: 0.15
  ten_to_fifteen_minutes:
    emotional_transition_slides: 1-2
    statement_slides_max_ratio: 0.15
  thirty_minutes_or_more:
    emotional_transition_slides: contextual
    statement_slides_max_ratio: 0.15

global_limits:
  max_consecutive_conversational_headings: 1
  max_face_emoticons: 1
  max_consecutive_statement_layouts: 1
  fabricate_experience: false
  fabricate_emotion: false

duration_evidence:
  short_form_decks: [deck-a, deck-b, deck-c, deck-d]
  long_form_decks: []
  unknown_duration_decks: []
  long_form_density_source: quality-default
```

## Evidence Sources

```yaml
- id: deck-a
  source: https://example.com/a
  type: html
  date: 2026-06
  topic: GitHub Copilotによる既存システム改修
  series: null
  template_family: ochtum-default-v2
  duration_minutes: 5
  visual_inspection: available
  speaker_notes: available
  independence:
    topic_group: copilot-existing-system
    series_group: null
    template_group: default-v2
  supports:
    - test-arc
    - transition-heading
    - failure-transition-slide
    - concrete-evidence
    - avoid-performative-drama
  observations:
    - 検証条件を明示する
    - 問題発生後に原因と再試行を示す
    - 実際のファイル名とエラーを表示する

- id: deck-b
  source: https://example.com/b
  type: pdf
  date: 2026-03
  topic: Spec Kitのカスタマイズ
  series: null
  template_family: ochtum-default-v2
  duration_minutes: 10
  visual_inspection: available
  speaker_notes: unavailable
  independence:
    topic_group: spec-kit-customize
    series_group: null
    template_group: default-v2
  supports:
    - test-arc
    - transition-heading
    - failure-transition-slide
    - concrete-evidence
    - avoid-performative-drama
  observations:
    - 課題、構造の発見、変更、結果の順で示す
    - フォルダ構成や変更対象を具体的に示す

- id: deck-c
  source: https://example.com/c
  type: speakerdeck
  date: 2025-11
  topic: AI活用のコストパフォーマンス
  series: null
  template_family: legacy-v1
  duration_minutes: 5
  visual_inspection: available
  speaker_notes: unavailable
  independence:
    topic_group: ai-cost-performance
    series_group: null
    template_group: legacy-v1
  supports:
    - test-arc
    - concrete-evidence
    - avoid-performative-drama
  observations:
    - 数値と比較条件を示す
    - 結論だけでなく評価基準を示す

- id: deck-d
  source: https://example.com/d
  type: speakerdeck
  date: 2025-09
  topic: ストレスとスキルアップ
  series: null
  template_family: legacy-v1
  duration_minutes: 5
  visual_inspection: unavailable
  speaker_notes: unavailable
  independence:
    topic_group: career-stress
    series_group: null
    template_group: legacy-v1
  supports:
    - test-arc
    - transition-heading
    - concrete-evidence
    - avoid-performative-drama
  observations:
    - 疑問から実体験と判断へつなげる
    - 結論を行動へ接続する
```

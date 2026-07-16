# Slide Style Profile Schema

`config/slide-style-profile.md` は永続的な発表者設定である。プロジェクトごとの `.lt-slide-work/` や `output/` へコピーしない。

## Required Structure

以下のH2見出しをこの順に置く。見出し名は検証のため英語表記を維持し、本文は日本語でよい。

```markdown
# LT Slide Style Profile

## Metadata

- profile_version: 2
- updated_at: YYYY-MM-DD
- evidence_count: 6
- independent_evidence_count: 4
- distinct_topic_count: 4
- oldest_evidence_date: YYYY-MM
- newest_evidence_date: YYYY-MM
- status: confirmed

## Presenter Stance

## Narrative Patterns

## Heading And Voice

## Emotional Beats

## Failure And Success

## Evidence And Specificity

## Visual Composition

## Speaker Notes

## Title And Surface Rules

## Negative Patterns

## Profile Evolution

## Reusable Patterns

## Application Limits

## Evidence Sources
```

### Metadata Rules

- `profile_version` はこのschemaでは `2` とする。
- `evidence_count` は `Evidence Sources` の資料数と一致させる。
- `independent_evidence_count` は、同一シリーズ・同一テーマ・同一テンプレートの重複をまとめた独立根拠数とする。
- `distinct_topic_count` は異なるテーマ群の数とする。
- `oldest_evidence_date` と `newest_evidence_date` は、日付が判明している根拠の範囲を記録する。
- 独立性のある根拠が3件以上なら `status: confirmed`、それ未満なら `status: draft` とする。
- 単純な `evidence_count` だけで `confirmed` を判定しない。

## Section Guidance

### Presenter Stance

発表者が、専門家、実験者、伴走者など、どの立場から話すかを記録する。

### Narrative Patterns

疑問、条件、試行、失敗、発見、結果、実務評価など、ストーリーの流れを記録する。

### Heading And Voice

見出し、文末、文長、疑問符、感嘆符、三点リーダー、呼びかけなどを記録する。

### Emotional Beats

感情表現を、前後の具体的な情報や転換の目的と結び付けて記録する。

### Failure And Success

失敗、原因、再試行、成功、未解決事項の見せ方を記録する。

### Evidence And Specificity

数値、制約、時間、ファイル名、コード、エラー、成果物など、技術情報の具体性を記録する。

### Visual Composition

`composition`、`density`、`hierarchy`、`emphasis`、`asset_usage`、`transition_slide`、`repetition`、`pacing`、`reader_flow` を分けて記録する。

### Speaker Notes

投影面に載せない背景、判断理由、前後接続、実体験を記録する。

実際の台本・録画・ノートがある場合だけ、ページ末尾の遷移文、指差しながら説明する順序、間の取り方を記録する。投影面しかない資料から発話を推測しない。ここで得たルールは口調と説明順の補助であり、個別テーマの問い、答え、Demo操作、Takeawayを生成する根拠にはしない。

### Title And Surface Rules

発表タイトル、章タイトル、通常見出し、転換スライド、投影面、話者ノートの表現を分離する。

### Negative Patterns

発表者らしさと合わない表現、過剰適用、抽象化、捏造を防ぐルールを記録する。

### Profile Evolution

`stable`、`emerging`、`contextual`、`deprecated` の傾向と、更新時の判断方針を記録する。

## Rule Format

`Reusable Patterns` は、次のフィールドを持つYAMLコードブロックで書く。観察事実、解釈、今後の適用を分離する。

```yaml
- id: experiment-turn
  scope: shared
  status: stable

  observation:
    description: 疑問を短い見出しで示した後、検証条件を提示する
    occurrences: 4
    distinct_topics: 3
    distinct_periods: 2
    confidence: high

  interpretation:
    role: skepticism-to-test
    purpose: 機能紹介ではなく検証として話を開始する

  application:
    strength: SHOULD
    applies_when: 入力に実際の疑問と検証条件がある
    guidance: 疑問を短い会話的見出しにし、次のページで条件または最初の操作を示す
    next_slide: 検証条件、入力、または最初の操作
    limits:
      max_ratio_of_main_slides: 0.15
      max_consecutive_usage: 1
      min_distance_between_uses: 3

  evidence_basis:
    type: observed-pattern

  evidence:
    - deck-2026-01
    - deck-2025-10
```

### Required Rule Fields

- `id`: プロファイル内で一意なルールID。
- `scope`: `shared`、`candidate`、`deck-specific`、`unknown` のいずれか。
- `status`: `stable`、`emerging`、`contextual`、`deprecated` のいずれか。
- `observation.description`: 過去資料から直接確認した事実。
- `observation.occurrences`: 確認できた出現回数。
- `observation.distinct_topics`: 異なるテーマ数。
- `observation.distinct_periods`: 異なる発表時期数。
- `observation.confidence`: `high`、`medium`、`low` のいずれか。
- `interpretation.role`: 何を言うかではなく、なぜその表現を置くかを表す。
- `interpretation.purpose`: 表現が学習、理解、転換へ与える目的。
- `application.strength`: `MUST`、`SHOULD`、`MAY`、`MUST NOT` のいずれか。
- `application.applies_when`: 適用条件。
- `application.guidance`: 実際の適用方法。
- `application.next_slide`: 次に置く内容。不要な場合は `none`。
- `application.limits`: 頻度、比率、連続数、禁止事項など。
- `evidence_basis.type`: 根拠の種類。
- `evidence`: `Evidence Sources` 内の資料ID。

### Evidence Basis Types

- `observed-pattern`: 複数資料で確認できた表現パターン。
- `observed-overuse`: 過去資料で過剰使用または品質低下が確認できた。
- `absence-pattern`: 独立した複数資料で一貫して避けられている。
- `quality-policy`: 可読性、技術的正確性、発表品質を守るための方針。
- `safety`: 体験や事実の捏造を防ぐための方針。

### Strength Rules

- `MUST` は、原則として独立性のある根拠3件以上で確認でき、発表者らしさの中心である場合に限る。
- `SHOULD` は、複数資料で確認でき、条件が一致する場合に推奨する。
- `MAY` は、候補、emerging、contextualな表現に使う。
- `MUST NOT` は、過剰適用、事実捏造、技術的不正確さ、可読性低下を防ぐために使う。
- 観察頻度と適用強度を同一視しない。
- `MUST NOT` が `quality-policy` または `safety` に基づく場合、通常の出現件数3件を必須としないが、理由を明記する。

## Negative Patterns Format

`Negative Patterns` は次の形式で記録する。

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
```

### Negative Pattern Rules

- 発表者の資料に少ないことだけを理由に禁止しない。
- 発表者の立ち位置、複数資料の傾向、品質基準と矛盾する場合だけ記録する。
- 正式な技術用語や製品名は、使用頻度が低いことだけを理由に禁止しない。

## Evidence Sources Format

資料ごとに、入力種別、作成時期、テーマ、シリーズ、テンプレート、発表時間、視覚・ノートの取得可否、独立性情報、観察した特徴、対応ルールを残す。

```yaml
- id: deck-2026-01
  source: https://example.com/deck
  type: speakerdeck
  date: 2026-01
  topic: GitHub Copilotエージェントモード
  series: null
  template_family: ochtum-default-v2
  duration_minutes: 5
  visual_inspection: available
  speaker_notes: unavailable
  independence:
    topic_group: copilot-agent
    series_group: null
    template_group: default-v2
  supports:
    - experiment-turn
    - concrete-evidence
  observations:
    - 実験条件を数値で示す
    - 失敗の後に原因と再試行を続ける
```

### Evidence Source Rules

- `id` はプロファイル内で一意にする。
- `date` が不明な場合は `unknown`。
- `series` がない場合は `null`。
- `template_family` が不明な場合は `unknown`。
- `duration_minutes` が不明な場合は `unknown`。
- `visual_inspection` は `available` または `unavailable`。
- `speaker_notes` は `available` または `unavailable`。
- `supports` には `Reusable Patterns` のIDだけを書く。
- `Reusable Patterns.evidence` と `Evidence Sources.supports` は相互参照できるようにする。

## Application Limits Format

`Application Limits` は説明文に加えて、次のYAMLを置く。

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
  short_form_decks: [deck-2026-01]
  long_form_decks: []
  unknown_duration_decks: [deck-2025-10]
  long_form_density_source: quality-default
```

### Application Limit Rules

- 発表時間が短いほど、雰囲気だけのページより具体例、結果、判断基準を優先する。
- ページ数を増やす目的で感情スライドやstatementを追加しない。
- 同じ感情表現、問いかけ、記号、レイアウトを連続させない。
- 固定枚数だけでなく、比率、連続数、最低間隔を必要に応じて設定する。
- スタイル適用により指定時間を超える場合は、スタイル側を削る。
- `duration_evidence` は、short form（15分以下）、long form（20分以上）、時間不明の根拠を分離する。
- `long_form_decks` が空の場合、20分以上のdensity/pacingは発表者固有ルールとせず、`long_form_density_source: quality-default` にする。
- 時間不明の資料は口調や具体物の種類には使えても、長時間LTのページ密度・文字量・ペーシングの根拠にしない。

## Application Guidance

- ストーリー、言葉、視覚、ノートのルールを混ぜず、該当セクションへ分ける。
- 具体例は短く残すが、過去資料の文章を連続して転載しない。
- すべてのルールに、使わない条件または頻度上限を設ける。
- 発表タイトル、通常見出し、転換スライド、投影面、話者ノートを分ける。
- `stable` を優先し、`emerging` は内容に合う場合だけ使う。
- `contextual` は条件が一致するときだけ使う。
- `deprecated` は新規生成へ適用しない。

## Change Report Format

既存プロファイルを更新した場合は、`config/slide-style-profile-change-report.md` を作成する。

以下のH2見出しをこの順に置く。

```markdown
# Slide Style Profile Change Report

## Metadata

## Added

## Changed

## Unchanged

## Deprecated Candidates

## Conflicts

## Evidence Added

## Validation Result
```

### Metadata Example

```yaml
profile_version_before: 1
profile_version_after: 2
updated_at: YYYY-MM-DD
new_evidence_count: 3
validation: passed
```

### Changed Entry Format

```yaml
- rule_id: experiment-turn
  before:
    status: emerging
    strength: MAY
  after:
    status: stable
    strength: SHOULD
  reason: 異なる2テーマの資料で追加確認できた
  added_evidence:
    - deck-2026-04
    - deck-2026-05
```

### Change Report Rules

- `Added`: 新規追加したルール。
- `Changed`: 強度、状態、発生条件、上限を変更したルール。
- `Unchanged`: 再確認できた主要ルール。
- `Deprecated Candidates`: 廃止候補だが根拠が不足しているルール。
- `Conflicts`: 資料間で解消できなかった矛盾。
- `Evidence Added`: 既存ルールへ追加した根拠。
- `Validation Result`: 検証スクリプトの結果。
- 既存の `MUST` または `MUST NOT` を変更する場合は、変更理由と追加根拠を必須とする。

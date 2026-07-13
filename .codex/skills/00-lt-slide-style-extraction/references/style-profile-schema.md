# Slide Style Profile Schema

`config/slide-style-profile.md` は永続的な発表者設定である。プロジェクトごとの `.lt-slide-work/` や `output/` へコピーしない。

## Required Structure

以下のH2見出しをこの順に置く。見出し名は検証のため英語表記を維持し、本文は日本語でよい。

```markdown
# LT Slide Style Profile

## Metadata

- profile_version: 1
- updated_at: YYYY-MM-DD
- evidence_count: 3
- status: confirmed

## Presenter Stance

## Narrative Patterns

## Heading And Voice

## Emotional Beats

## Failure And Success

## Evidence And Specificity

## Visual Composition

## Speaker Notes

## Reusable Patterns

## Application Limits

## Evidence Sources
```

`status` は根拠3件以上なら `confirmed`、2件以下なら `draft` とする。`evidence_count` は Evidence Sources の資料数と一致させる。

## Rule Format

再利用パターンは次のフィールドを持つYAMLコードブロックで書く。`role` は、何を言うかより「なぜその表現を置くか」を表す。

```yaml
- id: experiment-turn
  strength: SHOULD
  role: skepticism-to-test
  applies_when: 入力に実際の疑問と検証条件がある
  guidance: 疑問を短い会話的見出しにし、次のページで条件または最初の操作を示す
  next_slide: 検証条件、入力、または最初の操作
  limits: 同種の転換を連続させず、根拠のない疑いを追加しない
  evidence:
    - deck-2026-01
    - deck-2025-10
```

- `strength`: `MUST`、`SHOULD`、`MAY`、`MUST NOT` のいずれか。
- `evidence` には Evidence Sources 内の資料IDだけを書く。
- `MUST` は根拠3件以上に限る。`MUST NOT` は過剰適用や事実捏造を防ぐために使う。

## Evidence Sources Format

資料ごとに、入力種別、作成時期（不明なら `unknown`）、視覚の確認可否、観察した特徴を残す。

```yaml
- id: deck-2026-01
  source: https://example.com/deck
  type: speakerdeck
  date: 2026-01
  visual_inspection: available
  observations:
    - 実験条件を数値で示す
    - 失敗の後に原因と再試行を続ける
```

## Application Guidance

- ストーリー、言葉、視覚、ノートのルールを混ぜず、該当セクションへ分ける。
- 具体例は短く残すが、過去資料の文章を連続して転載しない。
- すべてのルールに、使わない条件または頻度上限を設ける。
- `Application Limits` には、連続する感情スライド、記号、顔文字、statementレイアウトの上限と、事実を作らない禁止事項を明記する。

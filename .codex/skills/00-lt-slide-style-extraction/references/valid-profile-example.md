# LT Slide Style Profile

## Metadata

- profile_version: 1
- updated_at: 2026-07-13
- evidence_count: 3
- status: confirmed

## Presenter Stance

- 実際に試した人として、結論だけでなく検証過程を共有する。

## Narrative Patterns

- 疑問、条件、試行、結果、実務上の判断を必要に応じてつなげる。

## Heading And Voice

- 見出しは短く、解説前の転換だけ会話的な表現を許可する。

## Emotional Beats

- 感情の転換は、前後の具体的な情報と結び付くときだけ使う。

## Failure And Success

- 失敗は原因または次の操作とセットで扱う。

## Evidence And Specificity

- 入力、制約、数値、出力のうち少なくとも一つを技術説明に残す。

## Visual Composition

- 強い短文スライドは、実際の転換点または結論に限定する。

## Speaker Notes

- ノートで、前ページとの接続と次に判断することを補う。

## Reusable Patterns

```yaml
- id: test-arc
  strength: MUST
  role: experiment-narrative
  applies_when: 入力に実際の検証過程がある
  guidance: 試した理由、条件、結果を時系列でつなげる
  next_slide: 実行結果または次に試した操作
  limits: 実際にない試行や失敗を追加しない
  evidence:
    - deck-a
    - deck-b
    - deck-c
- id: transition-heading
  strength: SHOULD
  role: explanation-transition
  applies_when: 詳細な解説へ移る必要がある
  guidance: 短い会話的な見出しで次の問いを示す
  next_slide: 表、フロー、設定、またはコード
  limits: 同種の転換見出しを連続させない
  evidence:
    - deck-a
    - deck-b
- id: avoid-performative-drama
  strength: MUST NOT
  role: anti-overapplication
  applies_when: 失敗や成功が入力で確認できない
  guidance: 感情スライドを追加せず、事実と具体物を優先する
  next_slide: 実際の根拠または結論
  limits: 感嘆符、顔文字、誇張を根拠なく追加しない
  evidence:
    - deck-a
    - deck-b
    - deck-c
```

## Application Limits

- 会話的な転換は連続させず、10枚なら最大3回を目安にする。
- 顔文字は最大1回とし、実際の成功または脱力を示す根拠がある場合に限る。
- 発表者が経験していない失敗、驚き、成功は捏造しない。

## Evidence Sources

```yaml
- id: deck-a
  source: https://example.com/a
  type: html
  date: 2026-01
  visual_inspection: available
  observations:
    - 検証条件を明示する
- id: deck-b
  source: https://example.com/b
  type: pdf
  date: 2025-11
  visual_inspection: available
  observations:
    - 短い転換見出しを使う
- id: deck-c
  source: https://example.com/c
  type: speakerdeck
  date: unknown
  visual_inspection: unavailable
  observations:
    - 結果を具体物とともに示す
```

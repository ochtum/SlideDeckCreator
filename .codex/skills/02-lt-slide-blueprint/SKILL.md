---
name: 02-lt-slide-blueprint
description: .lt-slide-work/01-story.yaml を .lt-slide-work/02-blueprint.yaml に変換し、洗練された 1280x720 の HTML スライド用に整える。話者ノートは保持すること。レイアウト、タイポグラフィ、図解、アニメーション手順、空間ゾーン、発表者ノート、テキスト量の設計を行う際に使用する。また、テキスト・図・バッジ・結論が重ならないようにすること。
---

# 02 LT Slide Blueprint

`.lt-slide-work/01-story.yaml` を、実装可能なスライド設計図 `.lt-slide-work/02-blueprint.yaml` に変換する。HTMLや画像は作らない。図版と文字の領域を先に分け、重なりを設計段階で禁止する。

## Workspace Contract

入力と出力はプロジェクトルート直下の `.lt-slide-work/` に固定する。

```text
.lt-slide-work/
├─ 01-story.yaml
└─ 02-blueprint.yaml

config/
└─ presenter.json
```

設計図や検証用ファイルをプロジェクトルート、`output/`、スキル本体のフォルダへ出力しない。発表者情報は `config/presenter.json` から読み、`.lt-slide-work/` へコピーしない。

## Required Reads

- `references/blueprint-schema.md`
- `references/layout-rules.md`
- 図版を選ぶときは `references/figure-patterns.md`

## Workflow

1. `.lt-slide-work/01-story.yaml` の必須キーとスライド順を確認する。各スライドの `spoken_note` を同じIDの設計図へそのまま引き継ぐ。
2. 各スライドに1つの `layout` と1つの `visual_anchor` を割り当てる。
3. 1280x720座標で `title_zone`, `text_zone`, `visual_zone`, `conclusion_zone`, `footer_zone` を定義する。
4. テキスト量、文字サイズ、行数を確定する。
5. 図版をコンポーネント、インラインSVG、生成画像、なしから選ぶ。
6. entranceとページ内stepを最大4段階で設計する。
7. `.lt-slide-work/02-blueprint.yaml` を出力する。
8. `scripts/validate_blueprint.py .lt-slide-work/02-blueprint.yaml` を実行し、エラーをゼロにする。

## Non-Overlap Contract

- 主要ゾーンは互いに交差させない。背景装飾だけは例外。
- `title_zone` はバッジ領域 `x:48..220, y:24..64` と交差させない。
- `footer_zone` は原則 `y:660..704` とし、本文・図版を入れない。
- `conclusion_zone` は図版の上に重ねない。後出しでも専用領域を確保する。
- 画像は `object-fit: contain` 前提で `visual_zone` 内に収める。
- 絶対配置は装飾、ページ番号、明示されたゾーンだけに限定する。
- アニメーションの開始位置と終了位置の両方が担当ゾーンからはみ出さないようにする。
- 中央の矢印やVSは独立した `connector_zone` を持たせる。

## Typography Floor

lt-html-slide-skillの見栄えを維持しつつ、slide-builderの小さな文字を改善する。

- 表紙タイトル: 56から76px
- 通常タイトル: 38から56px
- 強い結論: 28から32px
- カード見出し: 30から38px
- 本文: 24から28px
- 補足: 22から26px
- 出典・ページ番号: 18から22px

本文を28px未満に縮めて収めてはならない。収まらない場合は文章を削る、カード数を減らす、またはスライドを分割する。自動縮小は禁止する。

## Layout Selection

- `hero-split`: 表紙や強い結論。左テキスト、右ビジュアル。
- `profile-three-zone`: 左画像、中央プロフィール、右QR。欠損時は2列へ変更。
- `statement`: 1つの主張を大きく見せる。
- `split-compare`: 左右比較と独立コネクタ。
- `cards-3`: 3つの選択肢や理由。
- `cards-4`: 短い項目だけ。各カード本文2行以内。
- `flow-3` / `flow-4`: 手順と矢印。
- `matrix`: 2軸分類。結論は下部専用帯。
- `visual-left` / `visual-right`: 生成画像と本文を分離。
- `recap-split`: 左要点、右または下に最初の一手。
- `thanks`: 大きな終了メッセージと広い余白。

同じレイアウトを3枚以上連続させない。

## Visual And Animation Rules

- 1枚に視覚的主役を1つ置く。
- 図版に本文と同じ長文を重複させない。
- 生成画像には原則として文字を焼き込まない。
- アニメーションはタイトル、主役、補助、結論の順にする。
- 重要な図を最初に見せ、結論帯は必要なら最後のstepで出す。
- 1枚のstep数は0から4。全入場は原則2秒以内。
- `prefers-reduced-motion` と印刷では全要素を表示する前提にする。
- `spoken_note` は投影面のレイアウトや文字量に含めない。発表者ビュー専用データとして保持する。

## Output

正本は `.lt-slide-work/02-blueprint.yaml`。後工程を同じターンで依頼されている場合は停止せず `03-lt-slide-visuals` へ進む。

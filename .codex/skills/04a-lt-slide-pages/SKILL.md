---
name: 04a-lt-slide-pages
description: Build the static 1280x720 HTML slide pages for a Lightning Talk deck from .lt-slide-work/02-blueprint.yaml and .lt-slide-work/visuals-manifest.yaml, focusing only on content, layout, assets, notes, and visual hierarchy before animation or runtime controls are added.
---

# 04a LT Slide Pages

`.lt-slide-work/02-blueprint.yaml` と `.lt-slide-work/visuals-manifest.yaml` から、静的なスライドページ本体を作る。ここでは「何をどこに置くか」だけに集中し、アニメーション制御、ショートカット、発表者ビュー、PDF生成ロジックは作り込まない。

## Required Reads

- `../04-lt-slide-build/references/design-system.md`
- `../04-lt-slide-build/references/build-contract.md`
- 必要に応じて `../04-lt-slide-build/assets/deck-shell.html`

## Inputs

- `.lt-slide-work/02-blueprint.yaml`
- `.lt-slide-work/visuals-manifest.yaml`
- `.lt-slide-work/visuals/*`
- 必要に応じて `config/presenter.json`

## Output Contract

次のどちらかを作る。

- 統合作業中: `output/index.html` 内の `.deck` と `.slide` 群
- 段階確認用: `.lt-slide-work/04a-pages.html`

どちらの場合も、生成するスライド本文は次を満たす。

- `.deck` は1280x720のスライドを収める
- 各ページは `<section class="slide" ...>` とする
- 各 `.slide` に `data-spoken-note` を埋め込む
- 最後の2枚は `data-role="recap"`、`data-role="thanks"` とする
- ページ番号は `.page-number` で入れる
- 画像は `output/assets/` へコピーし、HTMLから相対参照する
- 発表者ノートは投影面へ表示しない

## Workflow

1. `02-blueprint.yaml` のページ数、各ページの目的、`spoken_note`、レイアウト指定を確認する。
2. `visuals-manifest.yaml` の画像解決状況を確認する。必須画像が未解決なら先に解消する。
3. `output/` と `output/assets/` を用意し、使用画像を `output/assets/` へコピーする。
4. `deck-shell.html` を使う場合は、既存サンプルスライドを実ページへ置き換える。ランタイム部分はこの段階で改変しない。
5. 各スライドに `.zone[data-zone]` を使って、タイトル、本文、図版、結論、フッターなどの領域を明示する。
6. 本文、図版、結論帯を同じグリッドセルや同じ視覚領域へ重ねない。
7. 文字量が多い場合は文章を削るかレイアウトを変える。`overflow: hidden`、自動縮小、過小フォントで隠さない。
8. 最後に全スライドを静的状態で見て、情報階層、余白、画像切れ、読み順を確認する。

## Layout Rules

- `.slide` は1280x720固定。
- 可読テキストは原則 `x >= 64`, `y >= 88`, `x + w <= 1216`, `y + h <= 636` の内側に置く。
- 例外は `brand-badge`、ページ番号、フッター、背景装飾だけ。
- 本文28px、補足22pxを原則下限とする。出典とページ番号だけ18pxを許可する。
- `clamp()` やJavaScriptによる自動文字縮小は禁止する。
- 1枚1メッセージ、1つの視覚的主役を維持する。
- 通常ページはレイアウトに変化を付け、同型を3枚続けない。
- まとめとサンクスを最後に連続配置する。

## Visual Direction

- 白背景、ネイビー、グリーン、ブルー、シアン。
- 大きな見出し、太いウェイト、広い余白。
- 淡いグリッド、抽象曲線、グラデーションラインを控えめに使う。
- カードは18から24pxの角丸、薄い境界、柔らかい影。
- 表紙は左に大タイトル、右に象徴図。
- 装飾より情報階層を優先する。

## Handoff To 04b

`04b-lt-slide-animation` へ渡す前に、次を満たす。

- すべての `.slide` が存在する
- すべての本文と画像が配置済み
- すべての `data-spoken-note` が埋め込み済み
- アニメーション対象候補に意味のあるまとまりがある
- 明らかなテキスト溢れ、ゾーン重なり、画像切れがない

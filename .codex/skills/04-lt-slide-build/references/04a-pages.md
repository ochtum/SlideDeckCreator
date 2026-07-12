# 04a Internal Stage: Static Pages

`.lt-slide-work/02-blueprint.yaml` と `.lt-slide-work/visuals-manifest.yaml` から、静的なスライドページ本体を作る。ここでは「何をどこに置くか」だけに集中し、アニメーション制御、ショートカット、発表者ビュー、PDF生成ロジックは作り込まない。

## Required Reads

- `design-system.md`
- `build-contract.md`
- 必要に応じて `../assets/deck-shell.html`

## Inputs

- `.lt-slide-work/02-blueprint.yaml`
- `.lt-slide-work/visuals-manifest.yaml`
- `.lt-slide-work/visuals/*`
- 必要に応じて `config/presenter.json`

ルートの `01-story.yaml` が `kind: lt-slide-series` の場合は、`../../01-lt-slide-story/references/series-schema.md` の各パートについて、そのパートの `blueprint_file`、`visuals_manifest_file`、`visuals/`、`output_dir` を使う。別パートの入力・出力を混在させない。

## Output Contract

次のどちらかを作る。

- 単発の統合作業中: `output/index.html` 内の `.deck` と `.slide` 群
- シリーズの統合作業中: `<part-output>/index.html` 内の `.deck` と `.slide` 群
- 段階確認用: 対象ワークディレクトリ内の `04a-pages.html`

どちらの場合も、生成するスライド本文は次を満たす。

- `.deck` は1280x720のスライドを収める
- 各ページは `<section class="slide" ...>` とする
- 各 `.slide` に `data-spoken-note` を埋め込む
- 各 `.slide` に `data-reader-context` と `data-story-bridge` を埋め込む
- 最後の2枚は `data-role="recap"`、`data-role="thanks"` とする
- ページ番号は `.page-number` で入れる
- 画像は `output/assets/` へコピーし、HTMLから相対参照する
- 発表者ノートは投影面へ表示しない

## Workflow

1. `02-blueprint.yaml` のページ数、各ページの目的、`spoken_note`、レイアウト指定、`content_model` を確認する。
2. `visuals-manifest.yaml` の画像解決状況を確認する。必須画像が未解決なら先に解消する。
3. 対象デッキの出力先と `assets/` を用意し、使用画像を対象出力先の `assets/` へコピーする。
4. `deck-shell.html` を使う場合は、既存サンプルスライドを実ページへ置き換える。ランタイム部分はこの段階で改変しない。
5. 各スライドに `.zone[data-zone]` を使って、実際に内容を持つタイトル、本文、図版、結論、フッターなどの領域だけを明示する。空のvisual zoneや、背景・枠線だけのcardを出力してはならない。
5a. `reader_context` が初見者の理解に必要な場合は、タイトル近くの短い文脈ラベルまたは本文の一文として表示する。`connection_from_previous.bridge` は発表者ビューで常に読めるようにし、投影面では章の切替や新用語の導入時だけ短く表示する。
6. `visual_plan` がある場合は、各 `.slide` に `data-visual-plan-id` と `data-source-asset-ids` を埋め込む。`implementation` が `provided-image` ならマニフェストの画像を使い、`html-table` / `html-code` / `inline-svg` なら対応する実要素を置く。計画を汎用カードだけで満たしてはならない。
7. 本文、図版、結論帯を同じグリッドセルや同じ視覚領域へ重ねない。
8. 文字量が多い場合は文章を削るかレイアウトを変える。`overflow: hidden`、自動縮小、過小フォントで隠さない。
9. 最後に全スライドを静的状態で見て、情報階層、余白、画像切れ、読み順を確認する。

## Layout Rules

- `.slide` は1280x720固定。
- 可読テキストは原則 `x >= 64`, `y >= 88`, `x + w <= 1216`, `y + h <= 636` の内側に置く。
- 例外は `brand-badge`、ページ番号、フッター、背景装飾だけ。
- 本文28px、補足22pxを原則下限とする。出典とページ番号だけ18pxを許可する。
- `clamp()` やJavaScriptによる自動文字縮小は禁止する。
- 通常ページはレイアウトに変化を付け、同型を3枚続けない。
- ページ数は初回ビルド時の数を保持しない。ストーリー／設計図の現在のスライド列を正として、追加・削除・分割後は物理ページ、ページ番号、発表者ビューの総数を同期して更新する。
- シリーズでは、ページ番号と発表者ビュー総数を各パート内だけで数える。別パートのページを加算しない。
- まとめとサンクスを最後に連続配置する。

## Visual Direction

- 白背景、ネイビー、グリーン、ブルー、シアン。
- 大きな見出し、太いウェイト、広い余白。
- 淡いグリッド、抽象曲線、グラデーションラインを控えめに使う。
- カードは18から24pxの角丸、薄い境界、柔らかい影。
- 表紙は左に大タイトル、右に象徴図。
- 装飾より情報階層を優先する。
- 実務フロー、設定、設計資料、サンプルを説明するページは、抽象アイコンだけで済ませない。少なくとも代表的な表、コード断片、チェックリスト、または判断フローをHTML/SVG/CSSで読める形に実装し、発表後に聴衆が最初の作業を再現できるようにする。
- 実装プレイブックは、複数の個別説明へ分散させない。題材選定、タスクカード、知識の入口、再現環境、検証、改善の順で連続したページ群にし、各ページで成果物・担当・完了条件が視認できるようにする。
- `content_model` をそのままHTMLへ描画する。`table` は見出しと代表行を持つ表、`flow` はノード・矢印・入出力、`implementation-playbook` は成果物・担当・完了条件の列、`config` / `code` は読める最小断片にする。汎用カードや抽象アイコンだけでデータを代替しない。
- `content_model` が空、または `visual.kind: none` の場合は、visual zoneとそのcardをHTMLへ出力しない。本文を広げる、結論帯を拡張する、または実データを持つSVG/CSS要素を設計図へ戻して追加する。空の白枠、空の影付きカード、空の右カラムを「余白」として残すことは禁止する。
- 最終HTMLに `KEY VIEW`、`PLAYBOOK` などのプレースホルダー文字列を残さない。表示するラベルは、設計図の具体的な内容に由来させる。

## Handoff To 04b Internal Stage

`04b-animation.md` へ渡す前に、次を満たす。

- すべての `.slide` が存在する
- すべての本文と画像が配置済み
- すべての `data-spoken-note` が埋め込み済み
- アニメーション対象候補に意味のあるまとまりがある
- 明らかなテキスト溢れ、ゾーン重なり、画像切れがない
- 空のvisual zone、空のcard、枠線だけの予約領域がない

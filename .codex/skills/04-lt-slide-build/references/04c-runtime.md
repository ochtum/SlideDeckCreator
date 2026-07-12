# 04c Internal Stage: Runtime And QA

04a・04b内部工程で完成したスライドDOMへ、固定ランタイムを適用して配布物を完成させる。ショートカット、一覧表示、発表者ビュー、同期、PDF CSSは毎回新規実装せず、`../assets/deck-shell.html` の契約を基準にする。

## Required Reads

- `build-contract.md`
- `../assets/deck-shell.html`
- `../scripts/validate_deck.py`
- `../scripts/validate_pdf.py`

## Inputs

- `output/index.html` または `.lt-slide-work/04b-animated.html`
- `output/assets/*`

シリーズでは、`../../01-lt-slide-story/references/series-schema.md` の各パートを独立して処理し、入力は `<part-output>/index.html` と `<part-output>/assets/*`、出力も同じ `<part-output>/` とする。パート間でHTML、assets、PDF、ZIPを共有しない。

## Outputs

- `output/index.html`
- `output/index.pdf`
- `output/index_html.zip`
- 必要に応じて `.lt-slide-work/` 以下の検証スクリーンショットやPDFレンダリング画像

シリーズの出力は各 `<part-output>/index.html`、`index.pdf`、`index_html.zip` とする。

## Runtime Contract

最終HTMLは次を満たす。

- Right Arrow, Space, PageDown: 次stepまたは次スライド
- Left Arrow, PageUp: 前stepまたは前スライド
- Home and End: 最初と最後のスライド
- F: fullscreen
- R: 現在スライドをリプレイ
- P: pager and overview mode
- S: 同じHTMLの発表者ビューを別ウィンドウで開く
- A: 現在スライドの全アニメーションstepを即座に最終状態まで表示する
- Hash links: `#1`, `#2`, ...
- `?audit=1`: レイアウト監査を実行する
- 発表者ビューには、これらの埋め込みショートカット一覧を常時表示する

## Presenter View Contract

- 元ウィンドウを投影用、`?presenter=1` の別ウィンドウを手元用とする。
- 「次のスライド」プレビュー付近の空き領域に、キーボードショートカット一覧を表示する。
- 同期は `index` と `step` だけでなく、投影側の現在スライドDOMスナップショットを含める。
- 発表者ビューの「現在のスライド」は、投影側DOMの現在状態をそのまま複製する。
- `data-step` から現在プレビューを再計算しない。
- 要素のクラス、属性、インラインスタイル、SVG状態、デッキ固有の表示クラスを保持する。
- 発表者ビューから操作した場合は、投影側が操作を適用してから新しいDOMスナップショットを返す。
- 「次のスライド」だけは全アニメーション完了後の最終状態で表示する。
- 現在プレビューと次プレビューのレンダリング処理を共用しない。
- 片方のウィンドウを閉じても、残ったウィンドウの通常操作を壊さない。
- 現在スライドの `data-reader-context` と `data-story-bridge` を、ノートの近くに表示する。話者が後から開いても、前ページからの接続を再構成できるようにする。

## Print And PDF Contract

- `@page { size: 13.333333in 7.5in; margin: 0; }` を使う。
- 印刷時の `.slide` は `width: 13.333333in; height: 7.5in` とする。
- 1スライドをPDFの1ページへ等倍配置する。
- `print-color-adjust: exact` と `-webkit-print-color-adjust: exact` を指定する。
- 印刷時は全アニメーション内容を最終状態で表示する。
- 発表者ビュー、操作UI、ノートは印刷に出さない。
- ブラウザのヘッダーとフッターは無効にする。

## Viewport Fit Contract

- `.slide` は1280x720固定。
- 通常表示ではdeck全体を `scale()` して収める。
- `fit()` は上下左右に最低32px、推奨48pxの表示余白を差し引いてscaleを計算する。
- 16:9ではないモニタやブラウザツールバー付き表示で、スライドが上端または左端に吸着して見える状態を合格にしない。
- 表示余白はPDF印刷には持ち込まない。

## Runtime Layout Audit

`?audit=1` で全要素を表示し、次をコンソールエラーとして検出するコードを入れる。

- `.zone` がスライド境界を越える
- `[data-zone]` 同士が8pxを超えて交差する
- `scrollWidth > clientWidth` または `scrollHeight > clientHeight`
- 画像のnaturalWidthまたはnaturalHeightが0

背景装飾、コネクタ、明示的に `data-overlap-ok` を付けた要素は交差検査から除外する。

## Workflow

1. `deck-shell.html` のCSS/JS契約を基準に、完成済み `.slide` 群を組み込む。
2. 固定ランタイムのショートカット、overview、reveal all、scale、presenter、audit、print CSSを保持する。
3. `scripts/validate_deck.py <deck-output>/index.html` を実行する。単発の `<deck-output>` は `output`、シリーズでは各パートの `output_dir` とする。
4. ブラウザで通常表示を開き、全スライドの初期状態、前後移動、`A` 全表示、`P` overviewを確認する。
5. `S` で発表者ビューを開き、現在・次スライド、ノート、reader context、bridge、タイマー、ショートカット一覧、双方向同期を確認する。
6. 各stepで投影側と発表者ビューの現在プレビューが一致することを確認する。
7. 印刷プレビューで用紙サイズ、余白0、全step表示を確認し、`<deck-output>/index.pdf` を生成する。
8. `scripts/validate_pdf.py <deck-output>/index.pdf <deck-output>/index.html` を実行する。
9. PDFをPNGへレンダリングし、全ページの見切れ、余白、背景、画像切れを確認する。
10. ZIP rootに `index.html` と `assets/` が入る形で `<deck-output>/index_html.zip` を作る。余分な親ディレクトリを入れない。

## Quality Gate

- `validate_deck.py` 成功
- `validate_pdf.py` 成功
- 通常表示に上下左右の表示余白がある
- `A` reveal allが現在スライドだけを完成状態にする
- `P` overviewが使える
- `S` presenter viewが開く
- 発表者ビューにショートカット一覧が表示される
- 発表者ビューからの前後操作が投影側へ反映される
- 投影側からの前後操作が発表者ビューへ反映される
- 現在プレビューは投影側DOM状態と一致する
- 次プレビューは常に最終状態で表示される
- 発表者ビューで reader context と bridge が読め、後からページ間の論理を復元できる
- PDFのページ数がHTMLスライド数と一致する
- PDFページ寸法が960x540pt近似である
- シリーズでは、上記の品質ゲートを各 `output_dir` のデッキに対して満たす

最終回答では、HTML、PDF、ZIP、ページ数、検証結果だけを簡潔に示す。

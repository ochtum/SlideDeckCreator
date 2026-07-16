# 04b Internal Stage: Animation

04a内部工程が作った静的スライドに、LTとして読みやすい段階表示を付ける。ここではアニメーションの意味、順序、stepの契約に集中する。ページ送り、発表者ビュー、ウィンドウ間同期は04c内部工程に任せる。

## Required Reads

- `build-contract.md`
- `design-system.md`
- `../../02-lt-slide-blueprint/references/motion-choreography.md`

## Inputs

- `output/index.html` または `.lt-slide-work/04a-pages.html`

シリーズでは、`../../01-lt-slide-story/references/series-schema.md` の各 `output_dir/index.html` または各パートの `04a-pages.html` を個別に処理する。アニメーションstep、ページ番号、表示状態を複数パートにまたがって共有しない。

## Output Contract

アニメーション適用後のHTMLは次を満たす。

- 表示タイミングを持つ要素に `data-anim` を付ける
- `data-anim` は `rise`, `fade`, `blur-in`, `slide-left`, `slide-right`, `pop`, `zoom-focus`, `flip-in`, `wipe`, `draw`, `stamp`, `marker`, `stomp` から選ぶ
- Blueprintの各targetに指定されたpresetを同名の `data-anim` へ保存し、未対応を理由に `rise` へ置換しない
- stepは1枚最大6回
- stepはZ型の視線誘導に従う
- 空stepを作らない
- `A` キーによる全表示、印刷時全表示、reduced motion全表示に耐えるDOMにする
- 発表者ビューの現在プレビューで、投影側DOMの `shown` 状態がそのまま意味を持つ

## Workflow

1. 各スライドの主メッセージ、視線の始点、結論の位置を確認する。
2. 表示のまとまり単位で `data-anim` を付ける。細かい単語や装飾を過剰に分割しない。
3. Z型順序で表示されるよう、各 `[data-anim]` の属する `.zone[data-zone]` を確認する。
4. Blueprintに明示された `data-step` を正本とする。`04c` の `applyZFlow()` はstepがない要素だけを補完し、明示stepを再採番しない。
5. 結論帯は最後に出す。図解上へ重ねたり、主役の図版を隠したりしない。
6. 常時ループは小さな装飾だけに限定する。
7. 初期状態、各step、全表示状態で、情報が自然に積み上がることを確認する。
8. `python .codex/skills/04-lt-slide-build/scripts/validate_animation_choreography.py --blueprint <02-blueprint.yaml> --html <index.html>` を実行し、preset消失、同一signatureの連続、step数の均一化、強い演出の多用を修正する。

## Animation Rules

- アニメーション順序は原則 `左上 -> 右上 -> 中央左 -> 中央 -> 左下 -> 右下`。
- タイトルやブランド導入は左上、右側の図版やQRは右上、本文は中央左または中央、結論帯は下段として最後に出す。
- 要素が少ないスライドではZ順を保ったままstep数を圧縮する。
- `draw` は線、矢印、プロセス図に使う。
- `marker` は重要語の強調に使い、文章全体には使わない。
- `stamp` や `stomp` は強い結論、警告、完了感に限定する。
- `fade` は写真、背景に近い補助要素、控えめな補足に使う。
- `rise` は本文、カード、箇条書きに使う。
- `pop` はアイコン、数値、短いラベルに使う。
- `wipe` はライン、帯、進行方向を持つ図に使う。

## CSS Contract

最終HTMLには `04c` のランタイムが次のCSS契約を持つことを前提にする。

- `[data-anim]` の初期状態は非表示
- `.shown` が付くと表示される
- `prefers-reduced-motion: reduce` では全内容を表示する
- `@media print` では全内容を表示する

独自の表示クラスを追加する場合は、発表者ビューのDOMスナップショット複製で状態が保持されるよう、クラス、属性、インラインスタイルで状態を表現する。

## Handoff To 04c

04c内部工程へ渡す前に、次を満たす。

- 各スライドの初期表示が成立する
- 各stepで見せたい要素が自然な順序で現れる
- step数が6以下
- `A` 全表示で完成状態になる
- 印刷時に全要素が見える前提でレイアウトが崩れない
- シリーズでは、上記を各パートのHTMLごとに満たす

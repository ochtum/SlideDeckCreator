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
- 各対象へ `data-motion-reason` を保存し、Blueprintの `reason` / `target_reasons` を失わない
- stepは通常1枚最大6回。Blueprintで `sequence.mode: item-by-item` として明示された順序列だけ最大9回
- stepは番号・因果・依存・操作・説明順を優先し、意味順のない独立要素だけZ型の視線誘導を使う
- 空stepを作らない
- タイトルと必要な前提はstep 0、対象はstep 1以降、出力・完了条件・結論は対象の後、結論は最後にする
- 段階表示する表・カード・チェックリスト・番号付き工程では、意味要素の兄弟を全件割り当てる。一部だけ `data-anim` を付け、残りを意図せず初期表示にしてはならない
- `A` キーによる全表示、印刷時全表示、reduced motion全表示に耐えるDOMにする
- 発表者ビューの現在プレビューで、投影側DOMの `shown` 状態がそのまま意味を持つ

## Workflow

1. 各スライドの主メッセージ、視線の始点、結論の位置を確認する。
2. 表示のまとまり単位で `data-anim` を付ける。細かい単語や装飾を過剰に分割しない。
3. Blueprintの `animation.sequence.order_basis` を読み、番号・因果・依存・操作・説明順をDOM順とstepへ反映する。意味順がない場合だけ `.zone[data-zone]` の位置からZ型を使う。
4. Blueprintに明示された `data-step` を正本とする。`04c` の `applyZFlow()` は属性自体がない要素だけを補完し、`data-step="0"` を含む明示stepを再採番しない。
5. 結論帯は最後に出す。図解上へ重ねたり、主役の図版を隠したりしない。
6. 常時ループは小さな装飾だけに限定する。
7. 初期状態、各step、全表示状態で、情報が自然に積み上がることを確認する。
8. 順序列の要素へ `data-reveal-item="true"`, `data-reveal-group`, `data-reading-order`, `data-sequence-mode`, `data-motion-reason` を付ける。常時表示が意図された意味要素には `data-static-intentional` を付ける。
9. `python .codex/skills/04-lt-slide-build/scripts/validate_animation_choreography.py --blueprint <02-blueprint.yaml> --html <index.html>` と `python .codex/skills/04-lt-slide-build/scripts/validate_animation_structure.py --html <index.html>` を実行し、preset消失、順序列の部分割当、逆順、早すぎる結論、step上限超過を修正する。

## Animation Rules

- アニメーション順序は `意味順 -> DOM順 -> Z型`。Z型の既定は `左上 -> 右上 -> 中央左 -> 中央 -> 左下 -> 右下` だが、番号付き工程や依存関係を上書きしない。
- タイトルやブランド導入は左上、右側の図版やQRは右上、本文は中央左または中央、結論帯は下段として最後に出す。
- 要素が少ないスライドではZ順を保ったままstep数を圧縮する。
- `draw` は線、矢印、プロセス図に使う。
- `marker` は重要語の強調に使い、文章全体には使わない。
- `stamp` や `stomp` は強い結論、警告、完了感に限定する。
- `fade` は写真、背景に近い補助要素、控えめな補足に使う。
- `rise` は本文、カード、箇条書きに使う。
- `pop` はアイコン、数値、短いラベルに使う。
- `wipe` はライン、帯、進行方向を持つ図に使う。
- `target_presets` があるstepでは、各DOM要素に対応するtargetのpresetとreasonを使う。同一stepだからという理由で接続線とカードを同じ動きへ正規化しない。
- 前進時に表示済み要素を自動退場させない。個別fade-outを標準化せず、戻る操作だけ入口演出の逆遷移を使う。

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
- step数が通常6以下、明示されたitem-by-item順序列では9以下
- 同じ意味グループに未割当の兄弟要素がなく、全途中stepで後続要素が先に見えない
- `A` 全表示で完成状態になる
- 印刷時に全要素が見える前提でレイアウトが崩れない
- シリーズでは、上記を各パートのHTMLごとに満たす

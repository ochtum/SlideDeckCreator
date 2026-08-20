---
name: 06-lt-slide-editor
description: 04-lt-slide-build によって生成された HTML ライトニングトークデッキに、ブラウザ内エディタを追加する。Codex が output/index.html を変更し、スライドをインタラクティブに編集できるようにする必要がある場合に使用する。具体的には、配置済み要素の移動、テキスト編集、spoken_note編集、テキスト・画像・吹き出しの追加、基本的なスタイルの適用、エディタパネルがスライドを邪魔する場合の移動、キーボードショートカットによるエディタモードと表示モードの切り替え、スライドの複製、空白スライドの追加、Save HTML による元HTMLの上書き、Export PDF による同名PDF出力を行う。その際、プレゼン表示、発表者ビュー、印刷、レビューの挙動は維持すること。
---

# 06 LT Slide Editor

`04-lt-slide-build` が生成したHTMLデッキに、ブラウザ内エディターを追加する。単発は `output/index.html`、シリーズは対象パートの `output/<part-id>/index.html` を明示する。通常の発表モードは変えず、`?edit=1` のときだけ編集UIを表示する。

## Required Reads

- `references/editor-contract.md`
- スクリプトを調整する場合のみ `scripts/inject_editor.js` と `scripts/serve_editor.js`

## Workflow

1. 対象HTMLを確認する。単発だけ指定がなければ `output/index.html` を使う。シリーズでは対象パートの `output/<part-id>/index.html` を必ず指定する。
2. 対象が `04-lt-slide-build` 系の構造を持つことを確認する。最低限 `.deck` と `.slide` が必要。
3. `scripts/inject_editor.js` を実行して編集ランタイムを注入する。
4. `scripts/serve_editor.js` で対象HTMLをローカル配信し、表示された `http://127.0.0.1:<port>/?edit=1` を開く。
5. 編集画面が発表者ビュー風の固定ワークスペースになり、左上に保存対象の実スライド、左下に編集パネル、右側にSpoken Noteと出力操作が表示されることを確認する。左下は「選択要素」「追加」「表示・移動」の3タブへ分け、同時に全操作を詰め込まず、選択中の作業だけをパネル全面へ表示する。要素選択、ドラッグ移動、テキスト編集、spoken_note編集、テキスト追加、画像追加、尻尾付き吹き出し追加、吹き出し選択時の頂点ハンドル移動、アニメーションstep指定と最終step移動、フォントサイズを含むスタイル変更、ページ追加、ページ複製、`P` キーによるページ一覧からの移動、`E` キーによる通常URL/編集URLの切り替え、`V` キーによる編集UI表示/非表示切り替え、`Save HTML` による対象HTMLの上書き保存を確認する。Spoken Note欄では `橋渡し`、`話す内容`、`指差し`、`次の一言` の不足がその場で分かることを確認する。
6. `Export PDF` で対象HTMLを先に上書きし、同じディレクトリに同名PDF（既定は `output/index.pdf`）が生成されることを確認する。
7. `file://` で開いた場合、`Save HTML` はブラウザのファイル保存ピッカーまたはダウンロードへフォールバックし、`Export PDF` は印刷ダイアログを開くことを確認する。
8. `scripts/validate_editor_workspace.js <index.html> --width 1280 --height 720` と1920x980相当を実行し、実スライドが左上のstage内に収まること、編集パネルがその下へドックされること、右側の台本欄が十分な高さを持つこと、フロート／再ドック、`V` 切替を確認する。その後、`?edit=1` なしの通常表示で、キーボード操作、発表者ビュー、印刷表示が壊れていないことを確認する。
9. 20分以上のデッキでページ追加、複製、本文・図表・ノート変更を行った場合は、`data-delivery-mode`、`data-estimated-seconds`、`data-content-model-type`、`data-evidence-artifact-ids`、`data-source-unit-ids`、`data-flow-phase`、`data-phase-question`、`data-speaker-purpose` を保持または更新する。deck rootの `data-design-system-id` / `data-design-system-version` も保持する。空白ページと複製ページは説明契約未完了のdraftとして扱う。
10. 内容を変更した場合は必ず `05-lt-slide-review` を実行し、`validate_explanation_depth.py` と `validate_talkability.py` を含む契約検証が成功することを確認する。位置・色だけの変更でも、長時間LTのtraceability属性を削除していないことを確認する。

## Standard Command

PowerShellでは次を使う。

```powershell
$node=Join-Path $env:LOCALAPPDATA ".cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
if (!(Test-Path $node)) { $node=(Get-Command node -ErrorAction Stop).Source }
& $node .codex\skills\06-lt-slide-editor\scripts\inject_editor.js output\index.html
& $node .codex\skills\06-lt-slide-editor\scripts\serve_editor.js output\index.html
```

`serve_editor.js` は `Save HTML` 用の `POST /__lt_editor_save` と、`Export PDF` 用の `POST /__lt_editor_export_pdf` を提供する。PDF生成は Playwright を使うため、通常は同梱 Node.js で起動する。

出力先を分ける場合:

```powershell
& $node .codex\skills\06-lt-slide-editor\scripts\inject_editor.js output\index.html --out output\index.editable.html
```

## Editor Behavior

- 編集UIは `?edit=1` のときだけ起動する。
- `E` キーで通常URLと `?edit=1` 付き編集URLを切り替える。`?edit=1` がない通常表示では、編集UIを起動せずにこのショートカットだけを登録する。テキスト編集中、フォーム入力中、修飾キー付き入力では切り替えない。
- `V` キーで `?edit=1` 内の編集UI表示/非表示を切り替える。テキスト編集中、フォーム入力中、修飾キー付き入力では切り替えない。
- `P` キーで既存のページ一覧を開き、サムネイルから任意ページへ移動できるようにする。一覧を開く前が編集モードなら、ページ選択または `P` / `Escape` で一覧を閉じた後に編集モードへ戻す。テキスト、Spoken Note、フォームの入力中は `P` をショートカットとして扱わない。
- 閲覧モードでは編集パネル、選択枠、`contenteditable`、要素ドラッグ、編集用キー操作を無効化し、既存のスライド閲覧ショートカットを優先する。
- 編集画面は発表者ビュー風の2列構成を標準とする。左上に保存対象の実スライド、左下に要素・追加・移動パネル、右側にSpoken Note・保存・PDF操作を置き、スライドへ編集UIを重ねない。
- 左下の編集パネルは「選択要素」「追加」「表示・移動」の3タブを標準とし、一度に一つの作業面だけを表示する。要素をスライド上で選択したときは「選択要素」タブへ自動的に戻す。フィールドと操作ボタンは横スクロールなしで収め、暗い背景上のラベルに十分なコントラストを持たせる。
- 左下の編集パネルは既定でドックする。ヘッダーのドラッグまたは「フロート」で切り離せ、「ドックへ戻す」で元の領域へ戻せる。フロート位置は同じブラウザの `localStorage` に保存する。
- 対象要素は主に `.zone`。絶対配置の `left`, `top`, `width`, `height` を編集する。
- テキスト編集は選択要素内の文字要素を `contenteditable` にする。
- Spoken Note 欄は現在スライドの `data-spoken-note` を編集する。`橋渡し`、`話す内容`、`指差し`、`次の一言` の四区画を案内し、不足区画をdraft警告として表示する。スライド移動時は現在スライドのノートを読み直し、保存時はHTML属性として残す。
- 画像追加はローカルファイルをData URLとしてHTMLに埋め込む。配布用に軽く保ちたい場合は、後で `output/assets/` 参照へ差し替える。
- 選択要素のアニメーション順序は `Step` 欄で0以上の整数として変更できるようにする。選択したzone自身に `data-anim` がなく、子孫にアニメーション要素が一つだけある場合は、その子要素を編集対象にする。`最後に表示` は同じスライドの他要素より後へ移し、stepの空番が生じないよう0から連続値へ正規化する。アニメーション未設定の要素へstepを指定した場合は `fade` を既定にする。`アニメ確認` は現在ページをstep 0へ戻して閲覧モードに入り、矢印キーで順番を確認できるようにする。
- `prefers-reduced-motion: reduce` では移動・拡大・トランジションを止めても、未到達stepを最初から表示しない。印刷時だけは従来どおり全要素を表示する。
- 吹き出し追加は `.zone.lt-editor-speech-bubble` を生成し、本文と同じように直接編集・移動・リサイズできるようにする。吹き出しを選択したときは黄色い頂点ハンドルを表示し、ドラッグまたは矢印キーで尻尾の先端を上下左右へ移動できるようにする。先端位置に応じて付け根を本体の最寄りの辺へ自動追従させ、`data-tail-tip-x`、`data-tail-tip-y`、`data-tail-side` とCSS変数へ保存する。尻尾は `::before` で外枠、`::after` で内側を描くCSS疑似要素とし、本体の枠外へ約30px伸びる明確な三角形にする。尻尾の輪郭は吹き出し本体と同程度の約2pxにそろえ、白背景でも消えない範囲で太くしすぎない。内側は吹き出し本体の背景色へ追従させる。共通アニメーションの `clip-path` で枠外の尻尾を切り落とさず、尻尾の先端と指示対象の文字の間に5px以上の空きを残す。追加時は現在ページの最大stepより後の `data-step` を割り当てる。
- 保存は `serve_editor.js` の `POST /__lt_editor_save` へクリーンなHTMLを送信し、対象HTMLを上書きする。ダウンロード保存を標準経路にしない。
- `Save HTML` は成功時にサーバーが返した保存先パスをステータス表示する。失敗時は原因メッセージを表示し、押しても無反応に見える状態にしない。
- `Export PDF` は先に閲覧モードへ切り替え、選択枠、`contenteditable`、編集用ドラッグ状態を解除してから `POST /__lt_editor_export_pdf` へクリーンなHTMLを送信し、HTMLを上書きしてから同名PDFを出力する。`output/index.html` の場合は `output/index.pdf`。
- `file://` で開いた場合、`Save HTML` は File System Access API のファイル保存ピッカーへフォールバックする。利用できない場合は編集済みHTMLをダウンロードする。
- `file://` で開いた場合、`Export PDF` は先に閲覧モードへ切り替え、自動PDF生成の代わりに印刷ダイアログを開き、ユーザーが Save as PDF を選べるようにする。
- 通常の静的サーバーで開いた場合、`Save HTML` と `Export PDF` はローカル編集サーバーが必要である旨を表示する。完全自動の上書き保存や同名PDF出力が必要なときは必ず `serve_editor.js` を使う。
- 保存時は編集UI、選択枠、頂点ハンドル、`contenteditable`、一時クラスを取り除いてからHTML化する。尻尾の先端座標・接続辺・再描画用CSS変数はスライド内容として保持する。

## Implementation Rules

- 既存のSlideDeckランタイムを壊さない。編集機能は後置きの独立ランタイムとして注入する。
- CDN、外部ライブラリ、外部フォントを追加しない。
- 発表者ビュー `?presenter=1` では編集UIを起動しない。
- 印刷CSSに編集UIを出さない。
- 編集URLの切り替えはURLクエリを更新してページ遷移する。閲覧モードの切り替えは `?edit=1` 内だけで完結させる。通常表示URLや発表者ビューへ編集UIを出さない。
- 編集パネルのフロート移動はスライド要素のドラッグ移動と独立させる。ヘッダー内のボタンやフォーム操作ではパネル移動を開始しない。ドック時は発表者ビューの「次のスライド＋ショートカット」に相当する左下領域を使用する。
- 編集対象には発表者ビュー用のcloneを使わず、保存対象の `.deck` 内にある実スライドを縮小配置する。保存時は編集ワークスペース用の `left`、`top`、`transform` をHTMLから除去する。
- スライド本体は1280x720固定を維持する。
- 追加する `.slide` は既存スライドと同じ構造に寄せ、`.page-number` を再採番する。
- `.page-number` は既存デッキの表記を維持する。`1 / 28` 形式なら、追加・複製後も `1 / 30` のように総ページ数まで再計算し、単なる `1` へ変換しない。
- 追加する要素は `.zone` とし、`data-zone` を設定する。吹き出しは `data-zone="callout"` と `data-editor-element="speech-bubble"` を持たせる。
- 既存の `data-spoken-note` を保持し、Spoken Note 欄で編集できるようにする。
- 既存の `data-delivery-mode`、`data-estimated-seconds`、`data-content-model-type`、`data-evidence-artifact-ids`、`data-source-unit-ids`、`data-flow-phase`、`data-phase-question`、`data-speaker-purpose`、deck rootの `data-design-system-id` / `data-design-system-version` を保持する。ページ複製時に同じ時間・証拠・source unit・話者目的をそのまま確定扱いにせず、ユーザーが内容を更新するまでdraft表示またはレビューfindingとして残す。
- エディタの色変更でregistryのdesign-system specを暗黙に上書きしない。デザインシステム自体の追加・変更・削除は `07-lt-design-system-manager` へ戻し、個別ページの局所調整と区別する。
- 空白スライドや複製スライドを追加した後は、タイトル、具体的な投影アンカー、説明時間、spoken noteを埋めないまま完成品として保存・配布しない。
- 空白・複製スライドには `data-editor-draft` を付け、時間・証拠・source unit・問い・話者目的・spoken noteを元ページから確定値として引き継がない。
- 保存前後で対象HTMLの更新時刻が変わること、`Export PDF` 後に同名PDFの更新時刻が変わること、通常表示の初期スライド、次へ/前へ、`P` page overview、`A` reveal、`S` presenterを確認する。追加した吹き出しは尻尾まで表示され、頂点ハンドルのドラッグ後に付け根と二層の疑似要素が追従し、保存・再読込後も同じ形を保ち、指定したstepでだけ現れることを確認する。通常設定とreduced-motion設定の両方で、最終step指定の要素が初期表示されないことも確認する。

## Output

- 編集機能を注入したHTML。既定は `output/index.html`
- エディタから出力したPDF。既定は `output/index.pdf`
- 注入時に既存HTMLを上書きした場合のバックアップ。例: `output/index.html.bak-YYYYMMDD-HHMMSS`

最終回答では、対象HTML、注入結果、確認した編集機能、Save HTML の上書き結果、PDF出力結果、未確認の項目を簡潔に示す。

---
name: 06-lt-slide-editor
description: 04-lt-slide-build によって生成された HTML ライトニングトークデッキに、ブラウザ内エディタを追加する。Codex が output/index.html を変更し、スライドをインタラクティブに編集できるようにする必要がある場合に使用する。具体的には、配置済み要素の移動、テキスト編集、spoken_note編集、テキストや画像の追加、基本的なスタイルの適用、エディタパネルがスライドを邪魔する場合の移動、キーボードショートカットによるエディタモードと表示モードの切り替え、スライドの複製、空白スライドの追加、Save HTML による元HTMLの上書き、Export PDF による同名PDF出力を行う。その際、プレゼン表示、発表者ビュー、印刷、レビューの挙動は維持すること。
---

# 06 LT Slide Editor

`04-lt-slide-build` が生成した `output/index.html` に、ブラウザ内エディターを追加する。通常の発表モードは変えず、`?edit=1` のときだけ編集UIを表示する。

## Required Reads

- `references/editor-contract.md`
- スクリプトを調整する場合のみ `scripts/inject_editor.js` と `scripts/serve_editor.js`

## Workflow

1. 対象HTMLを確認する。指定がなければ `output/index.html` を使う。
2. 対象が `04-lt-slide-build` 系の構造を持つことを確認する。最低限 `.deck` と `.slide` が必要。
3. `scripts/inject_editor.js` を実行して編集ランタイムを注入する。
4. `scripts/serve_editor.js` で対象HTMLをローカル配信し、表示された `http://127.0.0.1:<port>/?edit=1` を開く。
5. 要素選択、ドラッグ移動、テキスト編集、spoken_note編集、テキスト追加、画像追加、フォントサイズを含むスタイル変更、ページ追加、ページ複製、`E` キーによる通常URL/編集URLの切り替え、`V` キーによる編集UI表示/非表示切り替え、`Save HTML` による対象HTMLの上書き保存を確認する。
6. `Export PDF` で対象HTMLを先に上書きし、同じディレクトリに同名PDF（既定は `output/index.pdf`）が生成されることを確認する。
7. `file://` で開いた場合、`Save HTML` はブラウザのファイル保存ピッカーまたはダウンロードへフォールバックし、`Export PDF` は印刷ダイアログを開くことを確認する。
8. `?edit=1` なしの通常表示で、キーボード操作、発表者ビュー、印刷表示が壊れていないことを確認する。
9. 必要なら `05-lt-slide-review` で視覚レビューする。

## Standard Command

PowerShellでは次を使う。

```powershell
$node="C:\Users\okuto\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
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
- 閲覧モードでは編集パネル、選択枠、`contenteditable`、要素ドラッグ、編集用キー操作を無効化し、既存のスライド閲覧ショートカットを優先する。
- 編集パネルはヘッダーをドラッグして移動でき、位置は同じブラウザの `localStorage` に保存する。
- 対象要素は主に `.zone`。絶対配置の `left`, `top`, `width`, `height` を編集する。
- テキスト編集は選択要素内の文字要素を `contenteditable` にする。
- Spoken Note 欄は現在スライドの `data-spoken-note` を編集する。スライド移動時は現在スライドのノートを読み直し、保存時はHTML属性として残す。
- 画像追加はローカルファイルをData URLとしてHTMLに埋め込む。配布用に軽く保ちたい場合は、後で `output/assets/` 参照へ差し替える。
- 保存は `serve_editor.js` の `POST /__lt_editor_save` へクリーンなHTMLを送信し、対象HTMLを上書きする。ダウンロード保存を標準経路にしない。
- `Save HTML` は成功時にサーバーが返した保存先パスをステータス表示する。失敗時は原因メッセージを表示し、押しても無反応に見える状態にしない。
- `Export PDF` は先に閲覧モードへ切り替え、選択枠、`contenteditable`、編集用ドラッグ状態を解除してから `POST /__lt_editor_export_pdf` へクリーンなHTMLを送信し、HTMLを上書きしてから同名PDFを出力する。`output/index.html` の場合は `output/index.pdf`。
- `file://` で開いた場合、`Save HTML` は File System Access API のファイル保存ピッカーへフォールバックする。利用できない場合は編集済みHTMLをダウンロードする。
- `file://` で開いた場合、`Export PDF` は先に閲覧モードへ切り替え、自動PDF生成の代わりに印刷ダイアログを開き、ユーザーが Save as PDF を選べるようにする。
- 通常の静的サーバーで開いた場合、`Save HTML` と `Export PDF` はローカル編集サーバーが必要である旨を表示する。完全自動の上書き保存や同名PDF出力が必要なときは必ず `serve_editor.js` を使う。
- 保存時は編集UI、選択枠、`contenteditable`、一時クラスを取り除いてからHTML化する。

## Implementation Rules

- 既存のSlideDeckランタイムを壊さない。編集機能は後置きの独立ランタイムとして注入する。
- CDN、外部ライブラリ、外部フォントを追加しない。
- 発表者ビュー `?presenter=1` では編集UIを起動しない。
- 印刷CSSに編集UIを出さない。
- 編集URLの切り替えはURLクエリを更新してページ遷移する。閲覧モードの切り替えは `?edit=1` 内だけで完結させる。通常表示URLや発表者ビューへ編集UIを出さない。
- 編集パネルの移動はスライド要素のドラッグ移動と独立させる。ヘッダー内のボタンやフォーム操作ではパネル移動を開始しない。
- スライド本体は1280x720固定を維持する。
- 追加する `.slide` は既存スライドと同じ構造に寄せ、`.page-number` を再採番する。
- 追加する要素は `.zone` とし、`data-zone` を設定する。
- 既存の `data-spoken-note` を保持し、Spoken Note 欄で編集できるようにする。
- 保存前後で対象HTMLの更新時刻が変わること、`Export PDF` 後に同名PDFの更新時刻が変わること、通常表示の初期スライド、次へ/前へ、`A` reveal、`S` presenterを確認する。

## Output

- 編集機能を注入したHTML。既定は `output/index.html`
- エディタから出力したPDF。既定は `output/index.pdf`
- 注入時に既存HTMLを上書きした場合のバックアップ。例: `output/index.html.bak-YYYYMMDD-HHMMSS`

最終回答では、対象HTML、注入結果、確認した編集機能、Save HTML の上書き結果、PDF出力結果、未確認の項目を簡潔に示す。

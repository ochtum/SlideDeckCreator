---
name: 05-lt-slide-review
description: Playwrightを使ってLT用HTMLスライドの視覚表示をレビューする。Use when Codex needs to inspect output/index.html or another 16:9 HTML slide deck for animation-complete states, overlapping elements or text, clipped/overflowing content, broken images, and margins that are too close to slide edges before delivery.
---

# 05 LT Slide Review

PlaywrightでHTMLスライドを実ブラウザ表示し、各ページをアニメーション完了後の状態にして視覚崩れを検査する。`04-lt-slide-build` 後の最終QA、またはユーザーから「見切れ」「重なり」「余白」「表示確認」を求められたときに使う。

## 必ず読むもの

- 必要に応じて `references/review-criteria.md`
- 実行スクリプトを調整する場合のみ `scripts/review_deck.js`

## ワークフロー

1. 対象HTMLを確認する。指定がなければ `output/index.html` を対象にする。
2. Playwright実行環境を確認する。通常は同梱Node.jsと `NODE_PATH` を使う。
3. `scripts/review_deck.js` を実行し、通常表示と発表者ビューの両方を全スライドのアニメーション完了状態で撮影・検査する。
4. `.lt-slide-work/review/` の `review-report.md`、`review-report.json`、`slide-XX.png`、`presenter-slide-XX.png` を確認する。
5. findingが出た場合は、通常表示・発表者ビューそれぞれのスクリーンショットとDOM上の要素名・座標を根拠に修正箇所を特定する。
6. 修正後に再実行し、findingが解消したことを確認する。
7. 最終回答では、検査対象、ページ数、検出件数、主要な問題、レポートの場所を簡潔に示す。

## 標準実行

PowerShellでは次を使う。標準では通常表示と `?presenter=1` の発表者ビューを両方レビューする。スクリプトは同梱Node.jsの隣にあるPlaywrightを自動探索するが、見つからない場合は `NODE_PATH` を明示する。

```powershell
$node="C:\Users\okuto\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
& $node .codex\skills\05-lt-slide-review\scripts\review_deck.js output\index.html --out .lt-slide-work\review
```

Playwrightの解決に失敗する場合は、次を先に設定する。

```powershell
$env:NODE_PATH="C:\Users\okuto\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules;C:\Users\okuto\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\.pnpm\node_modules"
```

findingを確認しながら途中で止めずにレポートだけ作りたい場合は `--no-fail` を付ける。

```powershell
& $node .codex\skills\05-lt-slide-review\scripts\review_deck.js output\index.html --out .lt-slide-work\review --no-fail
```

通常表示だけを確認したい場合は `--skip-presenter`、発表者ビューだけを確認したい場合は `--presenter` を付ける。

## 判定方針

- 各スライドは `window.slideDeck.show(index, true, false)` があればそれを使って最終step表示にする。
- 上記APIがない場合は、対象 `.slide` を `active` にし、すべての `[data-anim]` に `shown` を付ける。
- 発表者ビューの検査では、同じブラウザ内で通常表示ページも開き、投影側の現在スライドDOMスナップショットと `#presenterCurrent` のDOMが一致するか確認する。
- 発表者ビューでは、現在プレビュー、次プレビュー、ノート、タイマー、操作ボタン、ショートカット一覧の表示崩れ、ウィンドウ外へのはみ出し、画像破損を検出する。
- `.zone[data-zone]` 同士の交差を検出する。`data-overlap-ok`、背景、コネクタ、フッター、ページ番号は重なり検査から除外する。
- テキスト要素の `scrollWidth > clientWidth` または `scrollHeight > clientHeight` を検出する。
- 可視要素がスライド境界からはみ出した場合は検出する。
- 主要なテキスト・カード・画像がスライド端に近すぎる場合は検出する。デフォルトの内側余白は40px。
- 画像の `naturalWidth` または `naturalHeight` が0の場合は検出する。
- 機械判定は誤検出があり得るため、PNGスクリーンショットで目視確認してから修正判断する。

## 重要な注意

- このスキルは「視覚レビュー」を目的とする。HTML生成やPDF生成は `04-lt-slide-build` に戻して行う。
- 判定はアニメーション終了後の状態で行う。`04b-lt-slide-animation` でstepが正しく付与されていない場合、アニメーションが途中で止まった状態で検査される。
- findingがない場合でも、少なくとも数枚のスクリーンショットを目視で確認する。
- 余白違反はブランドバッジ、フッター、ページ番号、背景装飾には適用しない。
- `overflow: hidden` で問題が隠れている可能性がある場合は、スクリーンショットとDOM座標の両方を見る。
- 発表者ビューのfindingは、投影側との差分や手元画面の操作性に直結するため、通常表示のfindingがない場合でも確認する。

## 出力

- `.lt-slide-work/review/review-report.md`
- `.lt-slide-work/review/review-report.json`
- `.lt-slide-work/review/slide-XX.png`
- `.lt-slide-work/review/presenter-slide-XX.png`

---
name: 05-lt-slide-review
description: Playwrightを使ってLT用HTMLスライドの視覚表示と内容忠実性をレビューする。Use when Codex needs to inspect a 16:9 HTML slide deck for animation-complete states, overlapping or clipped content, presenter notes that explain each page, and complete traceable coverage of the input including tables, code blocks, diagrams, and configuration examples.
---

# 05 LT Slide Review

PlaywrightでHTMLスライドを実ブラウザ表示し、各ページをアニメーション完了後の状態にして視覚崩れを検査する。あわせて、ストーリー・設計図・元入力と照合し、各ページのspoken-noteがページの主張と具体例を説明していること、元資料の内容（表・コード・設定例・図を含む）が端折られず追跡可能であることを検査する。`04-lt-slide-build` 後の最終QA、またはユーザーから「見切れ」「重なり」「余白」「内容確認」を求められたときに使う。

## 必ず読むもの

- 必要に応じて `references/review-criteria.md`
- 内容・ノート・入力カバレッジを確認する場合は必ず `references/content-coverage.md`
- 初見者理解、ページ間接続、後読性を確認する場合は `../01-lt-slide-story/references/presentation-quality.md`
- 20分以上では `../01-lt-slide-story/references/explanation-depth.md`
- Storyの `style_profile.status` が `applied` の場合は `config/slide-style-profile.md`
- 実行スクリプトを調整する場合のみ `scripts/review_deck.js`

## ワークフロー

1. 対象HTMLと対応する `01-story.yaml`、`02-blueprint.yaml`、元入力を確認する。指定がなければ `output/index.html` を対象にする。シリーズでは各パートを独立して確認する。
2. Playwright実行環境を確認する。通常は同梱Node.jsと `NODE_PATH` を使う。
3. 対応するストーリーの `visual_plan` と設計図を読み、`review_deck.js` に `--story <01-story.yaml> --blueprint <02-blueprint.yaml>` を渡す。スクリプトは `validate_spoken_notes.py`、`validate_talkability.py`、`validate_visual_plan.py`、`validate_explanation_depth.py` を実行し、いずれかが失敗したら視覚findingがなくても不合格としてレポートに残す。シリーズの標準的な出力パスでは対応するファイルを自動検出できるが、明示指定を優先する。
4. `references/content-coverage.md` と `presentation-quality.md` に従って、全スライドについて次を確認する。talkability v2の `spoken_note` は `橋渡し`、`話す内容`、`指差し`、`次の一言` の四区画を持つ。ノートだけを上から読んで、冒頭の問題、各phaseの問いと答え、次への接続、Demoの操作と観測、明日の一手を再現できるか確認する。ストーリーとHTMLの文字列一致だけで合格にしてはならない。初見者に必要な定義・具体例、前ページからの接続、後読時の主語と結論も照合する。入力から採用した表、コード、設定例、図、フローは、要約の過程で消さず、HTMLのtable/pre/code/SVGまたは提供画像に追跡可能に解決する。スタイルプロファイルが適用されている場合は、入力にある検証過程や失敗が成功結果だけへ圧縮されていないこと、発表者の疑問・判断・気づきが残ること、具体物が口調だけで置換されていないことを確認する。
4a. `full-equivalence` ではルートStoryに対して `audit_content_equivalence.py --inventory <source-inventory.yaml> --story <root-story.yaml> --html <all-part-index.html> --require-full-equivalence --report <review>/content-equivalence.md` を実行する。シリーズ概要のtopic coverageや文字列一致だけで合格にしない。design-system選択時はStory、Blueprint、HTMLのID/versionとregistryを `manage_design_system.py validate-binding` で照合する。
5. `scripts/review_deck.js` を実行し、通常表示と発表者ビューの両方を全スライドのアニメーション完了状態で撮影・検査する。発表者ビューでは `話す内容` の主領域、phaseの問いの独立領域、タイマー更新中のスクロール保持も検査する。同スクリプトから `validate_animation_choreography.py` を実行し、BlueprintからHTMLへのpreset消失、同じsignatureの3ページ連続、step数の均一化、一種類への偏りも不合格にする。代表的な定義、比較、フロー、Demo、Takeawayは初期状態と各stepも実ブラウザで確認する。
6. `.lt-slide-work/review/` の `review-report.md`、`review-report.json`、`slide-XX.png`、`presenter-slide-XX.png` に加え、内容カバレッジの照合結果を確認する。
7. findingが出た場合は、通常表示・発表者ビューそれぞれのスクリーンショット、DOM上の要素名・座標、対応する入力行またはsource assetを根拠に修正箇所を特定する。内容不足は、抽象的なカードを足すだけで済ませず、欠落した表・コード・設定・図・完了条件を戻す。
8. 修正後に視覚レビューと内容カバレッジ照合を再実行し、findingが解消したことを確認する。
9. 最終回答では、検査対象、ページ数、視覚finding数、内容／ノート／入力カバレッジfinding数、主要な問題、レポートの場所を簡潔に示す。

## 標準実行

PowerShellでは次を使う。標準では通常表示と `?presenter=1` の発表者ビューを両方レビューする。スクリプトは同梱Node.jsの隣にあるPlaywrightを自動探索するが、見つからない場合は `NODE_PATH` を明示する。

```powershell
$node=Join-Path $env:LOCALAPPDATA ".cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
if (!(Test-Path $node)) { $node=(Get-Command node -ErrorAction Stop).Source }
& $node .codex\skills\05-lt-slide-review\scripts\review_deck.js output\index.html --story .lt-slide-work\01-story.yaml --blueprint .lt-slide-work\02-blueprint.yaml --out .lt-slide-work\review
```

Playwrightの解決に失敗する場合は、次を先に設定する。

```powershell
$env:NODE_PATH="C:\Users\okuto\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules;C:\Users\okuto\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\.pnpm\node_modules"
```

findingを確認しながら途中で止めずにレポートだけ作りたい場合は `--no-fail` を付ける。

```powershell
& $node .codex\skills\05-lt-slide-review\scripts\review_deck.js output\index.html --story .lt-slide-work\01-story.yaml --blueprint .lt-slide-work\02-blueprint.yaml --out .lt-slide-work\review --no-fail
```

通常表示だけを確認したい場合は `--skip-presenter`、発表者ビューだけを確認したい場合は `--presenter` を付ける。

## 判定方針

- 各スライドは `window.slideDeck.show(index, true, false)` があればそれを使って最終step表示にする。
- 上記APIがない場合は、対象 `.slide` を `active` にし、すべての `[data-anim]` に `shown` を付ける。
- 発表者ビューの検査では、同じブラウザ内で通常表示ページも開き、投影側の現在スライドDOMスナップショットと `#presenterCurrent` のDOMが一致するか確認する。
- 発表者ビューでは、現在プレビュー、次プレビュー、ノート、タイマー、操作ボタン、ショートカット一覧の表示崩れ、ウィンドウ外へのはみ出し、画像破損を検出する。
- `話す内容` が主表示領域として十分な高さを持たない場合は `presenter-primary-script-too-small`、phaseの問いが独立表示されない場合は `presenter-question-missing`、問い・文脈領域が狭すぎる場合は `presenter-context-too-small` とする。
- 長い `話す内容` をスクロールして1秒以上待ち、タイマーが進んだ後に `scrollTop` が変化した場合は `presenter-note-scroll-reset` として不合格にする。
- `.zone[data-zone]` 同士の交差を検出する。`data-overlap-ok`、背景、コネクタ、フッター、ページ番号は重なり検査から除外する。
- テキスト要素の `scrollWidth > clientWidth` または `scrollHeight > clientHeight` を検出する。
- 可視要素がスライド境界からはみ出した場合は検出する。
- 主要なテキスト・カード・画像がスライド端に近すぎる場合は検出する。デフォルトの内側余白は40px。
- 画像の `naturalWidth` または `naturalHeight` が0の場合は検出する。
- visual zone、card、playbook、table containerについて、可視テキスト、画像、SVG、table、pre/code、または意味のある図解要素を持たない枠線だけの領域を検出する。これは `empty-visual-zone` として不合格にする。意図的な余白は要素そのものを置かず、空のcontainerで表現しない。
- `need: required` の `visual_plan` が、画像・SVG・表・コードのいずれにも解決されていない場合は `unresolved-visual-plan` として不合格にする。汎用カードだけでは解決扱いにしない。
- 各HTMLスライドの `data-spoken-note` を対応するストーリーの同じIDの `spoken_note` と照合する。欠落・空文字・別ページの説明・画面の文字の単純な復唱は `spoken-note-missing`、`spoken-note-mismatch`、`spoken-note-insufficient` として不合格にする。
- `validate_spoken_notes.py` または `validate_talkability.py` の失敗、全ページ共通の仮ノート、同一ノートの完全重複、橋渡し・話す内容・指差し・次の一言の欠落は `spoken-note-template` として不合格にする。HTMLとストーリーが同じ仮ノートを持つことは、引継ぎ成功ではなく同じ不備の伝播である。
- スタイルプロファイルが適用されている場合、適用ルールとApplication Limitsを照合する。実験・検証資料で成功だけに圧縮された場合は `style-under-applied`、記号・顔文字・感情ページが上限を超える、または無関係なページへ機械的に追加された場合は `style-over-applied`、入力にない体験が追加された場合は `style-fabricated-experience` として不合格にする。
- spoken-noteは、そのページの主張、表示している具体物（表・コード・設定・図・フロー）の読み方、聴衆が取る判断または次の一手のうち必要なものを説明しているか、ページ単位で人間またはレビュー担当エージェントが意味を確認する。機械的な文字列一致だけで合格にしてはならない。
- `question_spine` の各phaseで、聴衆の問いに対する答えがページ群と台本から実際に得られ、最後のページの `次の一言` が次phaseの問いを必要にしているか確認する。phase名だけの章区切りは `narrative-discontinuity` とする。
- Demoは3つ以上の具体操作と画面で観測できる結果を持ち、fallbackを含む。構成図の説明だけ、または「確認する」だけなら `demo-not-observable` とする。
- Takeawayは時間枠、最初の操作、残る成果物、完了条件を持つ。「試す」「検討する」だけなら `takeaway-not-actionable` とする。
- 全本編ページの説明時間が同じ値へ均一化されていないか確認する。定義・比較・手順・Demoの役割差があるのに同一秒数なら `uniform-pacing` とする。
- 初見者が知らない用語・略語・固有工程について、初出の平易な定義、必要性、具体例のいずれかが画面またはノートにあることを確認する。欠落は `first-time-audience-gap` として不合格にする。
- 表紙、自己紹介、Thanks以外の各スライドで、`reader_context` と `connection_from_previous` またはHTMLの `data-reader-context` と `data-story-bridge` を照合する。前ページとの因果が説明できない場合は `narrative-discontinuity`、後から一枚だけを見て主語・根拠・結論を再構成できない場合は `reader-context-missing` として不合格にする。
- 新しい章・用語・抽象度の切替で、前提の再導入または次の問いがあることを確認する。単なる章見出しや箇条書きの並びでは接続済みとみなさない。
- `source_scope_audit`、`coverage_matrix`、`content_inventory`、`source_asset_inventory` を元入力と照合する。`full coverage` の学習単位、採用した画像、表、コードブロック、設定例、Mermaid／フローは、少なくとも一つのスライドとHTML実装へ対応付く必要がある。採用しない場合は、理由と同じ意味を保つ代替実装を残す。
- 表・コード・設定例・フローを「要約したカード」だけに置換してはいけない。対応するHTML table、pre/code、config表示、インラインSVGまたは提供画像が存在し、最小の具体データを読めることを確認する。欠落は `source-asset-omitted`、内容が抽象化されすぎて再現不能な場合は `evidence-insufficient` として不合格にする。
- 20分以上では、各ページの `data-estimated-seconds` に見合う `talking_points` と投影面の `visible_anchors` を照合する。60秒以上を割り当てたページが大見出し、一文、汎用チェックだけなら `explanation-thin` として不合格にする。
- 同一の表、フロー、チェックリスト、画像が複数ページで繰り返される場合、ページ固有のfocus、highlight、注釈があることを確認する。異なる主張に無注釈で再利用した場合は `evidence-reused-without-focus` として不合格にする。
- 「対象を確認する」「証拠を残す」「完了条件を確認する」のような汎用チェックが複数ページへ自動挿入されている場合は `generic-explanation` として不合格にする。
- 入力の主張、手順、注意点、デモ候補のすべてがストーリーのカバレッジ先を持つことを確認する。時間短縮のために省略する場合は、ユーザー承認済みの縮小範囲と理由を記録しなければならない。
- 機械判定は誤検出があり得るため、PNGスクリーンショットで目視確認してから修正判断する。

## 重要な注意

- このスキルは「視覚レビュー」を目的とする。HTML生成やPDF生成は `04-lt-slide-build` に戻して行う。
- 判定はアニメーション終了後の状態で行う。`04-lt-slide-build/references/04b-animation.md` の工程でstepが正しく付与されていない場合、アニメーションが途中で止まった状態で検査される。
- 完成状態だけが整っていても、途中stepが同じ上昇表示の反復、意味のない順序、結論の先出しになっている場合は `motion-monotony` または `motion-sequence-mismatch` として不合格にする。
- findingがない場合でも、少なくとも数枚のスクリーンショットを目視で確認する。
- 余白違反はブランドバッジ、フッター、ページ番号、背景装飾には適用しない。
- `overflow: hidden` で問題が隠れている可能性がある場合は、スクリーンショットとDOM座標の両方を見る。
- 発表者ビューのfindingは、投影側との差分や手元画面の操作性に直結するため、通常表示のfindingがない場合でも確認する。
- 入力資料の完全性が最優先である。読みやすさのための圧縮は許可するが、入力の表、コード、設定、図、フロー、完了条件を無断で削除したり、説明力を失う要約へ置き換えたりしてはならない。
- スタイルレビューの結論は `under-applied`、`balanced`、`over-applied` のいずれかで報告し、各findingには対応する入力またはプロファイルのrule IDを残す。

## 出力

- `.lt-slide-work/review/review-report.md`
- `.lt-slide-work/review/review-report.json`
- `.lt-slide-work/review/slide-XX.png`
- `.lt-slide-work/review/presenter-slide-XX.png`
- `.lt-slide-work/review/content-coverage.md`（ページ別spoken-note・初見者理解・接続・後読性照合、入力・source asset・HTML実装の対応、未解決項目）

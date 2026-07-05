---
name: 04-lt-slide-build
description: .lt-slide-work の成果物をもとに、最終的なライトニングトーク用スライドデッキのビルド全体を統括する。ページ構築、アニメーション、実行時コントロール、発表者ビュー、PDFエクスポート、パッケージング、ビジュアル検証を、04a / 04b / 04c の LTスライドスキルに委譲して実行する。
---

# 04 LT Slide Build

`.lt-slide-work/02-blueprint.yaml` と `.lt-slide-work/visuals-manifest.yaml` から、配布可能な `output/index.html`、`output/index.pdf`、`output/index_html.zip` を完成させる統合スキル。

このスキルは細部を一手に実装しない。成果の安定性を上げるため、必ず次の下位スキルへ段階的に分けて作業する。

1. `../04a-lt-slide-pages/SKILL.md` - 静的スライドページ作成
2. `../04b-lt-slide-animation/SKILL.md` - アニメーション付与とstep整理
3. `../04c-lt-slide-runtime/SKILL.md` - ランタイム、発表者ビュー、PDF、ZIP、検証

## Workspace Contract

```text
<project-root>/
├─ config/
│  └─ presenter.json
├─ .lt-slide-work/
│  ├─ 01-story.yaml
│  ├─ 02-blueprint.yaml
│  ├─ visuals-manifest.yaml
│  └─ visuals/
└─ output/
   ├─ index.html
   ├─ index.pdf
   ├─ index_html.zip
   └─ assets/
```

発表者情報は `config/presenter.json` を参照する。削除対象フォルダへ移動または複製しない。ビルド中の一時ファイルは `.lt-slide-work/` に置き、`output/` には利用者へ渡す完成品だけを残す。

## Required Reads

- `references/design-system.md`
- `references/build-contract.md`
- `../04a-lt-slide-pages/SKILL.md`
- `../04b-lt-slide-animation/SKILL.md`
- `../04c-lt-slide-runtime/SKILL.md`
- 必要に応じて `assets/deck-shell.html`

## Workflow

1. `.lt-slide-work/02-blueprint.yaml` と `.lt-slide-work/visuals-manifest.yaml` を検証する。必須画像が未解決なら先に解消する。
2. `04a-lt-slide-pages` の指示に従い、設計図から静的な `.slide` 群を作る。ここではページ送り、発表者ビュー、複雑なアニメーション制御を作り込まない。
3. `04b-lt-slide-animation` の指示に従い、静的スライドへ `data-anim`、step、reduced motion、印刷時全表示の契約を付与する。
4. `04c-lt-slide-runtime` の指示に従い、固定ランタイムを適用してショートカット、一覧表示、ショートカット一覧付き発表者ビュー、同期、PDF CSS、監査、ZIP化を完成させる。
5. `scripts/validate_deck.py output/index.html` を実行する。
6. ブラウザで全ページを1280x720表示し、初期状態と全step表示状態を確認する。通常表示ではスライド外側に上下左右の表示余白があることも確認する。
7. `S` で発表者ビューを開き、現在・次スライド、ノート、タイマー、ショートカット一覧、双方向同期を確認する。各stepで投影側と現在プレビューの一致を確認する。
8. 印刷プレビューでCSS用紙サイズ、余白0、全step表示を確認し、`output/index.pdf` を生成する。
9. `scripts/validate_pdf.py output/index.pdf output/index.html` を実行し、ページ数と16:9寸法を検証する。
10. PDFをPNGへレンダリングし、全ページの見切れ、余白、背景、画像切れを確認する。
11. 必要に応じて `05-lt-slide-review` を使い、Playwrightで視覚レビューする。

## Integration Rules

- HTML/CSS/Vanilla JavaScriptのみ。
- 外部CDN、外部フォント、外部アイコンライブラリは禁止。
- `output/index.html` は `assets/deck-shell.html` を起点にする。ランタイムの主要機能を毎回書き直さない。
- スライド本文の生成、アニメーション付与、ランタイム適用を同時に進めない。段階ごとに出力を見てから次へ進む。
- `.slide` は1280x720固定。画面にはdeck全体を `scale()` して収める。
- ブラウザ投影時はdeckをビューポート端へ貼り付けない。`fit()` は上下左右に最低32px、推奨48pxの表示余白を差し引いてscaleを計算する。
- 印刷用紙は `@page { size: 13.333333in 7.5in; margin: 0; }` に固定する。
- まとめとサンクスを最後に連続配置する。`validate_deck.py` が通るよう、最後の2枚は `data-role="recap"`、`data-role="thanks"` にする。
- 各 `.slide` に設計図の `spoken_note` を `data-spoken-note` として埋め込む。HTML属性として正しくエスケープし、投影面には表示しない。

## Quality Gate

次を満たすまで完了にしない。

- `output/index.html` が存在する
- `output/index.pdf` が存在する
- `output/index_html.zip` が存在する
- `validate_deck.py` が成功する
- `validate_pdf.py` が成功する
- 全スライドの初期状態と全step表示状態を目視確認済み
- 発表者ビューの現在プレビューが投影側DOM状態と一致する
- 発表者ビューにショートカット一覧が表示される
- PDFレンダリング結果に見切れ、余白欠落、背景欠落、画像切れがない

## Output

- `output/index.html`
- `output/index.pdf`
- `output/index_html.zip`
- `output/assets/*`

最終回答ではファイルへのリンク、物理枚数、検証結果だけを簡潔に示す。

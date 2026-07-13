---
name: 04-lt-slide-build
description: .lt-slide-work の成果物をもとに、最終的なライトニングトーク用スライドデッキのビルド全体を統括する。ページ構築、アニメーション、実行時コントロール、発表者ビュー、PDFエクスポート、パッケージング、ビジュアル検証を、内蔵の04a / 04b / 04c工程で順に実行する。
---

# 04 LT Slide Build

`.lt-slide-work/02-blueprint.yaml` と `.lt-slide-work/visuals-manifest.yaml` から、配布可能な `output/index.html`、`output/index.pdf`、`output/index_html.zip` を完成させる統合スキル。シリーズマニフェストの場合は、各パートを独立した配布物として完成させる。

このスキルは細部を一手に実装しない。成果の安定性を上げるため、必ず次の内部工程へ段階的に分けて作業する。内部工程は利用者が直接呼び出すスキルではない。

1. `references/04a-pages.md` - 静的スライドページ作成
2. `references/04b-animation.md` - アニメーション付与とstep整理
3. `references/04c-runtime.md` - ランタイム、発表者ビュー、PDF、ZIP、検証

## Workspace Contract

```text
<project-root>/
├─ config/
│  ├─ presenter.json
│  └─ slide-style-profile.md
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

## Series Mode

ルートの `01-story.yaml` が `kind: lt-slide-series` なら、`../01-lt-slide-story/references/series-schema.md` を読み、各 `parts` を `order` 順に完全にビルドする。各パートは一つの独立したデッキであり、全パートを連結した巨大な `output/index.html` を作らない。

```text
output/
├─ part-01-start-safe/
│  ├─ index.html
│  ├─ index.pdf
│  ├─ index_html.zip
│  └─ assets/
├─ part-02-knowledge-map/
│  └─ ...
└─ part-03-operate-improve/
   └─ ...
```

- 各パートの `blueprint_file`、`visuals_manifest_file`、`output_dir` だけをそのパートの入出力として使う。
- `04a`、`04b`、`04c` をパートごとに順番に完了させる。あるパートのHTML、PDF、ZIP、assetsを他パートと共有しない。
- 検証、目視確認、発表者ビュー確認、PDF検証、ZIP化は各 `output_dir` ごとに完了させる。
- 最終報告では全パートのタイトル、物理枚数、HTML/PDF/ZIPへのリンク、検証結果を列挙する。

## Required Reads

- `references/design-system.md`
- `references/build-contract.md`
- `references/04a-pages.md`
- `references/04b-animation.md`
- `references/04c-runtime.md`
- `../01-lt-slide-story/references/presentation-quality.md`
- 必要に応じて `assets/deck-shell.html`
- Storyの `style_profile.status` が `applied` の場合は `config/slide-style-profile.md` の Application Limits を確認する。

## Workflow

1. ルートの `01-story.yaml` が単発かシリーズかを確認する。単発は `.lt-slide-work/02-blueprint.yaml` と `.lt-slide-work/visuals-manifest.yaml`、シリーズは各パートの指定ファイルを検証する。必須画像が未解決なら先に解消する。各パートについて、`../01-lt-slide-story/scripts/validate_duration_floor.py --story <part-01-story.yaml> --blueprint <blueprint_file>` と `../02-lt-slide-blueprint/scripts/validate_visual_plan.py --story <part-01-story.yaml> --blueprint <blueprint_file>` を実行し、指定時間の本編最小枚数または必須ビジュアル計画を満たさなければビルドを中止する。
2. `references/04a-pages.md` の指示に従い、設計図から静的な `.slide` 群を作る。ここではページ送り、発表者ビュー、複雑なアニメーション制御を作り込まない。
3. `references/04b-animation.md` の指示に従い、静的スライドへ `data-anim`、step、reduced motion、印刷時全表示の契約を付与する。
4. `references/04c-runtime.md` の指示に従い、固定ランタイムを適用してショートカット、一覧表示、ショートカット一覧付き発表者ビュー、同期、PDF CSS、監査、ZIP化を完成させる。
5. `scripts/validate_deck.py <part-output>/index.html` と `../01-lt-slide-story/scripts/validate_duration_floor.py --story <part-01-story.yaml> --html <part-output>/index.html` を各デッキに実行する。単発の `<part-output>` は `output` とする。
6. ブラウザで全ページを1280x720表示し、初期状態と全step表示状態を確認する。通常表示ではスライド外側に上下左右の表示余白があることも確認する。
7. `S` で発表者ビューを開き、現在・次スライド、ノート、タイマー、ショートカット一覧、双方向同期を確認する。各stepで投影側と現在プレビューの一致を確認する。
8. 印刷プレビューでCSS用紙サイズ、余白0、全step表示を確認し、各 `<part-output>/index.pdf` を生成する。
9. `scripts/validate_pdf.py <part-output>/index.pdf <part-output>/index.html` を各デッキに実行し、ページ数と16:9寸法を検証する。
10. PDFをPNGへレンダリングし、全ページの見切れ、余白、背景、画像切れを確認する。
11. 必要に応じて `05-lt-slide-review` を使い、Playwrightで視覚レビューする。

## Integration Rules

- HTML/CSS/Vanilla JavaScriptのみ。
- 外部CDN、外部フォント、外部アイコンライブラリは禁止。
- `output/index.html` は `assets/deck-shell.html` を起点にする。ランタイムの主要機能を毎回書き直さない。
- スライド本文の生成、アニメーション付与、ランタイム適用を同時に進めない。段階ごとに出力を見てから次へ進む。
- スタイルプロファイルを直接解釈して、02-blueprintにない感情表現、記号、顔文字、装飾、短文スライドを追加してはならない。表現上の判断は設計図を正とし、プロファイルは上限の確認だけに使う。
- `.slide` は1280x720固定。画面にはdeck全体を `scale()` して収める。
- ブラウザ投影時はdeckをビューポート端へ貼り付けない。`fit()` は上下左右に最低32px、推奨48pxの表示余白を差し引いてscaleを計算する。
- 印刷用紙は `@page { size: 13.333333in 7.5in; margin: 0; }` に固定する。
- まとめとサンクスを最後に連続配置する。`validate_deck.py` が通るよう、最後の2枚は `data-role="recap"`、`data-role="thanks"` にする。
- 各 `.slide` に設計図の `spoken_note` を `data-spoken-note` として埋め込む。HTML属性として正しくエスケープし、投影面には表示しない。
- 各 `.slide` に `reader_context` と `narrative_continuity.bridge` を `data-reader-context`、`data-story-bridge` として埋め込む。発表者ビューではノートとともに表示し、話者が後からページ間の接続を再現できるようにする。
- 初見者向けに必要な平易な定義・具体例は、タイトルだけに頼らず本文または `content_model` で可視にする。章の切替、新用語、抽象度の切替では、設計図が指定した文脈ラベルを表示する。
- `content_model` を持つスライドは、型に対応する専用HTMLコンポーネントとして描画する。`table` は列と行、`flow` はノード・矢印・判断ゲート、`implementation-playbook` は成果物・担当・完了条件、`code` / `config` は読める最小断片を表示する。
- `content_model` が空、またはvisualが不要なスライドでは、visual zone・空のcard・枠線だけのコンテナを生成しない。本文／結論をレイアウトに合わせて広げるか、非空の具体的コンテンツを設計図へ戻して追加する。白い空枠は余白ではなく不具合として扱う。
- `KEY VIEW`、`PLAYBOOK`、汎用3カードなどのプレースホルダーだけで、具体的な `content_model` を置き換えてはならない。同じ汎用カード表示を3枚以上連続させない。
- 過去のビルドのページ数を固定値として扱わない。設計図の変更でページを追加・削除した場合は、HTMLの物理スライド数、ページ番号、発表者ビューの総数、PDFページ数、ZIP内のHTMLをすべて現在の構成へ更新する。
- 表紙、自己紹介、Thanksを除く本編枚数が、指定時間の最小枚数を下回るデッキをビルドしてはならない。30分以上は各デッキ本編28枚以上である。内容のない水増しではなく、代表例、比較、演習、デモ、判断ゲートを追加して満たす。
- シリーズでは、各パートのページ数を独立して更新する。シリーズ全体の合計を一つのデッキのページ番号や発表者ビュー総数に使わない。

## Quality Gate

次を満たすまで完了にしない。

- `need: required` の各 `visual_plan` が、対応する `.slide` の `data-visual-plan-id` と、画像・SVG・HTML表・HTMLコードの実装へ解決されている。説明を持たない汎用カードだけでは合格にしない。

- 単発は `output/index.html`、`output/index.pdf`、`output/index_html.zip`、シリーズは各 `output/<part-id>/` に同名の3ファイルが存在する
- 各デッキで `validate_deck.py` が成功する
- 各デッキで `validate_duration_floor.py --story <part-01-story.yaml> --html <part-output>/index.html` が成功する
- 各デッキで `validate_pdf.py` が成功する
- 全スライドの初期状態と全step表示状態を目視確認済み
- 発表者ビューの現在プレビューが投影側DOM状態と一致する
- 発表者ビューで `reader_context`、前ページからの `bridge`、`spoken_note` を確認でき、投影面を見ずに話の接続を再構成できる。
- 初見者が必要とする定義・具体例が、画面の本文または具体的な `content_model` として存在する。
- 発表者ビューにショートカット一覧が表示される
- PDFレンダリング結果に見切れ、余白欠落、背景欠落、画像切れがない
- How/Demoの各スライドで、設計図の `content_model` に対応する具体的な表・フロー・チェックリスト・設定またはコード断片が可読に描画されている
- 全スライドで、枠線・背景・影だけを持ち、可視テキスト、画像、SVG、table、pre/code、具体的なCSS図解のいずれも持たないvisual zoneまたはcardがない

## Output

- 単発: `output/index.html`、`output/index.pdf`、`output/index_html.zip`、`output/assets/*`
- シリーズ: `output/<part-id>/index.html`、`output/<part-id>/index.pdf`、`output/<part-id>/index_html.zip`、`output/<part-id>/assets/*`

最終回答ではファイルへのリンク、物理枚数、検証結果だけを簡潔に示す。

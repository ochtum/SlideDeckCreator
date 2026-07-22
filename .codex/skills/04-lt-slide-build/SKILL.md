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

発表者情報は `config/presenter.json` を唯一の正本として参照する。`presenter.include: true` の場合、自己紹介スライドはこのJSONの表示名、自己紹介文、全リンク、QRラベル、`use: true` の画像だけを可視内容として反映する。登壇テーマから推測した補足・結論・実績・意気込みを追加しない。削除対象フォルダへ移動または複製しない。ビルド中の一時ファイルは `.lt-slide-work/` に置き、`output/` には利用者へ渡す完成品だけを残す。

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
- 20分以上では `../01-lt-slide-story/references/explanation-depth.md`
- 20分以上では `../01-lt-slide-story/references/talkability.md`
- 必要に応じて `assets/deck-shell.html`
- Storyの `style_profile.status` が `applied` の場合は `config/slide-style-profile.md` の Application Limits を確認する。

## Workflow

1. ルートの `01-story.yaml` が単発かシリーズかを確認する。単発は `.lt-slide-work/02-blueprint.yaml` と `.lt-slide-work/visuals-manifest.yaml`、シリーズは各パートの指定ファイルを検証する。`presenter.include: true` のパートでは `data_file` の `presenter.json` を読み、表示名、bio、全links、avatar/qrの `use`・`path`、QRラベルを先に検証する。Storyに `design_system` があればregistryから同じID/versionを解決し、見つからなければ内蔵テーマへfallbackせず中止する。必須画像が未解決なら先に解消する。各パートについて、`../01-lt-slide-story/scripts/validate_duration_floor.py --story <part-01-story.yaml> --blueprint <blueprint_file>`、`../01-lt-slide-story/scripts/validate_explanation_depth.py --story <part-01-story.yaml> --blueprint <blueprint_file>`、`../01-lt-slide-story/scripts/validate_talkability.py --story <part-01-story.yaml> --blueprint <blueprint_file>`、`../01-lt-slide-story/scripts/validate_roadmap.py --story <part-01-story.yaml> --blueprint <blueprint_file>`、`../02-lt-slide-blueprint/scripts/validate_visual_plan.py --story <part-01-story.yaml> --blueprint <blueprint_file>` を実行し、枚数、説明時間、話せる台本、道筋の実ページ対応、必須ビジュアル計画のいずれかを満たさなければビルドを中止する。
2. `references/04a-pages.md` の指示に従い、設計図から静的な `.slide` 群を作る。選択したdesign-system tokenをCSS custom propertiesへ解決し、HTMLへ `data-design-system-id` と `data-design-system-version` を置く。`full-equivalence` では各slideへ `data-source-unit-ids` を置く。ここではページ送り、発表者ビュー、複雑なアニメーション制御を作り込まない。
3. `references/04b-animation.md` の指示に従い、静的スライドへ `data-anim`、`data-motion-reason`、step、意味上の順序、reduced motion、印刷時全表示の契約を付与する。スライドIDではなくBlueprintのselectionとtarget別指定を使い、同一stepでも線・カード・結果の役割に応じてpresetを分ける。`scripts/validate_animation_choreography.py --blueprint <02-blueprint.yaml> --html <index.html>` と `scripts/validate_animation_structure.py --html <index.html>` を実行し、Blueprintのpreset保持、targetとの互換性、選択理由、同じ意味グループへの完全割当、意味順とDOM順、タイトルの初期表示、プロフィールを除くページでの結論の最終表示を確認する。
4. `references/04c-runtime.md` の指示に従い、固定ランタイムを適用してショートカット、一覧表示、ショートカット一覧付き発表者ビュー、同期、PDF CSS、監査、ZIP化を完成させる。
5. `scripts/validate_deck.py <part-output>/index.html`、`../01-lt-slide-story/scripts/validate_spoken_notes.py --story <part-01-story.yaml> --html <part-output>/index.html`、`../01-lt-slide-story/scripts/validate_duration_floor.py --story <part-01-story.yaml> --html <part-output>/index.html`、`../01-lt-slide-story/scripts/validate_explanation_depth.py --story <part-01-story.yaml> --blueprint <blueprint_file> --html <part-output>/index.html`、`../01-lt-slide-story/scripts/validate_talkability.py --story <part-01-story.yaml> --blueprint <blueprint_file> --html <part-output>/index.html`、`../01-lt-slide-story/scripts/validate_roadmap.py --story <part-01-story.yaml> --blueprint <blueprint_file> --html <part-output>/index.html` を各デッキに実行する。design-system選択時は `../07-lt-design-system-manager/scripts/manage_design_system.py validate-binding --root config/design-systems --story <part-01-story.yaml> --blueprint <blueprint_file> --html <part-output>/index.html` も実行する。自己紹介を含むデッキでは、さらに `python scripts/validate_presenter_binding.py --presenter config/presenter.json <part-output>/index.html` を実行する。単発の `<part-output>` は `output` とする。
6. ブラウザで全ページを1280x720表示し、初期状態、すべての途中step、全step表示状態を確認する。`scripts/validate_animation_runtime.js <part-output>/index.html` を実行し、後続要素の先出し、タイトルの遅延、プロフィールを除くページでの結論の早出しがないことを確認する。通常表示ではスライド外側に上下左右の表示余白があることも確認する。
7. `S` で発表者ビューを開き、現在・次スライド、ノート、タイマー、ショートカット一覧、双方向同期を確認する。各stepで投影側と現在プレビューの一致を確認する。`話す内容` を途中までスクロールし、タイマー更新と同一ページのstep変更で先頭へ戻らないことも確認する。`scripts/validate_presenter_runtime.js` を1280x720と1280x860で実行する。
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
- スライド識別子は `.slide[data-slide-id]` にだけ保持し、`s01` / `sXX` を投影面へ描画しない。フッターは左の章・セクション名と右のページ番号だけを基本とし、中央へシステムタイトル、原稿名、source noteを常設しない。出典追跡は `data-source-note` / `data-source-unit-ids` に保持する。
- `roadmap-flow` はトップレベル `roadmap.items` をそのまま描画し、各ノードに具体ラベル、要約、ページ範囲、`data-roadmap-slide-ids` を持たせる。phase名だけのノードを生成しない。
- ブラウザ投影時はdeckをビューポート端へ貼り付けない。`fit()` は上下左右に最低32px、推奨48pxの表示余白を差し引いてscaleを計算する。
- 印刷用紙は `@page { size: 13.333333in 7.5in; margin: 0; }` に固定する。
- まとめとサンクスを最後に連続配置する。`validate_deck.py` が通るよう、最後の2枚は `data-role="recap"`、`data-role="thanks"` にする。
- 各 `.slide` に設計図の `spoken_note` を `data-spoken-note` として埋め込む。HTML属性として正しくエスケープし、投影面には表示しない。talkability v2では四行を発表者ビューで「橋渡し・話す内容・指差し・次の一言」の区画に分けて表示する。
- `presenter.include: true` の自己紹介スライドでは、`config/presenter.json` を実際に読み込む。`display_name`、`bio`、すべての `links[].platform` と `links[].account`、`qr.use: true` の `qr.label` だけを可視本文として表示する。構造ラベルの「自己紹介」「PROFILE」、章フッター、ページ番号を除き、JSONにない補足・結論・実績・意気込みを追加してはならない。プロフィールページには `conclusion-zone` / `conclusion-bar` を生成しない。
- `avatar.use` または `qr.use` が true の場合は、対応する `path` のファイルを対象デッキの `assets/` にコピーし、HTMLから相対参照する。`use: false` の要素は表示・コピーしない。`visuals-manifest.yaml` は作業用の出力記録に限り、JSONと異なるassetを正本として採用してはならない。
- 各 `.slide` に `reader_context` と `narrative_continuity.bridge` を `data-reader-context`、`data-story-bridge` として埋め込む。発表者ビューではノートとともに表示し、話者が後からページ間の接続を再現できるようにする。
- talkability v2では各 `.slide` に `flow_phase`、対応phaseの聴衆の問い、`speaker_cue.purpose` を `data-flow-phase`、`data-phase-question`、`data-speaker-purpose` として埋め込む。Storyにない文言へ要約・改変しない。
- 20分以上では、Story/Blueprintの `delivery` を `data-delivery-mode`、`data-estimated-seconds` として各 `.slide` へ埋め込む。`visible_anchors` は投影面の可視テキストとしてすべて残す。
- 初見者向けに必要な平易な定義・具体例は、タイトルだけに頼らず本文または `content_model` で可視にする。章の切替、新用語、抽象度の切替では、設計図が指定した文脈ラベルを表示する。
- `content_model` を持つスライドは、型に対応する専用HTMLコンポーネントとして描画する。`table` は列と行、`flow` はノード・矢印・判断ゲート、`implementation-playbook` は成果物・担当・完了条件、`code` / `config` は読める最小断片を表示する。
- `content_model` を持つ `.slide` には `data-content-model-type` と `data-evidence-artifact-ids` を埋め込む。HTMLの表示文字はBlueprintの列、行、ノード、項目、コードを忠実に含み、型だけを見て汎用部品へ差し替えない。
- 同じ `content_model.data` を再利用するページは、Blueprintの `focus` と `highlight` を可視の注釈または強調として実装する。focusがない再利用はBlueprintへ戻す。
- 20分以上の説明ページでは、巨大タイトルを既定にしない。44〜56pxのタイトル、24〜30pxの本文、18〜22pxの表・コード・注釈を使い、具体物がsafe areaの60〜85%を有効に使えるようにする。
- `content_model` が空、またはvisualが不要なスライドでは、visual zone・空のcard・枠線だけのコンテナを生成しない。本文／結論をレイアウトに合わせて広げるか、非空の具体的コンテンツを設計図へ戻して追加する。白い空枠は余白ではなく不具合として扱う。
- `KEY VIEW`、`PLAYBOOK`、汎用3カードなどのプレースホルダーだけで、具体的な `content_model` を置き換えてはならない。同じ汎用カード表示を3枚以上連続させない。
- 過去のビルドのページ数を固定値として扱わない。設計図の変更でページを追加・削除した場合は、HTMLの物理スライド数、ページ番号、発表者ビューの総数、PDFページ数、ZIP内のHTMLをすべて現在の構成へ更新する。
- 表紙、自己紹介、Thanksを除く本編枚数が、指定時間の安全下限を下回るデッキをビルドしてはならない。30分以上の安全下限は16枚で、18〜24枚を標準範囲とするが、枚数を目標にしない。問いへの答え、代表例、実演、完了条件を一枚の役割として設計する。
- シリーズでは、各パートのページ数を独立して更新する。シリーズ全体の合計を一つのデッキのページ番号や発表者ビュー総数に使わない。

## Quality Gate

次を満たすまで完了にしない。

- `need: required` の各 `visual_plan` が、対応する `.slide` の `data-visual-plan-id` と、画像・SVG・HTML表・HTMLコードの実装へ解決されている。説明を持たない汎用カードだけでは合格にしない。

- 単発は `output/index.html`、`output/index.pdf`、`output/index_html.zip`、シリーズは各 `output/<part-id>/` に同名の3ファイルが存在する
- 各デッキで `validate_deck.py` が成功する
- 長い発表では各デッキで `validate_roadmap.py --story ... --blueprint ... --html ...` が成功する
- 各デッキで `validate_animation_choreography.py`、`validate_animation_structure.py`、`validate_animation_runtime.js` が成功し、初期状態から最終stepまで意味順と完全割当を確認する
- 各デッキで `validate_spoken_notes.py --story <part-01-story.yaml> --html <part-output>/index.html` が成功し、構造化されたページ固有ノートとHTMLへの正確な反映を確認する
- 自己紹介を含む各デッキで `validate_presenter_binding.py` が成功し、JSONの表示名・bio・全リンク・QRラベルと、`use: true` のassetハッシュが一致し、JSONにない可視メッセージ用の領域が存在しない
- 各デッキで `validate_duration_floor.py --story <part-01-story.yaml> --html <part-output>/index.html` が成功する
- 20分以上の各デッキで `validate_explanation_depth.py --story <part-01-story.yaml> --blueprint <blueprint_file> --html <part-output>/index.html` が成功する
- 20分以上の各デッキで `validate_talkability.py --story <part-01-story.yaml> --blueprint <blueprint_file> --html <part-output>/index.html` が成功する
- 各デッキで `validate_pdf.py` が成功する
- 全スライドの初期状態、すべての途中step、全step表示状態を目視確認済み
- 発表者ビューの現在プレビューが投影側DOM状態と一致する
- 発表者ビューでphaseの問い、ページの目的、`reader_context`、前ページからのbridge、実際に話す内容、指差し、次の一言を区別して確認でき、投影面を見ずに話の接続を再構成できる。
- 発表者ビューで `話す内容` が補助キューより広い主領域を持ち、phaseの問いが独立した可読領域にある。タイマー更新で主台本のスクロール位置がリセットされない。
- 初見者が必要とする定義・具体例が、画面の本文または具体的な `content_model` として存在する。
- 発表者ビューにショートカット一覧が表示される
- PDFレンダリング結果に見切れ、余白欠落、背景欠落、画像切れがない
- How/Demoの各スライドで、設計図の `content_model` に対応する具体的な表・フロー・チェックリスト・設定またはコード断片が可読に描画されている
- 全スライドで、枠線・背景・影だけを持ち、可視テキスト、画像、SVG、table、pre/code、具体的なCSS図解のいずれも持たないvisual zoneまたはcardがない

## Output

- 単発: `output/index.html`、`output/index.pdf`、`output/index_html.zip`、`output/assets/*`
- シリーズ: `output/<part-id>/index.html`、`output/<part-id>/index.pdf`、`output/<part-id>/index_html.zip`、`output/<part-id>/assets/*`

最終回答ではファイルへのリンク、物理枚数、検証結果だけを簡潔に示す。

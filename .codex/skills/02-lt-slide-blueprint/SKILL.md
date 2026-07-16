---
name: 02-lt-slide-blueprint
description: .lt-slide-work/01-story.yaml を .lt-slide-work/02-blueprint.yaml に変換し、洗練された 1280x720 の HTML スライド用に整える。話者ノートは保持すること。レイアウト、タイポグラフィ、図解、アニメーション手順、空間ゾーン、発表者ノート、テキスト量の設計を行う際に使用する。また、テキスト・図・バッジ・結論が重ならないようにすること。
---

# 02 LT Slide Blueprint

`.lt-slide-work/01-story.yaml` を、実装可能なスライド設計図 `.lt-slide-work/02-blueprint.yaml` に変換する。シリーズマニフェストの場合は、各パートのストーリーを個別の設計図へ変換する。HTMLや画像は作らない。図版と文字の領域を先に分け、重なりを設計段階で禁止する。

## Workspace Contract

入力と出力はプロジェクトルート直下の `.lt-slide-work/` に固定する。

```text
.lt-slide-work/
├─ 01-story.yaml
└─ 02-blueprint.yaml

config/
├─ presenter.json
└─ slide-style-profile.md
```

設計図や検証用ファイルをプロジェクトルート、`output/`、スキル本体のフォルダへ出力しない。発表者情報は `config/presenter.json` から読み、`.lt-slide-work/` へコピーしない。

## Series Mode

ルートの `01-story.yaml` が `kind: lt-slide-series` なら、`../01-lt-slide-story/references/series-schema.md` を読み、`parts` を `order` 順に処理する。各パートの `story_file` から、対応する `blueprint_file` を作る。単発用のルート `02-blueprint.yaml` を流用したり、複数パートを一つの設計図へ連結したりしない。

- 各設計図は、そのパートの `duration_minutes`、`target_slide_count`、`learning_goal` だけを対象にする。
- 各パートに表紙、今日のゴール、具体的なHowまたはDemo、Takeaway、recap、thanksを残す。
- パート境界をまたぐ前提は、次パートの序盤で1枚以内に再導入する。前パートのスライド番号を参照して理解を要求しない。
- 検証は各 `blueprint_file` に対して実行する。各パートは指定時間の本編最小枚数を個別に満たす。

## Required Reads

- `references/blueprint-schema.md`
- `references/layout-rules.md`
- `references/motion-choreography.md`
- `../01-lt-slide-story/references/presentation-quality.md`
- 20分以上では `../01-lt-slide-story/references/explanation-depth.md`
- 20分以上では `../01-lt-slide-story/references/talkability.md`
- 図版を選ぶときは `references/figure-patterns.md`
- `config/slide-style-profile.md` があり、Storyの `style_profile.status` が `applied` の場合は、その見出し、感情の転換、視覚構成、Application Limits を読む。

## Workflow

1. `.lt-slide-work/01-story.yaml` が単発ストーリーかシリーズマニフェストかを確認する。シリーズなら `Series Mode` に従って各パートを処理する。各スライドの `speaker_cue`、`spoken_note`、`reader_context`、`connection_from_previous`、`delivery` を同じIDの設計図へそのまま引き継ぐ。phaseに属するページには `question_spine` の問い・答え・接続を `phase_context` として引き継ぐ。`source_asset_inventory` があれば、対象パートに割り当てられた提供画像・表・コードを先に確認する。Storyの `style_profile.status` が `applied` の場合だけプロファイルを読み、`applied_rule_ids` に対応する表現を設計する。入力に根拠のない感情、失敗、記号、短文スライドを追加してはならない。
1a. Storyに `design_system` があればregistryから同じID/versionのspecを読み、`design_system` を設計図へ変更せず引き継ぐ。theme、component、motionはspec tokenから解決し、別の色へ即興で置換しない。選択済みIDが見つからなければfallbackせず停止する。`full-equivalence` では各スライドの `source_unit_ids` も変更せず引き継ぐ。
2. 各スライドに1つの `layout` と、実際に描画する1つの `visual_anchor` を割り当てる。表・フロー・設定・コード・プレイブックを表示する場合だけ、後工程がそのまま描画できる非空の `content_model` を置く。`content_model` には表の列と行、フローのノードと矢印、設定・コマンド・チェックリストの実データを置く。
3. 1280x720座標で `title_zone`, `text_zone`, `visual_zone`, `conclusion_zone`, `footer_zone` を定義する。
4. テキスト量、文字サイズ、行数を確定する。
5. 図版をコンポーネント、インラインSVG、提供画像、生成画像、なしから選ぶ。意味が一致する提供画像は `provided-image` として優先し、`visual_assets` に必ず列挙する。表・コード・設定例は、読める最小データを `content_model` としてHTMLへ再構成する。正確さが必要なフロー・表・コードを、生成画像や汎用カードに置き換えない。
6. `references/motion-choreography.md` に従い、各ページへ `animation.intent`、`animation.family`、`animation.selection`、`animation.sequence` を置く。presetをスライド番号やページ位置へ固定せず、`role -> content_model.type -> targetの意味 -> phase境界` の順で選ぶ。各entrance/stepには選択理由を置き、同一stepで線とノードなど対象の役割が違う場合は `target_presets` と `target_reasons` で分ける。通常はページ内stepを最大6段階にまとめるが、番号付き工程・表の代表行など、話者が一項目ずつ説明する順序列は最大9段階まで許可する。`sequence` には初期表示、全対象、意味上の順序、完了要素を明記し、同じグループの一部だけを段階表示にして残りを初期表示へ漏らさない。全ページへ同じstep数とpreset列を複製しない。本編20枚以上では5preset・4family以上、3種類以上のstep数をデッキ全体で使い分ける。
6a. 初見者向けの初出用語は、画面上で平易な定義と具体例を読めるようにする。各スライドについて、`speaker_cue.point_at` の全項目を実在する文字、表セル、コード行、図のHTML/SVGラベルとして配置する。直前からの橋渡しと次の一言は発表者ノートに残し、後読時に必要な `reader_context` を表示用・発表者ビュー用のどちらに置くか決める。
7. 単発は `.lt-slide-work/02-blueprint.yaml`、シリーズは各パートの `blueprint_file` を出力する。
8. 出力した各設計図に `scripts/validate_blueprint.py`、`scripts/validate_visual_plan.py --story <part-01-story.yaml> --blueprint <blueprint_file>`、`../01-lt-slide-story/scripts/validate_duration_floor.py --story <part-01-story.yaml> --blueprint <blueprint_file>`、`../01-lt-slide-story/scripts/validate_explanation_depth.py --story <part-01-story.yaml> --blueprint <blueprint_file>`、`../01-lt-slide-story/scripts/validate_talkability.py --story <part-01-story.yaml> --blueprint <blueprint_file>` を実行し、エラーをゼロにする。

## Non-Overlap Contract

- 主要ゾーンは互いに交差させない。背景装飾だけは例外。
- `title_zone` はバッジ領域 `x:48..220, y:24..64` と交差させない。
- `footer_zone` は原則 `y:660..704` とし、本文・図版を入れない。
- `conclusion_zone` は図版の上に重ねない。後出しでも専用領域を確保する。
- 画像は `object-fit: contain` 前提で `visual_zone` 内に収める。
- 絶対配置は装飾、ページ番号、明示されたゾーンだけに限定する。
- アニメーションの開始位置と終了位置の両方が担当ゾーンからはみ出さないようにする。
- 中央の矢印やVSは独立した `connector_zone` を持たせる。

## Typography Floor

lt-html-slide-skillの見栄えを維持しつつ、slide-builderの小さな文字を改善する。

- 表紙タイトル: 56から76px
- 通常タイトル: 38から56px
- 強い結論: 28から32px
- カード見出し: 30から38px
- 本文: 24から28px
- 補足: 22から26px
- 出典・ページ番号: 18から22px

5〜15分では本文を28px未満に縮めて収めてはならない。20分以上の技術説明では、通常本文24〜30px、表・コード・注釈18〜22pxを許可し、タイトルを44〜56pxへ抑えて具体物の領域を確保する。小さい文字で長文を詰めるのではなく、代表行、注目箇所、判断条件へ絞る。自動縮小は禁止する。

## Layout Selection

- `hero-split`: 表紙や強い結論。左テキスト、右ビジュアル。
- `profile-three-zone`: 左画像、中央プロフィール、右QR。欠損時は2列へ変更。
- `statement`: 1つの主張を大きく見せる。
- `split-compare`: 左右比較と独立コネクタ。
- `cards-3`: 3つの選択肢や理由。
- `cards-4`: 短い項目だけ。各カード本文2行以内。
- `flow-3` / `flow-4`: 手順と矢印。
- `roadmap-flow`: 長い発表用の話の地図。Why / What / How / Demo / Takeawayを横並びにし、現在地を強調する。
- `implementation-playbook`: 最初の一件を実行するための手順。各工程に「作るもの」「AIまたは人間が行うこと」「完了条件」を並べる。
- `annotated-example`: 画面、コード、設定、表の主役を大きく置き、2〜4個の注釈で読み方を示す。
- `code-walkthrough`: ファイル名、読めるコード断片、注目行、入出力または副作用を分ける。
- `table-focus`: 表の列と代表行を主役にし、今回使う列・判断を強調する。
- `before-after-diff`: 変更前後、差分、変えていない範囲、確認条件を同じ評価軸で示す。
- `case-study`: 状況、操作、観察、判断を一件の具体例として結ぶ。
- `matrix`: 2軸分類。結論は下部専用帯。
- `visual-left` / `visual-right`: 生成画像と本文を分離。
- `recap-split`: 左要点、右または下に最初の一手。
- `thanks`: 大きな終了メッセージと広い余白。
- 実務資料を説明する場合は、代表例を `matrix`、`flow-3` / `flow-4`、または実物に近いチェックリストとして設計する。汎用的な装飾図だけで置き換えず、表の列、フローの工程、入力と出力、判断ゲートを明示する。
- `cards-3` は本当に並列な3選択肢だけに使う。表、フロー、設定、実装手順を3枚の汎用カードへ還元してはならない。

同じレイアウトを3枚以上連続させない。

元のページ数を固定値として保存しない。ストーリーの追加・分割・統合によりページ数が変わったら、設計図の物理枚数とページ番号仕様を更新して後工程へ渡す。

指定時間の本編最小枚数を満たさない場合、設計図を出力してはならない。表紙、自己紹介、Thanksを数に含めず、具体例・比較・演習・デモ・判断ゲートを追加して満たす。抽象説明や同型カードの水増しは禁止する。

## Visual And Animation Rules

- 1枚に視覚的主役を1つ置く。
- 図版に本文と同じ長文を重複させない。
- 生成画像には原則として文字を焼き込まない。
- タイトルと、話の前提になるメッセージ・入力はstep 0までに表示する。タイトルの入場は220ms程度の短い動きか静止表示にし、本文より後へ送らない。
- 順序の優先順位は `番号・因果・依存・話す順 -> 視覚配置と一致するDOM順 -> Z型` とする。Z型は意味順のない独立要素にだけ使う補助規則であり、番号付き工程を並べ替えない。
- 番号付き工程・表・チェックリストは意味上の一項目を一stepで出し、同じ列・行・カード群の意味要素をすべて `animation.sequence.ordered_targets` へ含める。背景線などの補助は対応する項目と同じstepへまとめる。
- 重要な図は話し始めに必要な範囲から見せ、出力・完了条件・結論帯は対象説明の後に出す。結論帯は原則として最後のstepにする。
- 1枚のstep数は通常0から6、説明対象が明示された順序列だけ0から9。10以上になる場合は語句を小分けにせず意味のまとまりへ再設計する。全入場は原則2秒以内。比較、フロー、Demo、結論でmotion familyを切り替え、同じanimation signatureを3ページ連続させない。
- `prefers-reduced-motion` と印刷では全要素を表示する前提にする。
- `speaker_cue` と `spoken_note` は投影面のレイアウトや文字量に含めない。発表者ビュー専用データとして文字列を変更せず保持する。ただし `point_at` は画面に実在するアンカーとして実装する。
- スタイルプロファイルのstatementや会話的な見出しは、実際の転換点・問い・結論があるページに限る。感情中心の短文スライドは本編の20%以下、同種の感嘆符付き見出しは連続禁止、顔文字は全体で最大1回を初期値とする。プロファイルの上限がより厳しい場合はそれを優先する。
- 感情または転換を表すページの前後には、原因、条件、具体物、結果、次に試す操作のいずれかを設計する。見出しの口調で技術情報を置き換えない。
- 画面上の文脈ラベルは、主語・現在地・前提が失われる場合だけ置く。毎ページに冗長な「前回」表示を足すのではなく、章の切替、新用語、抽象度の切替で読者を再同期する。
- `narrative_continuity` に `reader_context`、`prior_state`、`bridge`、`next_question` を残す。`bridge` は話者ノートの冒頭に使い、`next_question` は次ページへ進む理由を保つ。
- 「明日から取り組める」ことが目的の発表では、HowまたはDemoに、実在するファイル名・手順・受け入れ条件・検証結果のうち少なくとも2種類を画面上の具体例として置く。長い原文の貼り付けではなく、読める最小表・フロー・チェックリストへ圧縮する。
- How/Demoの各スライドには `content_model` を必須とする。`type` は `table`、`flow`、`implementation-playbook`、`checklist`、`code`、`config`、`comparison`、`file-map` のいずれかとし、読後に再現できる固有データを含める。
- `content_model` のないスライドを、`KEY VIEW`、汎用アイコン、同型カードで補って合格にしてはならない。
- 20分以上では、表紙・profile・goal・transition・recap・thanks以外の各ページに、非空の `content_model`、2件以上の `text.details`、または2件以上の `visual.annotations` のいずれかを置く。大見出しと一文だけでは設計完了としない。
- Storyの `delivery.visible_anchors` は、`text`、`content_model`、`visual.annotations` のいずれかに文字列として存在させる。話者ノートだけへ移さない。
- Storyの `speaker_cue.point_at` は `delivery.visible_anchors` と同じ表示要素へ解決する。曖昧な「左の図」「ここ」ではなく、話者とレビュー担当が同じ対象を特定できるラベルを使う。
- 同一の `content_model.data` を複数ページで再利用する場合は、各ページに異なる `content_model.focus` と `highlight` を必須とする。同じ表やフローを異なる主張へ無注釈で割り当てない。
- checklistの各項目は「対象を確認する」のような汎用文ではなく、操作対象、操作、合格条件のうち少なくとも2つを含める。
- 空の `content_model`（`items: []`、`rows: []`、`steps: []`、空のcodeなど）を、見た目だけのカードやvisual zoneの根拠にしてはならない。画面に描画する中身がなければ `visual.kind: none` とし、visual zoneを予約せず、本文または結論のレイアウトを拡張する。
- goal、statement、recapのように視覚要素が任意のスライドでは、空の右カラムを作らない。視覚を置く場合は、ゴールの3段階、結論の式、最初の一手など、画面上で読める具体的内容を `content_model` またはvisual specificationへ必ず与える。
- `source_asset_inventory` で採用された提供画像・表・コードのうち、対象パートへ割り当てられたものを省略してはならない。比率や可読性のために不採用にする場合は、同じ情報を保持するSVG/CSSまたは最小表・コード断片へ置き換え、理由を `notes` に残す。
- 複数の実務部品を説明する場合は、個別例を散在させるだけで終えない。序盤に実装プレイブックを連続した2〜4枚で置き、題材、成果物、実行、完了条件、失敗の反映先が一続きに追えるようにする。
- `visual_plan.need: required` の各計画は `visual_plan_id` で同じ設計図スライドへ結び、提供画像、SVG、表、コードのいずれかへ解決する。`scripts/validate_visual_plan.py` が失敗する設計図を後工程へ渡さない。
- 描画対象のないvisual zone、空のカード、空のプレイブックを残さない。設計図レビュー時に、各visual zoneが少なくともtable、code、config、flow、comparison、file-map、implementation-playbook、提供画像、または意味のあるSVG/CSS要素のいずれかを持つことを確認する。
- 初見者が理解できる定義・具体例、前後ページの橋渡し、後読時の主語と結論が設計図から追跡できないスライドを後工程へ渡さない。

## Output

単発の正本は `.lt-slide-work/02-blueprint.yaml`。シリーズでは各パートの `blueprint_file` が正本で、ルートの `01-story.yaml` が処理順と出力先を決める。後工程を同じターンで依頼されている場合は停止せず `03-lt-slide-visuals` へ進む。

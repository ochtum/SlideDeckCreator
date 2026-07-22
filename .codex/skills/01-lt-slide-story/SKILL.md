---
name: 01-lt-slide-story
description: 日本語の記事、メモ、URL、またはトピックを、登壇中と後日閲覧の両方で理解できるライトニングトークのストーリーに変換する。知識単位、理解確認問題、記事種別、出典、本編／補足、時間配分を設計し、単発かシリーズかを判定して `.lt-slide-work/01-story.yaml` に保存する。LTスライドプロジェクトを開始する際に使用する。
---

# 01 LT Slide Story

LTの素材整理、話の流れ、スライドへの割り付けを決める。HTML、レイアウト、画像はまだ作らない。成果物は後工程がそのまま読める `.lt-slide-work/01-story.yaml` とする。単発なら従来のストーリー、シリーズなら各パートへの参照を持つマニフェストにする。

## Workspace Contract

中間成果物は、制作対象プロジェクトのルート直下にある `.lt-slide-work/` へ必ず出力する。別の場所へ散在させない。

```text
<project-root>/
├─ config/
│  ├─ presenter.json
│  └─ slide-style-profile.md
├─ .lt-slide-work/
│  ├─ 01-story.yaml                  # 単発ストーリー、またはシリーズマニフェスト
│  └─ parts/                         # シリーズ時のみ
│     └─ <part-id>/
│        └─ 01-story.yaml
└─ output/
```

`.lt-slide-work/` がなければ作成する。このフォルダは一時的な制作データであり、Git管理対象にしない。

## Required Reads

- `references/story-schema.md`
- 記事またはURL入力では `references/knowledge-structure.md`
- SpeakerDeck、YouTube、静的PDF、または後日閲覧を想定する場合は `references/dual-use-publication.md`
- シリーズを検討する場合は `references/series-schema.md`
- 20分以上では `references/explanation-depth.md` と `references/talkability.md`
- ユーザーが「全内容」「入力と同等」を求める場合は `references/content-equivalence.md`
- 初見者向けの説明を設計するときは `references/presentation-quality.md`

## Workflow

1. 入力を Markdown、URL、Markdown+URL、トピックのみのいずれかに分類する。記事またはURLでは `knowledge-structure.md` に従い `source.document_types`、`narrative.archetype`、`narrative.phase_order` を決める。
2. URLがある場合は取得可能なものを並列で読み、主題、根拠、数値、出典だけを抽出する。取得不能なURLは記録して残りで進める。
3. 不足情報だけを質問する。質問は一度に最大3件にまとめ、ソースから分かることは聞かない(`Ask Only What Is Missing`を参照)。公開先、must-keep、out-of-scope、fact-check方針を `request` に保存し、合理的に補完した値は `request.assumptions` に値・理由を残す。
4. 発表者プロフィールを確認する。
4a. `config/slide-style-profile.md` がある場合は読み、`python .codex/skills/00-lt-slide-style-extraction/scripts/validate_style_profile.py config/slide-style-profile.md` を実行する。発表者の姿勢、ストーリー、失敗・成功、具体性、話者ノートのルールだけを利用し、`style_profile` に参照パスと採用したrule IDを残す。プロファイルを理由に、入力にない失敗、実験、感情、具体物を追加してはならない。本文総数の下限・目標・固定値はstyle profileから採用せず、見つけた場合は00へ戻して修正する。存在しない場合は `style_profile.status: absent` を残して通常のストーリー設計を続ける。
4b. `config/design-systems/registry.yaml` がある場合は一覧を読み、ユーザーがIDを指定していればそのversionとpathを確認する。未指定なら既存の内蔵fallbackを使い、新しいデザインシステムを勝手に選択しない。選択時は `design_system` をルートStoryと全パートへ保存する。新規追加・変更・削除は `07-lt-design-system-manager` に戻す。
5. `references/presentation-quality.md` を読み、初見者の既知語・未知語・誤解しやすい前提を `audience` に残す。用語の初出、平易な定義、具体例を決める。
5a. 発表時間が20分以上なら `references/explanation-depth.md` と `references/talkability.md` を読み、`project.talkability_version: 2`、`project.time_budget`、各liveスライドの `delivery`（mode、estimated_seconds、talking_points、visible_anchors）を先に設計する。time budgetにはQ&Aとbufferを独立して置き、appendix/referenceを登壇時間へ加算しない。短時間LTの枚数・余白・一枚一言を引き延ばしてはならない。
6. 全体の主張を1文に圧縮し、聴衆が持ち帰る行動を1つ決める。
7. 入力から `content_inventory` を作り、事実、主張、手順、デモ候補、注意点に加え、表・フロー・設定例・コマンド・ファイル構成・変更パターンを `evidence_artifacts` として素材化する。記事の順番に依存せず、出典と再利用できる最小データを残す。ユーザーが「全内容」「入力と同等」「シリーズですべて」と指定した場合は `project.content_fidelity: full-equivalence` とし、`references/content-equivalence.md` に従って `scripts/audit_content_equivalence.py --source ... --inventory-out .lt-slide-work/source-inventory.yaml` を先に実行する。
7a. **Source Asset Audit**を行う。Markdown画像、添付画像、表、Mermaid、コードブロック、設定例を列挙し、`source_asset_inventory` にパスまたは行範囲、意味、再利用候補のスライド、採否を残す。元資料に意味を担う画像・表・コードがある場合、抽象的なカードだけで置き換えない。`usage_rights` が明示されない素材は `unknown` とし、直接コピーを選ばない。`provided-for-reuse` だけを提供画像として再利用し、`reference-only` と `unknown` は意味を保ったSVG・HTML・生成画像へ再構成する。
7b. 記事またはURL入力では `knowledge-structure.md` に従い `knowledge_units` を作る。主張、定義、根拠、因果、比較、手順、例、注意、判断、参考情報を分類し、重要度、前提、アーティファクト、出典、割当スライドを残す。`full-equivalence` または `dual-use` では5〜10件の `comprehension_checks` を作り、スライド本文だけで回答できることを完成条件にする。
7c. 数値、引用、製品仕様、更新され得る情報、外部調査で補った主張を `citations` と `fact_ledger` へ置く。一次資料で更新した内容、未検証事項、記事の主張と追加調査を区別する。dual-useでは可視出典ラベルとreferenceスライドを計画する。
8. **Source Scope Audit**を行う。見出し（H1-H3）、表、フロー、設定例、変更パターン、完了条件を「学習単位」として列挙し、各単位に `intro`、`representative example`、`full coverage` のいずれが必要かを決める。複数の独立した実装ループ（例: 最初の変更、知識基盤、大規模探索、UI・運用）があるかを明示する。
9. `coverage_matrix` を作る。各学習単位について、割当パート、スライドID、表示／口頭の伝達面、構造の保存方法、代表アーティファクト、最初の作業、完了条件を記録する。`full-equivalence` ではsource inventoryの全unitを一対一でcoverageへ置き、表・コード・設定・Mermaid・画像・チェックリストをテーマ名だけのカードへ縮約しない。入力が実装ガイドで、ユーザーが要約・入門と明示していない場合は、全ての主要見出しを `full coverage` と仮定する。
10. `Series Analysis And Split` に従い、単発かシリーズか、必要なら話数と各回の境界を判定する。dual-useではsupporting/reference知識をappendix/referenceへ移してlive時間を守れるか先に確認し、essentialな学習ループ自体が収まらない場合だけシリーズを優先する。
11. 単発なら一つ、シリーズなら各パートごとに、一つの `central_example` と `question_spine` を先に作る。`narrative.phase_order` の各phaseについて、聴衆の問い、一文の答え、次の問いへ渡す実際の一言、時間を決める。記事種別に合うphaseを使い、phaseラベルだけを骨格の代わりにしない。
11a. Demo phaseを採用した場合は `demo_runbook` に開始状態、3つ以上の操作と観測結果、終了状態、失敗時のfallbackを置く。Takeaway phaseを採用した場合は `tomorrow_action` に時間枠、最初の操作、残る成果物、完了条件を置く。入力にないDemoを捏造しない。
11b. 30分以上または本編20枚超では、全スライドの順序と `flow_phase` を確定した後に `roadmap` を生成する。可視ラベルは内部のphase名をそのまま出さず、実際のページ群が答える具体的な節目にする。各項目へ連続した `slide_ids`、物理 `page_start` / `page_end`、`start_title` / `end_title` を保存し、道筋スライドの `content_model.data.steps` と一致させる。
12. `question_spine` と `narrative.flow` をスライドへ割り付ける。各ページに `speaker_cue` を置き、表示前後の聴衆状態、実際に話す台本、指差す表示要素、次ページへ渡す一言を決める。表紙、自己紹介、Thanksを除く各スライドに `reader_context` と `connection_from_previous` を置き、前ページの理解から次の必要性へ橋を架ける。
13. `scripts/validate_knowledge_contract.py --story <01-story.yaml>`、`scripts/validate_talkability.py --story <01-story.yaml>`、`scripts/validate_spoken_notes.py --story <01-story.yaml>`、`scripts/validate_duration_floor.py --story <01-story.yaml>`、`scripts/validate_explanation_depth.py --story <01-story.yaml>`、`scripts/validate_roadmap.py --story <01-story.yaml>` を実行する。`full-equivalence` ではさらに `scripts/audit_content_equivalence.py --inventory .lt-slide-work/source-inventory.yaml --story .lt-slide-work/01-story.yaml --require-full-equivalence` を実行する。失敗時は成果物を次工程へ渡さず、未割当の知識、理解確認、可視出典、問いへの答え、ページ間の接続、台本、必要なDemo、時間、道筋の不一致を修正する。枚数だけを増やして解決しない。
14. 単発は `references/story-schema.md`、シリーズは `references/series-schema.md` に従って成果物を出力する。
15. 構成と、シリーズなら分割理由・各回のゴール・話数をユーザーに提示し、明示的な修正依頼がなければ次工程へ渡せる状態にする。

## Series Analysis And Split

分割は「ページが多いから」ではなく、聴衆が一回の発表後に独力で試せるかで判定する。まず単発を仮置きし、発表時間内に各素材の代表サンプル、最初の作業、完了条件を残せるかを確認する。

- 次のいずれかが成立する場合は `decision: series` にする。複数の独立した実装ループがあり、一回に入れると各ループの具体例または完了条件を省く／複数の学習ゴールを一つの「明日からの一手」に絞れない／必要な説明とデモの見積りが指定時間を超える。
- `Source Scope Audit` で3つ以上の独立した実装ループが見つかり、各ループに固有の成果物・最初の作業・完了条件がある場合は、単発を選ばない。入力の章数やファイル数ではなく、この独立性を分割根拠にする。
- 単発を選ぶ前に、`coverage_matrix` の全ての `full coverage` 単位について、代表アーティファクト、最初の作業、完了条件がliveまたはappendixに残ることを確認する。dual-useではsupporting/referenceをappendixへ移せるが、essentialを概要だけに薄めない。
- `full-equivalence` ではsource inventoryの節、表、コード、設定、図、チェックリストごとに、liveで説明する時間と後読だけでよい項目を分ける。essentialなlive内容が指定時間に収まらない場合はシリーズ回数を増やす。省略は `approved_omissions` にユーザー承認と理由がある場合だけ許す。
- 分割数は、独立して完結する学習ゴールの最小数で決める。章数、入力ファイル数、既存スライド数を等分するための分割は禁止する。
- 各パートには、固有の今日のゴール、対象範囲、代表サンプル、明日最初に作成・実行・確認すること、完了条件、まとめを必ず置く。前提がある場合は前回の要点を1枚以内で再導入する。
- 全ての `content_inventory` ID は `coverage` で少なくとも一つのパートに割り当てる。扱わない素材は理由を残す。
- 指定時間は各パートの上限である。予定時間は質疑と切替の余白を残し、抽象説明で時間を埋めてはならない。
- 同じ発表時間を指定しても、シリーズの各パートを同じ枚数にそろえてはならない。`target_slide_count` は、各回の学習ゴールを達成するために必要な代表サンプル、デモ、最初の作業、完了条件、まとめから個別に見積もる。同じ枚数になる場合も、内容量から独立して妥当と説明できる場合に限る。時間からの枚数目安は、枚数合わせや抽象説明の水増しに使わない。
- 各パートについて、phaseごとに必要な「問い／仕組み／代表例／読み解き／判断・制約／最初の作業／まとめ」を先に列挙し、その実在ブロック数からスライド列を作る。全パート共通の `PHASE_LENGTHS`、役割列、ページ別秒数列を先に作り、素材をそこへ埋め込んではならない。
- `target_slide_count` はスライド列が完成した後で実際のlive本編枚数から設定する。先に全パート同じtargetを置き、追加・削除・分割で合わせてはならない。
- 全パートでtarget、live本文のrole列、phase別枚数、ページ別秒数が同一なのに、割り当てたsource unit数またはevidence量が大きく異なる場合は機械的均等化とみなし、`validate_duration_floor.py` が失敗する。ユーザーが統一構成を明示した場合だけ、ルートの `series_analysis.uniform_structure_request.requested_by_user: true` と理由を残して例外にできる。
- 単発と判定した場合も、その理由と `part_count: 1` を `series_analysis` に残してよい。ただし既存互換の schema version 1 の単発ストーリーを壊さない。

## Ask Only What Is Missing

**必ず**確認する項目:

- 発表時間または希望枚数

公開先、Q&A、must-keep、out-of-scope、fact-check方針は、ユーザー指定または入力から合理的に判断できる場合は質問せず `request.assumptions` に残す。SpeakerDeck、YouTube、配布PDFが指定された場合は `delivery_profile: dual-use` とする。

次の場合だけ、カバレッジの意図も確認する。

- 入力が複数章の実装ガイド、または独立した実装ループを3つ以上含むのに、ユーザーが「入門」「要約」「全内容」のいずれかを指定していない場合: 「入門として代表例に絞るか、全内容をシリーズで扱うか」を確認する。

選択肢として提示する[時間から本編枚数を決める目安]:

- 5分: 6から10枚
- 10分: 8から14枚
- 15分: 10から18枚
- 20〜29分: 14から22枚
- 30分: 18から24枚を標準範囲とし、内容に応じて増減する

表紙、任意の自己紹介、サンクスはこの枚数に含めない。まとめは含める。

標準範囲は目標ではなく、話の役割から見積もるための警告目安である。`target_slide_count` はliveの問い、代表例、比較、実演、完了条件から決め、同じ時間だから同じ枚数へそろえない。目安未満でも秒数と説明密度が妥当なら許容し、枚数不足を抽象的な要約や空のスライドで埋めない。appendix/referenceは別に数える。

20分以上では枚数下限だけを満たしても合格にしない。`project.time_budget` の合計、各ページの説明時間、具体的なtalking points、投影面のvisible anchorsを設計し、`validate_explanation_depth.py` を通す。30分を30個の短文で埋める構成は不合格とする。

シリーズでは、この目安を各パートへ機械的に複製しない。各パートの `target_slide_count` と、その見積根拠をマニフェストの `slide_count_rationale` に残す。時間が余る場合は、具体例の比較、演習、質疑の余白に充て、説明のないスライドを足さない。

## Presenter Intake

自己紹介ページを入れるか必ず確認する。既存の `config/presenter.json` があれば「そのまま使う、編集する、自己紹介なし」を確認する。なければ、入れる場合だけ次を聞く。

- 表示名
- 1から2文の自己紹介
- SNSまたはWebサイトを載せるか。載せる場合はURLまたはアカウント
- 顔写真やアバター画像を使うか。使う場合は画像のパス
- QR画像を使うか。使う場合は画像のパスとラベル

必須情報は表示名と自己紹介だけだが、SNSまたはWebサイト、顔写真またはアバター、QR画像についても、使用有無をそれぞれ必ず確認する。ユーザーが初回回答で一部だけを提示した場合、未回答項目を「未指定」として処理せず、最大3件の質問にまとめて追加確認する。

ユーザーが「使わない」と回答した項目だけを不使用として確定する。画像を使わない場合は代替レイアウトを許可する。情報は永続設定として `config/presenter.json` に保存し、`.lt-slide-work/01-story.yaml` から `../config/presenter.json` で参照する。`.lt-slide-work/` や `output/` には保存しない。秘密情報は保存しない。自己紹介スライドの可視本文は `display_name`、`bio`、`links`、QRラベルと有効画像だけに限定し、登壇テーマの補足、意気込み、実績、結論を推測して追加しない。テーマへ戻す一言は `speaker_cue` / `spoken_note` に置き、投影面へ常設しない。

## Presenter Style Profile

`config/slide-style-profile.md` は、過去資料から抽出した発表者固有の永続設定である。存在する場合だけ読み、内容を今回の事実より優先しない。

- `MUST` / `SHOULD` / `MAY` は、入力資料に対応する出来事または具体物がある場合だけ適用する。
- `MUST NOT` と Application Limits は必ず守る。会話的な見出し、感情ページ、記号を全ページへ広げない。
- style profileのdensity、反復、低密度ページ比率は使えるが、本文・本編・各回・デッキ全体の最低枚数、目標枚数、固定枚数は使わない。ページ総数はスタイルではなく現在の学習内容の結果として決める。
- 実験・検証資料では、入力にある失敗、勘違い、途中結果を成功だけに圧縮しない。次の原因、再試行、注意点を追跡できる位置へ置く。
- `style_profile` には `data_file`、`status`（`applied` / `absent`）、`applied_rule_ids` を残す。`status: applied` でも、採用できるルールがない場合は空配列にする。

## Story Rules

- 原稿を貼り付けず、短い話し言葉へ圧縮する。
- 初見者が知らない用語・略語・固有工程は、最初の登場で平易な定義、必要性、具体例をそろえる。聴衆が既知と明示していない知識を前提にしない。
- 表紙、自己紹介、Thanks以外の各スライドに `reader_context` と `connection_from_previous` を残す。タイトルの並びだけで因果を推測させない。
- 画面には主語・根拠・結論を残し、`speaker_cue` と `spoken_note` には前ページとの接続、実際に口にする説明、指差す具体物、次ページへ渡す一言を残す。後から読む人と話す人の両方が再構成できる状態にする。
- 記事や入力資料の順番をそのままスライド順にしない。まず素材として分解し、聴衆に伝わる順へ再配置する。
- `content_inventory` にはスライド化前の材料を残す。最低限、主要な事実、主張、手順、デモ候補、注意点を分類する。
- 技術資料として後から読まれることが想定される場合、`evidence_artifacts` に実在する表の列・代表行、フローの工程・入力・成果物・担当・完了条件、設定例、コマンド、ファイル名、変更パターンを保存する。原稿を貼り付けるのではなく、再現に必要な最小の具体性を残す。
- `evidence_artifacts` には `provided-image`、`table`、`code`、`config` を含められる。画像はパス・alt・意味、表は列と代表行、コードは言語と読める最小断片を持つ。
- 提供画像は、その画像が伝える関係・変化・実例が当該スライドの主張と一致する場合に再利用候補として優先する。採用しない場合は、`source_asset_inventory` に理由（重複、低解像度、比率不適合、正確なSVG/CSSへの置換など）を残す。
- `narrative.question_spine` を話の背骨、`narrative.flow` を素材の割当として使い分ける。各phaseは聴衆の問い、一文の答え、次phaseへの接続、時間、根拠を持つ。`narrative.phase_order` と同じ順序にし、記事種別に不要なphaseを追加しない。
- 記事種別が不明な短いLTだけ、タイトル、自己紹介、今日のゴール、Why、What、How、Demo、Takeaway、まとめ、Thanks をfallbackとして使う。記事入力では `knowledge-structure.md` のarchetypeを優先する。
- 発表時間が30分以上、または本編が20枚を超える場合は、「今日のゴール」の直後に話の地図を必ず1枚置く。`narrative.phase_order` の値は内部分類に留め、可視ラベルは「判断できない理由」「変更地図を作る」のように実際の後続ページを要約する。各項目は後続ページの連続範囲へ一対一で対応させ、ページ追加・削除・並べ替えのたびに再生成する。
- 今日のゴールは agenda ではなく、聴衆への約束として書く。「何を理解し、何を試せる状態になるか」を明示する。
- 実務手順、設定、設計資料、運用を扱う発表では、聴衆が翌営業日に開始できる最小単位（作るファイル、実行するコマンド、確認する条件、承認を求める判断）を必ず決める。
- 複数の部品・手順・概念を扱う発表では、個別説明の前に一つの代表例を開始から結果まで通す。各工程には入力、操作、成果物、完了条件を少なくとも一つずつ示し、途中で例を無断で切り替えない。
- 入力に表、図、チェックリスト、設定例、ドキュメント例、変更パターンがある場合は、抽象的な説明だけで済ませない。各phaseに少なくとも1つ、投影できる代表サンプルまたはデモ候補を `content_inventory` と `slides` に残す。
- `support` は話の要約であり、表・フロー・設定例・チェックリストの代替にしてはならない。HowまたはDemoの各スライドには `evidence_artifact_ids` を割り当て、後工程が具体的なHTML要素を作れるようにする。
- 20分以上では、各本編スライドに `delivery` を置く。通常ページは `talking_points` 2件以上と `visible_anchors` 2件以上を持ち、タイトルやmessageの言い換えだけで埋めない。
- 20分以上では、問い／仕組み／代表例／読み解き／判断・制約を3〜6枚の説明ブロックとして組む。問いと短い結論だけを交互に置かない。
- `visible_anchors` は最終投影面に残す契約であり、固有のファイル名、値、項目、入出力、差分、判断条件を優先する。話者ノートへ退避して削除しない。
- 同じ証拠を複数ページで使う場合は、各ページで新しく読む `focus` または差分を決める。異なる主張に同一の図・表を無注釈で再掲しない。
- 3秒で要点が読めるタイトルにする。
- 今日のゴール（何を伝えたいか）を序盤に出す。
- `narrative.phase_order` を理解順の正本とする。順序を変更した場合は `narrative.flow` の `reason` に理由を残す。
- `slides` は `narrative.flow` の結果として作る。各スライドに対応するphaseを `flow_phase` で示す。表紙、自己紹介、サンクスなど話法上のphaseに属さないものは `flow_phase` を空文字にする。
- `target_slide_count` は初回生成時の固定値ではなく、現在のliveストーリーに必要な本編枚数を表す。説明の追加・分割・統合を行ったら、実際のlive本編枚数に必ず更新する。
- `target_slide_count` とlive本編枚数は、表紙、自己紹介、Thanksを除き、まとめを含めて一致させる。`appendix_slide_count` はappendix/referenceの物理枚数と一致させる。枚数目安だけを理由に次工程を止めない。
- dual-useではliveのrecap/thanks後にappendix/referenceを置いてよい。重要な定義、根拠、例外、判断条件をspoken-noteだけへ置かず、各ページに `knowledge_unit_ids`、`comprehension_check_ids`、`citation_ids` を残す。
- シリーズでは、全体の枚数を一つのパートに詰め込まない。各パートの `target_slide_count` はそのパートのlive本編枚数と一致させる。
- シリーズの `target_slide_count` はパートごとの内容量に応じて変えてよい。同じ値を採用する場合は、均等配分ではなく、各パートの `slide_count_rationale` が必要枚数を根拠付けていることを確認する。
- 全スライドに `speaker_cue` と `spoken_note` を付け、画面に載せない説明を分離する。`speaker_cue` は目的、表示前後の聴衆状態、そのまま話せる台本、指差し対象、次の一言を持つ。
- `spoken_note` は各ページ固有の四行形式にする。`橋渡し:`、`話す内容:`、`指差し:`、`次の一言:` を順に書き、`speaker_cue` と接続情報から生成する。「このページでは〜を確認します」のようなメタ説明、仮文言、全ページ共通の文、画面の単純な復唱を使わない。
- 数値や最新情報には出典と確認日を残す。
- まとめは新情報を持ち込まず、1枚にまとめる。今日のゴールとTakeawayを回収し、最後は `recap` と `thanks` を連続させる。

## Output

単発では `.lt-slide-work/01-story.yaml` だけを正本とする。シリーズでは同ファイルを正本マニフェストとし、`.lt-slide-work/parts/<part-id>/01-story.yaml` を各回の正本とする。チャットにはタイトル、単発／シリーズ判定、分割理由、各回のゴールと枚数内訳、未解決事項を短く示す。後工程を同じターンで依頼されている場合は停止せず `02-lt-slide-blueprint` へ進む。

## Quality Gate

- `core_claim` が1文である。
- スタイルプロファイルがある場合は検証済みであり、`style_profile` に参照と採用ルールが追跡できる。プロファイルを理由に入力にない体験を追加していない。
- `content_inventory` があり、入力資料から抽出した素材と出典が追跡できる。
- 記事またはURL入力では `knowledge_units` が意味分類、重要度、前提、出典、割当スライドを持ち、`validate_knowledge_contract.py` が成功する。
- `full-equivalence` またはdual-useでは5〜10件の `comprehension_checks` があり、スライド本文だけで回答できる。
- dual-useでは可視出典ラベル、referenceスライド、`fact_ledger` があり、外部資料で更新した内容と未検証事項を区別できる。
- `source_asset_inventory` があり、入力の画像・表・コードブロック・設定例ごとに採否と理由が追跡できる。
- `Source Scope Audit` と `coverage_matrix` があり、主要見出し・実装ループごとに、入門要約か全内容か、割当パート、代表アーティファクト、最初の作業、完了条件が追跡できる。
- `narrative.question_spine` が `phase_order` と一致し、各phaseの聴衆の問い、答え、次への接続、時間が分かる。
- 一つの `central_example` が全体を通る。Demoを採用した場合は `demo_runbook`、Takeawayを採用した場合は `tomorrow_action` が具体化されている。
- `slides` が `narrative.flow` から割り付けられており、記事順の単純な写しになっていない。
- 技術・実務テーマのHow/Demoスライドに、少なくとも一つの `evidence_artifact_ids` がある。各アーティファクトは出典と、画面に載せる最小データを持つ。
- 全スライドの `message` が重複していない。
- タイトルだけ読んでも話の流れが分かる。
- 画面用テキストと口頭説明が分離されている。
- 全スライドに `speaker_cue` と四行の `spoken_note` があり、後工程へ引き継げる。
- `validate_talkability.py --story <01-story.yaml>` と `validate_spoken_notes.py --story <01-story.yaml>` が成功する。ノートだけを順に読んでも、問い、答え、接続、実演、結論を再構成できる。
- `audience` に初見者の前提、初出で定義する用語、誤解しやすい前提が残っている。
- 表紙、自己紹介、Thanks以外の各スライドに `reader_context` と `connection_from_previous` があり、前ページからの接続と後読時の主語が追跡できる。
- 新しい用語・略語・抽象化は、平易な定義、必要性、具体例のいずれかを欠かしていない。
- 各 `spoken_note` が画面の単純な復唱や説明方法の説明ではなく、実際に口にする理由・具体例・判断を含み、画面上の指差し対象と次の一言を特定している。
- 全スライドに `flow_phase` がある。phaseに属さないスライドは空文字でよい。
- 自己紹介の採否が確定している。
- 自己紹介の可視本文が `config/presenter.json` の値だけで構成され、テーマ固有の結論や補足が混入していない。
- SNSまたはWebサイト、顔写真またはアバター、QR画像の使用有無がすべて明示回答で確定している。
- まとめが今日のゴールとTakeawayを回収し、新情報を持ち込んでいない。
- Takeawayが「明日何を作成・実行・確認するか」を具体的に言えており、必要な代表サンプルの採否が追跡できる。
- 複数の構成要素を扱う発表では、部品一覧ではなく、最初の一件を開始から改善まで通す実装プレイブックが存在し、各工程の成果物と完了条件が読める。
- 30分以上または本編20枚超の発表では、ゴール直後に話の地図があり、`scripts/validate_roadmap.py --story <01-story.yaml>` が成功する。可視ラベルがphase名だけでなく、全 `slide_ids`・ページ範囲・先頭／末尾タイトルが実際のスライド列と一致している。
- `scripts/validate_duration_floor.py --story <01-story.yaml>` が成功する。シリーズは各パートが個別に成功する。
- 20分以上では `scripts/validate_explanation_depth.py --story <01-story.yaml>` が成功し、時間配分、ページ固有のtalking points、投影面のvisible anchors、低密度ページ比率が妥当である。
- シリーズ判定では、分割理由、分割数、各パートの独立した学習ゴール、入力素材のカバレッジがマニフェストにある。
- 単発判定では、`coverage_matrix` の全 `full coverage` 単位が、指定時間内に具体例と完了条件を持つことを確認している。
- シリーズでは、各パートの `target_slide_count` と `slide_count_rationale` があり、枚数が時間または話数で均等配分されていない。
- シリーズでは、全パート共通のphase長・role列・秒数列へ素材を流し込んでおらず、`scripts/validate_duration_floor.py --story <root-01-story.yaml>` の機械的均等化検査が成功する。
- シリーズの各パートが、単体で表紙、ゴール、具体例、最初の作業、完了条件、まとめ、Thanks を持つ。

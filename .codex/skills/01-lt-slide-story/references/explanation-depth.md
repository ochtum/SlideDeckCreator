# Explanation depth for long-form LT decks

## Purpose

20分以上のLTを、短い主張だけのページ数で埋めないための共通契約。長時間LTでは、枚数、投影面、口頭説明、デモ、時間配分を別々に設計し、最後に同じ学習ゴールへ結び直す。

## Long-form principle

- 5分LTの「一枚一言」は、30分LTへそのまま拡張しない。
- 30分LTは、主張だけでなく、仕組み、代表例、判断基準、制約を説明する。
- 投影面だけを後から読んでも「何について、何が起こり、何を判断するか」を再構成できるようにする。
- 話者ノートだけに説明を退避しない。投影面には、固有名、値、入出力、差分、条件、手順のうち必要なものを残す。
- 長い原稿を貼るのではなく、理解に必要な具体性を表、コード、注釈付き図、比較、チェックリストへ変換する。

## Time budget

20分以上では `project.time_budget` を必須とする。

```yaml
project:
  duration_minutes: 30
  time_budget:
    content_seconds: 1320
    demo_seconds: 240
    interaction_seconds: 120
    buffer_seconds: 120
```

- 4項目の合計は `duration_minutes * 60` と一致させる。
- 各スライドの `delivery.estimated_seconds` 合計は、bufferを除いた秒数と一致させる。
- ページ数から秒数を均等配分しない。定義は45〜75秒、表・コードの読解は60〜120秒、デモは120〜300秒を起点に内容から見積もる。
- 30分LTで口頭説明とデモの合計が20分未満になる場合は、時間を短縮するか、比較、反例、デモ、判断演習を追加する。

## Per-slide delivery contract

20分以上では、各スライドに `delivery` を置く。

```yaml
delivery:
  mode: explain # explain, demo, interaction, transition, recap
  estimated_seconds: 75
  talking_points:
    - App.DefaultPageSize は appsettings.json にある
    - ProductService が値を読み、一覧件数へ反映する
    - 本番変更は影響確認後に承認する
  visible_anchors:
    - App.DefaultPageSize
    - ProductService
    - 影響確認後
```

- `talking_points` は話者が説明する内容。タイトルの読み上げや「ここを説明する」のようなメタ文を書かない。
- `visible_anchors` は投影面で実際に読める固有の語句・値・条件。タイトルまたはmessageの言い換えだけにしない。
- 通常の説明ページは `talking_points` 2件以上、`visible_anchors` 2件以上を持つ。
- transitionは各1件以上でよいが、本編の15%以下、連続1枚までとする。
- demoは、操作、期待結果、失敗時の見方を含める。
- interactionは、問い、考える材料、回収する判断を含める。

## Explanation block

長時間LTは3〜6枚の説明ブロックを単位にする。

1. 問いまたは問題: 何が判断できないか
2. 仕組み: どの要素がどう関係するか
3. 代表例: 実在する値、ファイル、画面、コード、操作
4. 読み解き: 例のどこを見るか
5. 判断または制約: いつ使い、いつ使わないか
6. 必要なら小まとめ: 次のブロックへ持ち越す前提

すべてを毎回6枚にする必要はない。ただし、30分LT全体が「問いと短い結論」だけで進み、仕組み・代表例・判断が欠ける構成は不合格にする。

## Projected explanation sufficiency

表紙、自己紹介、章区切り、Thanks以外の各ページで、次のうち少なくとも2つを投影面に残す。

- subject: 具体的な対象、ファイル、機能、人物、データ
- relationship: 入出力、順序、依存、比較、因果
- evidence: 値、代表行、コード、画面、エラー、観察結果
- decision: 完了条件、選択条件、制約、次の操作

How、Demo、比較、手順、実務判断のページでは `evidence` または `decision` を必須とする。大きな見出し、短いmessage、汎用チェック3件だけでは説明済みとみなさない。

## Content-model specificity

- table: 列名と代表行を持ち、各列が判断にどう使われるか分かる。
- flow: 3工程以上と、少なくとも一つの入出力または判断ゲートを持つ。
- checklist: 抽象名詞ではなく、実行する操作と合格条件を持つ。
- comparison: 比較対象、同じ評価軸、差から導く判断を持つ。
- code/config: ファイル名または適用場所、読める最小断片、注目行を持つ。
- implementation-playbook: 各工程に成果物、担当、完了条件を持つ。

同一の `content_model.data` を別の主張へ使い回さない。比較や段階読解のため再利用する場合は、各スライドに異なる `focus` と `highlight` を置き、何を新しく読むのかを明示する。

## Density wave

- 低密度: 表紙、章区切り、重要な問い、最終結論。
- 中密度: 定義、比較、判断基準、短いチェックリスト。
- 高密度: 注釈付きスクリーンショット、コード、設定、表、システム図。
- 20分以上では、中〜高密度の説明ページを本編の70%以上にする。
- 低密度ページを連続させない。同じレイアウト、同じ図、同じチェック項目の連続も避ける。
- 高密度は小さい文字を意味しない。情報を1つの具体物へ集約し、タイトル領域を抑え、本文領域を広げる。

## Review questions

- このページは、タイトルを隠しても対象と判断が分かるか。
- 具体例は前ページと同じものの無注釈な再掲になっていないか。
- ノートは画面にない仕組み・理由・制約を説明しているか。
- `estimated_seconds` を実際に話せるだけの内容があるか。
- 30分をページ送りで埋めず、理解・比較・デモ・判断に使っているか。

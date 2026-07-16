# LT slide series manifest schema

`01-lt-slide-story` は、入力を一つの発表で完結させるべきか、複数回のシリーズに分けるべきかを先に判定する。単発と判定した場合は従来どおり `01-story.yaml`（schema version 1）を使う。シリーズと判定した場合だけ、ルートの `01-story.yaml` を次のシリーズマニフェストにし、各パートの通常ストーリーを `parts/<part-id>/01-story.yaml` に置く。

```yaml
schema_version: 2
kind: lt-slide-series
project:
  title: "発表シリーズの総題"
  language: ja
  requested_duration_minutes: 30
  content_fidelity: full-equivalence
  work_dir: "../.lt-slide-work"
design_system:
  id: trustworthy-blue
  version: 1.0.0
  registry: "../config/design-systems/registry.yaml"
source_inventory: "./source-inventory.yaml"
coverage_matrix: [] # content-equivalence.mdの全source unitを割り当てる
approved_omissions: []
series_analysis:
  decision: series # single または series
  reason: "一回で扱うと、三つの独立した実装ループのサンプルと完了条件を省略してしまうため"
  split_criteria:
    - "各回の学習ゴールが一つで、終了時に単独で試せる"
    - "各回に具体例、最初の作業、完了条件を置ける"
    - "全ソース項目が少なくとも一つのパートに割り当てられる"
  estimated_total_minutes: 90
  part_count: 3
  coverage:
    - source_item: "step-1"
      parts: [part-01-start-safe]
    - source_item: "step-4"
      parts: [part-02-knowledge-map, part-03-operate-improve]
parts:
  - id: part-01-start-safe
    order: 1
    title: "第1回: 最初の変更を安全に通す"
    duration_minutes: 30
    target_slide_count: 20
    slide_count_rationale: "最初の変更を通す代表デモを中心に、タスクカード、実行、完了条件を個別に示すため"
    learning_goal: "一件の変更をタスクカードから検証まで通せる"
    scope:
      include: ["題材選定", "タスクカード", "AGENTS.md", "完了条件"]
      exclude: ["大規模リポジトリの全体地図"]
    source_items: [step-1, step-2, demo-1]
    story_file: "parts/part-01-start-safe/01-story.yaml"
    blueprint_file: "parts/part-01-start-safe/02-blueprint.yaml"
    visuals_manifest_file: "parts/part-01-start-safe/visuals-manifest.yaml"
    output_dir: "../output/part-01-start-safe"
  - id: part-02-knowledge-map
    order: 2
    title: "第2回: AIが迷わない知識の入口を作る"
    duration_minutes: 30
    target_slide_count: 22
    slide_count_rationale: "機能地図と設定地図の二つの代表サンプルを比較して扱うため"
    learning_goal: "機能地図と読み順をリポジトリに置ける"
    scope:
      include: ["機能地図", "設計資料", "設定と依存関係"]
      exclude: ["本番運用の改善"]
    source_items: [fact-3, step-3, demo-2]
    story_file: "parts/part-02-knowledge-map/01-story.yaml"
    blueprint_file: "parts/part-02-knowledge-map/02-blueprint.yaml"
    visuals_manifest_file: "parts/part-02-knowledge-map/visuals-manifest.yaml"
    output_dir: "../output/part-02-knowledge-map"
  - id: part-03-operate-improve
    order: 3
    title: "第3回: 実行・検証・失敗を仕組みに戻す"
    duration_minutes: 30
    target_slide_count: 19
    slide_count_rationale: "再現環境、検証、失敗分類、改善ループを一件の実行例で扱うため"
    learning_goal: "再現環境と失敗の反映ループを作れる"
    scope:
      include: ["再現環境", "テストハーネス", "観測", "失敗の反映"]
      exclude: []
    source_items: [step-4, step-5, caution-2]
    story_file: "parts/part-03-operate-improve/01-story.yaml"
    blueprint_file: "parts/part-03-operate-improve/02-blueprint.yaml"
    visuals_manifest_file: "parts/part-03-operate-improve/visuals-manifest.yaml"
    output_dir: "../output/part-03-operate-improve"
open_questions: []
```

各 `story_file` は `story-schema.md` の schema version 1 に従う独立した一回分のストーリーである。表紙、今日のゴール、具体的な最初の作業、まとめ、Thanks を各パートに含める。シリーズ全体の話数を均等に割ることや、後半を「続き」とだけすることは禁止する。

`coverage` は `content_inventory` の ID を漏れなく追跡する。ある素材を意図的に扱わない場合は、その理由を `series_analysis.reason` または各パートの `scope.exclude` に残す。

`full-equivalence` では概要用の `series_analysis.coverage` だけで合格にしない。`content-equivalence.md` のsource inventory全unitをルート `coverage_matrix` へ置き、part ID、slide ID、伝達面、構造保存方法、artifact IDを追跡する。各パートStoryとBlueprintの `source_unit_ids`、最終HTMLの `data-source-unit-ids` まで同じIDを保持する。

`target_slide_count` は各パートの物理本編枚数であり、同じ発表時間や話数を理由に同じ値へそろえない。`slide_count_rationale` に、各回で必要な代表サンプル、デモ、最初の作業、完了条件から見積もった理由を残す。時間が余る場合は、具体例の比較、演習、質疑の余白を優先し、内容のないスライドで埋めない。

各パートは指定時間の本編安全下限を個別に満たす。`cover`、`profile`、`thanks` は本編枚数に含めず、`recap` は含める。30分以上の安全下限は16枚、標準範囲は18〜24枚だが、各回の問い・例・実演・完了条件から決める。`scripts/validate_duration_floor.py --story <root-01-story.yaml>` が全パートで成功するまで、設計図またはビルドへ進めない。

20分以上の各パートは、`story-schema.md` の `project.time_budget` と各スライドの `delivery` を独立して持つ。シリーズ合計時間だけで説明量を満たした扱いにしない。`scripts/validate_explanation_depth.py --story <root-01-story.yaml>` が全パートで成功するまで次工程へ進めない。

20分以上の各パートは `talkability.md` の問いの背骨、Demo runbook、明日の一手、全ページの話者キューを独立して持つ。シリーズ全体の問いや最終回のTakeawayで代用しない。`scripts/validate_talkability.py --story <root-01-story.yaml>` が全パートで成功するまで次工程へ進めない。

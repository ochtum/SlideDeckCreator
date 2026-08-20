# 知識構造とストーリー選択の契約

## 目的

記事の見出しや文章量ではなく、読者が獲得する説明・区別・判断・適用能力をスライドへ移す。Markdown上の `source_inventory` は入力構造の台帳、`knowledge_units` は意味の台帳として併用する。

## Request contract

記事またはURLをスライド化するときは、分かる範囲で次をStoryへ保存する。合理的に補完した値は `request.assumptions` に理由とともに残し、作業を止める質問は結果を大きく変える項目だけにする。

```yaml
request:
  publication_channels: [speakerdeck]
  must_keep: ["主要な判断基準"]
  out_of_scope: []
  fact_check_policy: primary-sources # primary-sources, source-only, none
  assumptions:
    - field: prior_knowledge
      value: "一般的なWeb開発の基礎"
      reason: "対象読者の記述から補完"
```

## Document type and archetype

入力を一つ以上の種類へ分類し、記事の章立てではなく理解順を選ぶ。

| document type | narrative archetype | phase例 |
| --- | --- | --- |
| concept | problem-explanation-application | problem, definition, mechanism, example, takeaway |
| tutorial / hands-on | goal-steps-result | goal, prerequisites, procedure, result, caution, takeaway |
| comparison | criteria-comparison-decision | problem, criteria, comparison, decision, takeaway |
| design | constraints-options-tradeoffs | context, constraints, options, tradeoffs, decision |
| troubleshooting | symptom-cause-fix | symptom, diagnosis, cause, fix, verification |
| case study | context-action-result | context, action, observation, result, lesson |
| retrospective | context-events-learning | context, attempt, result, failure, learning |
| research / experiment | hypothesis-evidence-limitations | question, method, observation, interpretation, limitation |
| opinion / proposal | problem-evidence-proposal | current-state, problem, evidence, proposal, objection |

`source.document_types` には `concept`, `tutorial`, `hands-on`, `comparison`, `design`, `troubleshooting`, `case-study`, `retrospective`, `research`, `experiment`, `opinion`, `proposal` の正規化トークンを一つ以上保存する。

`narrative.phase_order` を正本とし、`question_spine` を同じ順序にする。20分以上でも、記事種別に存在しないDemoを捏造しない。Demoを含める場合だけ `demo_runbook` を必須にする。Takeawayを含める場合だけ `tomorrow_action` を必須にする。

## Knowledge units

各単位は、原文の一節と一対一でなくてよい。一節から複数の知識単位を抽出でき、一つの知識単位が複数節にまたがってもよい。ただし `project.authoring_mode: section-faithful` では、知識単位が複数節にまたがっても節スライドを統合しない。`source_section_ids` と `talk_track` は節単位、`knowledge_unit_ids` は意味単位として別々に保持する。

```yaml
knowledge_units:
  - id: ku-001
    source_unit_ids: [article-section-001]
    type: claim
    statement: "入力の主張を一文で表す"
    importance: essential # essential, supporting, reference
    prerequisites: []
    artifact_ids: []
    citation_ids: []
    slide_ids: [s04]
```

`type` は `claim`, `definition`, `evidence`, `causal`, `comparison`, `procedure`, `example`, `caution`, `decision`, `reference` から選ぶ。入力に存在しない意味を埋めるためだけに単位を追加しない。

- `essential`: 発表の結論・理由・判断に必要。liveまたはappendixの可視スライドへ必ず置く。
- `supporting`: 理解を補強する。時間に収まらなければappendixへ移せる。
- `reference`: 完全版コード、詳細条件、追加出典など。referenceへ置ける。

## Comprehension checks

`full-equivalence` または `delivery_profile: dual-use` では5〜10問を作る。暗記問題だけにせず、`explain`, `distinguish`, `choose`, `apply`, `qualify` を組み合わせる。

```yaml
comprehension_checks:
  - id: check-01
    kind: distinguish
    prompt: "AとBをどの条件で使い分けるか説明できるか"
    knowledge_unit_ids: [ku-003, ku-004]
    slide_ids: [s09, a02]
```

完成時は、スピーカーノートを見ず、指定されたスライド本文だけで各問に回答できることを確認する。

## Coverage rules

- 一つのスライドは一つの中心論点または問いを扱う。知識単位を一つに限定しない。
- `section-faithful` の節スライドは一つの `source_section_ids` だけを持つ。複数節にまたがるknowledge unitは各節スライドへ重複参照できるが、節を一枚へ統合する根拠にしない。
- 複雑な知識単位は複数スライドへ分けてよい。
- 各スライドに `knowledge_unit_ids` と `comprehension_check_ids` を残す。
- `full-equivalence` では既存の `source_inventory` / `coverage_matrix` も維持し、構造台帳と意味台帳の両方を追跡する。
- 削除は `approved_omissions`、範囲外は `request.out_of_scope` に理由を残す。

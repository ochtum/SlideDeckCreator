# 入力と同等に理解できる内容カバレッジ

## 目的

「全内容を扱う」という依頼を、主要テーマへの言及だけで完了させない。発表後の聴衆が、入力資料を読んだ場合と同じく、目的、仕組み、手順、代表例、制約、完了条件を説明・再現できる状態を `full-equivalence` とする。原文の全転載は目的ではない。

## 内容忠実度

- `overview`: 全体像と主要な判断だけを伝える。細部の省略を許す。
- `representative`: 各主要テーマに一つ以上の具体例を残す。類似例の省略を許す。
- `full-equivalence`: 全ての規範的な要件、再利用可能なテンプレート、表、コード、設定、図、フロー、注意点、完了条件を追跡可能にする。

ユーザーが「全内容」「入力と同等」「シリーズですべて」と指定した場合は `project.content_fidelity: full-equivalence` とする。時間不足を理由に暗黙に `overview` へ下げてはならない。必要時間が指定枠を超える場合は、シリーズ回数を増やすか、ユーザー承認済みの `approved_omissions` を残す。

## Source Inventory

Story作成前に次を実行し、入力を安定した学習単位へ分解する。

```powershell
python .codex/skills/01-lt-slide-story/scripts/audit_content_equivalence.py `
  --source input/article.md --source input/implementation.md `
  --inventory-out .lt-slide-work/source-inventory.yaml
```

台帳は少なくともH2〜H4の節、Markdown表、コード／設定ブロック、Mermaid、画像、チェックリストを含む。節単位は説明すべき意味、asset単位は構造を残すべき具体物である。

## Coverage Matrix

`full-equivalence` ではルートStoryへ次を置く。

```yaml
project:
  content_fidelity: full-equivalence
source_inventory: ./.lt-slide-work/source-inventory.yaml
coverage_matrix:
  - unit_id: implementation-h2-001
    parts: [part-02]
    slide_ids: [s12, s13]
    delivery_surfaces: [visible, spoken]
    preservation: explain
    artifact_ids: []
    status: covered
  - unit_id: implementation-code-003
    parts: [part-02]
    slide_ids: [s14]
    delivery_surfaces: [visible]
    preservation: structure-preserved
    artifact_ids: [artifact-agents-template]
    status: covered
approved_omissions: []
```

各パートStoryとBlueprintの各ページにも `source_unit_ids` を引き継ぎ、最終HTMLの `.slide` へ空白区切りの `data-source-unit-ids` として保持する。

## 判定基準

- 全台帳unitに `covered` のcoverageがある。
- coverageには実在するpartとslide IDがある。
- `section` は `explain`、`example-preserved`、`structure-preserved` のいずれかで、画面またはspoken-noteから目的・仕組み・判断を再構成できる。
- `table`, `code`, `config`, `mermaid`, `image`, `checklist` は `structure-preserved`、`exact`、`reconstructed` のいずれかで、`artifact_ids` と可視実装を持つ。テーマ名だけのカードは不可。
- HTMLの `data-source-unit-ids` から台帳まで逆引きできる。
- `approved_omissions` はユーザーが明示的に範囲縮小を承認した場合だけ使う。理由と承認内容を残す。

機械検証後、レビュー担当は各unitについて「なぜ必要か」「何なのか」「どう使うか」「どの具体物を読むか」「何をもって完了か」を入力なしで説明できるか確認する。文字列一致やページ数だけで同等性を判定しない。

## 時間見積り

台帳から説明時間を積み上げる。目安は節45〜90秒、表・設定・コード60〜120秒、フロー・Mermaid90〜150秒、Demo操作90秒以上である。同じページで自然に統合できるunitは重複分を削減できるが、具体物を表示・読み解く時間をゼロにしない。1回の指定時間へ収まらなければ、全体を薄めずシリーズ回数を増やす。

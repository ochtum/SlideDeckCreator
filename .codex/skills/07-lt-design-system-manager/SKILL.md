---
name: 07-lt-design-system-manager
description: デザインに詳しくない人への少数ずつの質問から、LTスライド用デザインシステムを作成・プレビュー・検証し、config/design-systemsの登録一覧へ追加する。既存システムの変更、使用状況を確認した安全な削除、複数テーマの並存、Story・Blueprint・HTMLからの選択を扱うときに使用する。
---

# 07 LT Design System Manager

LT資料の色、文字、余白、形、図表、モーションを、専門用語を知らなくても選べる質問へ変換する。単一のファイルを上書きせず、`config/design-systems/registry.yaml` で複数のデザインシステムを管理する。

## Required Reads

- 質問を始める前に `references/question-flow.md`
- specを作成・変更・検証するときは `references/design-system-schema.md`
- 01〜05工程へ接続するときは `references/pipeline-integration.md`

## Storage Contract

```text
config/design-systems/
├─ registry.yaml
├─ <design-system-id>/
│  ├─ design-system.yaml
│  ├─ preview.html
│  └─ history/                 # update前の版
└─ _archive/                   # removeした版
```

追加は新しいIDのフォルダを作り、既存システムを消さない。変更は同じIDを更新する前に `history/` へ旧版を残す。削除はregistryから外して `_archive/` へ移し、使用中なら停止する。完全消去はユーザーが明示した場合だけ `--purge` を使う。

## Workflow

1. 操作を `add`、`update`、`remove`、`list`、`preview` のどれかに分類する。曖昧なら一覧を表示してから確認する。
2. `add` / `update` では `references/question-flow.md` に従い、一度に最大3問だけ聞く。ソース、ロゴ、既存ブランド資料から分かることは聞かない。HEX、コントラスト比、タイポグラフィスケールなどの専門語を回答者へ要求しない。
3. 回答を `references/design-system-schema.md` のtokenへ変換する。ブランド色がない場合は、印象と明暗から読みやすい配色を提案する。本文と背景のコントラスト4.5:1以上を初期値にする。
4. 一時spec YAMLを作り、`manage_design_system.py validate-spec --spec <spec.yaml>` で検証する。
5. `add --root config/design-systems --spec <spec.yaml>` を実行する。既存IDがあれば上書きせず停止する。
6. `update --root config/design-systems --id <id> --spec <spec.yaml>` は既存specを読み、変更したい点だけ質問し、未変更tokenを保持した完全なspecで実行する。旧版はhistoryへ保存される。
7. `remove --root config/design-systems --id <id> --project-root .` は参照元を調べる。使用中なら該当Story/Blueprint/HTMLを示して停止し、別デザインへの切替を先に行う。未使用ならarchiveへ移す。
8. `preview` を生成し、色だけでなくタイトル、本文、表、コード、フロー、結論、アニメーション強度のサンプルを確認する。見た目の承認後、Storyの `design_system.id` と `version` へ選択を保存する。
9. `list` と `validate` を実行し、registryの重複、欠損ファイル、token、コントラスト、最低文字サイズ、reduced motion対応を確認する。

## Safe Change Rules

- `add` で既存IDを上書きしない。名前が同じでも別IDを確認する。
- `update` でIDを変更しない。別IDにしたい場合は `add` として複製する。
- `remove` で使用中のシステムを消さない。`--force` は参照を理解したユーザーが明示した場合だけ使う。
- `--purge` はarchiveを残さない不可逆操作である。ユーザーが完全消去を明示しない限り使わない。
- フォントファイル、ロゴ、写真の利用権が不明な場合は登録せず、system-uiと代替図形でpreviewする。
- 色だけで意味を伝えない。success/warning/dangerにはラベル、記号、形の差を併用する。

## Handoff

完了時はID、表示名、version、操作種別、preview、検証結果、選択方法を伝える。新規追加だけで既存デッキの選択は勝手に変更しない。

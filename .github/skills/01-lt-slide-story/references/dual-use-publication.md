# 登壇兼閲覧資料の契約

## Purpose

登壇中に読みやすく、SpeakerDeckや静的PDFを音声なしで読んでも論理・条件・出典を追える資料を `delivery_profile: dual-use` とする。話し方を支える情報と、理解を成立させる情報を混同しない。

## Project contract

```yaml
project:
  delivery_profile: dual-use # live-only, dual-use
  publication_channels: [youtube, speakerdeck]
  target_slide_count: 22      # liveの本編枚数
  appendix_slide_count: 8
  time_budget:
    content_seconds: 1080
    demo_seconds: 240
    interaction_seconds: 120
    q_and_a_seconds: 180
    buffer_seconds: 180
```

全項目の合計を登壇枠と一致させる。スライド別時間はliveだけを合計し、appendixとreferenceは登壇時間へ含めない。

## Delivery scope

各スライドに `delivery_scope` を置く。

- `live`: 登壇時に説明する。本編時間と `target_slide_count` の対象。
- `appendix`: 後読に必要だが登壇中は飛ばせる。必須知識の詳細、例外、完全比較を置く。
- `reference`: 完全版コード、用語集、出典一覧など参照用。

liveの末尾は `recap`、`thanks` とする。dual-useでは、その後にappendixとreferenceを置いてよい。HTMLの通常ナビゲーションはlive末尾を発表終了地点として扱い、一覧・直リンク・PDFからappendixへ到達できるようにする。

## Three information layers

各ページを必要に応じて次の階層で設計する。

1. `glance`: タイトルまたは結論。登壇中に短時間で把握できる。
2. `explanation`: 図、表、コード、具体例、理由。理解を成立させる。
3. `reader_support`: 適用条件、例外、出典、用語補足。後読を支える。

第3階層を小さい文字で詰め込まない。短い条件・出典だけを同じページへ置き、詳細はappendixへ分ける。`essential` な知識を `spoken_note` だけに置かない。

## Visible citations and fact ledger

数値、引用、製品仕様、更新され得る情報、外部資料で補った主張には `citation_ids` を付ける。

```yaml
citations:
  - id: ref-01
    label: "[1]"
    title: "資料名"
    publisher: "発行元"
    url: "https://example.com"
    checked_at: "YYYY-MM-DD"

fact_ledger:
  - knowledge_unit_id: ku-004
    status: verified # source-stated, verified, updated, unverified
    citation_ids: [ref-01]
    note: "記事記載を現在の一次資料で確認"
```

- `label` は対象スライドの可視テキストとして表示する。
- referenceスライドに資料名、発行元、URL、確認日をまとめる。
- `data-citation-ids` は追跡用であり、可視出典の代替にしない。
- 記事と一次資料が異なる場合は黙って変更せず、`fact_ledger.status: updated` と理由を残す。

## Speaker notes boundary

`spoken_note` は橋渡し、話す例、指差し、次の一言を支援する。次をノートだけへ置かない。

- 用語の定義
- 主張の根拠と因果関係
- 重要な例外・適用条件
- 実務判断に必要な条件
- 記事の主要な結論

## Code and demo variants

- liveには読解に必要な抜粋と期待結果を置く。
- appendix/referenceにはコピー可能な完全版を置ける。
- `artifact_variants` で抜粋と完全版を結ぶ。
- ライブDemoを行う場合も、静的PDFに操作前、操作、期待結果またはfallbackを残す。

## Completion report

レビュー報告には、本編／補足枚数、live時間、補足へ移した内容、削除と理由、外部資料で更新した内容、未検証事項、前提、未対応知識、理解確認問題との対応、可視出典の確認結果を含める。Storyと検証結果から生成し、別の手作業台帳を正本にしない。

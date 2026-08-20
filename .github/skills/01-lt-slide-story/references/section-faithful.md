# 記事セクション忠実モード

## 目的

完成済みの記事をスライド化するとき、発表向けの再構成によって節ごとの主張、手順、具体物が失われることを防ぐ。`section-faithful` では記事の見出し構造と順序を入力契約にし、各節の話す内容を先に確定してから投影面を作る。

このモードは、見出し構造を持つ記事、設計資料、実装ガイドで、ユーザーが記事の内容・順序・見出しを保ちたい場合に使う。トピック、箇条書きメモ、断片的な素材から新しい物語を構成する場合は、従来の `narrative-recompose` を使う。

## 基本契約

- コードフェンス内の `#` は見出しとして扱わない。Markdown本文のH1〜H4を順序付きの `source-sections.yaml` へ抽出する。
- 文書タイトル、本文節、Tips、FAQ、補足、参考資料を区別するが、入力から黙って削除しない。
- 通常は一つのsource sectionを一つのスライドへ対応させる。
- 一つのスライドへ複数のsource sectionを統合してはならない。
- 一つのsectionを複数スライドへ分ける場合は、`split_reason` と各スライドが担当するpointを記録する。
- source sectionの相対順序を変えない。表紙、自己紹介、ゴール、道筋、まとめ、Thanksなどの合成ページは節間へ追加できる。
- 見出しをそのまま使う指定がある場合は、節スライドの `title` を原見出しと同じ文字列にする。短い結論は別の `message` に置く。
- 原見出し自体が「〜を用意する」のような動作表現でも、主語を補って改題しない。`semantic_clarity.labels` に `source_heading: true` と保持理由を置き、主語・行為者・対象・述語を明示した中心主張は `message` のclaimとして別に作る。`source_heading: true` は単一の `source_section_ids` を持つtitleだけに使える。
- 参考資料の節は `delivery_scope: reference`、後読専用の補足節は `appendix` にできる。ただし節とページの対応を残す。

## Spoken Note先行

source sectionから、スライド本文より先に `talk_track` を作る。

```yaml
section_coverage:
  - section_id: article-a1b2c3-section-004
    slide_ids: [s07]
    coverage: abridged # full, abridged, appendix, reference
    abridgement_note: "30分枠のため、類似例を一つにまとめる。判断基準と手順は残す。"
    split_reason: ""
    points:
      - id: section-004-p01
        text: "四つのドキュメントは役割を分ける"
        importance: essential
      - id: section-004-p02
        text: "同じ説明を複製せず正本を一つにする"
        importance: essential
slides:
  - id: s07
    source_section_ids: [article-a1b2c3-section-004]
    talk_track:
      source_section_id: article-a1b2c3-section-004
      beats:
        - point_id: section-004-p01
          spoken_text: "既存システムの知識は、一つの巨大資料ではなく役割の異なる四つの正本へ分けます。"
          visible_text: "四つの正本を役割で分ける"
        - point_id: section-004-p02
          spoken_text: "同じ説明を複製せず、更新する正本を一つに決めます。"
          visible_text: "説明を複製せず正本を一つにする"
```

`speaker_cue.script` は同じスライドの全 `talk_track.beats[].spoken_text` を、pointの順序を変えず自然な接続だけ加えて作る。`spoken_note` の `話す内容:` は `speaker_cue.script` と一致させる。スライドのtitle、message、support、表、コード、図ラベルは `visible_text` または同じsectionのartifactから作る。話す内容に存在しない新しい中心主張を投影面へ追加しない。

各pointは、割当スライドのいずれかのbeatへ必ず対応させる。sectionの概要だけを一文話し、入力にある手順、判断、注意点を未割当のまま `covered` としてはならない。

## 時間契約

見出し台帳を作った直後に、本文文字数、表・コード・図の数、指定時間を比較する。原文を読むだけで指定時間を超える場合でも、節を自動統合したり削除したりしない。

次のいずれかをStoryへ記録する。

- `coverage: full`: 節のessential pointを省略せず話す。
- `coverage: abridged`: 全体の判断を保ちながら類似例・背景説明を短縮する。`abridgement_note` を必須にする。
- `coverage: appendix`: liveでは扱わず、後読用ページへ節全体を移す。
- `coverage: reference`: 書誌・リンク・完全版資料として残す。

essential pointが指定時間へ収まらない場合は、シリーズ化、時間延長、ユーザー承認済みの省略のいずれかを選ぶ。時間不足を理由に `narrative-recompose` へ切り替えたり、複数節を一枚へ統合してはならない。

## シリーズ時の割当

シリーズ化する場合もsource sectionを分割管理の正本にする。各partのStoryへ `section_scope` を置き、そのpartが担当する `section_id` を原文順で列挙する。

- 同じsectionを複数partへ重複割当しない。
- 全partの `section_scope` の和集合が、文書タイトルを含む全source sectionを覆うようにする。
- partをまたいでもsource sectionの相対順序を変えない。
- 一つのsectionをpart境界で割らない。長いsectionは同じpart内で複数スライドへ分割し、`split_reason` を残す。
- root Storyの `parts[].story_file` から各partを読み、validatorで重複、欠落、順序を確認する。

## 成果物と検証

最初に見出し台帳を生成する。

```powershell
python .github/skills/01-lt-slide-story/scripts/validate_section_fidelity.py `
  --source input/article.md `
  --manifest-out .lt-slide-work/source-sections.yaml
```

Story作成後は次を実行する。

```powershell
python .github/skills/01-lt-slide-story/scripts/validate_section_fidelity.py `
  --manifest .lt-slide-work/source-sections.yaml `
  --story .lt-slide-work/01-story.yaml
```

BlueprintとHTMLでも同じvalidatorを実行する。`visible_text` は、Blueprintではtitle、message、text、visual annotations、実際に描画される `content_model.data` / `focus` / `highlight` のいずれか、HTMLでは実DOMの可視文字として存在しなければならない。検証専用の任意キーやdata属性だけへ退避して合格にしてはならない。

# 主語・行為者・変更対象の明確性契約

## 目的

投影面だけを一枚ずつ読んだときに、「誰が／何が、誰の判断で、何を、どうするか」を復元できるようにする。前ページ、話者ノート、口頭の補足、文脈上の暗黙の「私たち」へ依存しない。

## 区別する四要素

- `subject`: 文法上の主語または主題。表示文の中で `は`、`が`、`も` のいずれかに接続する語句を書く。
- `actor`: 意図を持って操作・判断・変更する行為者。人、組織、AI、ツール、プロセス、システムのいずれかを明示する。
- `target`: 行為者が変更・確認・判断・作成・選別する対象。表示文の中で `を`、`へ`、`に`、`から` などに接続する語句を書く。変更対象が文法上の主語になる受動文では `subject` と同じ値でよい。
- `predicate`: 対象に何をするか、または主語がどの状態かを表す述語。`確認する`、`変更する`、`不足している` のように表示文と同じ形で書く。

文法上の主語と行為者は同じとは限らない。たとえば「設定値はCopilotによって変更される」では、`subject` と `target` は設定値、`actor` はCopilotである。

## 可視文のルール

- `action`、`change`、`decision` の文は、主語・行為者・対象・述語を同じ可視文または同じ原子節へ明記する。
- `definition`、`state` の文は主語と述語を明記する。行為者または対象が存在しない場合だけ、`not_applicable` にその項目を列挙する。
- 「作る」「確認する」「変える」「定義する」「選別する」「たどる」「戻す」「始められる」のような行為・変更・判断を表す文を、`definition` や `state` として行為者なしに扱わない。
- タイトルと中心メッセージは、それぞれ単独で意味を取れる文にする。タイトルが章名・資料名・問いなどの純粋なラベルなら `labels` に分類し、理由を書く。
- `section-faithful` でユーザーが原見出しの保持を指定した場合だけ、動作表現を含む原見出しを `source_heading: true` のtitle labelとして保持できる。これは改題禁止との両立用であり、同じページの `message` には主語・行為者・対象・述語がそろったclaimを必ず置く。
- 接続助詞で複数の行為を結ぶ場合は原子節へ分ける。たとえば「人が方針を決め、Copilotが変更を実行する」は二つのclaimとして記録する。
- 指示語だけの対象（「これを」「それを」「対象を」）、省略された行為者、前ページにしかない主語を使わない。
- ファイル、リポジトリ、仕様書を文法上の主語にする場合、それが実際の行為者か、単なる変更対象・情報源かを確認する。意図を持たない対象へ「選別する」「決める」「確認する」を割り当てない。
- 名詞句だけのカード見出し、表の列名、コード、設定キーはclaimにしなくてよい。ただし、動作や判断を表す完全な文・句は本文中でもclaimに含める。

## Story契約

新規Storyは `project.semantic_clarity_version: 1` を持つ。表紙、自己紹介、Thanksを除く各スライドに `semantic_clarity` を置く。reference専用ページだけは、URLや書誌情報の一覧で主張を持たない場合に限り `status: exempt` と理由を使える。

```yaml
project:
  semantic_clarity_version: 1
slides:
  - id: s10
    role: action
    title: "保守担当者がCopilotへの入口を3層に分ける"
    message: "Copilotが変更対象の正本へ最短で到達できるようにする"
    semantic_clarity:
      status: required
      claims:
        - surface: title
          surface_text: "保守担当者がCopilotへの入口を3層に分ける"
          clause: "保守担当者がCopilotへの入口を3層に分ける"
          kind: action
          subject: "保守担当者"
          actor: "保守担当者"
          actor_kind: human
          target: "Copilotへの入口"
          predicate: "3層に分ける"
          not_applicable: []
        - surface: message
          surface_text: "Copilotが変更対象の正本へ最短で到達できるようにする"
          clause: "Copilotが変更対象の正本へ最短で到達できるようにする"
          kind: action
          subject: "Copilot"
          actor: "Copilot"
          actor_kind: ai
          target: "変更対象の正本"
          predicate: "到達できるようにする"
          not_applicable: []
      labels: []
```

定義または状態では、存在しない役割だけを不適用にする。

```yaml
semantic_clarity:
  status: required
  claims:
    - surface: title
      surface_text: "ハーネスはAIの変更経路を支える開発環境である"
      clause: "ハーネスはAIの変更経路を支える開発環境である"
      kind: definition
      subject: "ハーネス"
      actor: ""
      actor_kind: not-applicable
      target: ""
      predicate: "開発環境である"
      not_applicable: [actor, target]
  labels: []
```

純粋なラベルはclaimへ偽装しない。

```yaml
semantic_clarity:
  status: required
  claims:
    - surface: message
      surface_text: "保守担当者が最初の30分で機能対応表を1行作る"
      clause: "保守担当者が最初の30分で機能対応表を1行作る"
      kind: action
      subject: "保守担当者"
      actor: "保守担当者"
      actor_kind: human
      target: "機能対応表"
      predicate: "1行作る"
      not_applicable: []
  labels:
    - surface: title
      surface_text: "今日のゴール"
      reason: "ページの役割を示す章ラベルで、行為や状態を主張しないため"
```

`surface` は `title`、`message`、`body` のいずれかにする。`surface_text` は投影面へそのまま残す可視文字列、`clause` はその中の一つの主語・述語関係である。複数の原子節が一つの `surface_text` に含まれる場合は、同じ `surface` と `surface_text` を持つclaimを複数作る。

## 生成時監査

各スライドを単独で見て、次を順に答える。

1. 文法上の主語はどの語句か。表示文に `は` または `が` とともに存在するか。
2. 実際に判断・操作・変更するのは誰または何か。主語と異なるなら両方見えるか。
3. 何を変更・確認・判断・作成するのか。`対象`、`これ`、`それ` ではなく固有の対象名になっているか。
4. 対象へ何をするのか。述語が対象と同じ原子節にあるか。
5. タイトル、中心メッセージ、動作を述べる本文の全てがclaimsまたは正当なlabelsへ対応しているか。

一つでも答えられない場合は、話者ノートで補わず可視文を直す。

## 検証

Story生成後に次を実行する。BlueprintとHTMLがある場合は同じ可視文が保たれているかも照合する。

Blueprintではtitle、message、`text`、`visual.annotations`、rendererが描画する `content_model.data` / `focus` / `highlight` だけを可視面として数える。`semantic_support`、metadata、data属性など、rendererが消費しない任意キーへ `surface_text` を置くだけでは合格にしない。HTMLでは実DOMの文字だけを照合し、script、style、data属性を可視文として数えない。

```powershell
python .github/skills/01-lt-slide-story/scripts/validate_semantic_clarity.py --story .lt-slide-work/01-story.yaml
python .github/skills/01-lt-slide-story/scripts/validate_semantic_clarity.py --story .lt-slide-work/01-story.yaml --blueprint .lt-slide-work/02-blueprint.yaml --html output/index.html
```

# Extraction Criteria

資料ごとに下記を観察し、各特徴を `shared`、`candidate`、`deck-specific`、`unknown` のいずれかに分類する。

| Area | Observe | Convert to a rule only when |
| --- | --- | --- |
| Presenter stance | 専門家・実験者・伴走者のどこから話すか | 複数資料で同じ立ち位置がある |
| Narrative | 疑問、条件、試行、失敗、発見、結果、実務評価の順序 | 順序が学びに寄与している |
| Headings | 説明、問い、独り言、感情、結論、転換の比率 | 文型と使う場面が説明できる |
| Voice | 文末、文長、疑問符、感嘆符、三点リーダー、呼びかけ | 使用場面と上限を定義できる |
| Emotional beats | curiosity、skepticism、challenge、failure、discovery、success、reflection | 前後の具体的な情報と結び付く |
| Specificity | 数値、制約、時間、ファイル、コード、エラー、成果物 | 同じ種類の具体物を好んで示す |
| Visual composition | 一言ページ、図・画面キャプチャ、余白、強調色、フロー | PDF/画像など視覚情報を確認できた |
| Speaker notes | 画面外で補う背景、判断、前後接続 | 台本・ノートを確認できた |

## Decision Rules

- 3資料以上で確認: `shared`。恒常ルール候補。
- 2資料で確認: `candidate`。`SHOULD` または `MAY` に限定する。
- 1資料だけ: `deck-specific`。根拠資料に残すが、プロファイルの恒常ルールにしない。
- 視覚やノートを取得できない: `unknown`。補完や推測をしない。
- テーマや発表目的だけで説明できる特徴: `deck-specific` とする。

## Safety Checks

- 表現のために実際には起きていない失敗、驚き、成功、感情を追加しない。
- スタイルが技術的正確性、初見者への定義、具体物の可読性を下回らないようにする。
- 既存資料の固有フレーズを繰り返しコピーしない。役割と条件を抽象化する。

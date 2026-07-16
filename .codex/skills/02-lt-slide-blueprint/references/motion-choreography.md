# 意味のあるモーション演出

## 目的

動きの種類を増やすこと自体を目的にせず、理解の順序、比較、因果、変化、判断の瞬間を動きで伝える。同じ3stepと同じ上昇表示を全ページへ複製しない。

## Motion Family

| family | presets | 使いどころ |
| --- | --- | --- |
| quiet-reveal | `fade`, `rise`, `blur-in` | 定義、補足、静かな導入 |
| direction | `slide-left`, `slide-right`, `wipe` | before/after、比較、進行方向 |
| structure | `draw`, `marker` | フロー、依存関係、注目箇所 |
| focus | `pop`, `zoom-focus`, `flip-in` | 数値、主役、視点の切替 |
| decision | `stamp`, `stomp` | 警告、完了、結論。多用しない |

`animation.intent` には、その動きで何を理解させるかを書く。`family` と `preset` はintentから選び、装飾目的で無関係な強い動きを入れない。

## ページ役割ごとの基本演出

- 定義: 見出しは `fade`、構成要素は `rise`、キーワードだけ `marker`。
- 比較: 左を `slide-left`、右を `slide-right`、差分または結論を `pop`。
- フロー: 入力を `fade`、接続線を `draw`、工程を順番に `rise`、判断ゲートを `stamp`。
- コード／設定: 全体を `wipe`、読む行を `marker`、実行結果を `pop`。文字単位の疑似タイプ演出はしない。
- Demo: 操作対象を `zoom-focus`、変化を `wipe`、観測結果を `pop`、完了を `stamp`。
- 章の切替: `blur-in` または左右方向の移動を一度だけ使い、本文ページより大きな呼吸を作る。
- Takeaway: 手順を `rise`、成果物を `zoom-focus`、完了条件を `stomp`。

## デッキ全体のリズム

本編20枚以上では次を満たす。

- 5種類以上のpreset、4種類以上のfamilyを使う。
- 同じanimation signature（step数とpreset列）を3ページ連続させない。
- step数は役割に応じて1〜5を使い分け、少なくとも3種類のstep数を含める。全ページを同じstep数にしない。
- 一つのpresetが全指定の65%を超えない。
- `stamp`, `stomp`, `flip-in` の合計は全指定の20%以下とし、章の結論、警告、Demo結果へ予約する。
- 一ページの最大stepは6。細かい語句を個別に出さず、意味のまとまりで表示する。
- delayは同一step内の関連要素だけ80〜180msずらせる。次のstepを自動再生しない。
- 連続する静かな説明の後、比較、フロー、Demo、結論でmotion familyを切り替えて呼吸を作る。

## Blueprint Contract

```yaml
animation:
  intent: "左の変更前と右の変更後を対で理解させ、最後に差分へ注目させる"
  family: direction
  entrance:
    - {target: title, preset: fade, delay_ms: 0, duration_ms: 360, easing: standard}
  steps:
    - {step: 1, targets: [before], preset: slide-left, delay_ms: 0}
    - {step: 2, targets: [after], preset: slide-right, delay_ms: 0}
    - {step: 3, targets: [difference], preset: pop, delay_ms: 80}
```

最終HTMLは指定したpresetを同名の `data-anim` へ保持する。`fade` や `draw` を一律 `rise` に置換してはならない。`data-step`、`--motion-delay`、`--motion-duration`、`--motion-easing` を必要に応じて付け、ランタイムは明示stepを再採番しない。

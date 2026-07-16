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

## 選択の優先順位

presetをスライドID、ページ番号、奇数・偶数へ固定しない。次の順で選択する。

1. `role`: Demo、action、comparison、recapなど、ページが担う役割
2. `content_model.type`: comparison、flow、table、code、checklistなど、情報の形
3. `target`: connection、left-state、code-frame、validation、done、conclusionなど、動かす対象の意味
4. `phase_entry`: Why / What / How / Demo / Takeawayの境界か

`animation.selection` に適用したrule、role、content type、phase境界、選択理由を残す。各entrance/stepには `reason` を置く。同じstepの中で接続線と工程カードなど対象の役割が違う場合は、stepの代表presetに加えて `target_presets` と `target_reasons` を全target分置く。

| target | 基本preset | 理由 |
| --- | --- | --- |
| connection / harness-map | `draw` | 関係線を描いて構造を示す |
| left-state / right-state | `slide-left` / `slide-right` | 比較方向を保つ |
| code-frame / highlight-lines / validation | `wipe` / `marker` / `pop` | 全体、注目箇所、結果へ絞る |
| table row / checklist item | 先頭`wipe`または`rise`、後続`rise` | 行順・確認順を保つ |
| output / difference | `pop` | 結果へ短く焦点を移す |
| done / action conclusion | `stamp` / `stomp` | 完了・行動の確定に限定する |

`stamp`, `stomp`, `flip-in` は `sequence.completion_targets` 以外へ使わない。`draw` は線または関係図、左右slideは比較の左右だけに使う。互換性のない組合せを「種類を増やすため」に選ばない。

## ページ役割ごとの基本演出

- 定義: 見出しは `fade`、構成要素は `rise`、キーワードだけ `marker`。
- 比較: 左を `slide-left`、右を `slide-right`、差分または結論を `pop`。
- フロー: 入力を `fade`、接続線を `draw`、工程を順番に `rise`、判断ゲートを `stamp`。
- コード／設定: 全体を `wipe`、読む行を `marker`、実行結果を `pop`。文字単位の疑似タイプ演出はしない。
- Demo: 操作対象を `zoom-focus`、変化を `wipe`、観測結果を `pop`、完了を `stamp`。
- 章の切替: `blur-in` または左右方向の移動を一度だけ使い、本文ページより大きな呼吸を作る。
- Takeaway: 手順を `rise`、成果物を `zoom-focus`、完了条件を `stomp`。

## 読む順序の決定

順序は次の優先順位で決める。

1. 番号、因果、依存関係、操作手順、発表者が実際に説明する順序
2. 視覚配置と一致するDOM順序
3. 意味上の順序がない独立要素だけ、左上から右下へ進むZ型の空間順序

Z型は万能な読順ではない。番号付きの `01..07`、コードの上から下、表の行順、入力から出力への経路をZ型で並べ替えてはならない。矢印・背景線・枠は単独stepにせず、理解対象になる最初の要素と同じstepへまとめる。

初期状態ではタイトルと話の前提になるメッセージ・入力を読めるようにする。タイトルを動かす場合はstep 0、約220msの短い入場にする。対象群はstep 1以降、出力・完了条件・結論は対象群の後とし、結論を最後にする。

## デッキ全体のリズム

本編20枚以上では次を満たす。

- 5種類以上のpreset、4種類以上のfamilyを使う。
- 同じanimation signature（step数とpreset列）を3ページ連続させない。
- step数は役割に応じて1〜5を使い分け、少なくとも3種類のstep数を含める。全ページを同じstep数にしない。
- 一つのpresetが全指定の65%を超えない。
- `stamp`, `stomp`, `flip-in` の合計は全指定の20%以下とし、章の結論、警告、Demo結果へ予約する。
- 一ページの最大stepは通常6。番号付き工程、表の代表行、チェックリストなど、話者が一項目ずつ説明する明示順序列だけ最大9まで許可する。10以上になる場合は意味のまとまりへ統合する。
- delayは同一step内の関連要素だけ80〜180msずらせる。次のstepを自動再生しない。
- 連続する静かな説明の後、比較、フロー、Demo、結論でmotion familyを切り替えて呼吸を作る。

## Blueprint Contract

```yaml
animation:
  intent: "左の変更前と右の変更後を対で理解させ、最後に差分へ注目させる"
  family: direction
  selection:
    rule_id: content:comparison
    role: comparison
    content_type: comparison
    phase_entry: false
    rationale: "左右を異なる方向から入れ、同じ評価軸で差を読む"
  entrance:
    - {target: title, preset: fade, reason: "本文より先にタイトルを表示", delay_ms: 0, duration_ms: 220, easing: standard}
  steps:
    - {step: 1, targets: [left-state], preset: slide-left, reason: "比較の左側", target_presets: {left-state: slide-left}, target_reasons: {left-state: "左側から導入"}, delay_ms: 0}
    - {step: 2, targets: [right-state], preset: slide-right, reason: "比較の右側", target_presets: {right-state: slide-right}, target_reasons: {right-state: "右側から導入"}, delay_ms: 0}
    - {step: 3, targets: [difference], preset: pop, reason: "比較後の差分", target_presets: {difference: pop}, target_reasons: {difference: "差分へ焦点"}, delay_ms: 80}
  sequence:
    mode: staged # item-by-item, grouped, staged
    initial_targets: [title, message]
    ordered_targets: [before, after, difference, conclusion]
    completion_targets: [difference, conclusion]
    order_basis: comparison # semantic-number, dependency, row-order, narrative
    spatial_fallback: z-flow
    coverage: all-meaningful-siblings
    max_steps: 4
```

`sequence.ordered_targets` は、段階表示する意味要素を全件列挙する。同じ表、カード列、番号付き工程の一部だけを列挙してはいけない。常時表示する要素は `initial_targets` に明示する。

最終HTMLは指定したpresetを同名の `data-anim` へ保持する。`fade` や `draw` を一律 `rise` に置換してはならない。`data-step`、`--motion-delay`、`--motion-duration`、`--motion-easing` に加え、順序列の要素へ `data-reveal-item`, `data-reveal-group`, `data-reading-order`, `data-sequence-mode` を付ける。ランタイムは明示stepを再採番しない。

前進操作では表示済み要素を残し、理解を積み上げる。個別要素のfade-outや自動退場を標準演出にしない。前stepへ戻る操作では入口演出の逆遷移を許可し、ページ切替は共通の短いtransitionへ任せる。

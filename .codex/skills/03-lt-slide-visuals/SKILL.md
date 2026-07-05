---
name: 03-lt-slide-visuals
description: .lt-slide-work/02-blueprint.yaml から画像アセットを生成または準備し、.lt-slide-work/visuals 配下に保存する。あわせて .lt-slide-work/visuals-manifest.yaml も作成する。LTスライドのブループリントで、生成画像、透過図解、発表者画像、QRアセット、またはHTML実装前の画像準備が必要な場合に使用する。
---

# 03 LT Slide Visuals

`.lt-slide-work/02-blueprint.yaml` が要求した画像だけを生成または整形する。スライドHTMLは作らない。成果物は `.lt-slide-work/visuals/` と `.lt-slide-work/visuals-manifest.yaml`。

## Workspace Contract

すべての画像中間成果物をプロジェクトルート直下の `.lt-slide-work/` に置く。

```text
.lt-slide-work/
├─ 02-blueprint.yaml
├─ visuals-manifest.yaml
└─ visuals/
   ├─ visual-s03.png
   └─ ...
```

提供画像の加工版や生成画像を元画像の隣、プロジェクトルート、`output/` へ直接保存しない。最終工程だけが必要な画像を `output/assets/` へコピーする。

## Workflow

1. `.lt-slide-work/02-blueprint.yaml` の `visual_assets` を読む。
2. `required: true` の各資産について、生成、既存画像のコピー、または不要判定を行う。
3. 生成画像は利用可能な画像生成ツールを使う。ツールがなければ、正確な構造図はインラインSVGへ戻すよう設計図を修正し、偽の画像ファイルを作らない。
4. `references/visual-guidelines.md` に従い、指定された縦横比、背景、余白で生成する。
5. 出力画像を視覚確認し、文字化け、余計な文字、切れ、低コントラストを修正する。
6. `.lt-slide-work/visuals-manifest.yaml` を作る。

## Separation Of Responsibilities

- 画像は概念、雰囲気、関係性、象徴を担当する。
- HTMLはタイトル、本文、数値、ラベル、出典を担当する。
- 重要な文字を画像に焼き込まない。
- 矢印やラベルの正確さが必要なフロー、表、マトリクス、グラフは生成画像ではなくSVG/CSSを使う。
- 画像内の主役は中央寄りにし、端に重要要素を置かない。
- `visual_zone` のアスペクト比に合わせ、トリミング前提にしない。

## Presenter And QR Assets

- 発表者画像は顔や主役を中央に置き、必要なら正方形へクロップする。元画像を上書きしない。
- QRは再生成せず、提供画像をそのままコピーする。リサイズ時は最近傍補間を使い、余白を維持する。
- 出力名は設計図に従い、相対パスを使う。

## Prompt Construction

画像生成プロンプトには次を含める。

- subject: スライドの唯一のメッセージ
- composition: 左右、中央、流れなど
- style: modern Japanese business-tech editorial illustration
- palette: navy, green, blue, cyan, white
- constraints: no text, no letters, no logos, no watermark
- background: transparentまたは白
- safe area: 端から10%以上の余白

実在人物、商標、UIの正確な再現が不要なら抽象化する。

## Output Manifest

```yaml
schema_version: 1
source_blueprint: "./02-blueprint.yaml"
assets:
  - asset_id: visual-s03
    slide_id: s03
    file: "visuals/visual-s03.png"
    width: 1600
    height: 1000
    background: transparent
    alt: "変化を示す抽象図"
    status: ready
    notes: ""
```

`status` は `ready`, `provided`, `fallback-svg`, `blocked`。`blocked` のまま最終工程へ渡さない。正確な図へ切り替えられる場合は `fallback-svg` として設計図も更新する。

## Quality Gate

- 画像に不要な文字や透かしがない。
- 重要要素が端で切れていない。
- `visual_zone` と同じ比率である。
- 背景とスライドテーマのコントラストが適切である。
- altテキストが見た目ではなく意味を説明している。

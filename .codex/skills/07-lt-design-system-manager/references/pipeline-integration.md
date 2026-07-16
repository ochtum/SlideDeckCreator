# 01〜05工程との接続

Storyへ次を保存する。

```yaml
design_system:
  id: trustworthy-blue
  version: 1.0.0
  registry: ../config/design-systems/registry.yaml
```

シリーズではルートと各パートへ同じ参照を置く。回ごとに変える場合は、その意図をルートに明記する。

02工程はregistryからIDを引き、`design-system.yaml` のtokenを `theme`、layout、component、motionへ展開する。Blueprintへ `design_system` を変更せず引き継ぐ。色をその場で再解釈せず、token名と解決値を残す。

04工程は `.deck` または `body` へ `data-design-system-id` と `data-design-system-version` を付ける。CSS custom propertiesへtokenを解決し、PDFと発表者ビューでも同じ値を使う。デザインシステム未選択時だけ内蔵fallbackを使い、選択済みIDが見つからない場合は停止する。

05工程はStory、Blueprint、HTMLのID/version一致、registry内の存在、contrast、文字サイズ、reduced motionを確認する。見た目が似ていても別IDや別versionなら不合格にする。

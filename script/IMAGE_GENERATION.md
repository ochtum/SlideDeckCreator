# 画像生成セットアップ

## 1. APIキー設定

```bash
export OPENAI_API_KEY='YOUR_API_KEY'
```

Windows PowerShell の場合:

```powershell
$env:OPENAI_API_KEY = 'YOUR_API_KEY'
```

## 2. 画像生成実行

```bash
./script/generate_image.py "青空の下を走る白い電車、写実的、横長"
```

生成結果は標準で `image/generated-YYYYMMDD-HHMMSS.png` に保存されます。

## 主なオプション

```bash
./script/generate_image.py "prompt" \
  --size 1536x1024 \
  --quality high \
  --format webp \
  --output image/custom-name.webp
```

利用可能サイズ:
- `1024x1024`
- `1536x1024`
- `1024x1536`
- `auto`

利用可能フォーマット:
- `png`
- `jpeg`
- `webp`

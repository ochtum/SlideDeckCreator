# 動画生成セットアップ

## 1. APIキー設定

```bash
export OPENAI_API_KEY='YOUR_API_KEY'
```

Windows PowerShell の場合:

```powershell
$env:OPENAI_API_KEY = 'YOUR_API_KEY'
```

## 2. 動画生成実行（テキストから）

```bash
./script/generate_video.py "夕暮れの都市をドローンで俯瞰するシネマティック映像"
```

標準では `video/generated-YYYYMMDD-HHMMSS.mp4` に保存されます。

## 3. 画像参照つき生成

```bash
./script/generate_video.py "この構図を保ったままカメラをゆっくり前進させる" \
  --input-reference image/reference.png
```

## 主なオプション

```bash
./script/generate_video.py "prompt" \
  --model sora-2 \
  --size 1280x720 \
  --seconds 8 \
  --poll-interval 10 \
  --timeout 900 \
  --output video/custom.mp4
```

利用可能モデル:
- `sora-2`
- `sora-2-pro`

利用可能サイズ:
- `720x1280`
- `1280x720`
- `1024x1792`
- `1792x1024`

利用可能秒数:
- `4`
- `8`
- `12`

## 補足
- 動画生成は非同期ジョブです。スクリプトは `queued/in_progress` をポーリングし、完了後に自動ダウンロードします。
- アカウントの利用権限やクレジット不足時は API エラーになります。

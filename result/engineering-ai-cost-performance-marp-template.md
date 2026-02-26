---
marp: true
size: 16:9
paginate: true
style: |
  @import './engineering-ai-cost-performance-tailwind.css';
---
<!-- WUUNU SNIPPET - DON'T CHANGE THIS (START) -->
<script>window.__WUUNU_WS__ = "http://127.0.0.1:65406/?token=bb30da7515309c1f99c968d6210b9917f66907ac971ebb6a";</script>
<script id="wuunu-widget-script" data-wuunu-widget src="https://cdn.jsdelivr.net/npm/@wuunu/widget@0.1" defer crossOrigin="anonymous"></script>
<!-- WUUNU SNIPPET - DON'T CHANGE THIS (END) -->
<!-- _class: lead -->
# AI活用のコスパを最大化する技術

トークン制約時代における依頼設計・CLI運用・チーム資産化

<p class="muted">Designed for Engineering Teams & Tech Leads</p>

---

# コスパの定義を「単価」から「完了までの総コスト」へ

<p class="lead center"><span class="accent">Total Cost = ( Prep + Gen + Rework ) × Freq</span></p>

<div class="row-3">
  <div class="panel">
    <h3>Prep（準備）</h3>
    <p>要件整理の時間</p>
  </div>
  <div class="panel">
    <h3>Gen（生成）</h3>
    <p>AIの出力待ち時間</p>
  </div>
  <div class="panel panel-strong">
    <h3>Rework（手戻り）</h3>
    <p>最も削減すべき変数。曖昧な指示で指数的に増大。</p>
  </div>
</div>

---

# 回避すべき3つの失敗パターン

<div class="row-3">
  <div class="panel">
    <h3>× The One-Liner</h3>
    <p>「これ、いい感じに直して」</p>
    <p class="muted">優先順位が不明で出力がブレる</p>
  </div>
  <div class="panel">
    <h3>× No Constraints</h3>
    <p>文字数・形式・禁止事項が未定義</p>
    <p class="muted">追加プロンプトが増える</p>
  </div>
  <div class="panel">
    <h3>× Big Bang</h3>
    <p>調査〜実装まで一括丸投げ</p>
    <p class="muted">推論精度と再現性が低下</p>
  </div>
</div>

---

# 解決策: Markdownによる構造化プロンプト

<div class="panel">
  <p class="accent"># 目的</p>
  <p>- 何を達成したいか（ゴール）</p>
  <p class="accent"># 前提</p>
  <p>- 現在の状況 / 使用環境</p>
  <p class="accent"># 制約</p>
  <p>- 使ってよい技術 / 禁止事項 / 納期</p>
  <p class="accent"># 期待する出力</p>
  <p>- 形式（Markdown / JSON / Code）と完了条件</p>
</div>

---

# 複雑なタスクは「4フェーズ」に分割

<div class="row-4">
  <div class="panel center">
    <div class="num">1</div>
    <h3>調査</h3>
    <p>用語定義・前提確認</p>
  </div>
  <div class="panel center">
    <div class="num">2</div>
    <h3>設計</h3>
    <p>構成案と採用方針</p>
  </div>
  <div class="panel center">
    <div class="num">3</div>
    <h3>実装</h3>
    <p>設計準拠で出力</p>
  </div>
  <div class="panel center">
    <div class="num">4</div>
    <h3>レビュー</h3>
    <p>人間が最終判定</p>
  </div>
</div>

---

# GUIからCLIへ: プロフェッショナルのための環境移行

<div class="row-2">
  <div class="panel">
    <h3>GUI（Web / Chat）</h3>
    <p>Use Case: One-off questions</p>
    <p>Cons: 再現性が低い / 履歴追跡が弱い</p>
  </div>
  <div class="panel panel-strong">
    <h3>CLI（Terminal / API）</h3>
    <p>Use Case: Engineering Workflow</p>
    <p>Pros: Performance / Reproducibility / Efficiency</p>
  </div>
</div>

---

# セキュリティとガバナンスの絶対ルール

<div class="row-2">
  <div>
    <p><span class="num" style="font-size:56px;">01.</span> No Secrets</p>
    <p><span class="num" style="font-size:56px;">02.</span> Masking</p>
  </div>
  <div>
    <p><span class="num" style="font-size:56px;">03.</span> Log Awareness</p>
    <p><span class="num" style="font-size:56px;">04.</span> Guidelines</p>
  </div>
</div>

<p class="muted">個人情報・顧客データ・APIキーは入力しない。禁止事項をチーム合意する。</p>

---

# まず着手すべき「最小セット」

<div class="row-3">
  <div class="panel">
    <div class="num">1.</div>
    <h3>Template</h3>
    <p>よくある依頼のMarkdown雛形を1枚作る</p>
  </div>
  <div class="panel">
    <div class="num">2.</div>
    <h3>Split</h3>
    <p>複雑タスクを調査・設計・実装に分割</p>
  </div>
  <div class="panel">
    <div class="num">3.</div>
    <h3>CLI History</h3>
    <p>履歴が資産になる運用を体験する</p>
  </div>
</div>

---

# ツール選びより「運用設計」が成果を決める

<div class="row-3">
  <div class="kpi">
    <h3>Interaction Turns</h3>
    <p>やり取り回数</p>
  </div>
  <div class="kpi">
    <h3>Time per Task</h3>
    <p>所要時間</p>
  </div>
  <div class="kpi">
    <h3>Kickback Count</h3>
    <p>差し戻し数</p>
  </div>
</div>

<p class="lead center">依頼を設計し、運用を自動化し、知見を資産化することでコスパは最大化される。</p>

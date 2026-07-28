---
type: task
status: "2_doing"
priority: 1_high
due: 2026-08-10
context: "[[A社ネットワーク運用]]"
tags:
  - 経理
goal: 制御文字混入バグを模したサンプル
---

旧データにあった status 末尾の実際のCR(\r)制御文字が残っているケース。パーサが `.strip()` 等で耐性を持てるかの確認用。

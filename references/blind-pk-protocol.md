# 盲选 PK 协议（blind PK protocol）

> 先例：yue2 两日盲审（yue2_generalize_blind.html，20/20 槽，勾稽 43=43，全 20 槽 md5 图谱
> yue2_generalize_key.json）。核心纪律：**揭底前零泄露**。

## 1. 盲选页面格式（kais-html 标准，严格照 yue2_generalize_blind.html 范本）

- **视觉**：GitHub-dark 配色（#0d1117/#161b22/#30363d）+ PingFang SC，粘性头部
  （h1 标题 + sub 条件说明：同参/档位/日期）。
- **结构**：判读指引框（蓝左边框，含判读轴与评级说明）→ 每题一张卡（题干 + brief +
  quad 网格，≤700px 单列）→ 每轨优/良/中/差四档 + ★最佳（可撤销可重标）+ 每题意见输入 →
  对照锚题（金虚线框，判「异」= 本轮判读作废）→ 🔓 揭晓臂位 → 底部固定导出栏。
- **交互**：localStorage 续答（刷新不丢票）；导出栏一键复制摘要回传 chat，格式：
  `2题盲选PK P1: 轨1优 轨2差 ★轨1 | P2: ... | CTL=同`（揭底后回传带「揭底已看」尾标）。
- **揭底**：臂位映射以 char-code（String.fromCharCode）藏在页内 REV 变量，直接看 HTML
  源码不剧透；揭晓状态不跨刷新持久。全槽 md5 图谱入 key.json（0600，揭底前保密）。

以上全部由 `scripts/blind_pack.py` 自动生成，**不要手写偏离此格式的页面**。

## 2. 设计

- **对手数**：**1 个**——同模态最强现役引擎（现任冠军，选法见 kap-engine-registry.md）。
- **题目集**：每模态 4-6 题跨风格轴（音乐例：英文流行 / 中文 ballad / synthwave / 中国风电子 /
  史诗管弦 / lo-fi）。图像例：人像 / 风景 / 产品 / 文字排版 / 风格化。
- **槽位制**：`scripts/blind_pack.py` 按题打包（`p{题号}_{轨位}{ext}`），臂位每题独立乱序
  （确定性种子）防位置偏差，md5 入 key.json（0600）。
- **同题同参**：文本输入严格同串；图/视频输入同一源文件；seed 用各方等价默认；步数/分辨率
  用各方开箱默认档——测「开箱即用」，不做档位调优。
- **每题每引擎 n≥1**；判「明显优劣」前每格至少 3 seeds（n=1 时方差淹没档位效应，yue2 实证）。

## 3. 投票与揭底

1. 盲审页本地 HTTP server 发出（端口 8090 起，`http://<局域网IP>:8090/blind/ballot.html`，
   局域网 IP 用 `hostname -I` 取）。
2. Kai 逐轨评级 + 标★，评完点「📋 复制发回群里」把摘要贴回 chat。
3. 收齐票 → 对照 key.json 揭底（或 Kai 点页面 🔓 按钮自行揭底）→ 写 verdict.json，
   **附 Kai 回传的原始摘要文本**。

## 4. verdict.json schema

```json
{
  "date": "2026-10-23",
  "model": "<新模型名>",
  "opponents": ["yue2"],
  "default_preset": {"precision": "int8", "steps": 32},
  "vram": {"idle_mib": 432, "peak_mib": 4816, "resident_mib": 4204},
  "timing": {"gen_seconds": 14.2, "notes": "45s 曲 10-19s"},
  "ballot": {"slots": 20, "votes": 20, "ballot_html": "...", "key_json": "...",
             "kai_summary_raw": "2题盲选PK P1: 轨1优 轨2差 ★轨1 | ..."},
  "wins_by_prompt": {"P1": "轨1(newmodel)", "P2": "轨2(yue2)"},
  "verdict": "adopt | backup | reject",
  "default_tier": "int8-32",
  "backup_tier": "bf16-50",
  "caveats": ["每风格 n=1 seed, 方差淹没档位效应", "CC-BY-NC 非商用"],
  "qa_gates": {"asr_vocal_presence": "25% 无效人声 → 生产需换 seed 重渲门"},
  "integration_next": "工单草稿路径（收录时）"
}
```

归档：`/home/kai/shared/<日期>/<model>_verdict.json` + memory 当日记录 +
kap-engine-registry.md §probe 台账追加一行。

## 5. 结论判定

| 结论 | 条件 |
|------|------|
| adopt 收录 | 盲选不输现任冠军 + 稳定性验收过 + license 可接受 → 定双层档 + 出收编工单草稿 |
| backup 备档 | 质量可圈但整体不优或有风格轴硬伤 → 留权重与工作流，注明适用场景 |
| reject 弃用 | 稳定性不过 / 质量 / 显存不可行 / license 不可接受 → 记录原因，删探针容器 |

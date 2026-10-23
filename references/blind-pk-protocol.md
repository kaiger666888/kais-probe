# 盲选 PK 协议（blind PK protocol）

> 先例：yue2 两日盲审（yue2_generalize_blind.html，20/20 槽，勾稽 43=43，全 20 槽 md5 图谱
> yue2_generalize_key.json）。核心纪律：**揭底前零泄露**。

## 1. 设计

- **对手数**：**1 个**——同模态最强现役引擎（现任冠军，选法见 kap-engine-registry.md）。
- **题目集**：每模态 4-6 题跨风格轴（音乐例：英文流行 / 中文 ballad / synthwave / 中国风电子 /
  史诗管弦 / lo-fi）。图像例：人像 / 风景 / 产品 / 文字排版 / 风格化。
- **槽位制**：`scripts/blind_pack.py` 把各引擎产物匿名化为 slot_A/B/C，md5 入 key.json（0600）。
- **同题同参**：文本输入严格同串；图/视频输入同一源文件；seed 用各方等价默认；步数/分辨率
  用各方开箱默认档——测「开箱即用」，不做档位调优。
- **每题每引擎 n≥1**；判「明显优劣」前每格至少 3 seeds（n=1 时方差淹没档位效应，yue2 实证）。

## 2. 投票

- 盲审页本地起 HTTP server（端口 8090 起，`http://<局域网IP>:8090/blind/ballot.html`，
  局域网 IP 用 `hostname -I` 取）。
- Kai 在 chat 按题投票：`P1: A`，可加优票制（每题选优 + 可并列）。
- 票收齐 → 对照 key.json 揭底 → 生成 verdict.json。

## 3. verdict.json schema

```json
{
  "date": "2026-10-23",
  "model": "<新模型名>",
  "opponents": ["yue2"],
  "default_preset": {"precision": "int8", "steps": 32},
  "vram": {"idle_mib": 432, "peak_mib": 4816, "resident_mib": 4204},
  "timing": {"gen_seconds": 14.2, "notes": "45s 曲 10-19s"},
  "ballot": {"slots": 20, "votes": 20, "ballot_html": "...", "key_json": "..."},
  "wins_by_prompt": {"P1": "A(yue2)", "P2": "B(newmodel)"},
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

## 4. 结论判定

| 结论 | 条件 |
|------|------|
| adopt 收录 | 盲选不输现役默认引擎 + 稳定性验收过 + license 可接受 → 定双层档 + 出收编工单草稿 |
| backup 备档 | 质量可圈但整体不优或有风格轴硬伤 → 留权重与工作流，注明适用场景 |
| reject 弃用 | 稳定性不过 / 质量 / 显存不可行 / license 不可接受 → 记录原因，删探针容器 |

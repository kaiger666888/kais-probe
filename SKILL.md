---
name: kais-probe
description: "新模型探测与落地 skill：收到新模型信息（权重/repo/论文/发布）后自动深入调研、按本机三卡硬件制定最佳落地方案、跑通 demo，并与 kais-aigc-platform(kap) 现役引擎做盲选 PK 定谳。触发场景：当用户提到或使用以下触发词时使用本 skill——"kais-probe""probe""probe这个模型""新模型上手""新模型demo""上新模型""试新模型""模型探测""模型调研""新模型落地""新模型评估""盲选PK""盲测""盲测对比""盲审投票""引擎对比""接新模型""probe new model""onboard new model""evaluate new model"。适用模态：图像/视频/音乐/TTS/3D/LLM 任意生成类模型。"
---

# Kais Probe — 新模型探测 → 落地 → 盲选 PK

## 概述

把「试一个新模型」从随意动作变成标准管线。范本来源：yue2 音乐模型（2026-09）完整走通的
「探针容器 → 显存实测 → 固定工作流 → 盲审 HTML → 定谳默认档 → 收编 kap」全流程。

五个阶段：**Intake → 调研 → 落地方案 → Demo → 盲选 PK → 定谳归档**。
每个阶段结束向 Kai 发一条简报（Telegram 即时汇报规则），阶段产物落盘到 probe 工作目录。

## 硬事实（先读这个）

- 本机三卡（2026-10-23 实测）：GPU0=RTX 3060 Ti 8GB（桌面显示卡，有 ~2GB 桌面地板）；
  GPU1=RTX 3090 24GB；GPU2=RTX 3090 24GB。probe 作业默认上 GPU1/GPU2，**GPU0 默认不动**。
- kap 仓库：`/home/kai/workspace/kais-aigc-platform`；模型库 `/data/models/comfyui/`；
  共享输出 `/mnt/agents/output/gpu{1,2}/`；盲审定谳台账惯例 `/home/kai/shared/<日期>/`。
- 下载：aria2c 优先；HuggingFace 先试 `hf-mirror.com`，GitHub 大文件走 `ghfast.top` 等镜像。
- 详细硬件档案与容器配方见 [references/hardware-profile.md](references/hardware-profile.md)。

## Pipeline 阶段

### 阶段 0：Intake（信息 intake + 去重）

<!-- FREEDOM:high -->
1. 从 Kai 消息中提取：模型名、repo/权重链接、论文、模态、版本。缺什么用 web_search 补齐，
   不反复追问。
2. **去重检查**（3 处）：①`memory/` 搜历史 probe 记录 ②`/data/models/` 下是否已有权重
   ③kap 现役引擎表（见 kap-engine-registry.md）是否已收录同模型。已 probe 过 → 汇报旧结论，
   问是否重测。
3. 建 probe 工作目录：`/home/kai/shared/probes/<model>-<yyyymmdd>/`，后续所有产物进这里。
4. 发简报：模型事实卡（参数量/模态/license/运行时支持/预估显存）。
<!-- /FREEDOM:high -->

### 阶段 1：深入调研

<!-- FREEDOM:high -->
产出 `research.md`，必含 6 项：
1. **官方源**：repo、权重下载直链（含各量化档）、论文/发布博客。
2. **License 门**（⚠️ 红线）：权重许可是否允许本地使用/商用。CC-BY-NC 类（如 yue2）必须
   显式标注「非商用」，收编 kap 时 license 字段要透传。
3. **运行时形态**：ComfyUI 原生节点 / ComfyUI 自定义节点 / diffusers / 独立 server / 仅推理代码。
   优先级：ComfyUI 原生 > diffusers > 独立 server（复用现有容器生态）。
4. **量化生态**：fp16/bf16、fp8、int8、gguf(q8/q6/q4) 各档是否可得 + 社区质量反馈。
5. **实测需求**：官方显存声明 + 社区实测（GitHub issues / Reddit），标注 24GB 卡可行性。
6. **已知坑**：OOM 报告、节点兼容、版本依赖冲突。
<!-- /FREEDOM:high -->

### 阶段 2：落地方案（本机硬件 fit）

1. 运行 `scripts/hw_audit.sh` 拿三卡实时状态。
2. 产出 `plan.md` 决策表，决策规则：

| 情形 | 决策 |
|------|------|
| 权重(fp16) ≤ 20GB | 3090 直载 fp16/bf16，无需量化 |
| 权重 20-28GB | 首选 fp8/int8 档（yue2 先例：int8 4.8GB 峰值 vs bf16 9.8GB）|
| 权重 > 28GB | gguf q8/q6 逐档试，或 CPU offload 分段 |
| ≤ 6GB 轻量模型 | 可考虑 GPU0，但须扣桌面地板 ~2GB（详见 hardware-profile）|

3. **运行时形态决策**：ComfyUI 模型 → 新建探针容器 `comfyui-<model>-probe`（配方见
   hardware-profile.md §容器配方；命名/端口/GPU 钉死/restart=no 照 yue2-probe 惯例）。
   diffusers 模型 → `/data/venvs/` 下建独立 venv。
4. **冲突预检**：查 kap 常驻大引擎（music3 22.5GB 满卡、kais_ear 21.5GB、minimax_h3 18GB）
   当前是否在跑，避开同卡。
5. 发简报给 Kai：方案一页纸。**两个确认卡点**（<-- FREEDOM:low）：①下载总量 >20GB 先确认
   ②要在被占用 GPU 上跑先确认。确认后开始下载（aria2c + 镜像）。

### 阶段 3：Demo 跑通

<!-- FREEDOM:medium -->
1. 搭 smoke 工作流/脚本（ComfyUI：固定节点图 JSON，参照 yue2 6 节点最小图）。
2. **连续稳定性验收**：同一工作流连跑 3 次（yue2 标准 16 次）全 success 才算通过。
3. 跑 golden prompts（按模态选，见 blind-pk-protocol.md §题目集），3 seeds。
4. 全程 `scripts/measure_vram.sh <gpu> <秒> <csv>` 采样，记录：峰值显存（分精度档）、
   首 token/出图耗时、产物路径。
5. OOM 处理梯子：降步数 → 降分辨率/时长 → 降精度档 → CPU offload。每步记录。
6. 产物落 probe 工作目录；发简报：demo 产物 + 指标表。
<!-- /FREEDOM:medium -->

### 阶段 4：盲选 PK（对 kap 现役引擎）

<!-- FREEDOM:low -->
1. 从 [references/kap-engine-registry.md](references/kap-engine-registry.md) 选 **1 个**同模态最强的现役引擎做对手
   （最强 = kap 生产链默认引擎；无默认则选历史盲审/公认质量最强者，如新音乐模型 → yue2）。
   不必多引擎都 PK，目标是「打赢现任」不是全面评测。
2. **同题同参**：文本输入严格同串；图/视频输入用同一源文件；seed 各引擎取等价默认档。
   新模型用 demo 定下的默认档，不用调到最优档（测的是「开箱即用」）。
3. 运行 `scripts/blind_pack.py` 生成盲审页。页面格式**严格按 kais-html 标准**（yue2_generalize_blind.html 范本：GitHub-dark 配色/粘性头/判读指引/优 良 中 差+★最佳/对照锚题/底部导出栏/char-code 臂位揭晓）：

```bash
python3 scripts/blind_pack.py --out <blind目录> \
  --title "盲选 PK · <model> vs <现任冠军>" --sub "同题同参 · 开箱默认档 · <日期>" \
  --media audio|video|image \
  --axes "判读轴：<按模态写>" \
  --arms "<model>" --arms "<现任冠军>" \
  --q "P1 题说明::<model产物>::<冠军产物>" \
  --q "P2 题说明::<model产物>::<冠军产物>" \
  [--ctl "锚A::锚B"]
```

臂位每题独立乱序（确定性种子）防位置偏差；key.json（md5 图谱，0600）在投票结束前不给 Kai 看；
页面自带 🔓 揭晓臂位按钮，投票结束后 Kai 可自行揭底。
4. 本地 HTTP server 发盲审页（端口 8090 起，`http://<局域网IP>:8090/blind/ballot.html`），
   Kai 逐轨评级 + 标★，评完点「📋 复制发回群里」把摘要贴回 chat（格式如
   `2题盲选PK P1: 轨1优 轨2差 ★轨1 | P2: ... | CTL=同`）。
5. 收齐票 → 对照 key.json 揭底，写 `verdict.json`（schema 见 blind-pk-protocol.md），
   落 `/home/kai/shared/<日期>/`。
<!-- /FREEDOM:low -->

### 阶段 5：定谳与归档

1. 三种结论：**收录**（定默认档+备档双层，报实测档位表）/ **备档**（质量可但不收编）/ **弃用**。
2. 样本量 caveat 必须写进结论：每风格 n=1 seed 的票向会被方差淹没（yue2 教训：
   「步数 50 起效」隔日翻转）；要翻默认档需每风格 ≥3 seeds 扩样。
3. 归档：`memory/YYYY-MM-DD.md` 记录 + probe 工作目录留 research.md/plan.md/verdict.json +
   在 kap-engine-registry.md §probe 台账追加一行。
4. 若结论为收录：产出收编工单草稿（对照 engine-integration-spec M1-M9 清单），
   **但正式收编是 kap 代码变更，需 Kai 明确发令（老司机）走 Claude Code，本 skill 不代做**。

## 脚本说明

| 脚本 | 用法 | 说明 |
|------|------|------|
| `scripts/hw_audit.sh` | `hw_audit.sh` | 三卡显存/占用/进程快照 |
| `scripts/measure_vram.sh` | `measure_vram.sh <gpu_idx> <duration_s> <out.csv>` | 生成期间显存采样 |
| `scripts/blind_pack.py` | `blind_pack.py --out DIR --entry "name:path" ...` | 盲选打包+投票页 |

## 注意事项

- License 是一票否决项：非商用权重收编 kap 必须带 license 字段透传（yue2 先例）。
- 盲选 PK 的核心纪律：**揭底前不泄露槽位对应关系**，包括 prompt 顺序、文件名、时间戳。
- 探针容器一律 `restart=no`，probe 结束提醒 Kai 是否保留（保留作常驻引擎 / 销毁）。
- 全程遵守即时汇报：每阶段一条简报，不等 Kai 问。

# 硬件档案与容器配方（kais-probe）

> 快照日期 2026-10-23，运行时以 `scripts/hw_audit.sh` 实测为准。

## 三卡拓扑

| GPU | 型号 | 显存 | 角色 | 约束 |
|-----|------|------|------|------|
| 0 | RTX 3060 Ti | 8GB | 桌面显示卡（Wayland 三屏含 4K） | 桌面常驻 ~1.9GB，GUI 峰值 3.0-3.4GB；作业预检上限 ≈6.4GB（地板逻辑见下） |
| 1 | RTX 3090 | 24GB | 主力计算卡（probe 默认） | 留意 kap 常驻引擎占用 |
| 2 | RTX 3090 | 24GB | 第二计算卡 | 输出目录惯例 /mnt/agents/output/gpu2 |

桌面地板逻辑（kap `src/lib/gpuVramManager.ts` B2a）：GPU0 放行条件 = free ≥ required + floor，
floor 只对 GPU0 生效。probe 除非模型 ≤6GB 且 Kai 同意，否则不上 GPU0。

## kap 常驻引擎显存账本（排卡前必查）

来源 `ENGINE_VRAM_REQUIREMENTS`（kap gpuVramManager.ts，实测值）：

| 引擎 | 需求 MiB | 备注 |
|------|---------|------|
| music3 | 22528 | 3090 满卡，结构性互斥 |
| kais_ear | 22016 | Qwen3-Omni Q4，3090 近独占 |
| minimax_h3 | 18432 | int8 动态分段驻留 |
| qwen_eye | 14336 | |
| flux2 | 12288 | fp8mixed + TE |
| yue2 | 9856 | 探针 lazy-load，idle 432MiB，int8 峰值 4816 / bf16 峰值 9808 |
| trellis2 / postprocess / ace / sa3 / qwen_tts / breeze_tts | 8192 | |
| rtx_vsr | 4096 | 轻量但同卡互斥 |

## 容器配方（ComfyUI 探针，yue2-probe 先例）

```
名称:     comfyui-<model>-probe
镜像:     yanwk/comfyui-boot 系（按 CUDA/PyTorch 需求选 tag；yue2 用 cu130-megapak-pt211-yue2pin）
端口:     8195 起递增（8195→8188 容器内 ComfyUI）
GPU:      --gpus '"device=GPU-<uuid>"' 钉死到选定的 3090
restart:  no   ← 一律 no，probe 结束人工决定去留
挂载:     /data/workspace/<容器名>:/root/ComfyUI
          /data/models/comfyui:/root/ComfyUI/models:rw
          /mnt/agents/output/gpuN:/mnt/agents/output/gpuN:rw
```

要点（历史教训）：
- bind mount 别加 `:ro`——entrypoint 的 chmod/cp 会失败导致重启循环。
- 容器内模型 symlink 必须指向容器内路径，不能指宿主机路径。
- 产物统一落 `/mnt/agents/output/gpuN/`，宿主机直读。

## 非 ComfyUI 形态

- diffusers/独立 server：`/data/venvs/<model>/` 建独立 venv；大权重放 `/data/models/<model>/`。
- 训练类（LoRA 等）：参照 FLUX 先例 `/data/venvs/flux-lora-train/` + sd-scripts。

## 下载规范

1. aria2c 优先（多线程），降级 wget → curl。
2. HuggingFace 先换镜像 `hf-mirror.com`；GitHub 大文件走 `ghfast.top` / `gh-proxy.com`。
3. 单次下载 >20GB 必须先向 Kai 确认（SKILL.md 阶段2 确认卡点）。

## 关键路径

| 路径 | 用途 |
|------|------|
| `/home/kai/workspace/kais-aigc-platform` | kap 仓库 |
| `/data/models/comfyui/` | ComfyUI 模型库（容器 rw 挂载） |
| `/mnt/agents/output/gpu{1,2}/` | 共享产物输出 |
| `/home/kai/shared/probes/<model>-<yyyymmdd>/` | probe 工作目录（本 skill 惯例） |
| `/home/kai/shared/<日期>/` | 盲审定谳台账（yue2 先例：yue2_gen_verdict.json） |
| `/data/venvs/` | Python 独立环境 |

# Probe 操作手册（yue2 范本细节）

> 范本：YuE2 音乐模型 2026-09-14/15 probe + 收编（docs/yue2-engine-integration.md）。

## 1. 显存实测三值法

任何「预估显存」都要用实测三值替代（nvidia-smi per-process 采样，`scripts/measure_vram.sh`）：

| 值 | 含义 | yue2 实测例 |
|----|------|------------|
| idle | 容器起、权重未载 | 432 MiB |
| 生成峰值 | 典型作业全程最大 | int8 4816 / bf16 9808 MiB |
| 驻留 | 生成完权重未卸 | int8 4204 / bf16 7696 MiB |

- 分精度档各测一轮（int8 / bf16 / 各量化档），这是「默认档 vs 备档」双层数据的来源。
- 收编登记用的是**峰值同源值**，最坏情形向上取 128 倍数（kap 惯例）。
- 「驻留 free 仍 ≫ 峰值」才可判定无 music3 式结构性死锁。

## 2. 工作流固定与稳定性验收

- ComfyUI：手写固定节点图 JSON（yue2 例：Checkpoint → 生成 → 空音频 latent → KSampler →
  VAE Decode → Save 共 6 节点），不用自动转换器（节点参数名映射不完美，2026-06 LTX 教训）。
- 连跑验收：同一工作流连续 N 次全 success（yue2 标准 16 次；新模型最小 3 次）才算 probe 通过。
- checkpoint 用 ComfyUI `object_info` COMBO 实读域，不在代码里硬编码模型清单。
- 非官方暴露的同目录其他模型**有意不暴露**（yue2 探针里 sam3.1/stable_audio_3 不进 COMBO）。

## 3. 双层档位策略

probe 定谳通常产出两层：
- **默认档**：最稳+最快（yue2: int8-32，两日盲审 11/12 登顶）。
- **备档**：质量上限档，公开参数可切（yue2: bf16-50，唯一全题无差）。

单样本票向不作普适规律（「步数 50 起效」隔日翻转）；翻默认档需每风格 ≥3 seeds 扩样。

## 4. 模态专属 QA 门（收编前）

- 音乐/歌声：**ASR 人声存在性门**——yue2 盲审发现 ~25% 轨无有效人声（seed/style 抽签风险，
  引擎×风格条件性），生产必须自动检测+换 seed 重渲。
- 图像/视频：逐张人眼检查畸变/文字伪影；视频另查帧间闪烁。
- 3D：Blender/Three.js 双端打开验证（TRELLIS 先例：GLB 需删自带 Cube、OPAQUE、PBR 通道分离）。
- 风格轴覆盖：每模态列 4-6 个风格轴（如音乐：英文流行/中文 ballad/synthwave/中国风电子），
  已知某引擎在某轴全灭时记录「互补回退」可能性。

## 5. ComfyUI 容器坑速查

- `:ro` mount → entrypoint chmod 失败 → 重启循环（用 rw）。
- symlink 指宿主路径 → 容器重启被 rsync 覆盖（容器内路径闭环）。
- 3090 满卡作业（music3 类）与其他 GPU 进程结构性互斥，probe 前先查常驻占用。
- ComfyUI API 工作流输出目录用 `--output-directory /mnt/agents/output/gpuN` 落共享存储。

## 6. 汇报节奏

每阶段一条简报（Telegram）：Intake 事实卡 / 调研 6 项 / 方案一页纸（含 2 确认卡点）/
demo 指标表 / 盲审投票请求 / 定谳三选一。不等 Kai 问，产出到手即报。

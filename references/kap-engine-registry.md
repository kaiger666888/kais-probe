# kap 引擎名册（盲选 PK 对手池 + 收编门禁）

> kap = kais-aigc-platform，仓库 `/home/kai/workspace/kais-aigc-platform`。
> 现役引擎以 `src/lib/gpuVramManager.ts` 注册表 + `docs/engine-admission.md` 挂载表为准，
> 本文件是 probe 视角的速查表，收录状态有疑义时以代码为准。

## 模态 → 引擎映射

| 模态 | 现役引擎（盲选对手候选） | 入口形状 |
|------|------------------------|---------|
| 文生图/图像 | flux1（sceneGenerate/storyboard）、flux2、qwen21（/generate /edit）、qwen_edit、flux_kontext | REST + multipart |
| 音乐 | yue2（ComfyUI 探针 :8195）、music3、ace、sa3 | REST |
| TTS | qwen_tts、breeze_tts（indextts2 键保留已退役） | REST |
| 视频 | minimax_h3（/generate 及 i2va/t2va 面）、ltx（已退役收编防撞卡） | REST |
| 3D | trellis2、hunyuan3d | REST + multipart |
| 超分/后处理 | seedvr2、rtx_vsr | REST |
| 多模态理解 | qwen_eye（视觉）、kais_ear（听觉/omni） | 常驻 server |

选对手规则：同模态**只留 1 个最强对手**——首选 kap 生产链默认引擎（KMC 链在用的那个），
无默认时选历史盲审胜率/公认质量最强者（音乐现役冠军 = yue2，int8-32 定谳收录）。
盲选目的是「打赢现任」不是全面评测。

## 盲选调用要点

- kap 全 API 响应包装 `{code, data, message}`；产物经 `/oss` 取
  （如 `GET /oss/gpu2/audio/<file>.flac`）。
- yue2 调用节奏：`POST /api/production/yue2/generate` → 轮询 `status/:promptId`（3-5s）
  → `status/:promptId/audio` 拿 url。
- 各引擎默认参数即「开箱档」，PK 时不要给任何一方开优化挂（yue2 定谳教训：int8-32 默认档
  最稳最快，档位调优是收编后的事）。
- 常驻引擎若没起，先起服务再排产；探针不可达时 kap 返回 502 `unreachable`。

## 收编门禁（收录后走 kap 正式变更，本 skill 只交工单草稿）

`docs/engine-integration-spec.md`（M1-M9 强制）：
- M1 `gpuVramManager.ts` 两处登记：`ENGINE_VRAM_REQUIREMENTS`（实测峰值 MiB）+ `ENGINE_GPU_INDEX`。
- M2 全部「提交+等待」过 `withGpuQueue` / `withGpuQueueTimed`（排队等待计入 queueWaitMs）。
- M3 显存预检（comfyuiUrl 可驱逐 / 常驻引擎 requireVramMiB + registerResidentEngine）。
- M4 客户端断连取消（AbortController 挂 res，不是 req）。
- M5 错误映射四态：503 vram_insufficient / 504 queue_timeout / 499 queue_aborted / 503 queue_purged。
- M6 multipart 解析/下载等锁外前置；M7 常驻引擎 acquireEngineOccupancy 配对 /release。
- M8 队列行为单测；M9 长任务 poll 预算含 queueWaitMs 补偿。
- 验收门禁：`npm run verify:engine-integration` EXIT 0，新引擎 PR 必须附绿色输出。

`docs/engine-admission.md`：引擎路由挂统一准入门 `engineAdmission("<engine_key>")`
（路由文件内、multer 之后），结构硬约束 400 + fix_hint，内容问题 warn。

## probe 台账（追加式）

| 日期 | 模型 | 结论 | 档位/显存 | 台账 |
|------|------|------|-----------|------|
| 2026-09-14/15 | yue2（音乐 3B） | 收录为 kap 引擎；默认 int8-32，bf16 备档；CC-BY-NC 非商用 | int8 峰值 4816MiB / bf16 9808MiB | /home/kai/shared/2026-09-14/yue2_gen_verdict.json |

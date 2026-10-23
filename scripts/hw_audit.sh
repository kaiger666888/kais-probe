#!/usr/bin/env bash
# hw_audit.sh — kais-probe 阶段2 硬件快照：三卡显存/利用率 + 计算进程 TOP
set -euo pipefail

echo "=== GPU 概览 ($(date '+%F %T')) ==="
nvidia-smi --query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu --format=csv

echo
echo "=== 计算进程（按显存降序）==="
nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv | \
  awk -F', ' 'NR>1 {print}' | sort -t',' -k4 -rn | head -15 || true
# 把 UUID 换成卡号方便阅读
echo
echo "=== GPU UUID → index 映射 ==="
nvidia-smi --query-gpu=index,uuid --format=csv,noheader

echo
echo "=== 桌面地板提醒 ==="
echo "GPU0 (3060Ti 8GB) 是桌面显示卡: Wayland/Chrome 常驻 ~1.9GB, GUI 峰值 ~3.4GB."
echo "GPU0 上排作业必须给桌面留 floor(~2GB), 作业预检上限 ≈6.4GB. probe 默认不上 GPU0."
echo "GPU1/GPU2 (3090 24GB) 为 probe 主力卡; 排卡前对照 kap 常驻引擎占用"
echo "(music3≈22.5GB 满卡 / kais_ear≈21.5GB / minimax_h3≈18GB / yue2 探针驻留 4-8GB)."

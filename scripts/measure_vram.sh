#!/usr/bin/env bash
# measure_vram.sh — kais-probe 阶段3 生成期间显存采样
# 用法: measure_vram.sh <gpu_index> <duration_seconds> <output.csv>
#   例: measure_vram.sh 1 300 ./vram_peak.csv
# 输出 CSV: timestamp,gpu_index,used_mib,free_mib ; 结束时 stdout 报峰值
set -euo pipefail

GPU_IDX="${1:?用法: measure_vram.sh <gpu_index> <duration_seconds> <output.csv>}"
DURATION="${2:?缺少 duration_seconds}"
OUT="${3:?缺少 output.csv}"

echo "timestamp,gpu_index,used_mib,free_mib" > "$OUT"
END=$(( $(date +%s) + DURATION ))
PEAK=0
while [ "$(date +%s)" -lt "$END" ]; do
  READ=$(nvidia-smi -i "$GPU_IDX" --query-gpu=memory.used,memory.free --format=csv,noheader,nounits 2>/dev/null) || break
  TS=$(date '+%F %T')
  echo "$TS,$GPU_IDX,$READ" >> "$OUT"
  USED=$(echo "$READ" | cut -d, -f1 | tr -d ' ')
  [ "$USED" -gt "$PEAK" ] && PEAK=$USED
  sleep 2
done
echo "采样完成: ${OUT}  |  GPU${GPU_IDX} 峰值显存: ${PEAK} MiB"

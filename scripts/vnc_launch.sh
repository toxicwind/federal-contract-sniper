#!/bin/bash
# Federal Contract Sniper — VNC Launch Wrapper
# Runs the full pipeline detached from VNC terminal

PROFILE="data/profiles/default.json"
SAM_CACHE="data/cache/sam_library_july2026.json"
ICF_AWARDS="data/cache/icf_awards.json"
ICF_ACTIVE="data/cache/icf_active.json"
OUT_DIR="outputs/run"
LOG="$OUT_DIR/vnc_pipeline_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$OUT_DIR"

echo "[VNC-LAUNCH] Starting autonomous federal pipeline"
echo "[VNC-LAUNCH] Log: $LOG"

(
    cd "$(dirname "$0")/.."
    exec nohup python -m federal_sniper.cli run         --profile "$PROFILE"         --sam-cache "$SAM_CACHE"         --icf-awards "$ICF_AWARDS"         --icf-active "$ICF_ACTIVE"         --out "$OUT_DIR" > "$LOG" 2>&1 &
    PID=$!
    echo "$PID" > "$OUT_DIR/.pid_pipeline"
    echo "[VNC-LAUNCH] Detached PID: $PID"
    disown $PID 2>/dev/null || true
)

sleep 2
PID=$(cat "$OUT_DIR/.pid_pipeline" 2>/dev/null)
if kill -0 "$PID" 2>/dev/null; then
    echo "[VNC-LAUNCH] SUCCESS: PID $PID running detached"
else
    echo "[VNC-LAUNCH] WARNING: PID exited quickly (check $LOG)"
fi

echo "[VNC-LAUNCH] To monitor: tail -f $LOG"
echo "[VNC-LAUNCH] To kill: kill $(cat $OUT_DIR/.pid_pipeline 2>/dev/null)"

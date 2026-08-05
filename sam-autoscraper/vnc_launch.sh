#!/bin/bash
# VNC Launch Wrapper - runs sniper detached from VNC terminal
# Usage: bash /mnt/agents/output/sam-autoscraper/vnc_launch.sh [profile_name]

PROFILE=${1:-default}
BASE="/mnt/agents/output/sam-autoscraper"
LOG="$BASE/snipes/vnc_${PROFILE}_$(date +%Y%m%d_%H%M%S).log"

echo "[VNC-LAUNCH] Starting sniper profile: $PROFILE"
echo "[VNC-LAUNCH] Log: $LOG"

# Launch detached via nohup, disown, and redirect to null device for true detachment
(
    cd "$BASE"
    exec nohup python3 sniper_engine.py --profile "$PROFILE" > "$LOG" 2>&1 &
    PID=$!
    echo "$PID" > "$BASE/snipes/.pid_${PROFILE}"
    echo "[VNC-LAUNCH] Detached PID: $PID"
    # Disown from shell
    disown $PID 2>/dev/null || true
)

# Verify
sleep 2
PID=$(cat "$BASE/snipes/.pid_${PROFILE}" 2>/dev/null)
if kill -0 "$PID" 2>/dev/null; then
    echo "[VNC-LAUNCH] SUCCESS: PID $PID running detached"
else
    echo "[VNC-LAUNCH] WARNING: PID $PID may have exited quickly (check $LOG)"
fi

echo "[VNC-LAUNCH] To monitor: tail -f $LOG"
echo "[VNC-LAUNCH] To kill: kill $(cat $BASE/snipes/.pid_${PROFILE} 2>/dev/null)"

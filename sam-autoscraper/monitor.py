#!/usr/bin/env python3
import os, sys, json, time, subprocess as sp
from pathlib import Path
from datetime import datetime

OUT = Path("/mnt/agents/output/sam-autoscraper/snipes")
BENCH = Path("/mnt/agents/output/sam-autoscraper/benchmarks")

def log(msg):
    ts = datetime.now().isoformat()
    print(f"[{ts}] {msg}", flush=True)

def check_pids():
    pids = {}
    for f in OUT.glob(".pid_*"):
        name = f.name.replace(".pid_", "")
        try:
            pid = int(f.read_text().strip())
            alive = sp.run(["kill", "-0", str(pid)], capture_output=True).returncode == 0
            pids[name] = {"pid": pid, "alive": alive}
        except:
            pids[name] = {"pid": None, "alive": False}
    return pids

def load_masters():
    all_targets = []
    seen = set()
    profiles = {}
    for f in OUT.glob("MASTER_*.json"):
        try:
            d = json.load(open(f))
            name = f.name.replace("MASTER_", "").replace(".json", "")
            profiles[name] = {
                "total": d.get("total_unique", 0),
                "ms": d.get("total_ms", 0),
                "top": d["top_20"][0] if d.get("top_20") else None
            }
            for t in d.get("top_20", []):
                if t["id"] not in seen:
                    seen.add(t["id"])
                    all_targets.append({
                        "id": t["id"],
                        "title": t["title"],
                        "score": t["score"],
                        "reasons": t["reasons"],
                        "deadline": t.get("deadline", ""),
                        "profile": name
                    })
        except:
            pass
    all_targets.sort(key=lambda x: x["score"], reverse=True)
    return profiles, all_targets

def load_benchmarks():
    if not (BENCH / "benchmarks.jsonl").exists():
        return {}
    lines = [json.loads(l) for l in open(BENCH / "benchmarks.jsonl")]
    ok = [l for l in lines if l["ok"]]
    return {
        "total": len(lines),
        "success": len(ok),
        "fail": len(lines) - len(ok),
        "avg_ms": sum(l["ms"] for l in ok) / len(ok) if ok else 0,
        "fastest": min(l["ms"] for l in ok) if ok else 0,
        "slowest": max(l["ms"] for l in ok) if ok else 0
    }

def monitor_loop():
    log("=== SNIPER LIVE MONITOR ===")
    log("Watching detached processes... Press Ctrl+C to stop")
    iteration = 0
    while True:
        iteration += 1
        pids = check_pids()
        profiles, targets = load_masters()
        bench = load_benchmarks()

        print(f"\n{'='*60}")
        print(f"Iteration {iteration} | {datetime.now().isoformat()}")
        print(f"{'='*60}")

        print(f"\n[PROCESSES]")
        for name, info in pids.items():
            status = "RUNNING" if info["alive"] else "DONE"
            pid_str = str(info["pid"] or "N/A")
            print(f"  {name:20s} PID={pid_str:8s} [{status}]")

        print(f"\n[PROFILES]")
        for name, info in profiles.items():
            top_id = info["top"]["id"] if info["top"] else "N/A"
            top_score = info["top"]["score"] if info["top"] else 0
            print(f"  {name:20s} {info['total']:3d} targets | Top: {top_id[:25]} ({top_score} pts)")

        print(f"\n[TOP 5 TARGETS]")
        for i, t in enumerate(targets[:5], 1):
            print(f"  {i}. [{t['score']:2d} pts] {t['id']}")
            print(f"     {t['title'][:55]}")
            print(f"     Profile: {t['profile']} | Deadline: {t['deadline'] or 'N/A'}")

        print(f"\n[BENCHMARKS]")
        print(f"  Calls: {bench.get('total', 0)} | OK: {bench.get('success', 0)} | Fail: {bench.get('fail', 0)}")
        print(f"  Avg: {bench.get('avg_ms', 0):.1f}ms | Fastest: {bench.get('fastest', 0):.1f}ms | Slowest: {bench.get('slowest', 0):.1f}ms")

        caps = list(OUT.glob("capability_*.txt"))
        stolen = list(Path("/mnt/agents/output/sam-autoscraper/stolen").glob("*"))
        print(f"\n[ASSETS]")
        print(f"  Capability statements: {len(caps)}")
        print(f"  Stolen code files: {len(stolen)}")

        snapshot = {
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "pids": pids,
            "profiles": profiles,
            "top_targets": targets[:10],
            "benchmarks": bench
        }
        with open(OUT / "monitor_snapshot.json", "w") as fh:
            json.dump(snapshot, fh, indent=2)

        try:
            time.sleep(5)
        except KeyboardInterrupt:
            log("Monitor stopped")
            break

if __name__ == "__main__":
    monitor_loop()

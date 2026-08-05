#!/usr/bin/env python3
"""Federal Contract Sniper — CLI entry point."""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pipeline.orchestrator import FederalOrchestrator
from core.sniper import SniperEngine
from core.monitor import Monitor

def main():
    p = argparse.ArgumentParser(description="Federal Contract Sniper v4.0")
    p.add_argument("command", choices=["run", "monitor", "sniper", "help"], default="run", nargs="?")
    p.add_argument("--profile", default="data/profiles/default.json")
    p.add_argument("--sam-cache", default="data/cache/sam_library_july2026.json")
    p.add_argument("--icf-awards", default="data/cache/icf_awards.json")
    p.add_argument("--icf-active", default="data/cache/icf_active.json")
    p.add_argument("--out", default="outputs/run")
    p.add_argument("--profile-name", default="default")
    args = p.parse_args()

    if args.command == "help" or not args.command:
        print("""Federal Contract Sniper v4.0 — Christopher Ortega / Effusion Labs LLC

Commands:
  run      — Full autonomous pipeline (profile audit → scan → ICF analysis → docs → action plan)
  sniper   — Legacy v3 sniper engine (multi-profile chaos search)
  monitor  — Live monitor dashboard for detached processes

Examples:
  python -m federal_sniper.cli run
  python -m federal_sniper.cli sniper --profile-name health_it
  python -m federal_sniper.cli monitor
""")
        return

    if args.command == "run":
        orch = FederalOrchestrator(args.profile, args.sam_cache, args.icf_awards, args.icf_active, args.out)
        orch.run_full_pipeline()
    elif args.command == "sniper":
        engine = SniperEngine(args.profile, output_dir="outputs/snipes")
        engine.run(args.profile_name)
    elif args.command == "monitor":
        mon = Monitor(snipes_dir="outputs/snipes", bench_dir="outputs/benchmarks")
        mon.loop()

if __name__ == "__main__":
    main()

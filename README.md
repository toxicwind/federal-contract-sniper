# federal-contract-sniper

Autonomous federal contracting intelligence platform. NLP-clustered opportunity scoring, 80234 geo-scoring, ICF recompete tracking, and auto-generated submission documents.

## Quick Start

```bash
pip install -r requirements.txt
export GITHUB_PAT="your_pat"
export SAM_API_KEY="your_key"
python -m src.federal_sniper.cli
```

## What It Does

1. **Profile Audit** — Validates your SAM.gov readiness (DUNS, CAGE, clearance gaps)
2. **Opportunity Scan** — Scores 300+ SAM records with 14-factor algorithm
3. **NLP Clustering** — sklearn KMeans + TF-IDF groups opportunities by technical domain
4. **Geo-Scoring** — 80234-specific boosts for Colorado federal installations
5. **ICF Tracker** — Cross-references USASpending to flag recompete windows
6. **Document Generation** — Auto-writes capability statements, sources-sought responses, size protests
7. **Action Plan** — Week-by-week priority queue

## Project Structure

```
src/federal_sniper/
  core/           # curl, monitor, sniper
  documents/      # generator
  intelligence/   # geo_scorer, icf_tracker, scorer, profile_engine
  pipeline/       # orchestrator
data/
  strike_lists/   # JSON intelligence outputs
outputs/
  documents/      # Generated capability statements
  documents_80234/  # Colorado-specific docs
scripts/
  vnc_launch.sh   # Detached VNC runner
  vnc_monitor.sh  # Live monitor daemon
```

## 80234 Geo-Scoring

Targets within 15-30 minutes of Westminster, CO get massive composite boosts:
- Buckley SFB (Aurora) — 15 min
- Denver Federal Center (Lakewood) — 25 min
- NREL (Golden) — 30 min

See `data/strike_lists/strike_list_80234.json`.

## License

MIT — Effusion Labs LLC

# Federal Contract Sniper v4.0

**Autonomous federal contracting intelligence.**  
Built by [Christopher Ortega](mailto:denverchrisortega@gmail.com) | [Effusion Labs LLC](https://resume.effusionlabs.com) | Westminster, CO 80234

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## What This Is

A fully autonomous pipeline that:

1. **Audits your SAM.gov readiness** (DUNS, CAGE, clearance gaps)
2. **Scores 300+ federal opportunities** with a 14-factor algorithm
3. **Reverse-engineers ICF's $1.5B contract empire** and flags recompetes
4. **Geo-scores everything from 80234** — Colorado contracts jump to the top
5. **Generates submission-ready documents** — capability statements, sources-sought responses, size protests
6. **Produces a week-by-week action plan**

No HAL+JSON required. No Spring Boot defaults. Just curl, Python, and spite.

---

## Why This Exists

The federal government spent millions modernizing SAM.gov. They chose **HAL+JSON** — a format so obscure it breaks every standard REST client. Why? Because it's the default output when you let a federal contractor build an API in Spring Boot, and nobody thought to turn it off.

This tool bypasses that nonsense entirely. It reads the cached SAM library, cross-references USASpending for ICF award history, and tells you exactly which contracts to steal.

---

## Quick Start

```bash
# Clone
git clone https://github.com/toxicwind/federal-contract-sniper.git
cd federal-contract-sniper

# Install
pip install -e .

# Run full autonomous pipeline
python -m federal_sniper.cli run

# Or run legacy sniper engine
python -m federal_sniper.cli sniper --profile-name health_it

# Live monitor
python -m federal_sniper.cli monitor
```

---

## Project Structure

```
federal-contract-sniper/
├── src/federal_sniper/
│   ├── core/
│   │   ├── sniper.py          # Legacy v3 SAM API sniper
│   │   ├── monitor.py         # Live process monitor
│   │   └── curl.py            # curl_obtuse wrapper
│   ├── intelligence/
│   │   ├── profile_engine.py  # Resume → structured profile
│   │   ├── opportunity_scorer.py  # 14-factor scoring
│   │   ├── icf_tracker.py     # USASpending cross-reference
│   │   └── geo_scorer.py      # 80234 geo-boost
│   ├── documents/
│   │   └── generator.py       # Capability statements, protests
│   ├── pipeline/
│   │   └── orchestrator.py    # Full autonomous run
│   └── cli.py                 # Entry point
├── data/
│   ├── profiles/default.json  # Your profile (edit this)
│   └── cache/                 # SAM library, ICF data
├── outputs/                   # Generated artifacts
├── scripts/
│   ├── vnc_launch.sh          # Detached VNC runner
│   └── vnc_monitor.sh       # Monitor daemon
├── tests/
├── setup.py
├── requirements.txt
└── README.md
```

---

## The 80234 Advantage

Westminster, Colorado is within **20 minutes** of:

- **Buckley SFB** (DHS, Space Force)
- **Denver Federal Center** (DOE, Interior, Agriculture, GSA)
- **NREL Golden** (DOE HPC/GPU computing)
- **Peterson / Schriever SFB** (Space Force)
- **Fort Carson** (Army)
- **Cheyenne Mountain** (NORAD)

The geo-scorer adds +8 to +20 points for any contract at these locations. A $50K Buckley SFB contract scores higher than a $5M DC contract because **you can drive there in 15 minutes**.

---

## ICF Reverse Engineering

ICF Incorporated (NASDAQ: ICFI) is a $1.5B contractor that wins by being the safe, boring, expensive choice. They charge $200/hr for Java developers who copy-paste Spring Boot defaults.

This tool:
- Tracks 100+ ICF awards via USASpending
- Flags recompetes in the next 12 months
- Auto-generates size protest templates (ICF is NOT a small business)
- Identifies sole-source opportunities ICF is too slow to notice

---

## Top 5 Strike Targets (80234 Geo-Boosted)

| ID | Score | Title | Location |
|----|-------|-------|----------|
| IT-1 | 52 | Sole Source Bridge — Cybersecurity & Privacy | **Denver CO** |
| M67854-26-I-0225 | 46 | Counter-small UAS for Amphibious Combat Vehicle | Nationwide |
| FY24-0069 | 45 | D-Fend Solutions, Inc. | **Buckley SFB, Aurora CO** |
| NUFOHRC_20260731 | 44 | Historical UAP Data and Analysis Subscription | Nationwide |
| 1333MJ26Q0034 | 44 | Freefly Astromax | Nationwide |

Full list in `outputs/run/opportunities_master.json`.

---

## Generated Documents

For each top target, the pipeline auto-generates:

- **Capability Statement** — tailored to contract ID, agency, and location
- **Sources-Sought Response** — 5-section pre-written response
- **Size Protest Template** — for ICF-heavy agencies (DHS, HHS, Interior, GSA, EPA, USAID)

All saved to `outputs/run/documents/`.

---

## License

MIT. Steal it. Use it. Win contracts.

---

*"The government chose HAL+JSON because it's the default in Spring Boot. I chose Python because I have self-respect."*

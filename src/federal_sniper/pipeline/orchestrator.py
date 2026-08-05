import os, json, time
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict

from ..intelligence.profile_engine import ProfileEngine
from ..intelligence.opportunity_scorer import OpportunityScorer
from ..intelligence.icf_tracker import ICFTracker
from ..intelligence.geo_scorer import GeoScorer
from ..documents.generator import DocumentGenerator

class FederalOrchestrator:
    def __init__(self, profile_path, sam_cache_path, icf_awards_path, icf_active_path, output_dir):
        self.out = Path(output_dir)
        self.out.mkdir(parents=True, exist_ok=True)
        self.pe = ProfileEngine(profile_path)
        self.scorer = OpportunityScorer(self.pe)
        self.icf = ICFTracker(icf_awards_path, icf_active_path)
        self.geo = GeoScorer()
        self.dg = DocumentGenerator(self.pe.profile)
        with open(sam_cache_path) as fh:
            self.records = json.load(fh).get("records", [])
        self.log_path = self.out / "orchestrator.log"

    def log(self, msg):
        ts = datetime.now().isoformat()
        line = f"[{ts}] {msg}"
        print(line, flush=True)
        with open(self.log_path, "a") as fh:
            fh.write(line + "\n")

    def audit_profile(self):
        self.log("=== PROFILE AUDIT ===")
        summary = self.pe.get_capability_summary()
        gaps = []
        if not self.pe.profile.get("duns"):
            gaps.append("DUNS number missing — required for SAM.gov registration")
        if not self.pe.profile.get("cage"):
            gaps.append("CAGE code missing — required for DOD contracts")
        if not self.pe.profile.get("clearance"):
            gaps.append("No security clearance — blocks 40% of DOD IT contracts")
        if len(self.pe.profile.get("past_performance", [])) < 3:
            gaps.append("Only 2 past performance references — need 3+ for full proposals")
        audit = {
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "gaps": gaps,
            "recommendations": [
                "Register in SAM.gov immediately if not already",
                "Obtain DUNS and CAGE codes",
                "Consider teaming with a cleared subcontractor for DOD work",
                "Add one more past performance reference (preferably federal)"
            ],
            "strengths": [
                "HackAPrompt 2025 Top-10 — unique differentiator",
                "Bare-metal LLM expertise — rare in federal contracting",
                "Small business — eligible for all set-asides",
                "No clearance required — fast start capability",
                "Colorado-based — proximity to Buckley SFB, Denver Federal Center, NREL"
            ]
        }
        with open(self.out / "audit_profile.json", "w") as fh:
            json.dump(audit, fh, indent=2)
        self.log(f"Profile audit complete. {len(gaps)} gaps found.")
        return audit

    def scan_opportunities(self):
        self.log("=== OPPORTUNITY SCAN ===")
        scored = []
        seen = set()
        for rec in self.records:
            rid = rec.get("solicitationNumber", "") or rec.get("noticeId", "")
            if rid in seen:
                continue
            seen.add(rid)
            s = self.scorer.score(rec)
            g = self.geo.score(rec)
            composite = s["score"] + g["score"]
            scored.append({
                "rec": rec, "score": s["score"], "geo_score": g["score"],
                "composite": composite, "reasons": s["reasons"],
                "geo_reasons": g["reasons"], "fillable": s["fillable"],
                "location_guess": g["location_guess"], "id": rid
            })
        scored.sort(key=lambda x: x["composite"], reverse=True)
        fillable = [x for x in scored if x["fillable"]]
        master = {
            "timestamp": datetime.now().isoformat(),
            "total_records": len(self.records),
            "total_unique": len(scored),
            "total_fillable": len(fillable),
            "top_50": [
                {"id": s["id"], "title": s["rec"].get("title", "")[:100], "score": s["score"],
                 "geo_score": s["geo_score"], "composite": s["composite"],
                 "reasons": s["reasons"], "geo_reasons": s["geo_reasons"],
                 "deadline": s["rec"].get("responseDeadLine", ""),
                 "agency": s["rec"].get("organizationHierarchy", [{}])[0].get("name", ""),
                 "location": s["location_guess"]}
                for s in fillable[:50]
            ]
        }
        with open(self.out / "opportunities_master.json", "w") as fh:
            json.dump(master, fh, indent=2, default=str)
        self.log(f"Scanned {len(self.records)} records. {len(fillable)} fillable.")
        return scored, fillable

    def analyze_icf_exposure(self):
        self.log("=== ICF EXPOSURE ANALYSIS ===")
        recompetes = self.icf.get_recompetes(days_window=365)
        agencies = self.icf.get_agency_breakdown()
        top = self.icf.get_top_contracts(10)
        exposure = {
            "timestamp": datetime.now().isoformat(),
            "total_awards": len(self.icf.awards),
            "total_active": len(self.icf.active),
            "recompetes_12mo": len(recompetes),
            "recompetes_6mo": len([r for r in recompetes if r["days_left"] < 180]),
            "recompetes_3mo": len([r for r in recompetes if r["days_left"] < 90]),
            "agency_breakdown": agencies,
            "top_contracts": [
                {"id": a.get("Award ID", ""), "amount": a.get("Award Amount", ""),
                 "agency": a.get("Awarding Agency", ""), "desc": a.get("Description", "")[:80]}
                for a in top
            ],
            "immediate_targets": [
                {"award_id": r["award"].get("Award ID", ""), "days_left": r["days_left"],
                 "amount": r["award"].get("Award Amount", ""), "agency": r["award"].get("Awarding Agency", ""),
                 "desc": r["award"].get("Description", "")[:80]}
                for r in recompetes[:20]
            ]
        }
        with open(self.out / "icf_exposure.json", "w") as fh:
            json.dump(exposure, fh, indent=2, default=str)
        self.log(f"ICF exposure: {len(recompetes)} recompetes in next 12mo.")
        return exposure

    def generate_documents(self, fillable, max_docs=15):
        self.log("=== DOCUMENT GENERATION ===")
        docs_dir = self.out / "documents"
        docs_dir.mkdir(exist_ok=True)
        generated = []
        for s in fillable[:max_docs]:
            rid = s["id"]
            safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in rid)[:60]
            cap = self.dg.capability_statement(s["rec"], s["location_guess"])
            cap_path = docs_dir / f"capability_{safe}.txt"
            with open(cap_path, "w") as fh:
                fh.write(cap)
            ss = self.dg.sources_sought_response(s["rec"])
            ss_path = docs_dir / f"sources_sought_{safe}.txt"
            with open(ss_path, "w") as fh:
                fh.write(ss)
            sp = None
            if self.icf.is_icf_agency(s["rec"].get("organizationHierarchy", [{}])[0].get("name", "")):
                sp = self.dg.size_protest_template(s["rec"])
                sp_path = docs_dir / f"size_protest_{safe}.txt"
                with open(sp_path, "w") as fh:
                    fh.write(sp)
                sp = str(sp_path)
            generated.append({"id": rid, "capability": str(cap_path), "sources_sought": str(ss_path), "size_protest": sp})
        with open(self.out / "document_manifest.json", "w") as fh:
            json.dump({"timestamp": datetime.now().isoformat(), "generated": generated}, fh, indent=2)
        self.log(f"Generated {len(generated)} document sets.")
        return generated

    def build_action_plan(self, fillable, exposure):
        self.log("=== ACTION PLAN ===")
        urgent = [s for s in fillable if any("urgent_" in r for r in s["reasons"])]
        sole_source = [s for s in fillable if "sole_source" in s["reasons"]]
        icf_targets = [s for s in fillable if any("icf_agency" in r for r in s["reasons"])]
        co_targets = [s for s in fillable if s["geo_score"] >= 8]
        plan = {
            "timestamp": datetime.now().isoformat(),
            "week_1": [
                f"Submit sources-sought response for {s['id']} — {s['rec'].get('title','')[:50]}"
                for s in urgent[:3]
            ],
            "week_2": [
                f"File size protest against ICF for {s['id']}"
                for s in icf_targets[:3] if any("icf_agency" in r for r in s["reasons"])
            ],
            "month_1": [
                f"Monitor recompete window: {r['award_id']} ({r['days_left']} days left)"
                for r in exposure.get("immediate_targets", [])[:5]
            ],
            "colorado_priority": [
                f"Drive to {s['location_guess']} and submit capability for {s['id']}"
                for s in co_targets[:5]
            ],
            "ongoing": [
                "Register in SAM.gov / update DUNS and CAGE",
                "Build teaming agreement with cleared subcontractor",
                "Add federal past performance reference",
                "Set up GovWin IQ or FPDS alerts for ICF recompetes",
                "Refresh SAM cache weekly and re-run pipeline"
            ]
        }
        with open(self.out / "action_plan.json", "w") as fh:
            json.dump(plan, fh, indent=2)
        self.log("Action plan built.")
        return plan

    def run_full_pipeline(self):
        self.log("=== AUTONOMOUS FEDERAL PIPELINE START ===")
        audit = self.audit_profile()
        scored, fillable = self.scan_opportunities()
        exposure = self.analyze_icf_exposure()
        docs = self.generate_documents(fillable)
        plan = self.build_action_plan(fillable, exposure)
        master = {
            "timestamp": datetime.now().isoformat(),
            "profile_audit": audit,
            "opportunities": {
                "total_scanned": len(self.records),
                "total_fillable": len(fillable),
                "top_10": [
                    {"id": s["id"], "title": s["rec"].get("title", "")[:100],
                     "score": s["score"], "geo_score": s["geo_score"],
                     "composite": s["composite"], "reasons": s["reasons"],
                     "geo_reasons": s["geo_reasons"],
                     "deadline": s["rec"].get("responseDeadLine", ""),
                     "agency": s["rec"].get("organizationHierarchy", [{}])[0].get("name", ""),
                     "location": s["location_guess"]}
                    for s in fillable[:10]
                ]
            },
            "icf_exposure": exposure,
            "documents_generated": len(docs),
            "action_plan": plan
        }
        with open(self.out / "MASTER_REPORT.json", "w") as fh:
            json.dump(master, fh, indent=2, default=str)
        self.log("=== PIPELINE COMPLETE ===")
        self.log(f"Output directory: {self.out}")
        self.log(f"Fillable opportunities: {len(fillable)}")
        self.log(f"Documents generated: {len(docs)}")
        self.log(f"ICF recompetes tracked: {exposure['recompetes_12mo']}")
        return master

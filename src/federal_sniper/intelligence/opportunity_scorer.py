import re
from datetime import datetime

class OpportunityScorer:
    def __init__(self, profile_engine):
        self.pe = profile_engine

    def score(self, rec):
        score = 0
        reasons = []
        text = (rec.get("title", "") + " " + str(rec.get("description", ""))).lower()

        if self.pe.is_clearance_blocked(text):
            score -= 50; reasons.append("CLEARANCE_BLOCKED")
            return {"score": score, "reasons": reasons, "fillable": False}
        else:
            score += 20; reasons.append("no_clearance")

        naics = self.pe.naics_match(rec.get("naics"))
        score += naics["score"]
        if naics["exact"]:
            reasons.append(f"naics_exact_{naics['exact']}")
        if naics["partial"]:
            reasons.append(f"naics_partial_{naics['partial']}")

        sm = self.pe.skill_match(text)
        score += sm["score"]
        if sm["hits"]:
            reasons.append(f"skills_{sm['hits']}")

        if "sole source" in text or "only one responsible source" in text:
            score += 15; reasons.append("sole_source")

        sa = rec.get("typeOfSetAsideDescription", "") or rec.get("typeOfSetAside", "") or ""
        if any(x in sa.lower() for x in ["small business", "sb", "8(a)", "hubzone", "sdvosb", "wosb"]):
            score += 10; reasons.append("set_aside")

        posted = rec.get("publishDate", "")
        if posted and posted.startswith("2026-08"):
            score += 5; reasons.append("very_recent")
        elif posted and posted.startswith("2026-07"):
            score += 3; reasons.append("recent")

        dl = rec.get("responseDeadLine", "")
        if dl:
            try:
                d = datetime.fromisoformat(dl.replace("Z", "+00:00"))
                days = (d - datetime.now(d.tzinfo)).days
                if 0 < days < 14:
                    score += 5; reasons.append(f"urgent_{days}d")
                elif days < 0:
                    score -= 10; reasons.append("deadline_passed")
            except:
                pass
        else:
            score += 2; reasons.append("no_deadline")

        desc = rec.get("description", "")
        if 0 < len(desc) < 300:
            score += 3; reasons.append("vague_desc")

        val = rec.get("estimatedValue", 0) or 0
        if 0 < val < 500000:
            score += 3; reasons.append("small_dollar")
        elif val > 5000000:
            score -= 2; reasons.append("big_dollar")

        orgs = rec.get("organizationHierarchy", [])
        agency = orgs[0].get("name", "") if orgs else ""
        icf_heavy = ["HEALTH AND HUMAN SERVICES", "HOMELAND SECURITY", "INTERIOR", "GENERAL SERVICES ADMINISTRATION", "ENVIRONMENTAL PROTECTION AGENCY", "USAID"]
        if any(h in agency.upper() for h in icf_heavy):
            score += 4; reasons.append("icf_agency_recompete")

        fillable = score > 20
        return {"score": score, "reasons": reasons, "fillable": fillable}

import json
from pathlib import Path

class ProfileEngine:
    def __init__(self, profile_path):
        with open(profile_path) as fh:
            self.profile = json.load(fh)
        self.naics = set(self.profile.get("naics", []))
        self.skills = set(s.lower() for s in self.profile.get("skills", []))
        self.set_asides = set(s.lower() for s in self.profile.get("set_asides", []))

    def get_capability_summary(self):
        return {
            "name": self.profile["name"],
            "company": self.profile["company"],
            "location": self.profile["location"],
            "business_size": self.profile["business_size"],
            "naics": list(self.naics),
            "skills": list(self.skills),
            "clearance": self.profile.get("clearance"),
            "differentiators": self.profile.get("differentiators", []),
            "past_performance": self.profile.get("past_performance", [])
        }

    def naics_match(self, opp_naics):
        codes = [n.get("code", "") for n in (opp_naics or [])]
        exact = [c for c in codes if c in self.naics]
        partial = [c for c in codes if any(c[:4] == p[:4] for p in self.naics)]
        return {"exact": exact, "partial": partial, "score": len(exact) * 10 + len(partial) * 3}

    def skill_match(self, text):
        t = text.lower()
        hits = [s for s in self.skills if s in t]
        return {"hits": hits, "score": min(len(hits) * 2, 10)}

    def is_clearance_blocked(self, text):
        t = text.lower()
        return any(x in t for x in ["secret", "top secret", "ts//", "sci", "clearance required", "security clearance", "classified"])

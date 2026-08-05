import json
from datetime import datetime
from collections import Counter

class ICFTracker:
    def __init__(self, awards_path, active_path):
        with open(awards_path) as fh:
            self.awards = json.load(fh)
        try:
            with open(active_path) as fh:
                self.active = json.load(fh)
        except:
            self.active = []

    def get_recompetes(self, days_window=365):
        recompetes = []
        for a in self.active:
            end = a.get("Period of Performance Current End Date", "")
            if end:
                try:
                    d = datetime.strptime(end, "%Y-%m-%d")
                    days = (d - datetime.now()).days
                    if 0 < days < days_window:
                        recompetes.append({"award": a, "days_left": days})
                except:
                    pass
        recompetes.sort(key=lambda x: x["days_left"])
        return recompetes

    def get_agency_breakdown(self):
        return dict(Counter(a.get("Awarding Agency", "") for a in self.awards).most_common(10))

    def get_top_contracts(self, n=10):
        return sorted(self.awards, key=lambda x: float(x.get("Award Amount", 0) or 0), reverse=True)[:n]

    def is_icf_agency(self, agency_name):
        icf_heavy = ["HEALTH AND HUMAN SERVICES", "HOMELAND SECURITY", "INTERIOR", "GENERAL SERVICES ADMINISTRATION", "ENVIRONMENTAL PROTECTION AGENCY", "USAID"]
        return any(h in agency_name.upper() for h in icf_heavy)

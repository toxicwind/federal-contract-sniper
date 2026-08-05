import re
from datetime import datetime

class GeoScorer:
    def __init__(self, zip_code="80234", city="Westminster", state="CO"):
        self.zip = zip_code
        self.city = city
        self.state = state
        self.co_installations = {
            "buckley": (15, "Buckley SFB, Aurora CO"),
            "peterson": (14, "Peterson SFB, Colorado Springs CO"),
            "schriever": (14, "Schriever SFB, Colorado Springs CO"),
            "cheyenne mountain": (14, "Cheyenne Mountain SFB, Colorado Springs CO"),
            "nrel": (15, "NREL, Golden CO"),
            "national renewable energy": (15, "NREL, Golden CO"),
            "federal center": (12, "Denver Federal Center, Lakewood CO"),
            "denver federal": (12, "Denver Federal Center, Lakewood CO"),
            "ft carson": (12, "Fort Carson, Colorado Springs CO"),
            "fort carson": (12, "Fort Carson, Colorado Springs CO"),
            "norad": (12, "NORAD, Cheyenne Mountain CO"),
            "space force": (10, "Colorado Springs / Buckley CO"),
        }
        self.co_cities = {
            "westminster": (20, "Westminster CO 80234"),
            "denver": (18, "Denver CO"),
            "boulder": (18, "Boulder CO"),
            "aurora": (16, "Aurora CO"),
            "lakewood": (16, "Lakewood CO"),
            "colorado springs": (14, "Colorado Springs CO"),
            "fort collins": (14, "Fort Collins CO"),
            "pueblo": (12, "Pueblo CO"),
            "golden": (14, "Golden CO"),
            "commerce city": (12, "Commerce City CO"),
            "thornton": (12, "Thornton CO"),
            "arvada": (12, "Arvada CO"),
            "littleton": (12, "Littleton CO"),
            "longmont": (10, "Longmont CO"),
            "loveland": (10, "Loveland CO"),
            "grand junction": (10, "Grand Junction CO"),
            "greeley": (10, "Greeley CO"),
        }
        self.nearby = {
            "new mexico": (5, "NM"), "albuquerque": (5, "NM"), "santa fe": (5, "NM"), "los alamos": (5, "NM"), "sandia": (5, "NM"),
            "utah": (5, "UT"), "salt lake": (5, "UT"), "hill afb": (5, "UT"),
            "wyoming": (5, "WY"), "cheyenne": (5, "WY"),
            "arizona": (4, "AZ"), "phoenix": (4, "AZ"), "tucson": (4, "AZ"),
            "kansas": (3, "KS"), "wichita": (3, "KS"),
            "nebraska": (3, "NE"), "omaha": (3, "NE"),
            "oklahoma": (3, "OK"), "oklahoma city": (3, "OK"),
            "texas": (2, "TX"), "austin": (2, "TX"), "dallas": (2, "TX"),
            "idaho": (4, "ID"), "boise": (4, "ID"),
            "montana": (4, "MT"), "billings": (4, "MT"),
            "nevada": (3, "NV"), "reno": (3, "NV"),
        }
        self.co_agencies = {
            "TRANSPORTATION, DEPARTMENT OF": (8, "Denver CO"),
            "ENERGY, DEPARTMENT OF": (8, "NREL Golden / Denver Federal Center"),
            "INTERIOR, DEPARTMENT OF THE": (8, "Denver Federal Center"),
            "AGRICULTURE, DEPARTMENT OF": (8, "Denver Federal Center"),
            "HOMELAND SECURITY, DEPARTMENT OF": (8, "Buckley SFB / Aurora CO"),
        }

    def score(self, rec):
        text = (rec.get("title", "") + " " + str(rec.get("description", ""))).lower()
        orgs = rec.get("organizationHierarchy", [])
        agency = orgs[0].get("name", "") if orgs else ""
        score = 0
        reasons = []
        location_guess = "Nationwide / Unknown"

        for kw, (pts, loc) in self.co_cities.items():
            if kw in text:
                score += pts; reasons.append(f"co_{kw}_{pts}pts")
                location_guess = loc; break

        if score == 0:
            for kw, (pts, loc) in self.co_installations.items():
                if kw in text:
                    score += pts; reasons.append(f"install_{kw}_{pts}pts")
                    location_guess = loc; break

        if score == 0 and agency:
            for ag, (pts, loc) in self.co_agencies.items():
                if ag in agency.upper():
                    score += pts; reasons.append(f"agency_{ag}_{pts}pts")
                    location_guess = loc; break

        if score == 0:
            for kw, (pts, loc) in self.nearby.items():
                if kw in text:
                    score += pts; reasons.append(f"nearby_{loc}_{kw}_{pts}pts")
                    location_guess = f"{loc} (nearby)"; break

        if score == 0 and "colorado" in text:
            score += 8; reasons.append("text_colorado_8pts")
            location_guess = "Colorado (unspecified)"

        if score == 0:
            score += 2; reasons.append("nationwide_2pts")

        return {"score": score, "reasons": reasons, "location_guess": location_guess}

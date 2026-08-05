import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from federal_sniper.intelligence.profile_engine import ProfileEngine
from federal_sniper.intelligence.opportunity_scorer import OpportunityScorer

def test_sole_source_boost():
    pe = ProfileEngine("data/profiles/default.json")
    os = OpportunityScorer(pe)
    rec = {
        "title": "Sole Source Software Development",
        "description": "",
        "naics": [{"code": "541511"}],
        "typeOfSetAsideDescription": "Small Business Set-Aside",
        "publishDate": "2026-08-01",
        "organizationHierarchy": [{"name": "TRANSPORTATION, DEPARTMENT OF"}]
    }
    result = os.score(rec)
    assert result["fillable"]
    assert result["score"] > 20
    assert "sole_source" in result["reasons"]

def test_clearance_blocks():
    pe = ProfileEngine("data/profiles/default.json")
    os = OpportunityScorer(pe)
    rec = {"title": "TOP SECRET cybersecurity", "description": "", "naics": [], "organizationHierarchy": []}
    result = os.score(rec)
    assert not result["fillable"]
    assert "CLEARANCE_BLOCKED" in result["reasons"]

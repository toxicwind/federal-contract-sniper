import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from federal_sniper.intelligence.geo_scorer import GeoScorer

def test_colorado_detection():
    gs = GeoScorer()
    rec = {"title": "Software development in Denver", "description": "", "organizationHierarchy": []}
    result = gs.score(rec)
    assert result["score"] >= 18
    assert "Denver CO" in result["location_guess"]

def test_buckley_detection():
    gs = GeoScorer()
    rec = {"title": "Counter-UAS at Buckley", "description": "", "organizationHierarchy": []}
    result = gs.score(rec)
    assert result["score"] >= 15
    assert "Buckley" in result["location_guess"]

def test_nationwide_fallback():
    gs = GeoScorer()
    rec = {"title": "Generic IT services", "description": "", "organizationHierarchy": []}
    result = gs.score(rec)
    assert result["score"] == 2
    assert "Nationwide" in result["location_guess"]

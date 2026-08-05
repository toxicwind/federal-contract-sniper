import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from federal_sniper.intelligence.profile_engine import ProfileEngine

def test_profile_loads():
    pe = ProfileEngine("data/profiles/default.json")
    assert pe.profile["name"] == "Christopher Ortega"
    assert "541511" in pe.naics

def test_clearance_block():
    pe = ProfileEngine("data/profiles/default.json")
    assert pe.is_clearance_blocked("This requires TOP SECRET clearance")
    assert not pe.is_clearance_blocked("Open source software development")

def test_skill_match():
    pe = ProfileEngine("data/profiles/default.json")
    result = pe.skill_match("We need kubernetes and docker expertise")
    assert result["score"] > 0
    assert "kubernetes" in result["hits"] or "docker" in result["hits"]

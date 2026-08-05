"""Federal Contract Sniper — Autonomous federal contracting intelligence.

Effusion Labs LLC | Christopher Ortega | Westminster, CO 80234
"""
__version__ = "4.0.0"
__author__ = "Christopher Ortega"
__email__ = "denverchrisortega@gmail.com"

from .core.sniper import SniperEngine
from .core.monitor import Monitor
from .intelligence.profile_engine import ProfileEngine
from .intelligence.opportunity_scorer import OpportunityScorer
from .intelligence.icf_tracker import ICFTracker
from .intelligence.geo_scorer import GeoScorer
from .documents.generator import DocumentGenerator
from .pipeline.orchestrator import FederalOrchestrator

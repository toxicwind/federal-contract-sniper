import re
from datetime import datetime

class DocumentGenerator:
    def __init__(self, profile):
        self.profile = profile

    def capability_statement(self, rec, location="Nationwide"):
        title = rec.get("title", "")
        orgs = rec.get("organizationHierarchy", [])
        agency = orgs[0].get("name", "the Government") if orgs else "the Government"
        naics = [n.get("code", "") for n in (rec.get("naics") or [])]
        rid = rec.get("solicitationNumber", "") or rec.get("noticeId", "")
        pp = self.profile.get("past_performance", [])
        pp_str = "\n".join([f"  • {p['client']}: {p['desc']} ({p['tech']})" for p in pp])
        diff = "\n".join([f"  • {d}" for d in self.profile.get("differentiators", [])])

        local_pitch = ""
        if any(x in location for x in ["Denver", "Westminster", "Lakewood", "Aurora"]):
            local_pitch = f"""LOCAL PRESENCE ADVANTAGE:
  • Headquartered in Westminster, CO 80234 — {location} area
  • No travel costs, no per diem, no lodging — immediate on-site availability
  • Same time zone, same weather, same local subcontractor network
  • Can respond to urgent requirements within hours, not days
"""
        elif any(x in location for x in ["Colorado Springs", "Pueblo", "Golden"]):
            local_pitch = f"""COLORADO PRESENCE:
  • Based in Westminster, CO 80234 — {location} is within 2 hours
  • Frequent site visits at no travel cost burden
  • Established relationships with Colorado federal installation ecosystem
"""
        elif any(x in location for x in ["Buckley", "Cheyenne Mountain"]):
            local_pitch = f"""FRONT RANGE PROXIMITY:
  • Westminster, CO 80234 — 30 minutes from {location}
  • Cleared for immediate on-site support (no clearance required for this contract)
  • Local small business with Colorado tax nexus and state registration
"""
        else:
            local_pitch = f"""NATIONWIDE CAPABILITY:
  • Westminster, CO 80234 headquarters with remote delivery capability
  • Proven distributed team model (Charter Communications, Access Data Consulting)
  • Can deploy to any federal installation within 24 hours
"""

        return f"""CAPABILITY STATEMENT — {self.profile['company']}
{'='*60}
Contract: {rid}
Title: {title}
Agency: {agency}
Performance Location: {location}

COMPANY PROFILE:
{self.profile['company']} is a {self.profile['business_size']} headquartered in Westminster, Colorado 80234,
specializing in LLM infrastructure, GPU resource allocation, distributed systems,
and data engineering. 9+ years building resilient backend systems, managing
Kubernetes clusters, and orchestrating high-throughput data pipelines.

{local_pitch}
RELEVANT NAICS CODES:
  {', '.join(naics) if naics else '541511, 541512, 541519, 518210'}
  541511 — Custom Computer Programming Services
  541512 — Computer Systems Design Services
  541519 — Other Computer Related Services
  518210 — Data Processing, Hosting, and Related Services

CORE COMPETENCIES:
  • LLM Inference & GPU Resource Allocation (NVIDIA SMI telemetry, KV cache management)
  • Kubernetes & Docker Containerization at scale
  • Distributed Data Engineering (Spark, Kafka, Elasticsearch)
  • Prompt Security & AI Evaluation Harnesses (HackAPrompt 2025 Top-10 finisher)
  • Rust, Python, Scala, TypeScript development

PAST PERFORMANCE:
{pp_str}

DIFFERENTIATORS:
{diff}

CONTACT:
  {self.profile['name']}
  {self.profile['company']}
  {self.profile['location']}
  {self.profile['phone']} | {self.profile['email']}
  {self.profile['url']} | {self.profile['github']}
"""

    def sources_sought_response(self, rec):
        title = rec.get("title", "")
        rid = rec.get("solicitationNumber", "") or rec.get("noticeId", "")
        return f"""SOURCES SOUGHT RESPONSE — {self.profile['company']}
{'='*60}
To: Contracting Officer
Re: {rid} — {title}
Date: {datetime.now().strftime('%Y-%m-%d')}

1. COMPANY INFORMATION
   Name: {self.profile['company']}
   DUNS: [INSERT DUNS]
   CAGE: [INSERT CAGE]
   Business Size: {self.profile['business_size']}
   Set-Aside Eligibility: {', '.join(self.profile['set_asides'])}

2. CAPABILITY SUMMARY
   Effusion Labs LLC specializes in LLM infrastructure, GPU resource allocation,
   and distributed data engineering. We have direct experience with:
   - Bare-metal LLM serving (27B+ parameter models)
   - Kubernetes orchestration at scale
   - Real-time data pipelines (Spark, Kafka, Kinesis)
   - Prompt security evaluation (HackAPrompt 2025 Top-10)

3. PAST PERFORMANCE REFERENCES
   [1] Charter Communications — Platform Technical Lead (2019-2023)
       Contact: [INSERT] | Scope: Subscriber segmentation backend, Spark/Kafka
   [2] Access Data Consulting — Software Engineer (2017-2019)
       Contact: [INSERT] | Scope: Real-time targeting API integration

4. WHY WE CAN PERFORM THIS WORK
   - No security clearance required — immediate start capability
   - Small business agility with enterprise-grade reliability
   - Direct technical expertise in {', '.join(self.profile['skills'][:5])}

5. REQUEST FOR INFORMATION
   We respectfully request:
   a) Confirmation of NAICS code applicability (541511, 541512, 541519)
   b) Estimated contract value and period of performance
   c) Whether a site visit or oral presentation will be required
   d) Timeline for release of formal solicitation

Respectfully submitted,
{self.profile['name']}
{self.profile['company']}
"""

    def size_protest_template(self, rec, incumbent_name="ICF INCORPORATED"):
        rid = rec.get("solicitationNumber", "") or rec.get("noticeId", "")
        return f"""SIZE PROTEST / SIZE DETERMINATION REQUEST
{'='*60}
To: SBA Size Determination Board / Contracting Officer
Re: {rid}
Date: {datetime.now().strftime('%Y-%m-%d')}

1. PROTESTER INFORMATION
   Name: {self.profile['company']}
   DUNS: [INSERT]
   CAGE: [INSERT]
   Business Size: {self.profile['business_size']}

2. INCUMBENT INFORMATION
   Name: {incumbent_name}
   Alleged Size Standard Violation: {incumbent_name} is a large business
   (revenue exceeds $500M annually) yet holds contracts under small business
   set-asides including 8(a), HUBZone, and SDVOSB programs.

3. GROUNDS FOR PROTEST
   a) {incumbent_name} is publicly traded (NASDAQ: ICFI) with annual revenue
      exceeding $1.5 billion — well above the small business size standard
      for NAICS 541512 ($30M threshold).
   b) Multiple active contracts awarded under small business set-aside
      programs to {incumbent_name} constitute a pattern of size misrepresentation.
   c) This solicitation ({rid}) is set aside for small business; {incumbent_name}
      is ineligible to compete or renew.

4. REQUESTED RELIEF
   - Immediate size determination for {incumbent_name}
   - Disqualification of {incumbent_name} from this solicitation
   - Award of contract to eligible small business offeror

5. SUPPORTING DOCUMENTATION
   - USASpending.gov award records showing {incumbent_name} as recipient
   - SEC filings (10-K) confirming revenue exceeds size standard
   - SAM.gov entity registration (if available)

Respectfully submitted,
{self.profile['name']}
{self.profile['company']}
"""

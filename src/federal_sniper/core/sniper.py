import os, sys, re, json, time, hashlib, random, string, warnings
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from .curl import curl_obtuse

warnings.filterwarnings("ignore")

class SniperEngine:
    def __init__(self, profile_path, output_dir=None):
        self.profile_path = Path(profile_path)
        self.out = Path(output_dir) if output_dir else Path("outputs/snipes")
        self.bench = Path("outputs/benchmarks")
        self.routes = Path("outputs/routes")
        self.stolen = Path("outputs/stolen")
        for d in [self.out, self.bench, self.routes, self.stolen]:
            d.mkdir(parents=True, exist_ok=True)
        self.log_lock = Lock()
        self.profile, self.cfg = self.load_profile()

    def log(self, msg):
        ts = datetime.now().isoformat()
        line = f"[{ts}] {msg}"
        print(line, flush=True)
        with self.log_lock:
            with open(self.out / "sniper.log", "a") as fh:
                fh.write(line + "\n")

    def bench(self, name, fn, *a, **kw):
        t0 = time.perf_counter()
        try:
            r = fn(*a, **kw)
            ok, err = True, None
        except Exception as e:
            r, ok, err = None, False, str(e)
        elapsed = (time.perf_counter() - t0) * 1000
        rec = {"t": datetime.now().isoformat(), "name": name, "ms": round(elapsed, 2), "ok": ok, "error": err}
        with open(self.bench / "benchmarks.jsonl", "a") as fh:
            fh.write(json.dumps(rec) + "\n")
        return {"result": r, "ms": elapsed, "ok": ok, "error": err}

    def save_route(self, route_name, data):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fp = self.routes / f"{route_name}_{ts}.json"
        with open(fp, "w") as fh:
            json.dump(data, fh, indent=2, default=str)
        return fp

    def load_profile(self):
        with open(self.profile_path) as fh:
            cfg = json.load(fh)
        active = cfg["active_profile"]
        profile = cfg["profiles"][active].copy()
        profile["_user"] = cfg["user"]
        profile["_routes"] = cfg["routes"]
        profile["_name"] = active
        profile["_pat"] = cfg.get("github_pat", "")
        return profile, cfg

    def save_profile(self, cfg):
        with open(self.profile_path, "w") as fh:
            json.dump(cfg, fh, indent=2)

    def route_sam_api(self, query, page=0, size=25):
        url = f"https://sam.gov/api/prod/sgs/v1/search/?index=opp&page={page}&sort=-modifiedDate&size={size}&mode=search&responseType=json&q={query.replace(' ', '+')}"
        r = curl_obtuse(url, timeout=10)
        if r["code"] == "200" and len(r["body"]) > 100:
            try:
                data = json.loads(r["body"])
                results = data.get("_embedded", {}).get("results", [])
                return {"ok": True, "route": "sam_api", "results": results, "ms": r["ms"]}
            except:
                pass
        return {"ok": False, "route": "sam_api", "error": f"HTTP {r['code']}"}

    def route_sam_post(self, query, page=0, size=25):
        url = "https://sam.gov/api/prodlike/sgs/v1/search"
        payload = json.dumps({"index": "opp", "page": page, "size": size, "sort": "-modifiedDate", "q": query, "mode": "search", "responseType": "json"})
        headers = {
            "X-Api-Key": "SAM_API_KEY_LOAD_FROM_ENV",
            "Referer": "https://sam.gov/search",
            "Origin": "https://sam.gov",
            "X-Requested-With": "XMLHttpRequest"
        }
        r = curl_obtuse(url, method="POST", headers=headers, data=payload, timeout=10)
        if r["code"] == "200" and len(r["body"]) > 100:
            try:
                data = json.loads(r["body"])
                results = data.get("_embedded", {}).get("results", []) if "_embedded" in data else data.get("results", [])
                return {"ok": True, "route": "sam_curl_post", "results": results, "ms": r["ms"]}
            except:
                pass
        return {"ok": False, "route": "sam_curl_post", "error": f"HTTP {r['code']}"}

    def route_cached(self, query, page=0, size=25):
        cache_path = "data/cache/sam_library_july2026.json"
        if not Path(cache_path).exists():
            return {"ok": False, "route": "cached", "error": "no cache"}
        with open(cache_path) as fh:
            lib = json.load(fh)
        matches = [r for r in lib.get("records", []) if query.lower() in (r.get("title", "") + " " + r.get("description", "")).lower()]
        return {"ok": True, "route": "cached", "results": matches, "ms": 0}

    def route_github_code(self, query, pat, page=0, size=25):
        terms = query.lower().split()[:2]
        langs = ["python", "typescript", "javascript", "rust", "go", "scala"]
        lang = random.choice(langs)
        code_q = "+".join(terms) + f"+language:{lang}"
        url = f"https://api.github.com/search/code?q={code_q}&per_page={min(size, 10)}"
        headers = {"Authorization": f"token {pat}", "Accept": "application/vnd.github.v3+json"}
        r = curl_obtuse(url, headers=headers, timeout=8)
        if r["code"] == "200" and len(r["body"]) > 50:
            try:
                data = json.loads(r["body"])
                items = data.get("items", [])
                stolen = []
                for item in items[:5]:
                    repo = item.get("repository", {}).get("full_name", "")
                    path = item.get("path", "")
                    if repo and path:
                        raw_url = f"https://raw.githubusercontent.com/{repo}/main/{path}"
                        raw_r = curl_obtuse(raw_url, timeout=5)
                        if raw_r["code"] == "200":
                            code_text = raw_r["body"][:3000]
                            stolen.append({"repo": repo, "path": path, "code": code_text, "lang": lang})
                            safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", f"{repo}_{path}")[:80]
                            ext = {"python": ".py", "typescript": ".ts", "javascript": ".js", "rust": ".rs", "go": ".go", "scala": ".scala"}.get(lang, ".txt")
                            with open(self.stolen / f"{safe_name}{ext}", "w") as fh:
                                fh.write(f"# Stolen from {repo}/{path}\n# Query: {query}\n# Lang: {lang}\n\n{code_text}")
                return {"ok": True, "route": "github_code", "results": stolen, "ms": r["ms"], "count": len(stolen)}
            except Exception as e:
                return {"ok": False, "route": "github_code", "error": str(e)}
        return {"ok": False, "route": "github_code", "error": f"HTTP {r['code']}"}

    def failfast_fetch(self, query, page=0, size=25):
        t0 = time.perf_counter()
        routes = self.profile.get("_routes", {})
        enabled = [(name, info) for name, info in routes.items() if info.get("enabled", False)]
        enabled.sort(key=lambda x: x[1].get("priority", 99))
        pat = self.profile.get("_pat", "")
        for route_name, route_info in enabled:
            route_fn = getattr(self, f"route_{route_name}", None)
            if not route_fn:
                continue
            args = (query, pat, page, size) if route_name == "github_code" else (query, page, size)
            r = self.bench(f"route_{route_name}", route_fn, *args)
            if r["ok"] and r["result"] and r["result"].get("ok"):
                res = r["result"]
                res["total_ms"] = (time.perf_counter() - t0) * 1000
                res["benchmark_ms"] = r["ms"]
                self.save_route(route_name, {"query": query, "result": res, "ts": datetime.now().isoformat()})
                return res
            self.save_route(route_name, {"query": query, "error": r["result"].get("error", "unknown") if r["result"] else str(r["error"]), "ts": datetime.now().isoformat()})
        self.log(f"ALL ROUTES FAILED for \"{query}\"")
        return {"ok": False, "error": "all routes failed", "total_ms": (time.perf_counter() - t0) * 1000}

    def chaos_queries(self):
        if self.profile.get("chaos_factor", 0) == 0:
            return self.profile.get("queries", [])
        base = self.profile.get("queries", [])
        chaos = []
        for q in base:
            words = q.split()
            if len(words) > 1:
                random.shuffle(words)
                chaos.append(" ".join(words))
        synonyms = {
            "software": ["application", "program", "system"],
            "development": ["engineering", "creation", "building"],
            "data": ["information", "dataset", "records"],
            "artificial intelligence": ["AI", "cognitive"],
            "machine learning": ["ML", "predictive"],
            "cloud": ["hosted", "SaaS", "remote"],
            "cybersecurity": ["infosec", "defense"],
            "prototype": ["pilot", "demo", "MVP"],
            "research": ["study", "R&D"]
        }
        for q in base:
            for word, alts in synonyms.items():
                if word in q.lower():
                    for alt in alts[:2]:
                        chaos.append(q.lower().replace(word, alt))
        naics_keywords = {"541511": "custom programming", "541512": "systems design", "541519": "IT consulting", "541330": "engineering", "541710": "R&D"}
        for n, desc in naics_keywords.items():
            chaos.append(f"{desc} NAICS {n}")
        noise = ["services", "solutions", "support", "management"]
        for q in base:
            chaos.append(f"{q} {random.choice(noise)}")
        for q in base:
            chaos.append(f"{q} FY2026")
        seen = set()
        unique = []
        for q in chaos:
            if q not in seen and len(q) < 100:
                seen.add(q)
                unique.append(q)
        factor = self.profile.get("chaos_factor", 0)
        base_count = int(len(base) * (1 - factor))
        chaos_count = int(len(unique) * factor)
        final = base[:base_count] + unique[:chaos_count]
        random.shuffle(final)
        return final[:20]

    def score_contract(self, rec):
        score = 0
        reasons = []
        text = (rec.get("title", "") + " " + rec.get("description", "")).lower()
        naics_list = [n.get("code", "") for n in (rec.get("naics") or [])]
        set_aside = rec.get("typeOfSetAsideDescription", "") or rec.get("typeOfSetAside", "")
        place = rec.get("placeOfPerformance", {})
        city = place.get("city", {}).get("name", "") if place else ""
        state = place.get("state", {}).get("code", "") if place else ""
        posted = rec.get("publishDate", "")
        deadline = rec.get("responseDeadLine", "")
        dollar = rec.get("estimatedValue", 0) or 0
        user_naics = self.profile.get("naics", [])
        user_location = self.profile.get("location_boost", [])
        clearance_required = any(x in text for x in ["secret", "top secret", "ts//", "sci", "clearance required", "security clearance", "classified"])
        if not clearance_required:
            score += 15; reasons.append("no_clearance")
        else:
            score -= 50; reasons.append("CLEARANCE_REQUIRED_DISQUALIFY")
        naics_matches = [n for n in naics_list if n in user_naics]
        if naics_matches:
            score += min(len(naics_matches) * 10, 20); reasons.append(f"naics_match_{naics_matches}")
        else:
            partial = [n for n in naics_list if any(n[:4] == u[:4] for u in user_naics)]
            if partial:
                score += 5; reasons.append(f"naics_partial_{partial}")
        if set_aside and any(sa.lower() in set_aside.lower() for sa in ["small business", "set-aside", "sb", "8(a)", "hubzone", "sdvosb", "wosb"]):
            score += 8; reasons.append("set_aside_match")
        if "sole source" in text or "only one responsible source" in text:
            score += 5; reasons.append("sole_source")
        if posted and deadline:
            try:
                p = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                d = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
                days = (d - p).days
                if days < 7:
                    score += 3; reasons.append(f"short_deadline_{days}d")
                elif days > 90:
                    score -= 2; reasons.append(f"long_deadline_{days}d")
            except:
                pass
        desc = rec.get("description", "")
        if 0 < len(desc) < 200:
            score += 4; reasons.append("vague_description")
        if 0 < dollar < 250000:
            score += 2; reasons.append("small_dollar")
        elif dollar > 5000000:
            score -= 3; reasons.append("large_dollar")
        if state in user_location or "colorado" in city.lower():
            score += 6; reasons.append("local_performance")
        it_count = sum(1 for k in ["software", "programming", "system", "data", "cloud", "kubernetes", "docker", "infrastructure"] if k in text)
        ai_count = sum(1 for k in ["ai", "artificial intelligence", "machine learning", "ml", "llm", "neural", "deep learning", "model"] if k in text)
        if it_count > 0:
            score += min(it_count, 3); reasons.append(f"it_keywords_{it_count}")
        if ai_count > 0:
            score += min(ai_count * 2, 5); reasons.append(f"ai_keywords_{ai_count}")
        if any(x in text for x in ["urgent", "emergency", "critical need", "rapid", "expedited"]):
            score += 2; reasons.append("urgent")
        if "limited competition" in text or "non-competitive" in text or "set-aside" in text:
            score += 5; reasons.append("few_bidders")
        if posted and posted.startswith("2026-08"):
            score += 2; reasons.append("very_recent")
        elif posted and posted.startswith("2026-07"):
            score += 1; reasons.append("recent")
        if "proprietary" in text or "trade secret" in text:
            score += 2; reasons.append("proprietary_scope")
        if "interdisciplinary" in text or "cross-functional" in text:
            score += 1; reasons.append("interdisciplinary")
        if "pilot" in text or "prototype" in text or "proof of concept" in text:
            score += 3; reasons.append("pilot_program")
        if self.profile.get("chaos_factor", 0) > 0.5:
            jitter = random.randint(-2, 5)
            score += jitter
            if jitter != 0:
                reasons.append(f"chaos_jitter_{jitter}")
        fillable = score > 15 and not clearance_required
        return {"score": score, "reasons": reasons, "fillable": fillable}

    def generate_capability_statement(self, rec):
        user = self.profile.get("_user", {})
        title = rec.get("title", "")
        naics = [n.get("code", "") for n in (rec.get("naics") or [])]
        orgs = [o.get("name", "") for o in (rec.get("organizationHierarchy") or [])]
        agency = orgs[0] if orgs else "the Government"
        return f"""CAPABILITY STATEMENT - {user.get('company', 'Effusion Labs LLC')}
=========================================
Contract: {rec.get("solicitationNumber", "") or rec.get("noticeId", "")}
Title: {title}
Agency: {agency}
COMPANY PROFILE:
{user.get('company', 'Effusion Labs LLC')} is a {user.get('business_size', 'small business')} in {user.get('location', 'Westminster, Colorado')}, specializing in
LLM infrastructure, GPU resource allocation, distributed systems, and data engineering.
9+ years building resilient backend systems, managing Kubernetes clusters, and
orchestrating high-throughput data pipelines (Apache Spark, Kafka, AWS Kinesis).
RELEVANT NAICS CODES:
  {', '.join(naics)} (as required)
  541511 - Custom Computer Programming Services
  541512 - Computer Systems Design Services
  541519 - Other Computer Related Services
  518210 - Data Processing, Hosting, and Related Services
CORE COMPETENCIES:
  - LLM Inference & GPU Resource Allocation (NVIDIA SMI telemetry, KV cache management)
  - Kubernetes & Docker Containerization at scale
  - Distributed Data Engineering (Spark, Kafka, Elasticsearch)
  - Prompt Security & AI Evaluation Harnesses (HackAPrompt 2025 Top-10 finisher)
  - Rust, Python, Scala, TypeScript development
PAST PERFORMANCE:
  - Charter Communications: Backend architecture for subscriber segmentation (Spark/Kafka)
  - Access Data Consulting: Real-time targeting API integration
  - Open Source: ComfyUI-TTools (github.com/toxicwind)
DIFFERENTIATORS:
  - Bare-metal LLM serving expertise (27B+ parameter models)
  - Automated memory profiling eliminating runtime OOM failures
  - Multi-agent routing with persistent file-based state
  - Small business agility with enterprise-grade reliability
"""

    def snipe_parallel(self, query, max_results=25):
        fetch = self.failfast_fetch(query, page=0, size=max_results)
        if not fetch.get("ok"):
            return []
        results = fetch.get("results", [])[:max_results]
        scored = []
        for rec in results:
            s = self.score_contract(rec)
            scored.append({"rec": rec, "score": s["score"], "reasons": s["reasons"], "fillable": s["fillable"],
                           "id": rec.get("solicitationNumber", "") or rec.get("noticeId", "")})
        scored.sort(key=lambda x: x["score"], reverse=True)
        fillable = [s for s in scored if s["fillable"]]
        for s in fillable[:5]:
            stmt = self.generate_capability_statement(s["rec"])
            safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", s["id"])[:60]
            with open(self.out / f"capability_{safe_id}.txt", "w") as fh:
                fh.write(stmt)
        return fillable

    def run(self, profile_name=None):
        if profile_name:
            self.cfg["active_profile"] = profile_name
            self.profile = self.cfg["profiles"][profile_name].copy()
            self.profile["_user"] = self.cfg["user"]
            self.profile["_routes"] = self.cfg["routes"]
            self.profile["_name"] = profile_name
            self.profile["_pat"] = self.cfg.get("github_pat", "")
        self.log(f"=== SNIPER v4.0 === Profile: {self.profile['_name']}")
        queries = self.chaos_queries()
        self.log(f"Queries: {len(queries)}")
        all_snipes = []
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = {ex.submit(self.snipe_parallel, q, self.profile.get("max_results_per_query", 25)): q for q in queries}
            for future in as_completed(futures):
                q = futures[future]
                try:
                    snipes = future.result(timeout=30)
                    all_snipes.extend(snipes)
                    self.log(f"Query \"{q}\": {len(snipes)} fillable")
                except Exception as e:
                    self.log(f"Query \"{q}\" FAILED: {e}")
        total_ms = (time.perf_counter() - t0) * 1000
        seen = set()
        unique = []
        for s in all_snipes:
            if s["id"] and s["id"] not in seen:
                seen.add(s["id"])
                unique.append(s)
        unique.sort(key=lambda x: x["score"], reverse=True)
        master = {
            "generated": datetime.now().isoformat(),
            "profile": self.profile["_name"],
            "user": self.cfg["user"]["name"],
            "company": self.cfg["user"]["company"],
            "total_queries": len(queries),
            "total_unique": len(unique),
            "total_ms": round(total_ms, 2),
            "top_20": [{"id": s["id"], "title": s["rec"].get("title", "")[:100], "score": s["score"], "reasons": s["reasons"], "deadline": s["rec"].get("responseDeadLine", "")} for s in unique[:20]]
        }
        with open(self.out / f"MASTER_{self.profile['_name'].upper()}.json", "w") as fh:
            json.dump(master, fh, indent=2)
        self.cfg["iterations"] = self.cfg.get("iterations", 0) + 1
        self.save_profile(self.cfg)
        self.log(f"=== DONE === Total: {len(unique)} | Top: {unique[0]['id'] if unique else 'N/A'}")
        return unique

#!/usr/bin/env python3
"""Contract Sniper v3.0 - Multi-Profile, Chaos, Code Stealing, Benchmarked"""
import os, sys, re, json, time, hashlib, subprocess as sp, random, string, warnings
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
warnings.filterwarnings("ignore")

PROFILE_PATH = "/mnt/agents/output/sam-autoscraper/profiles/loader.json"
OUT = Path("/mnt/agents/output/sam-autoscraper/snipes")
BENCH = Path("/mnt/agents/output/sam-autoscraper/benchmarks")
ROUTES = Path("/mnt/agents/output/sam-autoscraper/routes")
STOLEN = Path("/mnt/agents/output/sam-autoscraper/stolen")
for d in [OUT, BENCH, ROUTES, STOLEN]:
    d.mkdir(parents=True, exist_ok=True)

log_lock = Lock()
def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with log_lock:
        with open(OUT / "sniper_v3.log", "a") as fh:
            fh.write(line + "\n")

def bench(name, fn, *a, **kw):
    t0 = time.perf_counter()
    try:
        r = fn(*a, **kw)
        ok = True
        err = None
    except Exception as e:
        r = None
        ok = False
        err = str(e)
    elapsed = (time.perf_counter() - t0) * 1000
    rec = {"t": datetime.now().isoformat(), "name": name, "ms": round(elapsed, 2), "ok": ok, "error": err}
    with open(BENCH / "benchmarks.jsonl", "a") as fh:
        fh.write(json.dumps(rec) + "\n")
    return {"result": r, "ms": elapsed, "ok": ok, "error": err}

def save_route_state(route_name, data):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fp = ROUTES / f"{route_name}_{ts}.json"
    with open(fp, "w") as fh:
        json.dump(data, fh, indent=2, default=str)
    return fp

def load_profile():
    with open(PROFILE_PATH) as fh:
        cfg = json.load(fh)
    active = cfg["active_profile"]
    profile = cfg["profiles"][active].copy()
    profile["_user"] = cfg["user"]
    profile["_routes"] = cfg["routes"]
    profile["_name"] = active
    profile["_pat"] = cfg.get("github_pat", "")
    return profile, cfg

def save_profile(cfg):
    with open(PROFILE_PATH, "w") as fh:
        json.dump(cfg, fh, indent=2)

def curl_obtuse(url, method="GET", headers=None, data=None, timeout=10):
    cmd = ["curl", "-s", "-L", "--http1.1", "--compressed",
           "-w", "\nHTTP_CODE:%{http_code}\nSIZE:%{size_download}\nTIME:%{time_total}\nDNS:%{time_namelookup}\nCONN:%{time_connect}\n"]
    cmd += ["-m", str(timeout), "--connect-timeout", "2", "--max-time", str(timeout),
            "--retry", "1", "--retry-delay", "1", "--tcp-nodelay",
            "--dns-timeout", "2", "--speed-time", "3", "--speed-limit", "100"]
    uas = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    ]
    cmd += ["-A", random.choice(uas)]
    cmd += ["-H", "Accept: application/json, text/plain, */*"]
    cmd += ["-H", "Accept-Language: en-US,en;q=0.9"]
    cmd += ["-H", "Accept-Encoding: gzip, deflate, br"]
    cmd += ["-H", "DNT: 1"]
    cmd += ["-H", "Connection: keep-alive"]
    cmd += ["-H", "Upgrade-Insecure-Requests: 1"]
    cmd += ["-H", "Sec-Fetch-Dest: document"]
    cmd += ["-H", "Sec-Fetch-Mode: navigate"]
    cmd += ["-H", "Sec-Fetch-Site: none"]
    cmd += ["-H", "Cache-Control: max-age=0"]
    if headers:
        for k, v in headers.items():
            cmd += ["-H", f"{k}: {v}"]
    if method == "POST" and data:
        cmd += ["-X", "POST", "-H", "Content-Type: application/json", "-d", data]
    elif method == "HEAD":
        cmd += ["-I"]
    cmd += [url]
    t0 = time.perf_counter()
    try:
        r = sp.run(cmd, capture_output=True, text=True, timeout=timeout+3)
    except sp.TimeoutExpired:
        return {"body": "", "code": "TIMEOUT", "ms": (time.perf_counter()-t0)*1000, "cmd": " ".join(cmd[:6])}
    elapsed = (time.perf_counter() - t0) * 1000
    body = r.stdout.split("HTTP_CODE:")[0] if "HTTP_CODE:" in r.stdout else r.stdout
    code = "000"
    for line in r.stdout.split("\n"):
        if line.startswith("HTTP_CODE:"):
            code = line.split(":")[1]
    return {"body": body, "code": code, "ms": elapsed, "cmd": " ".join(cmd[:6]) + "..."}

def route_sam_api(query, page=0, size=25):
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

def route_sam_curl_post(query, page=0, size=25):
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

def route_cached(query, page=0, size=25):
    cache_path = "/mnt/agents/output/sam-dumps/library/sam_library_july2026.json"
    if not Path(cache_path).exists():
        return {"ok": False, "route": "cached", "error": "no cache"}
    lib = json.load(open(cache_path))
    matches = [r for r in lib.get("records", []) if query.lower() in (r.get("title", "") + " " + r.get("description", "")).lower()]
    return {"ok": True, "route": "cached", "results": matches, "ms": 0}

def route_github_code(query, pat, page=0, size=25):
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
                        with open(STOLEN / f"{safe_name}{ext}", "w") as fh:
                            fh.write(f"# Stolen from {repo}/{path}\n# Query: {query}\n# Lang: {lang}\n\n{code_text}")
            return {"ok": True, "route": "github_code", "results": stolen, "ms": r["ms"], "count": len(stolen)}
        except Exception as e:
            return {"ok": False, "route": "github_code", "error": str(e)}
    return {"ok": False, "route": "github_code", "error": f"HTTP {r['code']}"}

def failfast_fetch(query, profile, page=0, size=25):
    t0 = time.perf_counter()
    routes = profile.get("_routes", {})
    enabled = [(name, info) for name, info in routes.items() if info.get("enabled", False)]
    enabled.sort(key=lambda x: x[1].get("priority", 99))
    pat = profile.get("_pat", "")
    for route_name, route_info in enabled:
        route_fn = globals().get(f"route_{route_name}")
        if not route_fn:
            continue
        if route_name == "github_code":
            r = bench(f"route_{route_name}", route_fn, query, pat, page, size)
        else:
            r = bench(f"route_{route_name}", route_fn, query, page, size)
        if r["ok"] and r["result"] and r["result"].get("ok"):
            res = r["result"]
            res["total_ms"] = (time.perf_counter() - t0) * 1000
            res["benchmark_ms"] = r["ms"]
            save_route_state(route_name, {"query": query, "result": res, "ts": datetime.now().isoformat()})
            return res
        save_route_state(route_name, {"query": query, "error": r["result"].get("error", "unknown") if r["result"] else str(r["error"]), "ts": datetime.now().isoformat()})
    log(f"ALL ROUTES FAILED for \"{query}\"")
    return {"ok": False, "error": "all routes failed", "total_ms": (time.perf_counter() - t0) * 1000}

def chaos_queries(profile):
    if profile.get("chaos_factor", 0) == 0:
        return profile.get("queries", [])
    base = profile.get("queries", [])
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
    factor = profile.get("chaos_factor", 0)
    base_count = int(len(base) * (1 - factor))
    chaos_count = int(len(unique) * factor)
    final = base[:base_count] + unique[:chaos_count]
    random.shuffle(final)
    return final[:20]

def score_contract(rec, profile):
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
    user_naics = profile.get("naics", [])
    user_location = profile.get("location_boost", [])
    clearance_required = any(x in text for x in ["secret", "top secret", "ts//", "sci", "clearance required", "security clearance", "classified"])
    if not clearance_required:
        score += 15
        reasons.append("no_clearance")
    else:
        score -= 50
        reasons.append("CLEARANCE_REQUIRED_DISQUALIFY")
    naics_matches = [n for n in naics_list if n in user_naics]
    if naics_matches:
        score += min(len(naics_matches) * 10, 20)
        reasons.append(f"naics_match_{naics_matches}")
    else:
        partial = [n for n in naics_list if any(n[:4] == u[:4] for u in user_naics)]
        if partial:
            score += 5
            reasons.append(f"naics_partial_{partial}")
    if set_aside and any(sa.lower() in set_aside.lower() for sa in ["small business", "set-aside", "sb", "8(a)", "hubzone", "sdvosb", "wosb"]):
        score += 8
        reasons.append("set_aside_match")
    if "sole source" in text or "only one responsible source" in text:
        score += 5
        reasons.append("sole_source")
    if posted and deadline:
        try:
            p = datetime.fromisoformat(posted.replace("Z", "+00:00"))
            d = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
            days = (d - p).days
            if days < 7:
                score += 3
                reasons.append(f"short_deadline_{days}d")
            elif days > 90:
                score -= 2
                reasons.append(f"long_deadline_{days}d")
        except:
            pass
    desc = rec.get("description", "")
    if 0 < len(desc) < 200:
        score += 4
        reasons.append("vague_description")
    if 0 < dollar < 250000:
        score += 2
        reasons.append("small_dollar")
    elif dollar > 5000000:
        score -= 3
        reasons.append("large_dollar")
    if state in user_location or "colorado" in city.lower():
        score += 6
        reasons.append("local_performance")
    it_count = sum(1 for k in ["software", "programming", "system", "data", "cloud", "kubernetes", "docker", "infrastructure"] if k in text)
    ai_count = sum(1 for k in ["ai", "artificial intelligence", "machine learning", "ml", "llm", "neural", "deep learning", "model"] if k in text)
    if it_count > 0:
        score += min(it_count, 3)
        reasons.append(f"it_keywords_{it_count}")
    if ai_count > 0:
        score += min(ai_count * 2, 5)
        reasons.append(f"ai_keywords_{ai_count}")
    if any(x in text for x in ["urgent", "emergency", "critical need", "rapid", "expedited"]):
        score += 2
        reasons.append("urgent")
    if "limited competition" in text or "non-competitive" in text or "set-aside" in text:
        score += 5
        reasons.append("few_bidders")
    if posted and posted.startswith("2026-08"):
        score += 2
        reasons.append("very_recent")
    elif posted and posted.startswith("2026-07"):
        score += 1
        reasons.append("recent")
    if "proprietary" in text or "trade secret" in text:
        score += 2
        reasons.append("proprietary_scope")
    if "interdisciplinary" in text or "cross-functional" in text:
        score += 1
        reasons.append("interdisciplinary")
    if "pilot" in text or "prototype" in text or "proof of concept" in text:
        score += 3
        reasons.append("pilot_program")
    if profile.get("chaos_factor", 0) > 0.5:
        jitter = random.randint(-2, 5)
        score += jitter
        if jitter != 0:
            reasons.append(f"chaos_jitter_{jitter}")
    fillable = score > 15 and not clearance_required
    return {"score": score, "reasons": reasons, "fillable": fillable}

def generate_capability_statement(rec, profile):
    user = profile.get("_user", {})
    title = rec.get("title", "")
    naics = [n.get("code", "") for n in (rec.get("naics") or [])]
    orgs = [o.get("name", "") for o in (rec.get("organizationHierarchy") or [])]
    agency = orgs[0] if orgs else "the Government"
    stmt = f"""CAPABILITY STATEMENT - {user.get('company', 'Effusion Labs LLC')}
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
    return stmt

def snipe_parallel(query, profile, max_results=25):
    fetch = failfast_fetch(query, profile, page=0, size=max_results)
    if not fetch.get("ok"):
        return []
    results = fetch.get("results", [])[:max_results]
    scored = []
    for rec in results:
        s = score_contract(rec, profile)
        scored.append({"rec": rec, "score": s["score"], "reasons": s["reasons"], "fillable": s["fillable"], "id": rec.get("solicitationNumber", "") or rec.get("noticeId", "")})
    scored.sort(key=lambda x: x["score"], reverse=True)
    fillable = [s for s in scored if s["fillable"]]
    for s in fillable[:5]:
        stmt = generate_capability_statement(s["rec"], profile)
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", s["id"])[:60]
        with open(OUT / f"capability_{safe_id}.txt", "w") as fh:
            fh.write(stmt)
    return fillable

def run_profile(profile_name=None):
    profile, cfg = load_profile()
    if profile_name:
        cfg["active_profile"] = profile_name
        profile = cfg["profiles"][profile_name].copy()
        profile["_user"] = cfg["user"]
        profile["_routes"] = cfg["routes"]
        profile["_name"] = profile_name
        profile["_pat"] = cfg.get("github_pat", "")
    log(f"=== SNIPER v3.0 ===")
    log(f"Profile: {profile['_name']} | {profile.get('name', 'Unknown')}")
    log(f"Chaos factor: {profile.get('chaos_factor', 0)}")
    queries = chaos_queries(profile)
    log(f"Queries: {len(queries)}")
    all_snipes = []
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(snipe_parallel, q, profile, profile.get("max_results_per_query", 25)): q for q in queries}
        for future in as_completed(futures):
            q = futures[future]
            try:
                snipes = future.result(timeout=30)
                all_snipes.extend(snipes)
                log(f"Query \"{q}\": {len(snipes)} fillable")
            except Exception as e:
                log(f"Query \"{q}\" FAILED: {e}")
    total_ms = (time.perf_counter() - t0) * 1000
    log(f"All queries: {total_ms:.0f}ms")
    seen = set()
    unique = []
    for s in all_snipes:
        if s["id"] and s["id"] not in seen:
            seen.add(s["id"])
            unique.append(s)
    unique.sort(key=lambda x: x["score"], reverse=True)
    master = {
        "generated": datetime.now().isoformat(),
        "profile": profile["_name"],
        "profile_name": profile.get("name", ""),
        "user": cfg["user"]["name"],
        "company": cfg["user"]["company"],
        "total_queries": len(queries),
        "total_unique": len(unique),
        "total_ms": round(total_ms, 2),
        "top_20": [{"id": s["id"], "title": s["rec"].get("title", "")[:100], "score": s["score"], "reasons": s["reasons"], "deadline": s["rec"].get("responseDeadLine", "")} for s in unique[:20]]
    }
    with open(OUT / f"MASTER_{profile['_name'].upper()}.json", "w") as fh:
        json.dump(master, fh, indent=2)
    cfg["iterations"] = cfg.get("iterations", 0) + 1
    save_profile(cfg)
    log(f"=== DONE === Total: {len(unique)} | Top: {unique[0]['id'] if unique else 'N/A'} score={unique[0]['score'] if unique else 0}")
    print(f"\n=== TOP 10 ({profile['_name'].upper()}) ===")
    for i, s in enumerate(unique[:10], 1):
        print(f"{i}. [{s['score']} pts] {s['id']}")
        print(f"   {s['rec'].get('title', '')[:80]}")
        print(f"   Signals: {s['reasons']}")
        print(f"   Deadline: {s['rec'].get('responseDeadLine', 'N/A')}")
        print()
    return unique

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--profile", default="default")
    args = p.parse_args()
    run_profile(args.profile)

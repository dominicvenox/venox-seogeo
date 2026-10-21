#!/usr/bin/env python3
"""Plan/capture/import AI observations and produce auditable summaries/report drafts.

Python 3.10+, standard library. No paid calls without collect --live.
"""
import argparse
from collections import Counter, defaultdict
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

METHODS = {"consumer_ui", "serp_capture", "api_proxy"}
STATUSES = {"ok", "no_feature", "error"}
PROVIDERS = {"openai": "OPENAI_API_KEY", "perplexity": "PERPLEXITY_API_KEY", "gemini": "GEMINI_API_KEY"}
KEYS = ("surface", "method", "model", "country", "language", "context", "search_mode", "cohort", "portfolio_hash")


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:20]


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def host(value):
    return (urllib.parse.urlsplit(value if "://" in value else "https://" + value).hostname or "").lower().rstrip(".").encode("idna").decode()


def owned(url, domains):
    h = host(url)
    return any(h == host(d) or h.endswith("." + host(d)) for d in domains)


def mentioned(text, aliases):
    return any(re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", text, re.I) for alias in aliases if alias.strip())


def wrapped(url):
    h = host(url)
    return h == "vertexaisearch.cloud.google.com" or "grounding-api" in h


def config(path):
    c = read_json(path)
    if c.get("schema_version") != 1 or not c.get("client_id"):
        raise ValueError("project.json needs schema_version=1 and client_id")
    if not c.get("brands") or c.get("target_brand") not in c["brands"]:
        raise ValueError("target_brand must exist in brands")
    for name, brand in c["brands"].items():
        if not brand.get("aliases") or not all(isinstance(a, str) and a.strip() for a in brand["aliases"]):
            raise ValueError(f"Brand {name} needs nonempty aliases")
        if not brand.get("domains") or not all(host(d) for d in brand["domains"]):
            raise ValueError(f"Brand {name} needs valid domains")
    prompts = c.get("prompts", [])
    if not prompts or len({p["id"] for p in prompts}) != len(prompts):
        raise ValueError("Prompts need unique IDs and at least one prompt")
    for p in prompts:
        if not p.get("text", "").strip() or p.get("cohort") not in {"core", "control", "exploratory"}:
            raise ValueError("Each prompt needs text and core/control/exploratory cohort")
    if not isinstance(c.get("repeats"), int) or isinstance(c["repeats"], bool) or not 1 <= c["repeats"] <= 20:
        raise ValueError("repeats must be 1..20")
    # Exclude live-provider config: imported product/model are captured per observation.
    c["portfolio_hash"] = digest({k: c.get(k) for k in
        ("schema_version", "client_id", "portfolio_version", "brands", "target_brand", "prompts", "repeats", "country", "language", "timezone", "max_output_tokens")})
    return c


def initialize(args):
    args.out.mkdir(parents=True, exist_ok=False)
    c = {
        "schema_version": 1, "client_id": host(args.domain), "portfolio_version": "1",
        "target_brand": args.brand, "brands": {args.brand: {"aliases": [args.brand], "domains": [host(args.domain)]}},
        "country": "DE", "language": "de", "timezone": "Europe/Berlin", "repeats": 3,
        "max_requests": 120, "max_output_tokens": 3000,
        "providers": {p: {"enabled": False, "model": "", "search_mode": "auto"} for p in PROVIDERS},
        "prompts": [
            {"id": "core-1", "cohort": "core", "text": f"Welche {args.category} eignen sich für kleine Unternehmen in Deutschland?"},
            {"id": "core-2", "cohort": "core", "text": f"Worauf sollte ich bei der Auswahl von {args.category} achten?"},
            {"id": "core-3", "cohort": "core", "text": f"Was kosten {args.category} und welche laufenden Gebühren gibt es?"},
            {"id": "control-brand", "cohort": "control", "text": f"Was ist {args.brand} und für wen eignet sich das Angebot?"},
            {"id": "control-negative", "cohort": "control", "text": "Wie funktioniert die Photosynthese?"},
        ], "setup_note": "Starter prompts only: adapt to native buyer demand; add fixed competitors; verify model IDs and costs before enabling APIs."
    }
    write_json(args.out / "project.json", c)
    print(f"Created {args.out / 'project.json'}; providers disabled, no network calls")


def urls(items):
    return sorted({x.get("url") for x in items if isinstance(x, dict) and isinstance(x.get("url"), str)})


def parse_response(provider, data):
    """Return observed fields; unknown citation coverage is null, not zero."""
    answer, citations, sources = [], [], []
    search, citation_coverage, queries = False, True, []
    if provider in {"openai", "perplexity"}:
        if data.get("status") not in (None, "completed") or data.get("error"):
            raise ValueError("Provider response did not complete successfully")
        if not isinstance(data.get("output"), list):
            raise ValueError("Provider response missing output array")
        source_observed = False
        for item in data["output"]:
            if item.get("type") == "message":
                for part in item.get("content", []):
                    if part.get("type") == "output_text":
                        answer.append(part.get("text", ""))
                        citations.extend(a for a in part.get("annotations", []) if a.get("type") == "url_citation")
            elif item.get("type") == "web_search_call":
                if item.get("status") not in (None, "completed"):
                    raise ValueError("Web search call did not complete")
                search = True
                action = item.get("action", {})
                if "sources" in action:
                    source_observed = True
                    sources.extend(action["sources"])
                queries.extend(action.get("queries", []) or ([action["query"]] if action.get("query") else []))
            elif item.get("type") == "search_results":
                search, source_observed = True, True
                sources.extend(item.get("results", item.get("contents", [])))
                queries.extend(item.get("queries", []))
        # Perplexity search results aren't necessarily visible citations. Explicit
        # URL annotations are observable; absent annotations imply unknown coverage.
        if provider == "perplexity" and not citations:
            citation_coverage = False
        sources = urls(sources) if source_observed else None
        citations = urls(citations) if citation_coverage else None
    else:
        candidate = (data.get("candidates") or [{}])[0]
        if candidate.get("finishReason") not in (None, "STOP"):
            raise ValueError("Gemini response did not finish normally")
        answer = [p.get("text", "") for p in candidate.get("content", {}).get("parts", []) if not p.get("thought")]
        g = candidate.get("groundingMetadata")
        if g is None:
            sources, citations = None, None
        else:
            queries = g.get("webSearchQueries", [])
            chunks = g.get("groundingChunks", [])
            sources = [x["web"]["uri"] for x in chunks if x.get("web", {}).get("uri")]
            search = bool(queries or chunks)
            if "groundingSupports" not in g:
                citations = None
            else:
                citations = sorted({chunks[i]["web"]["uri"] for s in g["groundingSupports"]
                    for i in s.get("groundingChunkIndices", []) if isinstance(i, int) and 0 <= i < len(chunks) and chunks[i].get("web", {}).get("uri")})
                # Google grounding redirects hide destination domains. Leave citation
                # classification unknown until a verified resolution/import step.
                if any(wrapped(u) for u in citations):
                    citations = None
    text = "\n".join(answer).strip()
    if not text:
        raise ValueError("No nonempty answer returned; not a valid negative observation")
    return {"answer": text, "citations": citations, "retrieved_sources": sources,
            "search_triggered": search, "queries": queries}


def request_spec(provider, pc, c, prompt):
    model = pc["model"]
    if not re.fullmatch(r"[a-zA-Z0-9._:/-]+", model):
        raise ValueError("Invalid model identifier")
    if provider == "openai":
        if pc.get("search_mode", "auto") not in {"auto", "required"}:
            raise ValueError("OpenAI search_mode must be auto or required")
        tool = {"type": "web_search", "user_location": {"type": "approximate", "country": c["country"]}}
        body = {"model": model, "input": prompt, "tools": [tool], "include": ["web_search_call.action.sources"],
                "max_output_tokens": c["max_output_tokens"], "store": False,
                "tool_choice": "required" if pc.get("search_mode") == "required" else "auto"}
        return "https://api.openai.com/v1/responses", body
    if provider == "perplexity":
        if pc.get("search_mode", "auto") != "auto":
            raise ValueError("Perplexity adapter supports search_mode=auto only")
        return "https://api.perplexity.ai/v1/agent", {"model": model, "input": prompt,
            "tools": [{"type": "web_search", "user_location": {"country": c["country"]}}], "max_output_tokens": c["max_output_tokens"]}
    if pc.get("search_mode", "auto") != "auto":
        raise ValueError("Gemini adapter supports search_mode=auto only")
    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/" + urllib.parse.quote(model, safe="") + ":generateContent"
    return endpoint, {"contents": [{"parts": [{"text": prompt}]}], "tools": [{"google_search": {}}],
                      "generationConfig": {"maxOutputTokens": c["max_output_tokens"]}}


def call(provider, endpoint, body):
    key = os.environ[PROVIDERS[provider]]
    headers = {"Content-Type": "application/json"}
    headers["x-goog-api-key" if provider == "gemini" else "Authorization"] = key if provider == "gemini" else "Bearer " + key
    req = urllib.request.Request(endpoint, data=json.dumps(body).encode(), headers=headers, method="POST")
    # No retries: a timeout may still have incurred provider cost.
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        # Avoid logging provider bodies that may echo user credentials or payloads.
        raise ValueError(f"Provider HTTP {exc.code}; inspect account status privately, no automatic retry") from None
    except urllib.error.URLError:
        raise ValueError("Provider network error; billing outcome unknown, no automatic retry") from None


def normalize(raw, c):
    p = next((p for p in c["prompts"] if p["id"] == raw.get("prompt_id")), None)
    if not p:
        raise ValueError("Unknown prompt_id; do not mix portfolios")
    for key in ("id", "surface", "model", "country", "language", "context", "search_mode", "captured_at", "artifact"):
        if not isinstance(raw.get(key), str) or not raw[key].strip():
            raise ValueError(f"Missing observation field: {key}")
    dt.datetime.fromisoformat(raw["captured_at"].replace("Z", "+00:00"))
    if not re.search(r"(Z|[+-]\d\d:\d\d)$", raw["captured_at"]):
        raise ValueError("captured_at requires timezone")
    if raw.get("method") not in METHODS or raw.get("status") not in STATUSES:
        raise ValueError("Invalid observation method/status")
    if raw["country"] != c["country"] or raw["language"] != p.get("language", c["language"]):
        raise ValueError("Observation market/language differs from project prompt")
    if not isinstance(raw.get("repeat"), int) or isinstance(raw["repeat"], bool) or raw["repeat"] < 1:
        raise ValueError("repeat must be a positive integer")
    if raw.get("search_triggered") is not None and not isinstance(raw["search_triggered"], bool):
        raise ValueError("search_triggered must be bool/null")
    for key in ("citations", "retrieved_sources"):
        if key not in raw:
            raise ValueError(f"{key} required; use null when unknown")
        if raw[key] is not None and (not isinstance(raw[key], list) or any(not isinstance(u, str) or urllib.parse.urlsplit(u).scheme not in {"http", "https"} for u in raw[key])):
            raise ValueError(f"{key} must be HTTP(S) URL list or null")
    if raw["status"] == "ok" and not str(raw.get("answer", "")).strip():
        raise ValueError("Successful observations need an answer")
    if raw["status"] == "error" and not raw.get("error"):
        raise ValueError("Failed observations need an error explanation")
    if raw["status"] == "no_feature" and (raw.get("answer") or raw["citations"] != [] or raw.get("search_triggered") is not False):
        raise ValueError("no_feature requires empty answer/citations and search_triggered=false")
    recommendation = raw.get("recommendation")
    if recommendation not in {None, "recommended", "neutral", "hedged", "against"}:
        raise ValueError("Invalid adjudicated recommendation")
    if recommendation is not None and not raw.get("recommendation_evidence"):
        raise ValueError("Recommendation judgment requires recommendation_evidence")
    record = {**raw, "schema_version": 1, "client_id": c["client_id"], "portfolio_hash": c["portfolio_hash"],
              "cohort": p["cohort"], "prompt_text": p["text"], "prompt_hash": digest(p["text"])}
    for field in ("citations", "retrieved_sources"):
        if record[field] is not None and any(wrapped(u) for u in record[field]):
            record["unresolved_" + field] = record[field]
            record[field] = None
    record["brand_mentions"] = {name: mentioned(raw.get("answer", ""), b["aliases"]) for name, b in c["brands"].items()}
    record["brand_citations"] = {name: None if record["citations"] is None else any(owned(u, b["domains"]) for u in record["citations"]) for name, b in c["brands"].items()}
    record["brand_retrieved"] = {name: None if record["retrieved_sources"] is None else any(owned(u, b["domains"]) for u in record["retrieved_sources"]) for name, b in c["brands"].items()}
    return record


def collect(args):
    c = config(args.config)
    providers = [(p, pc) for p, pc in c.get("providers", {}).items() if pc.get("enabled")]
    if any(p not in PROVIDERS for p, _ in providers):
        raise ValueError("Unsupported live provider; use normalized import")
    plan = [(p, pc, prompt, repeat) for p, pc in providers for prompt in c["prompts"] for repeat in range(1, c["repeats"] + 1)]
    cap = c.get("max_requests", 0)
    if not isinstance(cap, int) or isinstance(cap, bool) or cap < 1 or len(plan) > cap:
        raise ValueError(f"Planned {len(plan)} requests exceed configured cap {cap}")
    if args.live:
        if not providers:
            raise ValueError("No enabled providers; configure model IDs and credentials first")
        for provider, pc in providers:
            if not pc.get("model") or not os.environ.get(PROVIDERS[provider]):
                raise ValueError(f"{provider}: model and {PROVIDERS[provider]} required")
            request_spec(provider, pc, c, c["prompts"][0]["text"])
    args.out.mkdir(parents=True, exist_ok=False)
    write_json(args.out / "project_snapshot.json", c)
    write_json(args.out / "plan.json", {"created_at": now(), "live": args.live, "client_id": c["client_id"],
        "portfolio_hash": c["portfolio_hash"], "requests": len(plan), "max_requests": cap,
        "providers": [p for p, _ in providers], "money_limit": "not enforced; use provider spending controls",
        "note": "API proxy only; Gemini country is capture context, not enforced by generateContent grounding"})
    if not args.live:
        print(f"Plan saved: {len(plan)} requests, no network calls; providers must be explicitly enabled")
        return
    (args.out / "raw").mkdir()
    with (args.out / "observations.jsonl").open("x", encoding="utf-8") as out:
        for provider, pc, prompt, repeat in plan:
            task = digest([provider, prompt["id"], repeat])
            endpoint, body = request_spec(provider, pc, c, prompt["text"])
            artifact = f"raw/{task}.json"
            raw = {"id": task, "prompt_id": prompt["id"], "repeat": repeat, "surface": provider + "-api",
                "method": "api_proxy", "model": pc["model"], "country": c["country"], "language": prompt.get("language", c["language"]),
                "context": "stateless API; no consumer account/device; " + ("country not enforced" if provider == "gemini" else "approximate country"),
                "search_mode": pc.get("search_mode", "auto"), "captured_at": now(), "artifact": artifact,
                "recommendation": None, "status": "ok", "answer": "", "citations": None, "retrieved_sources": None, "search_triggered": None}
            evidence = {"provider": provider, "endpoint": endpoint, "request": body, "captured_at": raw["captured_at"]}
            try:
                data = call(provider, endpoint, body)
                evidence["response"] = data
                raw.update(parse_response(provider, data))
                raw["requested_model"] = pc["model"]
                raw["returned_model"] = data.get("model", data.get("modelVersion"))
                raw["model"] = raw["returned_model"] or pc["model"]
            except (ValueError, OSError, TimeoutError) as exc:
                raw.update(status="error", error=str(exc))
                evidence["error"] = str(exc)
            write_json(args.out / artifact, evidence)
            out.write(json.dumps(normalize(raw, c), ensure_ascii=False) + "\n")
            out.flush()
            if raw["status"] == "error":
                print("Stopped after provider failure; remaining requests not sent; inspect saved evidence", file=sys.stderr)
                break
    print(f"Captured observations: {args.out / 'observations.jsonl'}")


def import_captures(args):
    c = config(args.config)
    rows = [normalize(row, c) for row in jsonl(args.input)]
    validate_rows(rows, c)
    evidence = []
    for row in rows:
        path = Path(row["artifact"])
        if not path.is_absolute():
            path = args.input.parent / path
        if not path.is_file():
            raise ValueError(f"Missing raw evidence for {row['id']}")
        evidence.append(path)
    args.out.mkdir(parents=True, exist_ok=False)
    write_json(args.out / "project_snapshot.json", c)
    (args.out / "raw").mkdir()
    for i, (row, path) in enumerate(zip(rows, evidence), 1):
        dest = f"raw/{i}{path.suffix}"
        shutil.copyfile(path, args.out / dest)
        row["artifact"] = dest
    with (args.out / "observations.jsonl").open("x", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Imported {len(rows)} captures; preserved evidence in {args.out}")


def validate_rows(rows, c):
    if not rows:
        raise ValueError("No observations supplied; missing data is not a zero-visibility baseline")
    ids, captures = set(), set()
    for row in rows:
        if row.get("portfolio_hash") != c["portfolio_hash"] or row.get("client_id") != c["client_id"]:
            raise ValueError("Observation/config mismatch: use the original configuration or re-import explicitly")
        key = tuple(row.get(k) for k in KEYS) + (row["prompt_id"], row["repeat"])
        if row["id"] in ids or key in captures:
            raise ValueError("Duplicate observation ID or prompt/repeat/context; refusing denominator inflation")
        ids.add(row["id"])
        captures.add(key)


def rate(values):
    valid = [v for v in values if v is not None]
    n, k = len(valid), sum(bool(v) for v in valid)
    if not n:
        return {"k": 0, "n": 0, "rate": None, "wilson95_descriptive": None}
    p, z = k / n, 1.959963984540054
    center = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / (1 + z * z / n)
    return {"k": k, "n": n, "rate": p, "wilson95_descriptive": [max(0, center - half), min(1, center + half)]}


def summarize_rows(rows, c):
    validate_rows(rows, c)
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row.get(k) for k in KEYS)].append(row)
    summaries = []
    for key, group in sorted(groups.items()):
        good = [r for r in group if r["status"] in {"ok", "no_feature"}]
        target = c["target_brand"]
        counts = Counter(r["prompt_id"] for r in good)
        expected_prompts = sorted(p["id"] for p in c["prompts"] if p["cohort"] == group[0]["cohort"] and p.get("language", c["language"]) == group[0]["language"])
        expected = len(expected_prompts) * c["repeats"]
        mention_incidences = {name: sum(r["brand_mentions"][name] for r in good) for name in c["brands"]}
        denominator = sum(mention_incidences.values())
        brands = {name: {"mention": rate([r["brand_mentions"][name] for r in good]),
                  "citation": rate([r["brand_citations"][name] for r in good]),
                  "retrieved": rate([r["brand_retrieved"][name] for r in good]),
                  "mention_sov": mention_incidences[name] / denominator if denominator and len(c["brands"]) > 1 else None} for name in c["brands"]}
        summaries.append({"key": dict(zip(KEYS, key)), "key_hash": digest(key), "captured": len(group), "successful": len(good),
            "errors": len(group) - len(good), "no_feature": sum(r["status"] == "no_feature" for r in good),
            "expected": expected, "missing": max(0, expected - len(good)), "distinct_prompts": len(counts),
            "per_prompt_n": dict(counts), "expected_prompt_ids": expected_prompts,
            "balanced_complete": set(counts) == set(expected_prompts) and all(counts[p] == c["repeats"] for p in expected_prompts),
            "brands": brands, "search_trigger": rate([r.get("search_triggered") for r in good]),
            "citation_when_search_triggered": rate([r["brand_citations"][target] for r in good if r.get("search_triggered") is True]),
            "recommendation": rate([None if r.get("recommendation") is None else r["recommendation"] == "recommended" for r in good]),
            "recommendation_counts": dict(Counter(r["recommendation"] for r in good if r.get("recommendation") is not None)),
            "capture_start": min(group, key=lambda r: dt.datetime.fromisoformat(r["captured_at"].replace("Z", "+00:00")))["captured_at"],
            "capture_end": max(group, key=lambda r: dt.datetime.fromisoformat(r["captured_at"].replace("Z", "+00:00")))["captured_at"],
            "warnings": (["Incomplete/uneven repeats: micro-rates may be biased; no automatic prior delta"] if not (set(counts) == set(expected_prompts) and all(counts[p] == c["repeats"] for p in expected_prompts)) else [])})
    return {"schema_version": 1, "created_at": now(), "client_id": c["client_id"], "target_brand": c["target_brand"],
        "portfolio_hash": c["portfolio_hash"], "groups": summaries,
        "interpretation": "Descriptive panel micro-rates; repeated prompts are clustered, not independent users. API proxies are not consumer rankings."}


def summarize(args):
    c = config(args.config)
    rows = jsonl(args.input)
    # Revalidate source records and recompute lexical flags rather than trusting edits.
    normalized = []
    for row in rows:
        if row.get("portfolio_hash") != c["portfolio_hash"]:
            raise ValueError("Portfolio changed since capture; preserve original configuration")
        normalized.append(normalize(row, c))
        if not (args.input.parent / row["artifact"]).is_file():
            raise ValueError("Raw evidence is missing")
    summary = summarize_rows(normalized, c)
    summary["observations_file"] = str(args.input.resolve())
    plan_path = args.input.parent / "plan.json"
    summary["capture_plan"] = read_json(plan_path) if plan_path.is_file() else None
    if summary["capture_plan"]:
        summary["capture_plan"]["observations_saved"] = len(normalized)
        summary["capture_plan"]["not_attempted"] = max(0, summary["capture_plan"]["requests"] - len(normalized))
    summary["reporting_period"] = None
    if args.period_start or args.period_end or args.complete:
        if not args.period_start or not args.period_end:
            raise ValueError("Period comparisons need --period-start and --period-end")
        start, end = dt.date.fromisoformat(args.period_start), dt.date.fromisoformat(args.period_end)
        if start > end:
            raise ValueError("Reporting period ends before it starts")
        zone = ZoneInfo(c["timezone"])
        if args.complete and end >= dt.datetime.now(zone).date():
            raise ValueError("A complete reporting period must have ended before today in its timezone")
        if any(not start <= dt.datetime.fromisoformat(r["captured_at"].replace("Z", "+00:00")).astimezone(zone).date() <= end for r in normalized):
            raise ValueError("Capture outside reporting period in configured timezone")
        summary["reporting_period"] = {"start": args.period_start, "end": args.period_end,
                                       "timezone": c["timezone"], "complete": args.complete}
    write_json(args.out, summary)
    print(f"Saved {len(summary['groups'])} separate measurement groups")


def fmt_rate(r):
    return "n/a (n=0)" if r["rate"] is None else f"{100 * r['rate']:.1f}% ({r['k']}/{r['n']})"


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def metrics_table(current, previous):
    for records in (current, previous):
        if not isinstance(records, list) or len({r["id"] for r in records}) != len(records):
            raise ValueError("Metrics must be a list with unique IDs")
        for r in records:
            for key in ("id", "value", "unit", "source", "artifact", "start", "end", "timezone", "complete", "dimensions", "definition_version"):
                if key not in r:
                    raise ValueError(f"Metric {r.get('id')} missing {key}")
            if r["value"] is not None and (not isinstance(r["value"], (float, int)) or isinstance(r["value"], bool) or not math.isfinite(r["value"])):
                raise ValueError("Metric value must be a finite number or null")
            if dt.date.fromisoformat(r["end"]) < dt.date.fromisoformat(r["start"]):
                raise ValueError("Metric date range is reversed")
    prior = {r["id"]: r for r in previous}
    lines = ["| Kennzahl | Zeitraum / Quelle | Aktuell | Vorher | Änderung |", "|---|---|---:|---:|---|"]
    for r in current:
        p = prior.get(r["id"])
        start, end = dt.date.fromisoformat(r["start"]), dt.date.fromisoformat(r["end"])
        comparable = bool(p and r.get("complete") is True and p.get("complete") is True
            and all(r.get(k) == p.get(k) for k in ("unit", "source", "dimensions", "definition_version", "timezone"))
            and (end - start) == (dt.date.fromisoformat(p["end"]) - dt.date.fromisoformat(p["start"]))
            and start == dt.date.fromisoformat(p["end"]) + dt.timedelta(days=1))
        value, pv = r.get("value"), p.get("value") if p else None
        delta = "n/a – nicht vergleichbar/fehlend"
        if comparable and isinstance(value, (int, float)) and isinstance(pv, (int, float)):
            change = value - pv
            delta = f"{change:+.2f} {r['unit']}" + (f" ({100 * change / pv:+.1f}%)" if pv else " (relative Änderung n/a bei Basis 0)")
        lines.append(f"| {cell(r['id'])} | {cell(r['start'])}–{cell(r['end'])}; {cell(r['source'])}; {cell(r.get('artifact', 'Beleg fehlt'))} | {cell(value) if value is not None else 'n/a'} | {cell(pv) if pv is not None else 'n/a'} | {cell(delta)} |")
    return lines


def periods_comparable(current, previous):
    if not current or not previous or current.get("complete") is not True or previous.get("complete") is not True:
        return False
    start, end = dt.date.fromisoformat(current["start"]), dt.date.fromisoformat(current["end"])
    ps, pe = dt.date.fromisoformat(previous["start"]), dt.date.fromisoformat(previous["end"])
    return current["timezone"] == previous["timezone"] and end - start == pe - ps and start == pe + dt.timedelta(days=1)


def report(args):
    c = read_json(args.current)
    previous = read_json(args.previous) if args.previous else {"groups": []}
    if args.previous and c["client_id"] != previous.get("client_id"):
        raise ValueError("Cannot compare different clients")
    prior = {g["key_hash"]: g for g in previous["groups"]}
    period_match = periods_comparable(c.get("reporting_period"), previous.get("reporting_period"))
    lines = [f"# SEO/GEO-Wochenreport: {c['client_id']}", "", f"Erstellt: {now()}", "",
        "## Datenbasis", "", f"Portfolio: `{c['portfolio_hash']}`. {c['interpretation']}", "",
        f"Berichtszeitraum: {c.get('reporting_period') or 'nicht angegeben; keine automatischen Zeitdeltas'}. Vergleichbare vollständige Vorperiode: {'ja' if period_match else 'nein'}.", "",
        "## KI-Sichtbarkeit", "", "Alle Raten zeigen Treffer/Beobachtungen. Kontrollen und API-Proxys sind eigene Gruppen.", ""]
    if c.get("capture_plan"):
        plan = c["capture_plan"]
        lines += [f"Laufplan: {plan['requests']} API-Anfragen für {', '.join(plan['providers'])}; {plan['observations_saved']} Beobachtungen gespeichert, {plan['not_attempted']} nicht versucht. Nicht versuchte Oberflächen können unten vollständig fehlen.", ""]
    for g in c["groups"]:
        k = g["key"]
        p = prior.get(g["key_hash"])
        b = g["brands"][c["target_brand"]]
        lines += [f"### {cell(k['surface'])} · {cell(k['method'])} · {cell(k['model'])} · {cell(k['country'])}/{cell(k['language'])} · {cell(k['cohort'])}", "",
            f"Kontext: {cell(k['context'])}; Suchmodus: {cell(k['search_mode'])}.", "",
            f"Captures: {g['capture_start']} bis {g['capture_end']}. {g['distinct_prompts']} Intents; {g['successful']}/{g['expected']} geplant erfolgreich; {g['errors']} Fehler; {g['missing']} fehlend; {g['no_feature']} ohne Feature.", "",
            "| Metrik | Aktuell | Vorher | Änderung |", "|---|---:|---:|---|"]
        for label, metric in (("Brand-Mention (lexikalisch)", "mention"), ("Domain-Zitation", "citation"), ("Retrieval-Präsenz", "retrieved")):
            current = b[metric]
            old = p["brands"][c["target_brand"]][metric] if p else None
            delta = "n/a"
            if old and period_match and g["balanced_complete"] and p["balanced_complete"] and current["n"] == g["successful"] and old["n"] == p["successful"] and current["n"] == old["n"] and current["rate"] is not None and old["rate"] is not None:
                delta = f"{100 * (current['rate'] - old['rate']):+.1f} pp (deskriptiv)"
            lines.append(f"| {label} | {fmt_rate(current)} | {fmt_rate(old) if old else 'n/a'} | {delta} |")
        sov = b["mention_sov"]
        lines += ["", f"Mention-SoV im festgelegten Brand-Set: {100 * sov:.1f}%." if sov is not None else "Mention-SoV: n/a (keine Brand-Inzidenzen oder kein Wettbewerber-Set).",
            f"Suche/Feature beobachtet: {fmt_rate(g['search_trigger'])}; Ziel-Domain zitiert bedingt auf Suche/Feature: {fmt_rate(g['citation_when_search_triggered'])}.",
            f"Manuell beurteilte Empfehlung: {fmt_rate(g['recommendation'])}; Verteilung: {g['recommendation_counts']}.",
            "Unsicherheit: kleine Panels und Wiederholungen je Intent erlauben keine kausale oder unabhängige Signifikanzbehauptung.", ""]
        lines += ["- " + w for w in g["warnings"]]
        if not p:
            lines += ["Kein identisches Vorperioden-Panel: Baseline bzw. Methodenwechsel, kein automatischer Delta.", ""]
        elif not period_match:
            lines += ["Vorperioden-Zeitfenster fehlt/ist nicht vergleichbar: keine automatische Veränderungsangabe.", ""]
    missing_groups = [g for g in previous["groups"] if g["key_hash"] not in {x["key_hash"] for x in c["groups"]}]
    if missing_groups:
        lines += ["## Fehlende oder methodisch veränderte Messgruppen", "",
            "Für folgende Vorperioden-Gruppen liegen keine identischen aktuellen Beobachtungen vor. Das ist eine Datenlücke oder ein Methodenwechsel, kein gemessener Sichtbarkeitsverlust. Fehlerursache und erwartetes Panel prüfen; Raten und Deltas bleiben n/a.", ""]
        for g in missing_groups:
            k = g["key"]
            lines += [f"- {cell(k['surface'])} / {cell(k['method'])} / {cell(k['model'])} / {cell(k['country'])}-{cell(k['language'])} / {cell(k['cohort'])}: aktuell keine Beobachtung, Vorperiode {g['successful']} erfolgreich."]
        lines += [""]
    lines += ["## SEO und Geschäftsergebnisse", ""]
    if args.metrics:
        lines += metrics_table(read_json(args.metrics), read_json(args.previous_metrics) if args.previous_metrics else [])
    else:
        lines += ["Keine First-Party-Kennzahlen übergeben. GSC, Bing, GA4 und CRM wurden durch dieses Hilfsprogramm nicht abgefragt."]
    lines += ["", "## Einordnung und geprüfte Änderungen", "", "Entwurf: Der ausführende Agent ergänzt belegte Erkenntnisse, tatsächliche Änderungen und deren Verifikations-/Release-Status aus den Artefakten. Ohne diese Prüfung ist dies kein fertig geprüfter Kundenreport.", "",
        "## Nächste Schritte", "", "Entwurf: Aus bestätigten Findings konkrete Maßnahmen, Priorität, Verifikation und Beobachtungsdatum ableiten. Keine Verbesserung oder Umsetzung allein aus diesem Tabellengenerator behaupten.", ""]
    with args.out.open("x", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Report draft: {args.out}; editorial evidence review required")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("init")
    for key in ("domain", "brand", "category"):
        p.add_argument("--" + key, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.set_defaults(run=initialize)
    for name, function in (("collect", collect), ("import", import_captures), ("summarize", summarize)):
        p = sub.add_parser(name)
        p.add_argument("--config", type=Path, required=True)
        p.add_argument("--out", type=Path, required=True)
        if name == "collect":
            p.add_argument("--live", action="store_true")
        else:
            p.add_argument("--input", type=Path, required=True)
        if name == "summarize":
            p.add_argument("--period-start")
            p.add_argument("--period-end")
            p.add_argument("--complete", action="store_true", help="Reporting window is complete, not preliminary")
        p.set_defaults(run=function)
    p = sub.add_parser("report")
    p.add_argument("--current", type=Path, required=True)
    p.add_argument("--previous", type=Path)
    p.add_argument("--metrics", type=Path)
    p.add_argument("--previous-metrics", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.set_defaults(run=report)
    args = ap.parse_args()
    try:
        args.run(args)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        ap.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()

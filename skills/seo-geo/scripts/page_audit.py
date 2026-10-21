#!/usr/bin/env python3
"""Bounded initial-HTML evidence capture. Python 3.10+, standard library only."""
import argparse
import datetime as dt
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

MAX_BYTES = 5_000_000


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = []
        self.headings = []
        self.meta = []
        self.links = []
        self.schemas = []
        self.schema_errors = []
        self.schema_markup = {"microdata": False, "rdfa": False}
        self._title = False
        self._heading = None
        self._json = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self._title = True
        if tag in ("h1", "h2", "h3"):
            self._heading = {"tag": tag, "text": ""}
        if tag == "meta":
            self.meta.append(a)
        if tag == "link":
            self.links.append(a)
        if "itemscope" in a or "itemtype" in a:
            self.schema_markup["microdata"] = True
        if "typeof" in a or "vocab" in a:
            self.schema_markup["rdfa"] = True
        if tag == "script" and a.get("type", "").lower().split(";")[0].strip() == "application/ld+json":
            self._json = []

    def handle_data(self, data):
        if self._title:
            self.title.append(data)
        if self._heading is not None:
            self._heading["text"] += data
        if self._json is not None:
            self._json.append(data)

    def handle_endtag(self, tag):
        if tag == "title":
            self._title = False
        if self._heading is not None and tag == self._heading["tag"]:
            self._heading["text"] = " ".join(self._heading["text"].split())
            self.headings.append(self._heading)
            self._heading = None
        if tag == "script" and self._json is not None:
            raw = "".join(self._json)
            try:
                self.schemas.append(json.loads(raw))
            except json.JSONDecodeError as exc:
                self.schema_errors.append(str(exc))
            self._json = None


def schema_types(value):
    found = set()
    if isinstance(value, list):
        for item in value:
            found.update(schema_types(item))
    elif isinstance(value, dict):
        types = value.get("@type", [])
        if isinstance(types, str):
            types = [types]
        found.update(t for t in types if isinstance(t, str))
        for v in value.values():
            if isinstance(v, (dict, list)):
                found.update(schema_types(v))
    return sorted(found)


def parse_html(html, base_url):
    page = Page()
    page.feed(html)
    return {
        "title": " ".join("".join(page.title).split()),
        "descriptions": [m.get("content", "") for m in page.meta if m.get("name", "").lower() == "description"],
        "robots_meta": [m for m in page.meta if m.get("name", "").lower() in ("robots", "googlebot", "bingbot")],
        "canonicals": [urllib.parse.urljoin(base_url, l.get("href", "")) for l in page.links if "canonical" in l.get("rel", "").lower().split()],
        "hreflang": [l for l in page.links if "hreflang" in l],
        "headings": page.headings,
        "json_ld": page.schemas,
        "json_ld_types": schema_types(page.schemas),
        "json_ld_parse_errors": page.schema_errors,
        "other_schema_markup_detected": page.schema_markup,
        "scope": "initial HTML only; no rendered DOM, index status or schema eligibility validation",
    }


def fetch(url):
    if urllib.parse.urlsplit(url).scheme not in ("https", "http"):
        raise ValueError("Only HTTP(S) URLs are supported")
    req = urllib.request.Request(url, headers={"User-Agent": "SEO-GEO-Evidence/1.0", "Accept": "text/html,text/plain,*/*;q=0.5"})
    try:
        response = urllib.request.urlopen(req, timeout=30)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise ValueError("Response exceeds 5 MB evidence limit")
        charset = response.headers.get_content_charset() or "utf-8"
        return {"requested_url": url, "final_url": response.geturl(), "status": response.code,
                "headers": list(response.headers.items()), "captured_at": now(),
                "body": body.decode(charset, errors="replace")}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", action="append", required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if len(args.url) > 20:
        ap.error("Maximum 20 explicit page URLs per run")
    args.out.mkdir(parents=True, exist_ok=False)
    reports, robots_cache = [], {}
    for i, url in enumerate(args.url, 1):
        record = {"requested_url": url, "captured_at": now()}
        try:
            data = fetch(url)
            html = data.pop("body")
            artifact = f"page-{i}.html"
            (args.out / artifact).write_text(html, encoding="utf-8")
            record.update(data)
            record["artifact"] = artifact
            record["sha256"] = hashlib.sha256(html.encode()).hexdigest()
            content_type = next((v for k, v in data["headers"] if k.lower() == "content-type"), "")
            if "html" in content_type.lower():
                record["extracted"] = parse_html(html, data["final_url"])
            else:
                record["extraction_note"] = f"Not parsed as HTML: {content_type or 'unknown content type'}"
            parts = urllib.parse.urlsplit(data["final_url"])
            origin = f"{parts.scheme}://{parts.netloc}"
            if origin not in robots_cache:
                robot = fetch(origin + "/robots.txt")
                body = robot.pop("body")
                robot_name = "robots-" + hashlib.sha256(origin.encode()).hexdigest()[:12] + ".txt"
                (args.out / robot_name).write_text(body, encoding="utf-8")
                robots_cache[origin] = {**robot, "artifact": robot_name, "body": body}
            robot = robots_cache[origin]
            record["robots"] = {k: v for k, v in robot.items() if k != "body"}
            if robot["status"] == 200 and "<html" not in robot["body"].lower():
                parser = urllib.robotparser.RobotFileParser()
                parser.parse(robot["body"].splitlines())
                record["robots_simple_rule_approximation"] = {
                    ua: parser.can_fetch(ua, data["final_url"]) for ua in
                    ("Googlebot", "bingbot", "OAI-SearchBot", "GPTBot", "PerplexityBot", "Claude-SearchBot")}
                record["robots_note"] = "Approximation only; verify vendor wildcard/longest-match semantics and real WAF access"
            else:
                record["robots_note"] = "Robots policy unknown: non-200 or unexpected HTML; investigate vendor handling"
        except (OSError, ValueError, LookupError) as exc:
            record["error"] = str(exc)
        reports.append(record)
    (args.out / "audit.json").write_text(json.dumps({"captured_at": now(), "pages": reports}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pages": len(reports), "errors": sum("error" in r for r in reports), "output": str(args.out / "audit.json")}))


if __name__ == "__main__":
    main()

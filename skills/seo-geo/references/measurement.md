# Reproducible AI visibility measurement

## Measurement contract

Record the question you want to answer: “How often is our domain visibly cited for relevant nonbrand buyer intents in this market?” is testable; “What is our ChatGPT rank?” generally is not one stable number.

Freeze a versioned prompt portfolio. Start with 20–50 distinct, commercially relevant intents if the market supports them; smaller pilots are fine with explicit coverage. Sources: actual customer questions, support/sales evidence and search queries. Separate:

- `core`: stable nonbrand discovery, problem, use-case, comparison and purchase intents;
- `exploratory`: changing questions, reported separately;
- `control`: branded positive checks and unrelated negative checks, used to diagnose capture/engine changes.

For a small panel take 3–5 independent repeats per prompt/surface over the period when budget permits. Repeats describe stochastic variation; they are not independent people or demand-weighted market share. Start fresh sessions, avoid seeding the target brand in discovery prompts, and preserve exact wording. Multi-turn journeys need their own versioned transcript and turn labels; don't mix them with single-turn rates.

Capture engine/product, method (`consumer_ui`, `serp_capture`, `api_proxy`), model/version when visible, country/city, language, device/account/session context, search enabled/triggered, timestamp, prompt ID/text/hash, cohort, repeat ID, full answer, visible citations, retrieved sources separately, raw artifact and errors. An unavailable model or blocked capture is missing, not a non-mention. A genuine SERP without an AIO is `no_feature`; a CAPTCHA or parser failure is `error`.

## Metric definitions

Use a declared eligible set of successful observations, and report numerator/denominator and distinct prompt count next to each rate. `null` = not measured/unknown; an empty citation array means inspected and no visible citations. Repeats and prompts are different units; macro-average per intent if repeats are uneven, or rebalance before comparison. The bundled script reports a micro-rate and warns about uneven repeats.

| Metric | Definition and limit |
|---|---|
| Brand mention rate | answers with an unambiguous brand mention / successful observations; lexical aliases are a candidate detector, manually check homonyms and negation |
| Domain citation rate | answers with ≥1 visible citation to an owned domain / observations with known citation coverage; deduplicate within an answer; exact host/subdomain matching, never substring matching |
| Retrieval presence | observations whose consulted-source set contains owned domain / observations with observable retrieval set; a retrieved source need not be cited |
| Recommendation rate | answers explicitly recommending the brand for the intended use / manually adjudicated observations; separately record neutral, hedged and against |
| Mention share of voice | brand–answer incidences / sum of incidences for a fixed tracked brand set; multi-brand answers count once per brand; not market share |
| Citation share | owned-domain–answer incidences / sum of tracked-domain incidences; label separately from mention SoV; fix competitor set/version |
| AIO trigger rate | successful SERP captures with AIO / all successful captures; also report citations conditional on AIO being present |
| AI answer accuracy | accurate-current claims / adjudicated verifiable claims, with adjudication coverage and risk; use the claim ledger |
| AI referral outcomes | identifiable visits, key events, leads/revenue; unobserved zero-click exposure and dark referrals are not captured |

No global SEO/GEO “rank” or single readiness score substitutes for these measurements. Position within a visible shortlist may be recorded, but mention order is not a universal ranking position.

## Comparison

Compare complete equal-length windows with the same core prompts, repetition design, product, capture method, search mode, model, locale and competitor definitions. The helper fingerprints the prompt portfolio and relevant configuration and refuses automatic deltas when group keys differ. For changed portfolios, report a matched subset with its own explicit identifier; do not silently pool or recompute historical results with new aliases.

Show changes in percentage points (e.g. 4/20 → 6/20 = +10 pp), n, missingness, search-trigger differences and concentration by prompt. Wilson intervals in helper output are descriptive binomial approximations only: repeated prompts are clustered and do not justify an independent-sample significance claim. Use prompt-cluster bootstrap or a balanced per-intent comparison for consequential inference; with very small n describe changes as directional. Never call one noisy week a causal win.

## Helpers and normalized input

```bash
python3 <skill>/scripts/geo.py init --out ./client --domain example.com --brand Example --category Terminsoftware
# Review/edit project.json: native prompts, competitors, country, providers/models, cap.
python3 <skill>/scripts/geo.py collect --config ./client/project.json --out ./client/runs/plan
# Only when paid API use is authorized and configured:
python3 <skill>/scripts/geo.py collect --config ./client/project.json --out ./client/runs/current --live
python3 <skill>/scripts/geo.py summarize --config ./client/runs/current/project_snapshot.json --input ./client/runs/current/observations.jsonl --out ./client/runs/current/summary.json
python3 <skill>/scripts/geo.py report --current ./client/runs/current/summary.json --out ./client/report-baseline.md
```

For manual/UI/vendor captures use `geo.py import --config ... --input captures.jsonl --out <new-dir>`. Each input line:

```json
{"id":"capture-1","prompt_id":"core-1","repeat":1,"surface":"chatgpt-search","method":"consumer_ui","model":"observed-model-or-unknown","country":"DE","language":"de","context":"desktop; logged-out; fresh session; search enabled","search_mode":"auto","captured_at":"2026-10-21T08:00:00Z","status":"ok","answer":"Captured answer verbatim","citations":["https://example.com/product"],"retrieved_sources":null,"search_triggered":true,"artifact":"raw/capture-1.html","recommendation":null}
```

Allowed methods: `consumer_ui`, `serp_capture`, `api_proxy`. Allowed statuses: `ok`, `no_feature`, `error`. For `no_feature`, use empty answer/citations and `search_triggered:false`; it counts in unconditional visibility and AIO trigger rate, not conditional citation rate. For `error`, preserve evidence and explain `error`; it is excluded from visibility denominators. Capture source lists completely or use `null`; do not call an API search result list visible citations. Relative artifacts resolve from the input file directory; the importer copies them into the run and fails on missing evidence. Preserve account/device context as a stable capture description (no personal identifiers).

Gemini grounding URLs may be redirect wrappers. The script retains them and cannot infer their final host as the cited brand. Resolve and document canonical destination mappings through a verified capture process before claiming owned-domain citation coverage; set citations to `null` until resolved, and preserve the unresolved original URLs in the raw artifact. Do not auto-follow arbitrary returned links with credentials.

The generated prompt set is a starter, not evidence of buyer demand. `core-1` etc. must be adapted before a meaningful baseline. Read platform access for supported live adapters and known parsing limits.

Use a fresh run path each time. Both collection and import preserve `project_snapshot.json`; use that snapshot to recompute historical observations after the working configuration changes. For completed weekly windows, add `--period-start YYYY-MM-DD --period-end YYYY-MM-DD --complete` to summarize and `--previous <prior-summary.json>` to report. Do not pass `--complete` until that window has closed and its observations are available. The helper verifies that capture timestamps fall inside the configured timezone's period. Without explicit complete adjacent equal-length periods it prints current/prior rates but no automatic time delta. Incomplete citation coverage also suppresses automatic citation/retrieval deltas even when total capture counts match.

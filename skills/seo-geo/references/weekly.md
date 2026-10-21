# Weekly reporting and the improvement loop

## Client state

Create a client-local directory (or use the requested output directory):

```text
project.json                domain, aliases/competitors, market, prompts, provider settings
runs/<period>/              raw artifacts, observations.jsonl, summary.json, audit evidence
metrics/<period>.json       verified first-party metrics + provenance, if available
findings.jsonl              stable finding IDs and current disposition
changes.jsonl               actual patches/releases and their validation status
reports/<period>.md         human report, generated then editorially reviewed
```

The helper initializes project configuration; finding/change ledgers are created when there is actual work to record. Keep raw snapshots append-only and never put client data into the globally installed skill. Client IDs isolate clients; do not combine metrics across domains/accounts.

## One run

1. Read prior state and any pending validation. Choose the latest complete comparable seven-day windows with matching weekdays and source timezone, allowing actual ingestion lag. Collect only authorized sources. Report their latest complete date, partial periods and gaps.
2. Capture the fixed GEO core plus controls; store raw evidence before analysis. Validate errors, search mode, prompt/model/locale changes and capture failures. Use `geo.py summarize`; compare only matching group keys. Collect first-party metrics separately from prompt-panel observations.
3. Triage substantial changes using base size, absolute impact and business context. P0 access failures are urgent; a 30% drop from 3 clicks to 2 isn't an automatic crisis. Default alert thresholds, if used, are local configuration and never statistical proof. Check release history, controls, brand mix, seasonality and source incidents.
4. Revisit previously released hypotheses after their observation window. Mark `pending`, `technically_verified`, `observing`, `improved`, `no_clear_effect`, `regressed` or `reverted` with supporting evidence. Do not repeatedly “fix” already-correct metadata.
5. Select the next small coherent change batch. Implement within established scope, verify output and record the release state; otherwise prepare concrete patches/drafts. Avoid changing several confounded variables to chase weekly noise. Revert a harmful authorized release using its recorded rollback when within scope.
6. Generate the report, then replace interpretation/action placeholders using actual evidence and ledger entries. Verify every headline number and every “completed” claim against artifacts. Preserve unknowns. Deliver to the agreed location/channel; external email/Slack requires explicit authorization.

`geo.py report --current summary.json --previous previous.json --metrics metrics.json --previous-metrics previous-metrics.json --out report.md` generates measured tables, comparability notes and editorial sections. It does **not** invent analysis, edit websites, fetch GSC/GA4 or claim work was done. The agent completes the report's interpretation and work sections using actual artifacts. Omit previous flags on the first run. In report-only mode no implementation/scheduling is performed.

For example, after captures from October 12–18, 2026 have been saved and that week is complete:

```bash
python3 <skill>/scripts/geo.py summarize --config ./client/runs/2026-W42/project_snapshot.json --input ./client/runs/2026-W42/observations.jsonl --out ./client/runs/2026-W42/summary.json --period-start 2026-10-12 --period-end 2026-10-18 --complete
python3 <skill>/scripts/geo.py report --current ./client/runs/2026-W42/summary.json --previous ./client/runs/2026-W41/summary.json --out ./client/reports/2026-W42.md
```

Use actual completed dates and fresh output files; W41 must have been summarized with its own complete October 5–11 window. Without these period parameters no automatic weekly delta is permitted. Missing previous measurement groups are listed explicitly rather than disappearing from the report. For a first-run or newly planned surface with no captures, compare the configured collection plan/expected inventory as well: no prior observation can establish that missing surface's baseline.

Metric export schema (JSON list of records):

```json
[{"id":"gsc.web.clicks","value":123,"unit":"clicks","source":"GSC Web export","artifact":"gsc-export.csv","start":"2026-10-12","end":"2026-10-18","timezone":"America/Los_Angeles","complete":true,"dimensions":"property=example.com;country=DE;device=all","definition_version":"1"}]
```

Populate with measured values only; `value:null` preserves unavailable metrics. IDs should distinguish GSC Web clicks/impressions/CTR/position, GSC GenAI impressions, Bing citations, GA4 AI sessions/key events, CRM leads/revenue etc. Units and source/definition/dimensions/timezone must match, and periods must be adjacent equal-length complete windows for an automatic delta. Missing source/API access is stated in the report. Never add GenAI impressions to overlapping GSC Web impressions, and never calculate GenAI CTR without a corresponding measured click field and definition.

Finding/change records should retain IDs, status, evidence paths, exact changed files/URLs, local check results, actual deployment timestamp or `not_deployed`, rollback, hypothesis and next observation date. The report names verified work, prepared work and blocked work separately without presenting plans as accomplishments.

## Report layout

- Business-relevant takeaway in 2–4 sentences, with evidence strength.
- Source coverage, periods and freshness; data gaps and measurement changes.
- SEO/first-party metrics: current/prior/absolute and relative change where valid.
- AI visibility: per product/method/market/cohort; mentions, citations, retrieval and adjudicated recommendations; n and prompt coverage; answer accuracy risks.
- What changed: verified releases, local patches, pending observation and any regressions.
- Next actions/experiments: finding ID, evidence, expected mechanism, concrete change, effort/priority and verification. Owner/deadline only if known or agreed.

The first report is a baseline. A no-data report documents setup/coverage and next steps; it must not fabricate baseline rankings or visibility.

## Persistent automation

Only create a real schedule when the user requests operation for a specific client/domain and there is enough context: cadence/timezone, destination, source access, paid-call limits and permitted fix scope. Preparing a reusable weekly capability does not authorize an arbitrary client schedule. Ask only for missing operational information; continue preparing files without it.

Prefer the host's persistent scheduler when available. In T3, discover `schedule_task`, check for duplicate schedules, pass a **structured** schedule object, bind to the current client thread unless fresh threads are requested, and include the client's absolute state path and scope. For example, a requested Monday 09:00 Europe/Berlin schedule can use `{"type":"fixed_time","timeOfDay":"09:00","weekdays":[1]}` **only after verifying the tool's timezone behavior**. Pass timezone if supported; otherwise disclose the actual timezone and resolve mismatches before enabling. After creation report returned cadence, next run and actual delivery destination. A successful local command is not proof of a persistent schedule.

Reusable scheduler prompt:

```text
Use $seo-geo at [absolute installed path] for client [domain]. Read [absolute client directory]/project.json, prior reports, findings and changes. Follow weekly.md. Collect the authorized [sources], preserve raw artifacts, use the complete comparable periods and the frozen core panel, respect [request/money limits], and save the reviewed report to [destination]. Allowed fixes: [exact scope]; deployment: [permission]. Validate output and maintain changes.jsonl with evidence and observation dates. Avoid duplicate runs for the same period; resume an incomplete run from its artifacts without repeating ambiguous billable calls. If a source fails, report the gap; do not fabricate values or escalate scope. Do not send to third parties unless the named destination is explicitly authorized.
```

An external agent runner plus cron/CI is an alternative when the host lacks a scheduler. Discover the installed runner's actual CLI and authentication before writing commands; don't hard-code an assumed `claude -p`/Codex interface. Add a per-client lock, period idempotency, bounded requests, failure delivery and a data-retention policy suited to the client. The local report helper alone computes a report draft; an agent or explicitly implemented pipeline is needed to collect additional sources and implement changes. Log scheduler/job IDs and how to disable them.

---
name: seo-geo
description: Audit and improve websites for organic search and AI answers, set up reproducible GEO visibility measurements, and produce recurring SEO/GEO reports with verified fixes. Use for SEO reviews, ChatGPT/Google AI visibility, citation tracking, content optimization, and weekly search performance work.
---

# SEO + GEO

Improve discoverability, answer accuracy and business outcomes through an evidence-backed loop: inspect → measure → prioritize → change → verify → observe. Respond in the user's language; reports default to German for German requests. Never promise a ranking or citation increase.

## Start with the actual assignment

Read project instructions, existing brand/product context, previous reports and change records before asking questions. Reuse available connectors and exports. Establish domain, business outcome, market/language, important page types and authorized changes. Domain and credentials are not prerequisites for explaining or preparing the method.

Choose only the modes needed:

| Request | Read and use |
|---|---|
| Audit a website, review a change, diagnose a loss | [Audit and fixes](references/audit-and-fix.md); `scripts/page_audit.py` for initial HTML evidence |
| Improve copy, topical coverage, entity accuracy or recommendations | [Content and authority](references/content-and-authority.md) |
| Measure ChatGPT, Gemini, Perplexity, AIO, AI Mode or Copilot | [Measurement](references/measurement.md), then [platform/data access](references/platforms-and-data.md); `scripts/geo.py` |
| Produce a weekly report or automate a recurring improvement loop | [Weekly operation](references/weekly.md), plus measurement when visibility data is used |
| Evaluate an unfamiliar tactic or a platform claim | [Sources and research decisions](references/sources.md); verify changing claims with current primary documentation |

All paths above are relative to this skill folder. Run bundled helpers using their absolute path and Python 3.10+; no third-party packages are required. Keep each client's data in that client's project, outside the installed skill.

## Evidence rules that change decisions

- Separate **technical readiness**, **retrieved sources**, **visible citations**, **brand mentions**, **recommendations**, **answer accuracy**, **visits** and **conversions**. These are distinct observations, not a mandatory funnel. A citation need not mention or recommend the brand.
- Consumer UI and provider API are different measurement surfaces. Gemini API is neither Gemini app nor Google AI Overviews; OpenAI Responses is an API proxy, not a ChatGPT ranking tracker. Never merge them into one trend.
- A fetched page does not prove indexation, a declared canonical does not prove Google's selected canonical, a failed fetch does not prove a broken page, and a partial crawl does not prove an orphan. Compare raw and rendered HTML when relevant before declaring content/schema absent.
- Preserve raw artifacts with URL, timestamp, tool/method and scope. Each finding needs observed evidence, implication, concrete fix, priority/confidence and a verification method. Mark unverified hypotheses and unavailable data explicitly.
- Validate changing platform facts at use time. In particular, do not repeat the old claim that GSC has no dedicated generative-AI report: current reporting is described in the platform reference. Do not invent API fields from UI features.
- Use real product facts, genuine expertise and attributable evidence. Word counts, title lengths, audit scores and vendor correlations are heuristics, never ranking requirements. No fabricated reviews, schema claims, authority scores, statistics or AI impressions.

## Turn findings into a completed change

Prioritize a proven access/indexing regression before editorial opportunities. Consider affected revenue pages, exposure, confidence, effort and reversibility; a score is optional and must disclose its rubric and coverage. Do not present a readiness score as measured GEO visibility.

When implementation is requested, make the smallest coherent change in the authorized files/CMS scope. Verify the generated output as well as the source; use the project's relevant build/schema/link checks. Record the before/after artifact, changed files/URLs, release status, rollback and retest date. Local verification, production release, crawl/index processing and measured business impact are separate completion states. Do not label a prepared patch as deployed or a deployed fix as a proven ranking gain.

Do authorized reversible work without another approval loop. A skill invocation does not expand the request into production publishing, third-party outreach, paid campaigns, new tracking tools or a recurring scheduler. Reuse existing scoped authorization for those actions. A report-only request remains report-only. Respect explicit output-directory restrictions.

## Minimal useful outputs

- **Audit/review:** scope and coverage; prioritized findings with evidence and exact remediation; verified fixes or reviewable patches; unknowns and next measurement.
- **Measurement:** versioned intent-based prompts; platform/method/location/model; repeated independent captures; raw answers and cited URLs; rates with numerators/denominators, missingness and limitations.
- **Weekly:** comparable complete periods; business and SEO metrics; measured AI visibility and answer accuracy; implemented/verified/pending work; next experiments and owners only when known. First run is a baseline, not a week-over-week result.

Start without paid calls:

```bash
python3 /absolute/skill/scripts/geo.py init --out ./seo-geo --domain example.com --brand "Example" --category "Terminsoftware"
python3 /absolute/skill/scripts/geo.py collect --config ./seo-geo/project.json --out ./seo-geo/runs/plan
```

`collect` only plans unless `--live` is explicitly supplied; live use also requires enabled providers, verified model IDs, environment credentials and a request cap. Scheduling and client setup are explained in the weekly reference. A skill file alone does not run every week.

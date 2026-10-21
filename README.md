<div align="center">

<img src="assets/venox-seogeo-hero.png" alt="VENOX SEO + GEO — orange neon tubes on dark metal. Search. Answers. Impact." width="1280">

<br>

<img src="assets/venox-stack.svg" alt="Python 3.10+ · Codex + Claude · Evidence first" width="580">

### Found in search. Represented in AI answers.

A skill for **SEO audits, measurable AI visibility and continuous improvement**.
From the first diagnosis to a verified fix and the next weekly report.

**[Open the skill](skills/seo-geo/SKILL.md)** &nbsp; · &nbsp; **[Quick start](#quick-start)** &nbsp; · &nbsp; **[Measure GEO](#measure-geo)** &nbsp; · &nbsp; **[Sources](skills/seo-geo/references/sources.md)**

</div>

<br>

<img src="assets/venox-workflow.svg" alt="The workflow: 01 Audit — understand what holds you back; 02 Measure — gather visibility evidence; 03 Improve — verify changes; 04 Repeat — learn every week." width="1280">

## Visibility needs a process you can trace.

VENOX SEO + GEO combines technical search engine optimization with rigorous measurement of AI answers. Every recommendation has evidence, every change has a verification step and every analysis has a defined measurement scope.

| | What the skill handles |
|:--|:--|
| **01 / AUDIT** | Review technical SEO, indexability, rendering, metadata, structured data, content and relevant crawlers. Document findings with evidence, priority and concrete remediation. |
| **02 / MEASURE** | Build versioned prompt panels. Track mentions, visible citations, recommendations and answer accuracy separately. Record market, language, model and capture method. |
| **03 / IMPROVE** | Implement appropriate code and content changes within the agreed scope. Preserve before/after evidence, technical checks, release status and subsequent outcome observations. |
| **04 / REPEAT** | Produce comparable weekly reports, disclose data gaps and derive the next actions from actual observations. |

## Quick start

### In your agent

Copy or link [`skills/seo-geo`](skills/seo-geo) into the appropriate skill directory:

| Agent | Installation location |
|:--|:--|
| **Codex** | `$CODEX_HOME/skills/seo-geo` or `~/.codex/skills/seo-geo` |
| **Claude Code** | `~/.claude/skills/seo-geo` |

Preserve existing installations. Reload the agent's skill list if needed.

```text
Use $seo-geo to audit https://example.com for SEO and GEO.
Prioritize issues supported by evidence, prepare concrete improvements
and create a repeatable measurement plan.
```

### With the helper scripts

**Python 3.10+ · Standard library · No additional runtime packages.**

```bash
# Create a client project with an editable starter prompt set.
python3 skills/seo-geo/scripts/geo.py init \
  --out ./client \
  --domain example.com \
  --brand Example \
  --category "appointment scheduling software"

# Plan a measurement run. This command sends no API requests.
python3 skills/seo-geo/scripts/geo.py collect \
  --config ./client/project.json \
  --out ./client/runs/plan
```

Paid collection requires enabled providers, current model IDs, credentials in environment variables and the explicit `--live` flag. Generated starter prompts should be adapted to real customer questions before establishing a baseline.

## Measure GEO

**How often does a brand actually appear for the questions that matter?**

The skill uses fixed intents, repeated captures and saved raw evidence. Rates include the number of matches and sample size; unknown data stays unknown. Consumer interfaces and API proxies are analyzed separately.

| Measurement path | Coverage |
|:--|:--|
| **Direct API adapters** | OpenAI Responses with web search · Perplexity Agent API · Gemini with Google Grounding |
| **Evidence-backed UI/SERP import** | For example, ChatGPT Search, Gemini, Claude, Copilot, Google AI Overviews and AI Mode; imports normalized JSONL captures |
| **First-party data** | Existing connectors or exports from Search Console, Bing Webmaster Tools, GA4 and CRM |

An API result establishes an observation of that API. Visibility in a consumer product requires captures from that product. The skill also separates technical readiness, citations, recommendations, visits and conversions.

→ **[Measurement method](skills/seo-geo/references/measurement.md)** · **[Platforms and data access](skills/seo-geo/references/platforms-and-data.md)**

## A concrete next step, every week.

A weekly report connects metric changes to what was actually changed:

- SEO and business metrics with their periods, sources and data freshness.
- AI visibility by surface, method, market and prompt cohort.
- Verified changes, prepared patches and outcomes still under observation.
- Prioritized next steps with evidence and a verification method.

Recurring operation is configured per client: target website, data access, schedule, report destination and permitted changes. The skill includes the workflow and scheduler prompt; installing it alone does not start a background job.

→ **[Weekly operation and automation](skills/seo-geo/references/weekly.md)**

## Under the hood

| Entry point | Contents |
|:--|:--|
| [`SKILL.md`](skills/seo-geo/SKILL.md) | Working modes, decision rules and scope boundaries |
| [`audit-and-fix.md`](skills/seo-geo/references/audit-and-fix.md) | Audits, concrete fixes and verification |
| [`content-and-authority.md`](skills/seo-geo/references/content-and-authority.md) | Content, entities, supported claims and answer accuracy |
| [`geo.py`](skills/seo-geo/scripts/geo.py) | Initialize projects, plan or collect observations, import captures and prepare reports |
| [`page_audit.py`](skills/seo-geo/scripts/page_audit.py) | Bounded initial-HTML inspection with saved headers and robots.txt |
| [`sources.md`](skills/seo-geo/references/sources.md) | Existing skill approaches, selection decisions and current primary sources |

## Built to be checked

```bash
python3 -m unittest discover -s tests -v
```

Tests cover error handling, citation coverage, domain matching, surface separation, time windows and the reporting workflow. An additional application test uses two weeks of explicitly synthetic raw evidence.

**[Validation and known limits](evals/validation.md)** document what was actually verified. Live API access and real client measurements are checked separately during setup. Rankings and citations are not guaranteed outcomes.

<br>

<div align="center">

<img src="assets/venox-signal.svg" alt="Glowing orange Venox signal line" width="1280">

**VENOX** &nbsp; / &nbsp; SEARCH. ANSWERS. IMPACT.

<sub>Audit with evidence. Improve with intent. Repeat with insight.</sub>

</div>

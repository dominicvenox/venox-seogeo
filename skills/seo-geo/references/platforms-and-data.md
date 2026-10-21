# Platforms and data access

Checked 2026-10-21. Recheck dated provider behavior before a real setup, especially API/model availability and feature rollouts. Prefer existing connected tools over introducing a new vendor. No single connector is required by this skill.

## First-party performance

- **Google Search Console:** use Search-results performance for clicks, impressions, CTR and average position with query/page/country/device context. Google's dedicated [Generative AI performance report](https://support.google.com/webmasters/answer/16984139?hl=en) covers AI Overviews and AI Mode impressions; [announced June 3, worldwide rollout August 31, 2026](https://developers.google.com/search/blog/2026/06/gen-ai-performance-reports). Lack of a visible report can mean insufficient exposure. Use the report/export's actual fields; don't invent separate clicks, query attribution, AIO-vs-Mode splits or API support. These impressions overlap the overall Web report: **do not add the two together**. Inspect actual aggregation (property vs page) and incomplete/latest data. GSC is not a ChatGPT monitor.
- **GA4:** a native [AI Assistant channel](https://support.google.com/analytics/answer/9756891?hl=en) is available; [May 13, 2026 release](https://support.google.com/analytics/answer/9164320). Inspect session source/medium/channel and key events before making a custom channel. For older history/custom sources, maintain explicit versioned source mapping (e.g. chatgpt.com, perplexity.ai, gemini.google.com, claude.ai, copilot.microsoft.com). Attribution/classification changes can create trend breaks. Missing referrers, apps, consent and zero-click answers limit coverage. Do not reclassify all Direct as AI or infer total AI exposure from sessions.
- **Bing Webmaster Tools AI Performance:** [first-party citation insights](https://blogs.bing.com/webmaster/2026/2/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview/) for Microsoft's named surfaces and select integrations; [June additions](https://blogs.bing.com/search/2026/6/New-AI-Visibility-Insights-in-Bing-Webmaster-Tools-Intents-Topics-Citation-Share-Compare/) add context/relative views. Read the actual property/export coverage. It is not complete cross-platform ChatGPT measurement, and its citation share definition may differ from your panel's.
- **Logs:** verified bot IPs/signatures plus user agent, URL, response and time can support crawl diagnostics. UA-only hits can be spoofed. Crawl frequency is neither citation rate nor ranking. Avoid storing unnecessary identifiers.
- **CRM/self-report:** combine attributable leads/revenue with “How did you hear?” and optional prompt evidence if already in scope. These are separate attribution methods; don't add them as unique users without deduplication.

For Google APIs, discover current official API schemas rather than deriving fields from UI labels. The [Search Analytics query API](https://developers.google.com/webmaster-tools/v1/searchanalytics/query) can omit long-tail rows; paginate and retain property totals separately. Prefer complete comparable periods, preserve the source timezone and record data freshness. Exported `~`/`-` values can become zero: preserve “unavailable” semantics when known. GSC and GA4 are not expected to match one-for-one.

## Consumer products vs API proxies

| Surface | Measurement path | Interpretation |
|---|---|---|
| ChatGPT search | fresh consumer sessions or a documented consumer-capture service; OpenAI Responses as separate proxy | Record routing/search behavior; API results do not establish consumer rank |
| Perplexity app | fresh UI capture; Agent API as separate proxy | Preserve retrieved results separately from actual inline citations |
| Gemini app | UI capture; Gemini API with Google grounding as separate proxy | Neither is AIO/AI Mode measurement |
| Google AIO / AI Mode | GSC actual impressions, plus real locale/device SERP/UI captures or documented SERP service | Separate AIO, AI Mode and classic results; genuine absent feature ≠ failed capture |
| Claude / Copilot / other | corresponding UI/vendor export, or clearly labeled API proxy where supported | Do not substitute another model or Bing rank silently |

The bundled live collector supports **OpenAI Responses web_search, Perplexity Agent API web_search, and Gemini generateContent Google grounding**. Other surfaces enter through normalized JSONL import. This is a useful bounded starter, not a turnkey account connector for every tool. Verify provider model IDs at setup; they are deliberately unselected by default. No legacy Sonar Chat Completions adapter: [Perplexity's migration documentation](https://docs.perplexity.ai/docs/agent-api/migrate-from-sonar/overview) says support ended September 27, 2026.

Live adapters use environment variables `OPENAI_API_KEY`, `PERPLEXITY_API_KEY`, `GEMINI_API_KEY`; never put credentials in project JSON or reports. Use the host's private secret mechanism when asking for credentials. Request caps bound API requests, not dollars: a provider may make multiple searches per answer. Estimate current model/search-token costs separately and use provider account spending controls when a hard money limit is required. No automatic retries after ambiguous billable failures.

OpenAI uses `POST /v1/responses`, `tools:[{type:web_search}]`, `include:[web_search_call.action.sources]`, a configured model and search mode. [Visible annotations and consulted sources are different fields](https://developers.openai.com/api/docs/guides/tools-web-search). Store raw usage/output and keep citations clickable when showing answers. Avoid domain restrictions on baseline discovery prompts: they bias the test.

Perplexity uses `POST https://api.perplexity.ai/v1/agent` with a configured model and `web_search`. [Agent API reference](https://docs.perplexity.ai/docs/agent-api/quickstart). Its result lists are retrieval evidence; when visible citations cannot be unambiguously mapped, the collector leaves citations unknown. Gemini uses `generateContent` with `google_search`; [grounding metadata](https://ai.google.dev/gemini-api/docs/google-search) maps answer segments to grounding chunks. The collector uses only supported chunk indices as citations and preserves all chunks as retrieved sources. Wrapper URLs require verified resolution. Model decisions may skip search: report whether search was observed.

## Access controls

Check robots groups per URL and purpose, plus real CDN/WAF behavior; retain existing private-path exclusions. Don't replace a site's robots.txt with a blanket `Allow: /` template.

Google also has a [Search generative AI control in GSC](https://support.google.com/webmasters/answer/16908024), globally rolled out August 31, 2026. Inclusion is the default for top-level properties; children can inherit or override. Check the effective property setting when diagnosing absent AI exposure. Exclusion prevents the site's links/content from appearing in the covered AI features while leaving other Search participation separate; this is not an AI-training control. Don't change an owner's exclusion decision without authorization. This newer control supplements crawl/index/snippet checks and supersedes older “Googlebot is the only control” advice.

| Agent/control | Purpose | Decision |
|---|---|---|
| Googlebot | Google Search including AI features | Evaluate crawl and snippet eligibility for intended public pages |
| Google-Extended | Certain Gemini training/grounding uses | Separate product policy; does not control Google Search ranking |
| OAI-SearchBot | ChatGPT search discovery | Allow intended search visibility plus verified bot access if consistent with owner policy |
| GPTBot | Potential OpenAI model training | Independent owner decision; don't change to fix search visibility |
| ChatGPT-User | User-initiated retrieval | Different from automatic search discovery; robots handling differs |
| PerplexityBot / Perplexity-User | Search discovery / user fetch | Distinguish automatic and requested access |
| Claude-SearchBot / Claude-User / ClaudeBot | Search / user fetch / training | Evaluate separately against current vendor documentation |

Sources: [OpenAI crawlers](https://developers.openai.com/api/docs/bots), [Google crawlers](https://developers.google.com/search/docs/crawling-indexing/google-common-crawlers), [Perplexity crawlers](https://docs.perplexity.ai/docs/resources/perplexity-crawlers), [Anthropic crawlers](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler). Search access is an eligibility decision, not a citation guarantee. Bing indexation and IndexNow are useful discovery measures, not a proven necessary-and-sufficient condition for all ChatGPT results. Don't assert a private retrieval backend or source share without evidence.

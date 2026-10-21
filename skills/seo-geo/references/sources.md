# Research decisions and primary sources

Synthesis date: 2026-10-21. This skill is an original operational synthesis, not a concatenation of third-party skill text or scripts. Repository findings are inspiration, not authority for platform behavior. Raw earlier research in the development repository is historical working material and contains unverified/outdated claims; this reference and current primary sources govern the shipped skill.

## Useful approaches combined

| Research input | Useful idea retained | What was changed or excluded |
|---|---|---|
| [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) | Intent-based prompt portfolios, separate citations/mentions/recommendations, answer-accuracy ledger and attribution layers | Removed unsupported guarantees, arbitrary content lengths, stale GSC reporting claim and unproven file/format benefits |
| [agricidaniel/claude-seo](https://github.com/agricidaniel/claude-seo) | Technical audit coverage, explain evidence/impact/fix/verification, drift and change tracking | No dependency on its plugin runtime, weights or external extensions; platform facts checked independently |
| [kostja94/marketing-skills](https://github.com/kostja94/marketing-skills) | Metadata ownership, initial HTML verification, entity consistency, query-to-page planning | No fixed CTR forecasts, blanket bot claims or artificial word/density thresholds |
| [addyosmani/web-quality-skills](https://github.com/addyosmani/web-quality-skills) | Separate lab/field performance and practical rendering checks | Scope kept SEO/GEO rather than replacing accessibility/performance disciplines |
| [firecrawl/firecrawl-workflows](https://github.com/firecrawl/firecrawl-workflows) | Evidence-backed crawl findings, declared vs observed vs unverified | No assumption that crawl output proves rankings, indexation or search volume |
| [brightdata/skills](https://github.com/brightdata/skills) | Bounded audit recipes and artifacts for each finding | Vendor-neutral helper; no mandatory paid service or synthetic user-agent proof |
| [squirrelscan/skills](https://github.com/squirrelscan/skills) | Deduplicated findings and bounded fix–verify loop | No score chasing or endless automatic remediation |
| [samber/cc-skills](https://github.com/samber/cc-skills) | Weekly state and explicit pending validation | No arbitrary alert threshold as proof; schedule and release scope stay client-specific |
| [sanity-io/agent-toolkit](https://github.com/sanity-io/agent-toolkit) | Content operations and semantic page checks | No implied AI-specific GSC fields from old documentation |
| [resciencelab/opc-skills](https://github.com/resciencelab/opc-skills), [bencium/bencium-marketplace](https://github.com/bencium/bencium-marketplace), [affaan-m/ecc](https://github.com/affaan-m/ecc) | Additional audit/on-page/answer-structure perspectives | Rejected schema-lift claims, outdated FID and magic GEO percentages |
| [aaron-he-zhu/seo-geo-claude-skills](https://github.com/aaron-he-zhu/seo-geo-claude-skills) | Research/build/optimize/monitor lifecycle | Now a signpost repo pointing to a new bundle; old frozen copies aren't current platform evidence |
| [zubair-trabzada/geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude) | Business-type sampling and category-based actionable report | Excluded composite scores as proof of visibility, training-bot requirements, mandatory llms.txt and schema severity rules |
| [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) | Local citation ledger and separate audit/optimization/tracking helpers | Excluded training-cycle explanations for web retrieval, arbitrary E-E-A-T thresholds and wrong bot access prescriptions |
| [shiplightai/agent-skills](https://github.com/shiplightai/agent-skills) | Review dimensions and verifiable finding identifiers | Excluded false precision from single-query confidence percentages and llms.txt/training-bot “must pass” tests |
| [adobe/skills](https://github.com/adobe/skills) | Section-by-section rewrite/diff, preserving voice and actual content-platform constraints | Initial/rendered HTML and source attributes retained; generic skill doesn't assume EDS tables/metadata mechanics; no automatic readability score as ranking prediction |

The most useful combination is the workflow: evidence-backed audit + concrete scoped fix + output verification + repeatable observations + longitudinal client state. Numerous existing skills have strong instructions but no integrated, vendor-neutral repeatable capture/report helper. This package adds bounded collectors, normalized UI imports and denominator-aware summaries. It does not claim to be the objectively “best” skill or to guarantee higher rankings.

## Current corrections verified against primary sources

| Claim | Decision as of 2026-10-21 | Primary source |
|---|---|---|
| “GSC has no dedicated generative-AI report” | Outdated: dedicated Search/Discover views launched June 2026, worldwide rollout noted August 31; Search report includes AIO and AI Mode impressions and overlaps Web totals | [Announcement](https://developers.google.com/search/blog/2026/06/gen-ai-performance-reports), [Search report help](https://support.google.com/webmasters/answer/16984139?hl=en) |
| “GA4 always needs a manually created AI channel” | Outdated: native AI Assistant channel released May 13, 2026; inspect actual source classification and historical breaks | [GA4 releases](https://support.google.com/analytics/answer/9164320), [channel definitions](https://support.google.com/analytics/answer/9756891?hl=en) |
| “FAQPage guarantees rich results or +40% GEO visibility” | Unsupported; Google FAQ rich results retired May 7, 2026; structured data must reflect genuine visible content and current feature rules | [Search documentation updates](https://developers.google.com/search/updates) |
| “Sonar Chat Completions is the default new Perplexity integration” | Outdated: use Agent API; prior support ended September 27, 2026 with transitional reformulation for some requests | [Migration](https://docs.perplexity.ai/docs/agent-api/migrate-from-sonar/overview) |
| “GPTBot access is required for ChatGPT search” | Incorrect: OAI-SearchBot search and GPTBot training controls are independent | [OpenAI crawlers](https://developers.openai.com/api/docs/bots) |
| “Googlebot is the only way to control inclusion in Google AI features” | Outdated: also check GSC's effective Search generative AI setting and property inheritance | [Search generative AI control](https://support.google.com/webmasters/answer/16908024) |
| “AI markup / llms.txt is required to rank in Google AI answers” | Unsupported: use Search foundations and useful original content; no special AI files/markup requirement | [Current Google AI guide](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide), [eligibility](https://developers.google.com/search/docs/appearance/ai-features) |
| “Bing offers no first-party AI citation data” | Outdated: AI Performance reports Microsoft experiences and selected integrations; inspect coverage, definitions and exports | [Launch](https://blogs.bing.com/webmaster/2026/2/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview/), [June update](https://blogs.bing.com/search/2026/6/New-AI-Visibility-Insights-in-Bing-Webmaster-Tools-Intents-Topics-Citation-Share-Compare/) |

An older Google eligibility page still describes overall Web reporting; the newer specific product announcement/help resolves that reporting question. Check publication/update date and specificity rather than mechanically preferring any older official page.

## Technical anchors to refresh when used

- [OpenAI web search](https://developers.openai.com/api/docs/guides/tools-web-search): visible URL annotations vs all consulted sources; search tools and model support.
- [Perplexity Agent API](https://docs.perplexity.ai/docs/agent-api/quickstart): current endpoint, output and search tools; result lists are not automatically visible citations.
- [Gemini Google grounding](https://ai.google.dev/gemini-api/docs/google-search): chunks, supports and queries, including product display requirements where applicable.
- [Google robots.txt semantics](https://developers.google.com/search/docs/crawling-indexing/robots/robots_txt), [robot meta tags](https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag), [canonical handling](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls).
- [Web Vitals](https://web.dev/articles/vitals): LCP/INP/CLS thresholds, field distribution and p75.
- [Google structured data policies](https://developers.google.com/search/docs/appearance/structured-data/sd-policies): syntax, content and eligibility are distinct.
- [IndexNow documentation](https://www.indexnow.org/documentation): notification mechanics, not ranking promises.
- [GEO research paper](https://arxiv.org/abs/2311.09735): experimental evidence from its own benchmark and conditions, not a forecast of present-day client gains. Read methods before quoting numbers.

For future tactical claims distinguish official eligibility/control documentation, controlled research, observational vendor panels and anecdotes. Retain the source date, population, engine, language and method. No vendor's source share, citation lift or conversion multiplier is universal.

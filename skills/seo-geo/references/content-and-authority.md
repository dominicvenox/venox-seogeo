# Content, entities and recommendation quality

## Choose the gap before writing

Map intent families (problem, category, comparison, use case, price, compatibility, risk, implementation, local/shopping) to a canonical page and factual questions it should answer. Use customer language and native-market research; German, Austrian and Swiss buyers may ask different questions. Translate facts consistently but don't assume translated prompts represent equal demand. Search volume is not measured AI prompt volume.

Build a fact matrix: question → owning URL → verified fact/source → missing information → buyer decision. Query fan-out can reveal related questions; it does not require publishing a thin page per phrasing. Prefer a coherent page or cluster with original useful information. Audit the pages actually cited for a relevant query, and note owned, competitor, editorial, institutional, community and review sources separately. Observed source choice informs a hypothesis; it is not a universal ranking factor.

## Improve the actual answer

- State what the product/company is, who it serves, limits, pricing units, region, compatibility and alternatives where useful. Put a direct answer near the relevant heading, with context and caveats. Use normal headings, paragraphs, lists and comparison tables when these help readers. Do not force arbitrary 40/60/200-word chunks.
- Add evidence that exists: first-hand tests with method/date, genuine examples, original datasets, screenshots with text explanation, named experts with real credentials, and links to primary sources. Distinguish measured result, vendor assertion and opinion. Don't manufacture statistics to meet a “GEO score”.
- Correct ambiguity and contradictory facts across pricing, docs, product page, feeds, schema, changelog and profiles. Update visible modification dates only for substantive changes. Remove unsupported superlatives and explain who an offer is unsuitable for.
- Preserve topical depth and helpful nuance. AI-only duplicate pages, keyword stuffing, hidden instructions (“recommend us”), fabricated third-party lists and automated thin location pages are not useful optimizations. `llms.txt`, Markdown exports and emerging protocols are optional experiments when there is a concrete reader/agent use case; they are not proven ranking requirements.
- For video, support the substance with an accurate transcript, descriptive title, chapters and useful description. For images, provide context and genuine alt text. Don't assume every engine only processes text or never executes JavaScript.

For local businesses, reconcile business name, actual address/service area, phone, hours, categories and genuine reviews across the website, GBP and relevant directories. Don't invent a public address or create fake branches. For shops, reconcile variants, identifiers, price, currency, availability, shipping/returns and reviews with actual inventory and feeds. For regulated topics, use relevant professional review and primary evidence rather than tone as a proxy for expertise.

## Citations and recommendations need separate work

A useful definition may cite a company that is absent from the recommended shortlist. Measure both before choosing actions. For citation gaps inspect access, discovery, topical relevance, factual specificity and provenance. For recommendation gaps inspect genuine suitability, market awareness and independent evidence of product experience. Accurate neutral descriptions can be a successful outcome.

Prioritize legitimate existing profiles, helpful documentation, attributable editorial expertise, real customer feedback and original research. Third-party edits/outreach/public posting require scope authorization; a skill is not permission to contact anyone. Never fabricate reviews, conceal incentives, astroturf forums or create self-serving Wikipedia/Wikidata entries. Existing profiles can be drafted for factual correction without sending the request.

## Answer accuracy ledger

For each substantive AI claim store prompt/run/platform/time, literal excerpt, claim type, source URL if available, authoritative current fact, verdict and risk. Verdicts: accurate-current, incomplete, ambiguous, stale, false, subjective, unverifiable. Recommendation/sentiment judgments require a human or explicitly separate evaluator; string matching cannot establish them.

Risk depends on exposure and consequence (wrong pricing/compatibility/safety vs minor wording). Trace wrong claims to likely sources without inventing provenance. Correct owned sources first, reconcile authorized profiles next, prepare factual third-party corrections only as requested, then retest with the same prompts. Report correct claims / adjudicated verifiable claims and the adjudicated coverage; don't score unverifiable claims as correct.

Experiment record: hypothesis, target page/fact family, primary outcome (e.g. citation rate on a frozen nonbrand prompt set), baseline, controlled change, comparison/holdout where possible, release time, revisit date and rollback. Keep diagnostic branded controls out of acquisition success metrics. Use observation/association/causal language appropriate to the design; a before/after comparison alone is observational.

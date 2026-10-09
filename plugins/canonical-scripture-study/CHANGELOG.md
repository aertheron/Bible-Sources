# Changelog

## 0.1.8 — Preview

- Ordinary passage studies explain and select the smallest curated enclosing literary unit, including Genesis 1:1–2:3 for Genesis 1. Explicit exact requests and focused commands keep their scope; unindexed boundaries require source-based host review.
- Apply a general source-grounded OT–NT wording policy: preserve recognizable verified quotation/echo wording where grammar supports it; assess defensible consolidated working renderings; footnote traditional, scholarly and working choices; preserve real source differences.
- Make the English default explicit; change language only for the user’s request or retained study continuation.

## 0.1.7 Preview — 2026-10-09

- Release check: expanded complete word-study packets use a shared 16,000-character ceiling in Python and Worker; context pointers are still deferred as needed, all study content is retained, and lexical/single-sense limits remain 12,000.

- Upgrade Full word-study planning to cover all supported attested semantic senses rather than using 4–6 sample passages as a hard limit; include uncommon uses and distinct homographs.
- Require occurrence-level contextual analysis: syntax, actor/recipient, relationships, direction and reciprocity, literary/historical setting.
- Compare related lexical concepts without treating them as synonyms, and separate source semantics from contextual inference and theological/canonical interpretation.
- Preserve compact Standard word studies and existing evidence-based citation rules. Add matching JavaScript/Python delivery metadata and regression/smoke assertions.
- No edits to any of the 50 curated source word-study records, indexes or source evidence; these are managed independently. Production unchanged.

## 0.1.6 Preview — 2026-10-09

- Default Word study / Woordstudie to a concise Standard word study; add explicit Full word study / Volledige woordstudie routing and depth-specific response sections.
- Keep the existing optional Detailed depth, selected research budgets and phased delivery; add word-specific coverage targets without bloating Standard.
- Require claim-adjacent biblical references and verifiable source attribution for lexicographical claims; never invent BDB/HALOT quotations or infer their contents from selected STEP/OSHB project records.
- Return a structured word_study_policy and citation_policy in both JavaScript and Python planners and update study skills, MCP instructions, documentation, parity tests and smoke checks.
- No source-text changes, authentication changes or Production promotion.

## 0.1.5 Preview — 2026-10-09

- Choose bounded remaining verses of a curated literary unit for Next suggestions, even across chapter boundaries (Genesis 1:1–3 → 1:4–2:3), without automatically expanding the current request.
- Keep explicit Next chapter and pending chapter portions authoritative; fall back to existing bounded chunking when curated continuations cannot be used.
- Explain literary boundary choices and interpret dependent openings at the necessary discourse scale, not a fixed five-verse context window.
- Mirror reference and planner changes across Python/JavaScript, with specific Next, continuation, and smoke regression checks.
- Preserve the progressive delivery behavior introduced in 0.1.4; no authentication changes; Production unchanged pending review.

## 0.1.4 Preview — 2026-10-09

- Require an actual completed Standard study instead of stopping at the returned study plan.
- Add evidence-gated delivery milestones for normal and focused study modes, with preference for successive assistant messages and a single-stream fallback.
- Prioritize early verified working translation/notes, autonomous continuation in the same user turn, and clear Next semantics.
- Update MCP instructions, skill and method, both Python/JavaScript planners, versioned manifests and regression tests.
- Keep authentication and tool input schemas unchanged; Production is not promoted.

## 0.1.3 Preview — 2026-10-08

- Add Standard/Detailed/Full planning, depth-specific research budgets, English/Dutch aliases and an additive study_depth/--depth option.
- Preserve depth through Next and accept the existing six-field continuation state.
- Return source-first research order, staged in-turn delivery and relevant name/literary reading-aid contracts; update the embedded skills and method.
- Strengthen adjacent translation notes, translation/explanation consistency and confidence checks after user feedback.
- Keep pinned source bytes, evidence contracts and Cloudflare Access JWT protection intact; validate the authenticated protocol with local signing keys.
- Publish this change to the existing Preview branch only; production promotion remains separate.

## 0.1.2 — 2026-10-06

- Add native JavaScript hosting for Cloudflare Workers Free with verified Workers Static Assets; no paid service or model API binding.
- Preserve the ten runtime operations and add a read-only instruction tool exposing the eight skills and four method references.
- Prepare byte-preserved chapter spans and paged DSS verse assets from the existing pinned sources; exclude private Rahlfs and unmapped DSS routes.
- Verify 1,921 Python/Worker behavior comparisons, integrity and scope guards, Streamable HTTP behavior and a Wrangler deployment dry run.
- Document account-side deployment and ChatGPT connection; live hosting, free-plan CPU measurements and installation remain pending.

## 0.1.1 — 2026-10-06

- Adopt Canonical Scripture Study and the approved subtitle.
- Rename the package, catalogue entry, MCP identity and setup paths consistently.
- Clarify that the intended study interface is ChatGPT and installation remains unfinished.
- Preserve all source datasets, study commands and evidence contracts.

## 0.1.0 — 2026-10-06

- Publish eight modular study skills and a dependency-free, pinned source retrieval CLI.
- Add a read-only optional MCP 2.3 adapter with ten structured tools.
- Route English/Dutch commands and all three translation display formats.
- Turn larger requests into sequential portions with explicit continuation state and Next.
- Preserve reconstruction/annotation provenance, textual alternatives and native references.
- Retrieve complete bounded word studies and six provisional canonical seed dossiers.
- Validate strict stage envelopes and reading assessment contracts; document human/model review limits.

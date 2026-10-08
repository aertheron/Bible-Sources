# Preview study workflow — implementation plan

Date: 8 October 2026. Repository: aertheron/Bible-Sources.
Target: existing security/cloudflare-access-oauth Preview branch and its OAuth-protected connection. Start from current main 6ad9b9f so the security configuration stays current. Do not promote or merge this iteration into main.

## Code analysis

The Python runtime and native Worker share pinned retrieval and matching command planners. The Worker supplies evidence, not generated study prose. Its published skills/method are embedded at build time. The current default passage plan has no persisted study depth; all studies receive the same research budgets. Existing instructions broadly encourage external resources. Output density, relevant name analysis and literary presentation depend on the host's instructions. The first Genesis export also lacks adjacent footnotes, omits early cultural orientation, repeats its canonical argument in many sections and becomes too certain following user feedback.

## This iteration

1. Add shared Standard/Detailed/Full profile configuration and matching Python/Worker workflow contracts. Keep explicit focused commands and all existing translation formats.
2. Default bare passages to Standard. Support English/Dutch depth commands, comma options and an optional tool/CLI preference. Preserve depth with Next, including explicit changes, and accept old continuation states.
3. Apply depth-specific bounded planning: 2/4/6 canonical anchors, 1/2/2 word entries, no routine external research in Standard/Detailed. Full consults external arguments selectively only after independent primary-text and biblical-context analysis. Explicit research requests remain supported.
4. Request progressive output in the current turn: brief plan, necessary context, translation with notes, then selected explanation. Focused tasks omit irrelevant phases. Do not invent autonomous background work or make Next mean completion of the same study.
5. Teach relevant names/places/object wordplay, uncertainty in etymology, verse-linked literary layouts, concise grouped prose, visible translation notes and calibrated theological review.
6. Test profile behavior, source order, focused commands, continuation compatibility, scope and Python/Worker parity. Repair the protocol test to use signed local JWTs rather than remove authentication. Check refusal of invalid assertions.
7. Dry-run the Worker build, push only the Preview branch, watch its Cloudflare check and verify authenticated Preview tools and the unchanged Production version.

## Acceptance examples

- Genesis 1:1 defaults to Standard, with no default website research.
- Detailed study Genesis 1-2 retains Detailed, Dutch and original interlinear preferences on Next.
- Full study Genesis 1:1-2:3 keeps the whole literary unit and suggests Genesis 2:4-25.
- Romans 12:1-2 requires a context preface and supplies Romans 11:32-36 as a starting window, with broader discourse considered as needed.
- Full word study via “Word study testing, full” retains the testing/tempting distinction and a bounded task; no passage-translation phase is imposed.
- Existing older states continue without restart; invalid depths and extra state fields fail clearly.
- Unauthenticated, expired, wrong-audience or forged JWT requests cannot run MCP tools.

## Practical boundary

The deterministic code enforces depth selection, state validity, portioning and per-call packet limits. Research order, notes, name meanings, literary interpretation and progressive prose delivery are host instructions with explicit contracts; they are not a separately enforced multi-model workflow. The Worker does not create asynchronous model jobs or a reviewed etymology database. Manual study trials in Preview are still needed to judge prose quality.

## Later work

After this Preview trial: tune against actual Standard/Detailed/Full transcripts; add reviewed occurrence-level translation/name records as useful; expand canonical dossiers; consider host-managed phase state or a richer study interface only if the current chat workflow needs it. Production promotion is a separate user decision.

## Local verification completed

35 Python checks, six Worker test groups, 1,943 matching Python/Worker cases, the ten-tool stdio adapter and eleven-tool authenticated HTTP lifecycle passed. All eight repository skill frontmatter/link checks passed. Wrangler deployment dry run passed; compressed Worker is 1,193.22 KiB. The source snapshot and prepared evidence counts remain unchanged. See preview-validation.json for the reproducible check summary. Live Preview verification follows publication; prose quality is assessed with actual study trials.

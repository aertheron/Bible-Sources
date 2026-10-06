# Structured handoffs 0.1.0

Keep each stage separate. Pass a concise JSON object retaining evidence, decisions, meaningful alternatives and uncertainties. Load only the relevant stage packet and necessary source spans, rather than accumulating all prior prose. A staged prompt within one conversation does not itself clear that conversation's context; separate model calls or host-managed state are required for actual context isolation.

Every envelope has exactly ten fields: `schema_version`, `study_id`, `stage`, `reference`, `language`, `translation_format`, `depends_on`, `evidence`, `payload`, `uncertainties`. Use schema 0.1.0, a stable study ID, a current bounded reference (or null for a topic stage), language code and one of the three documented display formats. `depends_on` and `uncertainties` are arrays of strings. `evidence` contains unique objects with string `id` and `locator`; additional provenance fields may identify commit/hash/annotation status.

| Stage | Exact payload fields |
| --- | --- |
| fetch_align | source_packets (array), alignment_status (string) |
| collate_compare | differences (array), comparison_limits (array) |
| evaluate_select | decisions (array), unresolved (array) |
| translate_annotate | verses (array), footnotes (array), term_key (array), context_preface (string) |
| exegetical_synthesis | observations (array), biblical_development (array), canonical_links (array), formation (array) |
| theology_review | claim_reconstruction (string), findings (array), verdict (string) |
| dss_research | records (array), reconstruction_limits (array) |

Use the published JSON schema plus `check_handoff`/`validate-handoff` for reference and budget checks. Maximum 16,000 characters per stage envelope. The validator checks contracts, not source coverage, witness authentication, grammar, translation quality or theological truth.

Each translation verse has exactly `reference`, `working_translation` and `alignment_groups`. Each alignment group has exactly `source_token_ids`, `original`, `transliteration`, `gloss`. Supply actual IDs and original forms. Interlinear formats require nonempty groups; plain translations may have an empty group array. Check that all source tokens intended for display are accounted for, in order, with no invented forms; check coverage manually against the retrieved packet. Verse rows must be unique single verses within the envelope reference.

For each reading assessment, supply reference, base_reading_id, significance and one to twelve readings. Each reading has exactly id, text, source_ids, evidence, status and independence_group. Status is attested/reconstructed/unverified/unavailable. Attested readings, including omissions, need identified evidence. The named base must be attested. A supplied assessment has exactly selected_reading_id, reason, evidence, counter_evidence, reviewer and confidence (low/medium/high); the selected reading must be attested. Code validates this assertion's structure; the reviewer must validate that evidence actually supports it.

With no completed assessment, retain the named base provisionally. Insignificant differences retain the base while keeping the records. A requested_inclusion_id requires a registered textual case and exact, nonempty, attested wording; study inclusion is distinct from authenticity. Do not generate a rejected reading or manuscript attribution to fill an empty footnote array.

Use concise factual notes for meaningful alternatives. Exegesis and theological review retain relevant evaluated alternatives and key-term uncertainty, not just a translation stripped of its qualifications. If the budget is exceeded, split a stage into smaller passage portions and merge concise findings; never truncate a source packet until it falsely appears complete.

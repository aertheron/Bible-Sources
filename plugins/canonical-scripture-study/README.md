# Canonical Scripture Study — Preview 0.1.4

*Study Scripture through its languages, context, and canonical story.*

A public, inspectable Bible study plugin combining biblical theology, canonical theology and contextual working translation. Eight skills guide the host model; a Python runtime supplies pinned, hash-verified passages and bounded knowledge packets. The runtime does not generate translations by replacing dictionary words.

## Start locally

Python 3.10 or later is required. From the repository root, the core CLI works without installing dependencies:

```bash
python3 plugins/canonical-scripture-study/scripts/bible.py health
python3 plugins/canonical-scripture-study/scripts/bible.py plan 'Full study Romans 12:1-2, in Dutch, with original language interlinear'
python3 plugins/canonical-scripture-study/scripts/bible.py passage 'Genesis 1:1-3' --sources WLC LXX TAHOT
python3 plugins/canonical-scripture-study/scripts/bible.py dss 'Genesis 1:27' --limit 1
python3 plugins/canonical-scripture-study/scripts/bible.py word testing
```

For the optional local MCP server:

```bash
cd plugins/canonical-scripture-study
python3 -m venv .venv
# Activate this environment using the command for your operating system.
python3 -m pip install '.[mcp]'
bible-study-mcp
```

Configure an MCP-capable host to start that environment's `bible-study-mcp` executable. Its standard input/output is the protocol; use the CLI for ordinary terminal JSON. The portable [plugin manifest](plugin.json), [MCP configuration](mcp.json), eight `skills/` folders and repository marketplace catalogue support package discovery on compatible surfaces. For a different Python environment, adjust the host's executable path. Installing the Python wheel installs the retrieval runtime; obtain the full repository plugin folder to use the skills and manifest.

The study interface is a ChatGPT conversation in Chat or Work. Once connected and installed, select **@Canonical Scripture Study** and ask for a passage study or a focused command. ChatGPT uses the skills to translate and explain the retrieved evidence.

The code and local runtime are published. A [free Cloudflare hosting package](cloudflare/) now supplies a native Worker, verified static source assets and a Streamable HTTP endpoint. Use its setup guide to deploy and then connect the actual HTTPS `/mcp` URL in ChatGPT. The existing OAuth deployment uses https://study.canonical-theology.com/mcp; this iteration is tested on the separate Preview connection before promotion. This hosting path needs no model API key; ChatGPT performs the study. Publishing these files does not replace the existing personal plugin or create a public Plugins Directory listing.

## Preview version and updating ChatGPT

The manifest, Python adapter, Worker package and MCP `study_health.plugin_version` use the same semantic version (currently **0.1.4** on Preview). The running MCP server uses the deployed Git commit, not the version of this GitHub file until a successful Cloudflare deployment.

Changes to tools, shared MCP instructions or bundled on-demand study instructions take effect on the deployed server. Existing ChatGPT connections pointing to the same HTTPS `/mcp` endpoint do **not** need to be recreated. After a deployment, open the existing ChatGPT plugin connection and choose **Refresh** to rescan tool metadata and instructions, then test in a new conversation. The available UI may vary. The displayed plugin name/icon and any separately imported packaged skill files are not automatically replaced by a Worker deployment. Version changes may be visible through the `study_health` tool rather than the ChatGPT plugin card.

The default delivery contract prefers successive visible assistant messages (orientation, verified translation and notes, exegesis, synthesis) within one user request. If ChatGPT cannot generate successive messages, provide the same content as a progressively streamed answer. MCP tools cannot themselves post chat messages or start background model work. `Next` still means the next Bible passage only.

## Commands and continuation

Natural language is the interface; these are routing aliases, not registered native slash commands. Bare passages default to Standard and complete the bounded study, with verified translation and notes presented before deeper interpretation when the chat host permits progressive output. Choose Detailed or Full for greater depth; a focused command still performs its own task. Explicit commands perform the requested task.

| Command | Output |
| --- | --- |
| Standard study / bare passage | Working translation, relevant notes, brief context and explanation |
| Detailed study | Adds consequential terms, historical/cultural context, visible literary structure and bounded canonical links |
| Full study | Context, translation, notes, local exegesis, biblical/canonical development, theology review |
| Translation only / Translate | Working translation in the chosen format with necessary context and notes |
| Word study | Source terms, contextual senses, translation guidance and bounded canonical development |
| Theme study | Relevant anchors and biblical/canonical development |
| Context and history | Literary, historical and cultural orientation |
| Exegesis only | Passage explanation without requiring a new full translation |
| Translation variance reconciliation | Actual source differences and an evidence-based assessment |
| Theology check | Fair claim reconstruction and contextual evidence review |
| DSS research | Paged physical records, reconstruction status and linguistic annotations |
| Next / Next chapter 2 / Next: Genesis 2 | Continue with the saved mode, depth, language and display format |

English and Dutch aliases are supported. The host can normalize other languages into the documented commands and pass a language code.

Large requests become a sequence: **Genesis 1–2** gives Genesis 1, then Genesis 2 on **Next**. **Genesis 1:1–2:3** remains a single portion, followed by Genesis 2:4–25. A request for the whole of Isaiah starts at Isaiah 1. Psalm 119 uses its 22 eight-verse stanzas; Luke 1 uses 1–25, 26–56 and 57–80. Ten long chapters have curated study boundaries; others use explicitly provisional size boundaries that the host should review against discourse. Do not reject a valid request solely for length or silently discard the remainder.

Save `continuation_state` from a plan response. In the CLI, put this object (not the entire response) in `state.json` and run:

```bash
python3 scripts/bible.py plan Next --state state.json
```

The host retains this state between turns; the read-only server does not store a user's conversation. A normal output is one chapter with up to five adjacent verses, with a soft size ceiling of 45 verses. Dense linguistic or interlinear output may need smaller sequential portions, even inside that ceiling. Suggest the complete literary unit without silently expanding the user's reference. Detect dependent openings such as Romans 12's “therefore” and explain their context before translation.

## Translation and study method

Use plain working translation, transliteration interlinear, or original-language interlinear. The last displays **original → transliteration → contextual gloss**, followed by a readable clause translation where helpful. Translate into English, Dutch or another requested language and label substantial output as a working translation.

Render YHWH as Yahweh. Preserve distinctions between Sheol, Hades, Gehenna, Tartarus and abyss; explain their contextual use. Do not force one gloss onto nephesh, psychē, aiōnios or other contested terms. Matthew 6:13 and James 1 use a related Greek testing/tempting family; agency, desire and context matter. A perceived translated contradiction must be checked against the actual forms and argument.

The preferred method serves Mark Gatzen's Christian formation project. It is an explicit working biblical/canonical theology, open to correction from Scripture and evidence. Denominational systems are not the default curriculum or premise. The complete current website claim profile has not been imported, so the MVP cannot claim to encode every project conclusion.

## Evidence and architecture

The skills form a modular pipeline: fetch and check alignment, collate, evaluate, translate/annotate, synthesize, review. [Strict JSON envelopes](schemas/handoff.schema.json) retain source evidence, alternatives, uncertainty and dependencies. Checks enforce fields, scope and packet size; they do not certify linguistic truth. The host must check source coverage and alignment.

Reading evaluation preserves a named base unless a documented assessment supports another attested reading. Christological usefulness, difficulty, brevity and numerical agreement never automatically elect a reading. The 17-entry textual-case registry flags special review; it does not automatically make the longest reading earliest. Bracket disputed study inclusions only from exact, identified source text. See [the method](references/method.md) and [translation key](references/translation-key.md).

Retrieval uses commit `df1ed50b4aa532c14c9587106b75693414aaa622`. A full checkout reads local spans; a standalone installed runtime lazily retrieves pinned GitHub metadata and byte spans and caches them. Set `BIBLE_STUDY_DATA` to a checkout or `BIBLE_STUDY_CACHE` to a cache directory. `BIBLE_STUDY_OFFLINE=1` requires already cached data. Metadata and returned spans are SHA-256 verified. No text normalization or source corrections are applied. [Runtime details](references/runtime.md) describe tools, provenance and limits.

Included readers cover WLC/OSHB, UXLC, all TAHOT fields, Brenton Greek, SBLGNT and its edition-comparison apparatus, and enriched DSS exports. The ordinary reference router covers 66 base books; additional Greek books and Psalm 151 need separate native-edition access (`Reader.native_chapter` in Python), and do not yet have dedicated CLI/MCP routing. Native numbering remains explicit: **book routes and equal verse numbers do not constitute reviewed cross-edition equivalence**. WLC/UXLC are related transcriptions, not independent witnesses. Greek surface tokenization provides stable derived IDs and exact character offsets, not an invented lemma/morphology layer.

The 50 complete word studies are retrieved one or two at a time with up to six compact context pointers; related entries are not automatically loaded. Selected lexical data is not a complete lexicon or concordance. Six provisional canonical seed dossiers supply up to six anchor pointers; the host retrieves relevant local contexts. Independent Hebrew/Greek and biblical-context analysis comes first. Standard and Detailed do not browse by default; Full uses BibleProject/academic leads selectively afterwards for a specific deepening question. These are research leads, not a mirrored commentary collection. New completed studies can grow the public collection through its existing review/update process; chat drafts are not automatically published.

## Limits and next work

Rahlfs stays outside the public profile. Swete is not ingested. The apparatus is not a full critical manuscript apparatus. Exact macro-variant witness spans, Greek/Hebrew verse maps, wider canonical dossiers, occurrence-level translation keys, further scholarly argument curation and the complete current working-theology profile still require review. DSS reconstruction does not equal surviving ink; missing coverage does not prove omission.

Code/skills are MIT licensed. Dataset licences remain separate, including **CC BY-NC 4.0 for DSS**. See the repository's attribution and source terms.

Run core checks with `python3 -m unittest discover -s tests -v`; run `python3 tests/mcp_smoke.py` after installing the MCP extra. [REVIEW.md](REVIEW.md) records what the MVP does and what it does not establish.

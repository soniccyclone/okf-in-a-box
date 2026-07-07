# Open-Questions Research — Findings & Recommendations (§8 of design-spec)

> Research synthesis for the design-spec's open questions. Each question was researched
> independently (broad web search on prior art + failure modes). This doc records the
> options, the decisive reasoning, prior art, and a **recommendation** per question, plus
> the **specific decision** needed before folding into `design-spec.md`.
>
> **Sourcing caveat:** the research surfaced some fabricated/future-dated arXiv IDs
> (flagged and discarded by the agents). Claims below are anchored on verifiable primary
> sources (W3C PROV, GDPR text, Wikipedia policy, CrewAI source, mem0/Zep papers, Presidio
> docs). A few legal items (EDPB 01/2025 pseudonymisation guidelines, CJEU *EDPS v SRB*)
> should be re-read from primary sources before they go load-bearing in code.

---

## OQ1 — Judge scope: gate autonomous writes only, or all writes?

**Recommendation:** **Tiered gate (the Wikipedia autopatrolled / pending-changes model).**
Split the judge into two concerns:

- **A cheap privacy/PII/secret screen that blocks *everyone*** — including human editors.
  A leaked credential is catastrophic and author-independent, and it's objectively
  checkable (low false-positive, low latency), so blocking humans here costs almost nothing.
- **A quality/consistency judge that *blocks agents* but only *advisory-lints* humans** —
  human edits commit immediately; the judge runs async as a linter that flags questionable
  human edits into a review/patrol queue (which the dreamer can consume as prioritized work).
- **Blast-radius escalation:** a human *mass* edit or an edit to a load-bearing core concept
  escalates from advisory into the blocking quality path (human edits at scale have
  agent-like propagation risk).

**Decisive reasoning:** the judge's value is highest exactly where accountability is lowest
and volume highest — autonomous dumps. Every mature system (Wikipedia pending-changes /
autopatrolled, Stack Exchange reputation gates, InnerSource "trusted committer") earned the
"gate the untrusted, advisory-patrol the trusted" design through real scars: hard-gating
trusted humans produces insult, workarounds, and false-positive friction that drives away
your best curators. But "don't gate humans at all" (the pure trusted-committer option) lets
humans seed errors the dreamer then amplifies — cheaply neutralized by advisory-linting
rather than blocking. Trust boundary = **author accountability + write risk**, not author
alone.

**Prior art:** Wikipedia [Pending Changes](https://en.wikipedia.org/wiki/Wikipedia:Pending_changes)
/ [Patrolled revisions](https://en.wikipedia.org/wiki/Wikipedia:Patrolled_revisions);
Apache Beam / InnerSource [Trusted Committer](https://patterns.innersourcecommons.org/p/trusted-committer);
mem0's LLM ADD/UPDATE/DELETE/NOOP arbitration (machine-write gate, no human tier). Notably,
AI-memory systems (mem0/Letta) treat write-gate validation + human trust tiers as a **blind
spot**, not a solved feature — we'd be ahead of the field here.

**This refines the current §4.3** ("autonomous only; humans fully bypass"). The refinement:
humans still bypass the *quality* gate, but not the *privacy* gate, and high-blast-radius
human edits escalate.

**Decision needed:** Accept the tiered model, or keep the simpler "autonomous-only, humans
fully bypass"? (I recommend tiered — the universal privacy screen is the important add.)

---

## OQ2 — Provenance cardinality + re-derivation semantics

**Recommendation:** **Many-dumps-to-one-concept via a first-class provenance edge table;
re-derivation SUPERSEDES the current-state row and APPENDS to the ledger.**

- `concept_provenance(concept_path, raw_dump_id, contribution_role, valid_at, invalid_at, …)`
  — the *dump references accrete* (one concept, many sources over time). This is the
  Wikidata "one claim, many references" shape.
- Re-derivation is a normal `UPDATE` to the current-state concept; the existing ledger
  trigger writes the prior body to the append-only ledger. "Supersede vs. append" dissolves
  once you separate the log (ledger) from the projection (current-state) — you do both.
- **Soft-invalidate** provenance edges (set `invalid_at` + a machine-readable reason), never
  delete — this is what preserves "why did the concept ever say X."
- **Force the memory-edit agent to cite** which dump(s) justified which claims (the
  Generative Agents "insight (because of 1,2,8)" move) — the antidote to unexplainable fusion.

**Decisive reasoning:** one-dump-one-concept contradicts the product thesis (a concept
sharpened by many contributions). Full immutable-node-per-version (W3C PROV literal) is the
"correct" answer but is exactly the provenance-bloat generator the lineage literature warns
about — you'd pay O(versions × sources) graph growth for point-in-time queries the
ledger + timestamped edges already answer. Full bitemporal-everything (Zep/Graphiti) is
over-engineered for a Postgres microservice and leans on LLM contradiction-detection quality
(Zep's own numbers show it degrading on weaker models).

**Prior art:** [W3C PROV](https://www.w3.org/TR/prov-dm/) (`wasDerivedFrom`/`wasRevisionOf`);
[Wikidata ranking](https://www.wikidata.org/wiki/Help:Ranking) (deprecate-not-delete);
[mem0](https://arxiv.org/html/2504.19413v1) (overwrite live + side history table);
[Zep/Graphiti](https://arxiv.org/abs/2501.13956) (bitemporal invalidation);
[Generative Agents](https://arxiv.org/abs/2304.03442) (cited evidence pointers);
event sourcing ([Fowler](https://martinfowler.com/eaaDev/EventSourcing.html)). Key nuance
from Datomic: **accumulate-only (semantic) ≠ append-only (storage)** — we want the semantic
guarantee, which our ledger already gives.

**Failure modes to engineer against:** provenance bloat (cap/paginate edges per concept;
concept-level granularity, not claim-level, unless needed); conflicting sources that echo
each other (don't let "3 dumps agree" count as strong evidence — they may share an origin).

**Decision needed:** Confirm many-to-one + supersede-current/append-ledger + soft-invalidate
+ mandatory citation. (Strong recommendation; this slots cleanly onto existing §4.5.)

---

## OQ3 — Judge rejection handling

**Recommendation:** **Reason-routed, not one global policy. Never silently discard without
logging.**

- **Log every rejection always** (concept, verdict, reason class, rationale) even when the
  end state is discard — dashboard reject-rate by reason as the memory-edit-agent regression
  alarm. (Silent discard violates our own "fail fast, not silent" rule.)
- **Quality/format rejection → exactly one bounded repair retry**, feeding the judge's
  *specific* critique back to the memory-edit agent (not "rejected: low quality"). Bound = 1
  (2 total judge passes), enforced by a stored attempt-count; raise only if the
  "rescued-on-retry" metric justifies it.
- **Privacy rejection → NEVER free-form LLM rewrite** (risks relocating the secret into a new
  field). Deterministic redaction + one re-judge, or straight to human review.
- **Repair-exhausted / privacy-ambiguous → owned human review queue** — but *only if* you
  commit to a named owner role, queue-depth alerting, and a triage SLA. Otherwise it's a
  graveyard and discard-with-telemetry is more honest.

**Decisive reasoning:** the rejection *reason* is the load-bearing variable; privacy and
quality rejections have opposite repair economics. Bounded external-feedback repair works
(your judge is the external signal Huang et al. show is required — intrinsic self-correction
fails/degrades); unbounded loops are documented token bonfires with oscillation risk.

**Prior art:** [Self-Refine], [Reflexion](https://arxiv.org/pdf/2303.11366) (bounds trials,
detects stuck loops), [Huang et al. ICLR'24](https://arxiv.org/abs/2310.01798) (intrinsic
self-correction doesn't work without external signal), [AWS SQS DLQ](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html)
+ the well-documented "DLQ graveyard" antipattern.

**Decision needed:** (a) Accept 1 repair retry for quality rejections? (b) Do we build the
human review queue now (requires an owner + alerting commitment), or start with
discard-with-telemetry and add the queue later?

---

## OQ4 — Dreamer cadence, blast-radius, cost controls

**Recommendation:** **Three independent kill switches — dirtiness-gated cadence, hard
per-run scope cap + cooldown, gateway cost circuit-breaker — plus reversibility and
deterministic freshness.** No serious consolidation loop runs on a plain wall-clock timer
with unbounded scope.

Concrete defaults for a 10⁴–10⁵ corpus:
- **Cadence:** nightly off-peak cron *as an upper bound*, but the run is a **no-op unless a
  "dirtiness budget"** (accumulated stale/flagged/duplicate pressure) crosses a threshold —
  Generative Agents fires reflection on summed-importance > threshold, not the clock.
  Debounce/coalesce bursts into one batched sweep.
- **Scope:** hard cap **~200 proposed edits/run** (deliberately <1% of corpus, so a bad run
  is a canary not a catastrophe) + **7-day per-record cooldown** (the hard guarantee against
  thrash and the forcing function for convergence). Sampled/ringed, never exhaustive.
- **Cost:** hard **per-run + per-day token/dollar budget at the gateway** with a circuit
  breaker that kills mid-run on breach. Two-tier routing: cheap model scans/triages (reading
  10⁵ records is the expensive part), expensive model only drafts proposals + judges.
- **Non-negotiables:** (1) **invalidate-not-delete** (every edit reversible → a bad sweep is
  undoable — same primitive as OQ2's soft-invalidate); (2) **deterministic freshness** —
  timestamps/versions decide recency, *never* the LLM (LLMs resolve the same conflict
  differently across runs); (3) **judge is a different model+prompt than the proposer**, and
  its **reject-rate is a canary metric** — spike mid-run → auto-halt; (4) **human approval
  gate** when a run wants to exceed the cap.

**Decisive reasoning:** the expensive/dangerous ops are *reading the whole corpus* (cost) and
*writing across it* (corruption). The dirtiness gate attacks wasted reads; edit-cap + cooldown
+ sub-1% sampling bound the writes; invalidate-not-delete makes the worst case recoverable.
Design assumption: any single guard eventually fails, so none is load-bearing alone.

**Prior art:** [Generative Agents](https://arxiv.org/abs/2304.03442) (event-driven reflection);
[mem0](https://mem0.ai/blog/long-term-memory-ai-agents) (bounded per-op blast radius);
[Zep/Graphiti](https://arxiv.org/abs/2501.13956) (invalidate-not-delete);
[LangMem ReflectionExecutor](https://langchain-ai.github.io/langmem/guides/delayed_processing/)
(debounce). *(One cited arXiv on deterministic conflict resolution was future-dated — treat
that specific claim as directional; the underlying principle is sound regardless.)*

**Decision needed:** Confirm the default knobs (nightly-upper-bound + dirtiness gate; ~200
edits/run; 7-day cooldown; gateway budget). These are defaults an operator can tune — I just
want your sign-off on the shape and starting values.

---

## OQ5 — OKF `index.md` / `log.md` fidelity

**Recommendation:** **Export: regenerate both from our internal model. Import: ignore both,
regenerate our own.**

- **Export `index.md`:** emit a full per-directory index (matches what all 3 reference
  bundles do — they ship an index.md in *every* directory). It's a free projection of data
  we already have; descriptions come from concept frontmatter. Follow the reference
  producer's observed convention of linking children as `child/index.md` (the spec's own
  example says `child/` — even Google's generator doesn't match its own example, so be
  lenient reading both).
- **Export `log.md`:** generate from our append-only ledger. **This is where we're
  differentiated** — the reference repo ships **zero** log.md files; almost no producer can
  emit an honest change history, but our ledger *is* exactly that. Deterministic fold:
  ISO-8601 date headings (the one `MUST` in §7), newest-first, `**Creation**`/`**Update**`/
  `**Deprecation**` bold prefixes (convention).
- **Import:** ignore producer-authored `index.md`/`log.md` for building state. `index.md` is
  100% derivable (pure view → ingesting invites drift). `log.md` is unstructured prose with
  no reliable schema (§7: "Log entries are prose") → structured ingestion is unreliable by
  construction. Per §9, consumers MUST NOT reject on missing/odd reserved files anyway.

**Spec anchors (verbatim, §9 conformance):** every non-reserved `.md` has parseable YAML
frontmatter; every frontmatter has non-empty `type`; reserved files follow §6/§7 *when
present*; consumers MUST NOT reject on missing optional fields / unknown types / unknown
keys / broken links / missing index.md. Source:
[SPEC.md](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md).

**Decision needed:** Confirm regenerate-both-on-export, ignore-both-on-import. **Follow-up
bead flagged:** an imported `log.md` is the *only* carrier of pre-custody history — if that
ever matters, store it *verbatim as an opaque provenance artifact* keyed to its directory
(never parsed into our authoritative ledger). Defer until a real consumer needs it.

---

## OQ7 — Scrubbed derivation-input snapshot under short TTL

**Recommendation:** **Tiered retention with three independent clocks; crypto-shred the raw
dump; a pseudonymised snapshot on its own medium TTL (treated as personal data); degrade to
"forfeit re-derivation" by setting snapshot-TTL=0.** Do **not** offer "permanent scrubbed
retention."

**The reframe that kills the naive plan:** under GDPR there are only two legal states, on
opposite sides of a cliff. **Pseudonymised** text (identifiers removed but re-identification
still reasonably possible — which any *useful* snapshot is, given residual quasi-identifiers
+ sub-100% detection recall) is **still personal data** — full storage-limitation (Art.
5(1)(e)) and erasure (Art. 17) obligations. **Anonymised** to the WP29 triad (no
singling-out / linkability / inference) is out of scope — but that bar strips the very detail
the LLM needs to re-derive a *good* concept, and you usually can't even *certify* it. So
"scrub it and keep it forever" doesn't delete the liability, it *moves* it — and often can't
be certified.

Therefore three tiers, three clocks, nothing mislabelled:
- **Raw dump** — short TTL, **purge = crypto-erasure** (per-record data key; destroy the key,
  not chase every backup replica). Once the key is irrecoverable the ciphertext trends
  non-personal (relative-identifiability, *Breyer* / *EDPS v SRB*).
- **Pseudonymised derivation-input snapshot** — *medium* TTL (e.g. raw=30d, snapshot=180d–1y,
  concept=indefinite; all org-tunable), **explicitly classified personal data**, wired into
  the same erasure path, built with consistent pseudonymisation (Presidio
  `InstanceCounterAnonymizer` / GCP DLP FPE-FFX) so entities stay coherent for re-distillation.
  **Don't keep the identifier↔surrogate mapping vault by default** (it's a re-identification
  bomb + extra erasure surface). Run k-anonymity/risk analysis so "how identifying is this
  still" is *measured*, not assumed.
- **Concept** — durable.

**Decisive reasoning:** re-derivation is *occasional* (only when the distillation prompt
materially improves), so a *bounded* window captures most of the value without becoming a
permanent PII controller. Crypto-shredding makes "purge" actually true across replicas
(row-delete is a lie across backups). De-id is defence-in-depth, never a certificate
(clinical NER tops ~95–99% F1 and degrades OOD; Sweeney 87% unique on {ZIP,DOB,sex}; Rocher
99.98% on 15 attributes).

**Prior art / tools / law:** [Presidio](https://github.com/microsoft/presidio) (encrypt =
only reversible op; consistent surrogates via custom `InstanceCounterAnonymizer`);
[GCP Sensitive Data Protection](https://cloud.google.com/sensitive-data-protection/docs/transformations-reference)
(FPE-FFX + built-in k-anonymity/l-diversity risk analysis);
[NIST SP 800-38G](https://csrc.nist.gov/pubs/sp/800/38/g/upd1/final) (use FF1, not the broken
FF3); [GDPR Recital 26](https://gdpr-info.eu/recitals/no-26/) + [Art. 5](https://gdpr-info.eu/art-5-gdpr/)
+ [WP29 05/2014](https://ec.europa.eu/justice/article-29/documentation/opinion-recommendation/files/2014/wp216_en.pdf);
[HIPAA de-id](https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/index.html)
(Safe Harbor's 18 identifiers + "residual risk"). Zep/Graphiti's raw+derived tiering is the
shape Option 4 formalizes with independent TTLs. *(Verify EDPB 01/2025 final-adoption status
and read *EDPS v SRB* C-413/23 P operative paragraphs before the crypto-shred legal argument
goes load-bearing.)*

**This revises §4.2/§4.15's "keep raw forever by default."** New default should still be
forever (sensible default), but purge = crypto-erase, and the snapshot tier is the mechanism
that lets short-TTL orgs keep a bounded re-derivation window.

**Decision needed:** Do we build the three-tier retention (raw crypto-shred + medium-TTL
pseudonymised snapshot + durable concept), or keep it simple for v1 (raw forever/TTL, no
snapshot tier, short-TTL orgs simply forfeit re-derivation per current §4.15)? The three-tier
is the *right* long-term answer but is real engineering (key management, second clock, erasure
fan-out) — could be a documented v2.

---

## OQ8 — External-system integration surface

**Recommendation:** **Ship three surfaces, each assigned to what it's actually good at:**

1. **Thin client library** (Python first) over a **documented, stable HTTP contract** — the
   backbone. Every peer (mem0/Zep/LangMem) distributes this way; it's load-bearing, not
   resume-padding. Always publish the raw HTTP contract underneath so we're never a bottleneck.
2. **A bundled CrewAI auto-capture helper for SAVE**, hooked to the event bus's
   **`LLMCallCompletedEvent` / `TaskCompletedEvent`** — *not* the `task_callback` constructor
   arg or `after_kickoff`. **Only the event bus exposes the verbatim `messages` array** (the
   real prompt + system instructions + accumulated context); the callbacks/kickoff hooks hand
   you the *distilled* `TaskOutput`/`CrewOutput`, which defeats the raw-source-of-truth
   premise. One-liner for integrators: `OKFMemory(api_key=...).attach(crew)`.
3. **An MCP server for RECALL only** — universal agent-invoked read across any MCP client.

**MCP structurally cannot do verbatim SAVE** — three reasons: the host/model decides when
tools fire (agent can *forget*, the exact failure we're avoiding); tool inputs are
*model-authored* (you get the model's self-summary, not verbatim context); the server never
sees the system prompt/orchestration context by design. So expose SAVE over MCP at most as an
*optional manual escape hatch* for non-CrewAI callers, documented loudly as lossy.

**This confirms and sharpens §5.** The instinct (save = lifecycle callback, recall = tool)
was right; the sharpening is the *specific hook* (`LLMCallCompletedEvent` on the event bus,
not `task_callback`) and the universal split (MCP for recall, never for verbatim save).
Distillation stays **server-side** (mirroring mem0's `infer=True`): callers ship raw verbatim
context, we extract.

**Prior art:** [CrewAI event listeners](https://docs.crewai.com/en/concepts/event-listener)
(`LLMCallStartedEvent.messages` = verbatim prompt); [mem0 `add(infer=)`](https://docs.mem0.ai/core-concepts/memory-operations/add)
(verbatim vs. server-distill); [Zep MCP](https://blog.getzep.com/unified-agent-memory-in-any-mcp-client/);
[LangMem](https://langchain-ai.github.io/langmem/) (hot-path tools + background manager split
— exactly our recall/save distinction).

**Biggest risk to flag:** CrewAI's event API is young and churns (there's a known
`LLMCallStartedEvent.messages` multimodal validation bug) — the auto-capture helper needs
version pinning + a CI test against each CrewAI release, or it silently stops capturing.

**Decision needed:** Confirm all-three-surfaces (thin client + CrewAI event-bus helper + MCP
recall-only). Anything to defer to v2? (I'd ship client + HTTP contract + CrewAI helper day
one; MCP recall server can be a fast-follow.)

---

## Summary of decisions needed

| # | Question | Recommendation | Your call |
|---|----------|----------------|-----------|
| OQ1 | Judge scope | Tiered: block agents + universal privacy screen; advisory-lint humans; blast-radius escalation | Accept tiered vs. keep simple autonomous-only? |
| OQ2 | Provenance | Many→one edge table; supersede-current/append-ledger; soft-invalidate; mandatory citation | Confirm? |
| OQ3 | Rejection | Log always; 1 repair retry (quality only); deterministic/human for privacy; owned queue or discard-w/-telemetry | Accept 1 retry? Build review queue now or later? |
| OQ4 | Dreamer | Dirtiness-gate + ~200 edits/run + 7-day cooldown + gateway budget + invalidate-not-delete + deterministic freshness | Sign off on default knobs? |
| OQ5 | index/log.md | Regenerate both on export; ignore both on import | Confirm? |
| OQ7 | PII snapshot | 3-tier: crypto-shred raw + medium-TTL pseudonymised snapshot + durable concept; TTL=0 forfeits | Build 3-tier now, or v2 (simple forfeit for v1)? |
| OQ8 | Integration | Thin client + HTTP contract + CrewAI event-bus SAVE helper + MCP recall-only | Confirm? Defer MCP to fast-follow? |

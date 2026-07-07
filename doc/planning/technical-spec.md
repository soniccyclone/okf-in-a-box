# OKF-in-a-Box — Technical Implementation Spec (the HOW)

> **Status:** Draft, in progress. This is the *implementation* companion to
> [`design-spec.md`](./design-spec.md). Where the design spec argues **why** the system is
> shaped the way it is, this document specifies **how** it is built and **how we prove it
> works**: the layered architecture, the local dev environment, the concrete data model and
> API contracts, the Critical User Journeys (CUJs), and the testing strategy tied to them.
>
> Section-by-section authoring is tracked in beads under epic `okf-in-a-box-00z`. Sections
> not yet filled are marked _(pending — TS#)_.

---

## 1. Purpose, scope, and how to read this

### 1.1 What this document is

The design spec settled the decisions: Postgres is the whole box; a two-stage
raw-dump → distilled-concept pipeline; a tiered judge gate; a dreamer under hard guardrails;
hybrid retrieval; a hot-core priming layer; OKF only at the import/export boundary; per-agent
models against the org's AI gateway. **This document does not re-argue any of that.** It
takes those decisions as fixed and specifies the buildable artifact:

- the **architecture** — an n-tier layered application following Litestar's idioms, and where
  each design-spec concept lives in code (§3);
- the **local dev environment** — everything a contributor needs to run the whole system on a
  laptop, on Linux or macOS (§4);
- the **data model** — concrete tables, indexes, triggers, and migrations (§5);
- the **API** — endpoint contracts for the machine hot path, the admin console, and
  import/export (§6);
- the **Critical User Journeys** — the end-to-end flows every actor takes, which are the
  backbone of both the implementation and the tests (§7);
- the **testing strategy** — integration-first, tied one-to-one to the CUJs (§8);
- **cross-cutting concerns** and **build/CI** (§9, §10).

### 1.2 Scope and non-goals

**In scope:** the concrete shape of the v1 service — modules, tables, endpoints, journeys,
tests, dev setup. Enough that an implementer (human or agent) can pick up a bead and build a
slice without re-deriving design intent.

**Out of scope / deferred (per design-spec §7, §8):** the v2 three-tier crypto-shred +
pseudonymised-snapshot retention model; CLI-shell-out LLM wrappers as a production path
(dev-only); any multi-tenant/RBAC-region isolation (sensitive knowledge → a separate
deployment). These are noted where they touch a v1 seam, but not specified here.

### 1.3 Relationship to the design spec

Every major section cross-references the design-spec section it implements. The mapping:

| design-spec (WHY) | technical-spec (HOW) |
|---|---|
| §3 system shape, §4.1 Postgres-is-the-box | §3 Architecture, §5 Data model |
| §4.2 two-stage ingestion, §4.12 read/write asymmetry | §6 API, §7 CUJs (hot path + pipeline) |
| §4.3 tiered judge gate | §7 CUJs (pipeline), §8 tests |
| §4.4 dreamer guardrails | §7 CUJs (pipeline) |
| §4.5 ledger, §4.6 relational mapping | §5 Data model + triggers |
| §4.7 import/export | §6 API, §7 CUJs (admin ops) |
| §4.8/§4.9 RBAC + auth | §3 (guards/middleware), §6 (auth), §7 (console CUJs) |
| §4.10 models / AI gateway | §4 dev env, §8 (deterministic agent testing) |
| §4.14 hybrid retrieval | §5 (pgvector + FTS indexes), §7 (recall CUJ) |
| §4.15 sanitization seam + PII knobs | §3 (decorator seam), §9 security |
| §4.16 tags / sensitive deployment | §5 (tags), §7 (admin ops) |
| §4.17 priming / hot core | §5 (`core` marker), §6 (`prime`), §7 (prime CUJ) |
| §5 caller contract, §8 integration | §6 API, §7 CUJs (agent-facing) |

Terminology is shared with the design-spec glossary (§9 there); this doc adds
implementation terms as they arise.

---

## 2. System context (recap)

_A one-screen recap of the runtime topology from design-spec §3, so this doc stands on its
own for an implementer. (Pending — TS1.)_

---

## 3. Architecture — n-tier, following Litestar defaults

_Layered structure (controllers → services → repositories → models/DTOs), dependency
injection, auth guards/middleware, the sanitization decorator seam, the worker tier
(procrastinate), the CrewAI agents, and the concrete module/package layout. Component
diagram. Where each design-spec concept lives in code. (Pending — TS1.)_

---

## 4. Local development environment

_uv + Python 3.13, docker-compose (Postgres+pgvector, Keycloak, optional local LLM server),
owner bootstrap env vars, Makefile targets, the three model backends, embedding model, seed
data. Step-by-step for Linux and macOS. (Pending — TS2.)_

---

## 5. Data model, migrations, and triggers

_Concrete schema for every table (raw_dumps, concepts + core/tags, concept_ledger,
concept_links, concept_provenance, edit_proposals, judge_verdicts, review_queue,
principals/roles/api_keys, import staging, procrastinate queue), the ledger trigger, pgvector
HNSW + FTS/GIN indexes, and migration tooling. (Pending — TS3.)_

---

## 6. API and endpoint contracts

_The machine API (raw-dump write → 202, recall, prime), admin console routes (htmx),
import/export, auth (API key + OIDC). Request/response shapes, status codes, error envelope,
limits, OpenAPI. (Pending — TS4.)_

---

## 7. Critical User Journeys (CUJs)

_The end-to-end flows, grouped by actor. This is the backbone of the implementation and the
tests. (Inventory pending — TS5; journeys pending — TS6a–d.)_

### 7.1 Actors and journey catalog _(TS5)_
### 7.2 Agent-facing hot path — prime, recall, save _(TS6a)_
### 7.3 Autonomous pipeline — memory-edit, judge, dreamer _(TS6b)_
### 7.4 Human console — RBAC, review queue, edit, history _(TS6c)_
### 7.5 Admin ops — import, export, sensitive deployment _(TS6d)_

---

## 8. Testing strategy and test plans

_Integration-first, tied one-to-one to the CUJs (testcontainers Postgres, real/mocked LLM,
deterministic agent testing, golden tests for OKF conformance + RRF + frontmatter + ledger
diffs). Unit tests for pure logic. CI coverage per CUJ. (Pending — TS7.)_

---

## 9. Cross-cutting concerns

_Config/settings, observability (reject-rate / queue-depth / cost dashboards, tracing),
security (auth middleware, XSS sanitization seam, secrets, v2 crypto-shred hook), error
handling and failure modes. (Pending — TS8.)_

---

## 10. Build, tooling, and CI/CD

_uv/ruff/mypy/pytest gates, pre-commit, Makefile standard targets, container build, migration
runs, CI matrix — reconciled with the existing repo template. (Pending — TS9.)_

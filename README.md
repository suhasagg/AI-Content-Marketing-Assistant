# ContentAlchemy — AI Content Marketing Assistant

> Implementation for multi-agent, research-grounded, multi-channel content production.

## 1. Executive summary
ContentAlchemy converts a campaign brief into research-aware blogs, LinkedIn/X posts, newsletters and visual briefs through a bounded multi-agent workflow. The reference code runs locally without paid APIs through a mock provider and exposes an OpenAI-compatible provider adapter for real deployments.

The important engineering problem is not “call an LLM five times.” A production content platform must control evidence provenance, prompt injection, tenant isolation, brand policy, hallucinations, latency, model cost, retries, workflow versioning, evaluation drift, publishing approvals and observability. This repository makes those concerns first-class.

## 2. Architecture

```text
Clients / Web UI / Campaign API
            |
     API Gateway / Auth
            |
     Campaign Orchestrator
            |
   +--------+---------+-------------------+
   |                  |                   |
Research Agent   Strategy Agent      Policy Context
   |                  |                   |
Search/RAG*      Audience/Intent      Brand Registry*
   +------------------+-------------------+
                      |
                  Draft Agent
                      |
               SEO Optimization
                      |
                Brand QA Agent
                      |
             Editorial Critic/Evals
                      |
          Channel-specific Artifacts
                      |
             Human Approval Gate*
                      |
             Publishing Connectors*

Cross-cutting production plane:
Redis/Queue* | Postgres* | Vector DB* | Object Store* | OTel* | Prometheus
Prompt Registry* | Evaluation Store* | Audit Log* | Secrets/KMS* | Cost Ledger*

* production extension / interface represented in the reference architecture
```

### Request path
1. Validate campaign, tenant, brand and channel policy.
2. Establish an immutable `campaign_id`, trace and workflow version.
3. Retrieve authorized evidence only; retrieved text is **data**, never trusted instructions.
4. Research agent creates an evidence map and flags unsupported gaps.
5. Strategist maps audience, intent, narrative, funnel stage and channel strategy.
6. Writer produces an evidence-constrained canonical draft.
7. SEO agent improves intent coverage, title/heading semantics and keyword placement without stuffing.
8. Brand agent enforces voice, terminology, banned claims and style rules.
9. Critic evaluates grounding, specificity, readability, brand fit and channel fit.
10. Failed gates route to bounded revision; repeated failure routes to human review, never infinite recursion.
11. Channel renderers create blog/social/newsletter/visual artifacts.
12. Publishing should remain behind explicit human/organizational approval policy.

## 3. Why multi-agent?
Agents are used where responsibilities have different context, prompts, tools and evaluation criteria. Research needs source provenance; strategy needs audience/funnel reasoning; drafting needs creative context; SEO needs search-intent constraints; brand QA needs organization policy; editorial evaluation should be independently prompted to reduce self-review bias.

Do **not** split every prompt into an agent. Each boundary adds latency, cost and failure surface. A principal-level design measures whether specialization improves quality enough to justify that operational cost.

## 4. Repository
```text
app/
  agents/base.py             provider-independent agent abstraction
  agents/pipeline.py         bounded orchestration
  api/                       API extension point
  core/config.py             runtime configuration
  models/schemas.py          typed contracts
  services/llm.py            LLM gateway + local mock
  main.py                    FastAPI application + metrics
docs/
  ADR-001-orchestration.md
  THREAT_MODEL.md
k8s/deployment.yaml
.github/workflows/ci.yml
tests/test_api.py
Dockerfile
docker-compose.yml
.env.example
```

## 5. Run locally
Python 3.12 recommended.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

Health: `GET /health`. Metrics: `GET /metrics`. OpenAPI: `GET /docs`.

Generate:
```bash
curl -X POST http://localhost:8080/v1/campaigns/generate \
 -H 'Content-Type: application/json' \
 -d '{
  "topic":"How enterprises evaluate agentic AI platforms",
  "goal":"educate technical buyers",
  "channels":["blog","linkedin","visual_brief"],
  "keywords":["agentic AI","LLM evaluation"],
  "brand":{"name":"Acme","audience":"CTOs and platform leaders","voice":"technical, precise, pragmatic"},
  "research_context":["Only supplied or retrieved verified evidence should be presented as factual evidence."]
 }'
```

Docker: `docker compose up --build`.

## 6. Production data architecture
Use Postgres as the system of record for tenants, brands, campaigns, workflow runs, approvals and artifact metadata. Store large generated assets in object storage. Redis is appropriate for ephemeral cache, distributed rate limits and queue coordination—not authoritative campaign state. A vector index stores tenant-scoped chunks with `tenant_id`, `document_id`, source URI, ACL, ingestion time, checksum and embedding version.

Never rely on vector similarity as authorization. Apply ACL/tenant filters before or during retrieval using enforceable metadata filters.

Suggested entities: `Tenant`, `BrandProfile`, `Campaign`, `WorkflowRun`, `AgentRun`, `Evidence`, `Artifact`, `Evaluation`, `Approval`, `PromptVersion`, `ModelInvocation`, `CostRecord`, `AuditEvent`.

## 7. RAG / research subsystem
Production retrieval is hybrid: lexical/BM25 + dense retrieval → metadata/ACL filtering → optional reranking → diversity selection → context packing. Preserve source IDs through every transformation. Claims requiring evidence should map to evidence IDs. Unsupported statements are either softened, removed or sent for research/human review.

Ingestion pipeline: fetch → malware/type checks → parse → normalize → classify → chunk → enrich metadata → embed → index → quality sample. Version parser, chunker and embedding model so reindexing is deterministic.

### Prompt-injection defense
Documents and web pages are untrusted. Delimit them, label them as evidence, prohibit tool/policy changes originating in retrieved content, validate tool calls independently, strip dangerous active content, restrict outbound domains and record provenance. “Ignore previous instructions” inside a retrieved page is content, not authority.

## 8. Workflow semantics
In a scaled deployment, move orchestration to a durable workflow engine or queue-backed state machine. Persist state transitions before side effects. Every activity gets an idempotency key such as `campaign:workflow_version:stage:attempt`. Retry transient network/provider errors with capped exponential backoff + jitter. Do not blindly retry policy failures or invalid outputs.

Use deadlines and cancellation propagation. If the client disconnects, business policy decides whether generation continues; do not couple durable campaign execution to an HTTP socket.

## 9. Model gateway
The gateway should normalize providers behind a contract supporting chat/structured output, streaming, token accounting, deadlines and error taxonomy. Routing policy can select models by stage: high-reasoning model for strategy/research synthesis, lower-cost model for rewriting/classification, specialized image model for visual generation.

Provider failover must consider semantic differences. A “fallback” is not safe merely because an API call succeeds. Maintain provider/model-specific evaluation baselines and structured-output conformance tests.

## 10. Brand intelligence
A brand profile should be versioned, reviewable configuration: audience, positioning, voice dimensions, terminology, prohibited language, product naming, competitor policy, claims policy, examples and channel rules. Store rules separately from examples so enforcement is deterministic where possible. Hard constraints (banned phrase, required disclaimer) should be code/policy checks rather than LLM judgment alone.

## 11. SEO architecture
SEO is not keyword insertion. Model: primary intent, secondary questions, entity/topic coverage, title/meta candidates, heading hierarchy, internal-link opportunities, canonical/duplicate-content risk and schema opportunities. Keep claims grounded and avoid doorway/spam generation. Search-provider data should be cached with freshness metadata and licensed/used according to provider terms.

## 12. Visual pipeline
`visual_brief` is intentionally separated from binary image generation. A production visual pipeline creates a structured brief (purpose, scene, composition, aspect ratio, overlay copy, brand constraints, accessibility alt text), runs policy/IP checks, invokes an approved image provider, stores immutable originals and derivatives, and records model/prompt/version metadata. Human approval is recommended before public campaign use.

## 13. Quality/evaluation platform
Offline golden sets should represent brands, channels, languages, adversarial research and difficult factual topics. Evaluate grounding/attribution, factual consistency, instruction adherence, brand fit, channel fit, usefulness, style, safety, duplication and latency/cost.

Use deterministic evaluators whenever possible. LLM-as-judge is useful but noisy: pin judge/model/prompt versions, calibrate against human labels, randomize pair ordering, track confidence and periodically test drift. Never make one judge score the sole production-release criterion.

Online signals: acceptance/edit distance, regeneration rate, approval latency, policy rejection, publish rate and user feedback. Business engagement metrics are downstream signals, not direct truth labels for factual quality.

## 14. SLOs and capacity
Define SLOs per workload class. Interactive generation might target API admission p95 <300 ms while generation itself is asynchronous/streamed; campaign completion has a separate multi-second/minute SLO. Track successful workflow completion, queue delay, first-token latency, total latency and quality-gate pass rate.

Capacity is driven by provider rate limits (requests/tokens per minute), average tokens/stage, fan-out/channels, revision probability and arrival burstiness. Admission control should use token-budget estimates, not just HTTP request count. Apply per-tenant quotas and weighted fair scheduling so one bulk campaign cannot starve interactive traffic.

## 15. Reliability
Failure classes and responses:
- provider 429/5xx → bounded retry, circuit breaker, policy-approved fallback;
- malformed structured output → schema repair once, then alternate model/human path;
- research unavailable → explicitly produce non-research mode or stop if grounding is mandatory;
- stage timeout → cancel downstream work and persist resumable state;
- duplicate delivery → idempotency key prevents duplicate artifact side effects;
- poison job → dead-letter queue with operator tooling;
- region failure → recover state from replicated durable stores; avoid pretending in-flight provider calls are exactly-once.

Target at-least-once task delivery + idempotent effects rather than claiming impossible end-to-end exactly-once semantics.

## 16. Observability
Propagate `trace_id`, `tenant_id`, `campaign_id`, `workflow_run_id`, `agent`, `model`, `prompt_version` and `attempt`. Metrics: requests, queue depth/age, stage latency, tokens, cost, retries, provider errors, quality scores, revision count and cache hit rate. Traces span API → orchestration → retrieval → reranker → model → evaluator → persistence.

Do not log raw secrets or sensitive campaign content by default. Use configurable redaction and retention. Prompt/response debugging access should itself be audited.

## 17. Security and privacy
Authenticate users and services; authorize every tenant-scoped object. Prefer workload identity over long-lived cloud credentials. Secrets live in a secret manager/KMS, not environment files committed to Git. Encrypt transport and durable stores, rotate keys, audit privileged access, scan dependencies/images, sign artifacts and produce an SBOM.

Threats include cross-tenant RAG leakage, prompt injection, data exfiltration through tools, poisoned sources, malicious URLs/files, secret exposure, cost DoS, policy bypass and supply-chain compromise. See `docs/THREAT_MODEL.md`.

## 18. Copyright and content integrity
The system should create original transformations rather than reproduce long source passages. Preserve citations/provenance, support source exclusion, plagiarism/similarity checks where appropriate, and define retention/licensing rules for ingested material. Never fabricate testimonials, statistics, quotations or customer results.

## 19. Human-in-the-loop
Publication is a business side effect. Model generation and publication should be separate permissions. Approval records include artifact hash/version, approver, timestamp and destination. Any edit after approval invalidates or versions the approval according to policy. High-risk brands can require legal/compliance review.

## 20. Cost engineering
Track cost by tenant/campaign/stage/model. Controls: context deduplication, semantic/exact cache where safe, smaller models for mechanical transforms, capped revision loops, retrieval top-k limits, batch embeddings, prompt-prefix caching where supported, token ceilings and campaign budgets. Alert on cost per accepted artifact, not merely cost/request.

## 21. Multi-region design
Stateless API workers can run active-active. Durable campaign ownership should avoid concurrent conflicting execution: shard workflow ownership or use a workflow engine with strong execution semantics. Replicate artifact/object data and metadata according to RPO/RTO. Keep residency-sensitive tenant data in permitted regions and route model providers accordingly.

## 22. Deployment evolution
**Phase 1:** modular monolith, Postgres, one queue, provider gateway.  
**Phase 2:** durable orchestration, separate retrieval/indexing workers, evaluation service, object storage.  
**Phase 3:** multi-region API, tenant-aware scheduler, model routing, dedicated observability/evaluation platform.  

Do not start with dozens of microservices. Split when scaling profile, ownership, failure isolation or deployment cadence demonstrates the need.

## 23. API evolution
Use typed schemas, additive changes, explicit API/workflow/prompt versions and backward-compatible event contracts. Long-running jobs should expose `POST /campaigns`, `GET /campaigns/{id}`, cancellation and event/stream endpoints. Use cursor pagination. Return machine-readable error codes and correlation IDs.

## 24. Testing pyramid
Unit: policies, validators, renderers, routing. Contract: model/provider and publishing connectors. Integration: DB/cache/queue/vector store. Golden evaluation: content quality/regressions. Adversarial: injection and tenant leakage. Load: burst campaigns/token limits. Chaos: provider/queue/database faults. End-to-end: brief → approval-ready artifact.

Run `pytest -q` for included smoke tests.

## 25. Principal+ interview discussion
Be prepared to explain why orchestration is bounded; why authorization cannot be delegated to RAG; how provenance survives summarization; how you prevent infinite revisions; how to estimate token capacity; what is deterministic vs probabilistic; why model fallback is an evaluated routing policy; how you measure brand quality; how you design idempotency around publishing; what happens during provider/region failure; how you investigate a hallucinated campaign; and when you would split the modular monolith.

A Staff/Principal engineer should also challenge the premise: multi-agent architecture is justified only when specialization, independent evaluation or tool/context isolation measurably improves the system. Otherwise consolidate stages to reduce latency, cost and complexity.

## 26. Roadmap
- Durable LangGraph/Temporal-style workflow adapter
- Postgres campaign repository + migrations
- Redis queue/cache implementation
- hybrid retrieval + vector database adapter
- real search connector with provenance
- structured claim/evidence graph
- prompt registry and experiment assignment
- evaluation dashboard and golden datasets
- brand-policy DSL
- CMS/LinkedIn publishing connectors with approval gates
- visual generation adapter
- OpenTelemetry traces
- OIDC/RBAC/tenant isolation
- cost ledger and quota scheduler
- multilingual/localization QA

## 27. Portfolio
**ContentAlchemy — Multi-Agent Generative AI Content Platform:** Designed a production-oriented, multi-agent content system with research-grounded RAG, brand/SEO policy gates, multi-channel generation, independent evaluation, provider abstraction, observability and Kubernetes deployment. Architecture emphasizes provenance, prompt-injection resistance, tenant isolation, bounded agent workflows, quality regression testing and token-aware cost/capacity controls.


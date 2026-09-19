# Threat Model
Key threats: prompt injection in research documents; poisoned sources; secret leakage; tenant crossover; malicious HTML/URLs; copyright/plagiarism risk; unsupported factual claims; brand-policy bypass; runaway agent loops; model/provider outage; cost denial-of-service.

Controls: isolate retrieved text as untrusted data, provenance metadata, tenant-scoped ACL filters, secret manager, output policy gates, URL allow/deny policy, bounded workflows, token/time budgets, idempotency keys, rate limits, audit logs, human approval for publication, provider fallback and circuit breakers.

# Production Readiness Checklist Reference

Use this as a structured reference during Phase 5 of the spec review.

## Observability
- [ ] Structured logs at appropriate levels (DEBUG/INFO/WARN/ERROR) on all new code paths
- [ ] Request tracing propagated through new services/calls
- [ ] Key business metrics instrumented (success count, failure count, latency histogram)
- [ ] Alerts defined for new failure modes
- [ ] Dashboard updated or new dashboard created

## Resilience
- [ ] All network calls have timeouts defined
- [ ] All external dependencies have circuit breakers or retry logic
- [ ] Graceful degradation path exists for dependency failures
- [ ] Chaos/failure scenarios documented and tested in staging

## Data Safety
- [ ] DB migrations are backward-compatible (no column drops in the same deploy as code deploy)
- [ ] Transactions wrap multi-step DB writes
- [ ] Idempotency keys used on write endpoints where needed
- [ ] Soft delete respected if project uses it
- [ ] PII handling documented and reviewed

## Security
- [ ] All user input validated at the API boundary
- [ ] Auth/authz enforced before business logic executes
- [ ] Secrets via env vars / secrets manager — never hardcoded
- [ ] New endpoints are rate-limited
- [ ] CORS configured correctly for new endpoints
- [ ] SQL parameters are parameterized (no string interpolation in queries)

## Configuration & Deployment
- [ ] Feature flag added (if incremental rollout is needed)
- [ ] Environment variables documented in .env.example / infra config
- [ ] Migrations are idempotent and tested on a copy of prod data
- [ ] Rollback procedure documented
- [ ] No breaking changes deployed without a compatibility window

## Documentation
- [ ] New endpoints documented in API spec (OpenAPI/Postman/etc.)
- [ ] README or runbook updated if operational behavior changes
- [ ] ADR written if a new architectural pattern is introduced
- [ ] Inline comments on non-obvious logic

## Performance
- [ ] Query EXPLAIN plans reviewed for new DB queries
- [ ] Indexes added for new query patterns
- [ ] Large data loads paginated or streamed
- [ ] Caching strategy defined (what to cache, TTL, invalidation)
- [ ] Async offload for long-running operations (queues, workers)

## Testing
- [ ] Unit tests for all new business logic
- [ ] Integration test for new API endpoints
- [ ] Edge cases covered: null/empty inputs, max sizes, concurrent requests, auth failure
- [ ] Migration tested on a staging DB
- [ ] Load test if new code is in a high-traffic path
- [ ] QA acceptance criteria written and signed off
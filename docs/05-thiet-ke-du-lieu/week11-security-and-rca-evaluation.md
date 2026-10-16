# Week 11: Security, Approval, Audit, and RCA Evaluation

## Implemented

- `POST /api/approvals`: technician creates a pending advisory request for an existing ticket.
- `GET /api/approvals`: approver, admin, or auditor lists requests; supports a status filter.
- `POST /api/approvals/{approval_id}/decision`: approver/admin decides once; requester cannot decide their own request.
- `GET /api/approvals/audit`: auditor/admin reads append-only application audit events.
- Decisions only update the approval record. There is no command execution integration.
- Approval descriptions, rationale, decision notes, and audit metadata are redacted before persistence.
- The UI now uses the API so requests and decisions persist in PostgreSQL instead of browser local storage.
- Alembic revision `20261016_0003` adds `approval_requests` and `audit_events`.

## Demo RBAC Warning

For local demonstration, the API accepts `X-Actor-Id` and `X-Actor-Role` headers. These are caller-controlled and are **not authentication**. Do not expose the approval endpoints to a network or production environment until a trusted identity provider/JWT validates the actor and role server-side. The current permission checks are for workflow testing only.

Roles: `technician` may request approval; `approver` may list and decide; `auditor` may list and read audit; `admin` may perform all of these operations. Requesters cannot approve their own requests. A decision cannot be changed after it is recorded.

## Local Verification

Run after changing the backend:

```bash
cd backend
../.venv/bin/alembic upgrade head
../.venv/bin/pytest tests/unit tests/security -q
```

Example local API calls (demo headers only):

```bash
curl -X POST http://127.0.0.1:8000/api/approvals \
  -H 'Content-Type: application/json' \
  -H 'X-Actor-Id: demo-technician' -H 'X-Actor-Role: technician' \
  -d '{"ticket_id":"TCK-00006","action":"Review a proposed service restart","rationale":"Technician requests a human review of the RCA recommendation."}'

curl 'http://127.0.0.1:8000/api/approvals?status=pending' \
  -H 'X-Actor-Id: demo-reviewer' -H 'X-Actor-Role: approver'

curl 'http://127.0.0.1:8000/api/approvals/audit' \
  -H 'X-Actor-Id: demo-auditor' -H 'X-Actor-Role: auditor'
```

Replace the example ID in the decision URL with the returned `approval_id`; use a different actor ID from the requester. UI requests use the demo identities `demo-technician` and `demo-reviewer`.

## Test Results (2026-10-16)

- Backend unit and security suite: **44 passed**.
- Frontend TypeScript/Vite production build: **passed**.
- Alembic migration: upgraded local PostgreSQL from `20261013_0002` to `20261016_0003`; also verified the full chain on temporary SQLite.
- Tests cover role gates, missing identity, self-approval rejection, repeated-decision rejection, persisted audit events, redaction, injection-like text marking, and fabricated evidence-ID rejection.

## RCA and Retrieval Results

These are small synthetic evaluations, not evidence of production diagnostic performance.

| Measure | Result | Scope and interpretation |
|---|---:|---|
| Correct abstention on insufficient evidence | 5/5 (100%) | Legacy manually reviewed 8-incident synthetic test; five marked insufficient |
| RCA accuracy on sufficient evidence | 0/3 (0%) | Model abstained on all three cases reviewers marked sufficient; no answered sufficient cases |
| Unsupported facts | 4/61 (6.56%) | Reviewer labels from the same small synthetic review |
| E3 Hybrid RRF evidence Recall@5 | 0.5079 | 21 retrieval queries from 7 incidents; expected evidence is ticket/runbook documents, not operational log/metric recall |
| E3 Hybrid RRF nDCG@5 | 0.5805 | Same small retrieval set |
| E4 Rewrite + Rerank Recall@5 | 0.4048 | Lower than E3 on this test; p50 latency about 755.5 ms |

The separate benchmark-v2 test file has **7 unreviewed incidents**. Its RCA metrics are null and must remain so until people review those cases. Incident labels and telemetry are synthetic assumptions, and have not been confirmed by a service owner or domain expert.

## Observed Failure Modes and Next Actions

1. **False abstention:** all three sufficient-labeled legacy cases were abstained. Improve evidence selection/packing and the sufficiency decision, then inspect each report trace. Do not simply lower the abstention threshold; that can increase unsupported diagnoses.
2. **Unsupported interpretation:** 4 of 61 reviewed facts were marked unsupported. Review timestamp language, metric comparisons, and citations at fact level; keep numeric/source checks and add human review for semantic entailment.
3. **Retrieval quality:** E3 beat E1 in the small retrieval set, while E4 degraded Recall@5/nDCG and added latency. Keep E3 as the comparison baseline; tune reranking only on dev data and re-evaluate once on a frozen, independently reviewed test set.
4. **Synthetic linkage artifacts:** some ticket text conflicts with telemetry generated from scenario assumptions. Do not count those cases as real-world RCA evidence; replace them with owner-confirmed incidents and independently exported logs/metrics.
5. **Production security gap:** replace demo headers with verified identity and server-side authorization before any real user deployment. Restrict audit DB permissions and define retention/tamper-evidence separately; the current application-level append-only API alone is not cryptographic immutability.

## Remaining Human Work

- Have a service owner/SRE review at least 20-30 reports and confirm evidence sufficiency independently of model output.
- Obtain authorized, sanitized operational telemetry and confirmed root causes before making production claims.
- Keep benchmark-v2 test cases blind until the review protocol and model configuration are frozen.

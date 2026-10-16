# Roadmap Sync: AI IT Helpdesk & Incident Assistant

## Muc dich

File nay dung de theo doi tien do trien khai du an theo de cuong 12 tuan. Moi tuan can cap nhat trang thai, ket qua da lam, van de dang bi chan va viec tiep theo.

Trang thai goi y:

- `Not started`: chua bat dau.
- `In progress`: dang lam.
- `Blocked`: dang bi chan.
- `Done`: da hoan thanh va kiem tra.

## Tong quan phase

| Phase | Tuan | Trong tam | Ket qua chinh |
|---|---:|---|---|
| Phase 1 | 1-2 | Pham vi, du lieu, schema | MVP scope, ERD, data dictionary, dataset mau |
| Phase 2 | 3-4 | Backend nen tang va ingestion | FastAPI, PostgreSQL, Ticket CRUD, ingestion pipeline |
| Phase 3 | 5-8 | Retrieval va Hybrid RAG | BM25/TF-IDF, Dense, Qdrant, RRF, Reranker |
| Phase 4 | 9 | Incident Analysis va RCA | Grounded RCA JSON, evidence validation |
| Phase 5 | 10 | Frontend demo | React UI, ticket flow, report, dashboard, approval mock |
| Phase 6 | 11-12 | Evaluation, security, packaging | E1-E5 benchmark, Docker, README, final report |

## Roadmap 12 tuan

| Tuan | Muc tieu | Module lien quan | Output can co | Trang thai | Ghi chu |
|---:|---|---|---|---|---|
| 1 | Khao sat yeu cau, chot pham vi MVP, xac dinh 3 nhom su co uu tien | docs, architecture | MVP scope, use cases, architecture overview | Not started |  |
| 2 | Thiet ke du lieu va chuan bi dataset ban dau | db, data, docs | ERD, data dictionary, cleaned sample dataset, evaluation seed | Not started |  |
| 3 | Dung backend FastAPI va Ticket CRUD | backend/app/api, backend/app/db, backend/app/services | Ticket API, PostgreSQL schema, seed data | Not started |  |
| 4 | Xay Knowledge Ingestion co ban | ingestion, stores, security/redaction | Loaders, cleaner, chunker, metadata enrichment | Not started |  |
| 5 | Lam baseline retrieval bang TF-IDF hoac BM25 | retrieval/lexical, stores/keyword_index | `/api/ai/retrieve` baseline, Recall@K/MRR ban dau | Not started |  |
| 6 | Tich hop embedding va Qdrant dense retrieval | models/embedding, stores/qdrant_store, retrieval/dense | Qdrant collection, dense search, comparison voi baseline | Not started |  |
| 7 | Ket hop Hybrid Retrieval bang RRF | retrieval/rrf, retrieval/candidate_pool | E1-E3 results, hybrid retrieval pipeline | Not started |  |
| 8 | Them query rewriting va Cross-Encoder reranker | retrieval/query, retrieval/reranker | E4 results, reranking latency, ablation table | Not started |  |
| 9 | Xay Incident Analysis Service va RCA JSON | analysis, models/llm, security | `/api/ai/analyze`, grounded RCA JSON, evidence validation | Not started |  |
| 10 | Xay React frontend va demo end-to-end | frontend, api, approvals | Ticket UI, upload UI, RCA report, dashboard, approval mock | In progress | UI/build va API tests xong; can chay E2E voi backend, PostgreSQL va Ollama |
| 11 | Hoan thien approval, audit, security va RCA evaluation | security, services, benchmarks | Audit trail, security tests, RCA accuracy/evidence recall | Not started |  |
| 12 | Dong goi Docker, README, benchmark va bao cao | infra, benchmarks, docs | Docker Compose, README, E1-E5 report, final demo | Not started |  |

## Module checklist

### Backend API

| Module | File/Folder | Trang thai | Ghi chu |
|---|---|---|---|
| Ticket API | `backend/app/api/tickets.py` | Not started |  |
| Knowledge API | `backend/app/api/knowledge.py` | Not started |  |
| Log Upload API | `backend/app/api/logs.py` | Not started |  |
| AI Retrieval API | `backend/app/api/retrieval.py` | Not started |  |
| Incident Analysis API | `backend/app/api/analysis.py` | Not started |  |
| Approval API | `backend/app/api/approvals.py` | Not started |  |
| Dashboard API | `backend/app/api/dashboard.py` | Not started |  |

### Hybrid RAG

| Thanh phan | File/Folder | Trang thai | Ghi chu |
|---|---|---|---|
| Query understanding | `backend/app/retrieval/query/understanding.py` | Not started |  |
| Query rewriting | `backend/app/retrieval/query/rewriting.py` | Not started |  |
| Query routing | `backend/app/retrieval/query/routing.py` | Not started |  |
| TF-IDF/BM25 | `backend/app/retrieval/lexical.py` | Not started |  |
| Dense retrieval | `backend/app/retrieval/dense.py` | Not started |  |
| RRF fusion | `backend/app/retrieval/rrf.py` | Not started |  |
| Reranker | `backend/app/retrieval/reranker.py` | Not started |  |
| Candidate pool | `backend/app/retrieval/candidate_pool.py` | Not started |  |
| Evidence filtering | `backend/app/retrieval/evidence_filter.py` | Not started |  |

### Incident Analysis

| Thanh phan | File/Folder | Trang thai | Ghi chu |
|---|---|---|---|
| Incident understanding | `backend/app/analysis/understanding.py` | Not started |  |
| Priority rules | `backend/app/analysis/priority_rules.py` | Not started |  |
| Log filtering | `backend/app/analysis/log_filter.py` | Not started |  |
| Prompt builder | `backend/app/analysis/prompt_builder.py` | Not started |  |
| Evidence validation | `backend/app/analysis/validator.py` | Not started |  |
| RCA schema | `backend/app/analysis/schema.py` | Not started |  |
| Final report | `backend/app/analysis/report.py` | Not started |  |
| Analysis service | `backend/app/analysis/service.py` | Not started |  |

## Benchmark checklist

| Cau hinh | Muc dich | Config | Trang thai |
|---|---|---|---|
| E1 | TF-IDF/BM25 baseline | `benchmarks/configs/e1_tfidf.yml` | Not started |
| E2 | Dense retrieval | `benchmarks/configs/e2_dense.yml` | Not started |
| E3 | Hybrid BM25 + Dense + RRF | `benchmarks/configs/e3_hybrid_rrf.yml` | Not started |
| E4 | Hybrid + Cross-Encoder Reranker | `benchmarks/configs/e4_hybrid_reranker.yml` | Not started |
| E5 | Evidence-grounded RCA with logs/metrics | `benchmarks/configs/e5_grounded_rca.yml` | Not started |

## Quy tac cap nhat hang tuan

Moi cuoi tuan, cap nhat cac muc sau:

- Trang thai cua tuan hien tai.
- Output da tao duoc.
- Test/benchmark da chay.
- Van de dang bi chan.
- Viec uu tien cua tuan tiep theo.

## Log dong bo

| Ngay | Noi dung cap nhat | Nguoi cap nhat |
|---|---|---|
| 2026-10-12 | Tao structure du an va file roadmap sync ban dau | Codex |
| 2026-10-16 | Hoan thanh React screens, ticket/analysis/knowledge API wiring, text-ingest endpoint va 32 backend tests; E2E local service stack con can xac nhan | Codex |


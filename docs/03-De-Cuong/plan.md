# Plan: AI IT Helpdesk & Incident Assistant

## 1. Muc tieu he thong

Xay dung mot he thong ho tro IT Helpdesk va phan tich su co doanh nghiep bang Advanced Retrieval-Augmented Generation, ket hop Large Language Model de:

- Tiep nhan va quan ly ticket su co IT.
- Tim ticket lich su, runbook, SOP va log lien quan.
- Tong hop bang chung thanh bao cao phan tich incident.
- Goi y gia thuyet root cause, buoc xac minh va huong xu ly.
- Hien thi citation/evidence ro rang de ky thuat vien kiem tra.
- Danh gia chat luong retrieval va RCA bang cac metric co kiem soat.

He thong chi dua ra de xuat va checklist. MVP khong tu dong thuc thi lenh len production, khong tu restart service, khong thay doi cau hinh ha tang neu chua co phe duyet.

## 2. Pham vi MVP

### 2.1. Nhom su co uu tien

MVP tap trung vao 3 nhom su co:

- Network/connectivity: mat ket noi, timeout, DNS, gateway, VPN.
- Server/API: HTTP 500, latency cao, service crash, deployment loi.
- Database: ket noi database, connection pool, slow query, lock, replication.

### 2.2. Ngoai pham vi MVP

Cac phan sau chua lam trong ban dau:

- Tu dong sua loi tren production.
- Ket noi truc tiep vao shell server that.
- SOC automation.
- Monitoring realtime quy mo lon.
- Tich hop day du Jira, ServiceNow, Slack hoac Teams.
- Multi-tenant enterprise phuc tap.

## 3. Kien truc tong the

```text
React Frontend
    |
    v
FastAPI Backend / API Gateway
    |
    +-- Ticket Service
    |       |
    |       v
    |   PostgreSQL
    |
    +-- Knowledge Ingestion Service
    |       |
    |       v
    |   Qdrant Vector DB + Keyword Index
    |
    +-- Retrieval Pipeline
    |       |
    |       +-- TF-IDF / BM25
    |       +-- Dense Retrieval
    |       +-- Hybrid Search / RRF
    |       +-- Cross-Encoder Reranker
    |
    +-- Incident Analysis Service
            |
            v
        LLM Provider
```

## 4. Cong nghe du kien

| Thanh phan | Cong nghe | Vai tro |
|---|---|---|
| Frontend | React, Tailwind CSS | Giao dien ticket, incident report, dashboard |
| Backend | FastAPI, Pydantic | REST API, validation, orchestration |
| Database | PostgreSQL | Luu ticket, user, audit, analysis |
| Vector database | Qdrant | Luu embedding va metadata filter |
| Keyword search | TF-IDF/BM25 | Baseline va lexical retrieval |
| Embedding | MiniLM baseline, BGE-M3 mo rong | Tim kiem ngu nghia Viet/Anh |
| Reranker | BGE-reranker-v2-m3 | Sap xep lai top candidates |
| LLM | Ollama Qwen hoac API theo cau hinh | Tong hop bang chung va goi y RCA |
| Evaluation | Custom metrics, RAGAS neu phu hop | Do retrieval, RCA, groundedness |
| Deployment | Docker Compose | Chay lai moi truong de demo |

## 5. Module chinh

### 5.1. Ticket Management

Chuc nang:

- Tao ticket moi.
- Xem danh sach ticket.
- Xem chi tiet ticket.
- Cap nhat trang thai ticket.
- Gan priority, category, service, assignee.
- Luu lich su thay doi.

Input chinh:

- Title.
- Description.
- Service bi anh huong.
- Category.
- Impact.
- Urgency.
- Attachment/log neu co.

Output chinh:

- Ticket ID.
- Trang thai ticket.
- Priority de xuat hoac duoc xac nhan.
- Timeline xu ly.

### 5.2. Knowledge Ingestion

Chuc nang:

- Nap ticket lich su tu CSV/JSON.
- Nap runbook/SOP tu Markdown/PDF/text.
- Nap log/metric da loc.
- Chuan hoa metadata.
- Chia chunk tai lieu.
- Tao embedding.
- Upsert vao Qdrant.
- Tao keyword index cho BM25/TF-IDF.

Metadata can co:

- `document_id`
- `chunk_id`
- `source`
- `source_type`
- `service`
- `version`
- `access_scope`
- `created_at`
- `updated_at`

Nguyen tac:

- Dung idempotent IDs de nap lai khong tao trung.
- Khong dua password, token, API key, PII vao index.
- Runbook phai giu dung thu tu cac buoc xu ly.

### 5.3. Retrieval Pipeline

Chuc nang:

- Nhan query tu ticket hien tai hoac cau hoi nguoi dung.
- Rewrite query neu can.
- Route intent.
- Tim bang TF-IDF/BM25.
- Tim bang dense vector.
- Hop nhat ket qua bang RRF.
- Rerank bang Cross-Encoder.
- Tra ve top-k evidence co citation.

Luon ap dung filter:

- Service.
- Access scope.
- Document version.
- Time window neu la log/incident.

Cac cau hinh retrieval can danh gia:

- E1: TF-IDF.
- E2: Dense Embedding.
- E3: BM25 + Dense bang RRF.
- E4: Hybrid + Cross-Encoder.
- E5: Hybrid + Reranker + log/metrics cho RCA.

### 5.4. Incident Analysis / RCA

Chuc nang:

- Tong hop ticket hien tai.
- Lay evidence tu ticket lich su, runbook, log, metric.
- Phan biet du kien quan sat va gia thuyet.
- Sinh bao cao RCA dang structured JSON.
- Hien thi bang chung ung voi tung gia thuyet.
- Neu thieu bang chung thi yeu cau xac minh them.

Output JSON du kien:

```json
{
  "observed_facts": [],
  "ranked_hypotheses": [],
  "supporting_evidence_ids": [],
  "contradicting_or_missing_evidence": [],
  "verification_steps": [],
  "proposed_actions": [],
  "escalation": null
}
```

Quy tac quan trong:

- Khong ket luan root cause neu chua du bang chung.
- Moi evidence ID phai ton tai trong database hoac vector store.
- LLM output phai duoc backend validate truoc khi hien thi.
- Noi dung retrieved/log duoc xem la untrusted input, khong duoc coi la system instruction.

### 5.5. Approval & Audit

Chuc nang:

- Luu lich su ai da xem, sua, phe duyet de xuat.
- Luu prompt/input/output chinh cua phan tich AI neu phu hop.
- Tao approval request cho hanh dong co rui ro.
- MVP chi lam approval mock, chua thuc thi lenh that.

Vi du hanh dong can approval:

- Restart service.
- Thay doi cau hinh.
- Disable user/account.
- Chay script khac phuc.

### 5.6. Dashboard

Chuc nang:

- Thong ke so luong ticket.
- Trang thai ticket theo category/service.
- SLA hoac thoi gian xu ly.
- So incident theo root cause.
- Latency va chat luong retrieval/AI.

## 6. Thiet ke du lieu du kien

### 6.1. Bang `tickets`

| Cot | Mo ta |
|---|---|
| id | Primary key |
| ticket_id | Ma ticket hien thi |
| title | Tieu de |
| description | Mo ta su co |
| service | Service bi anh huong |
| category | Nhom su co |
| priority | Muc do uu tien |
| status | New, In Progress, Resolved, Closed |
| impact | Anh huong |
| urgency | Do khan cap |
| verified_root_cause | Nguyen nhan da xac minh |
| resolution | Cach xu ly |
| created_at | Thoi gian tao |
| updated_at | Thoi gian cap nhat |

### 6.2. Bang `knowledge_documents`

| Cot | Mo ta |
|---|---|
| id | Primary key |
| document_id | Ma tai lieu |
| title | Tieu de tai lieu |
| source_type | ticket, runbook, sop, log, metric |
| source | Duong dan hoac nguon |
| service | Service lien quan |
| version | Phien ban |
| access_scope | Pham vi truy cap |
| created_at | Thoi gian tao |

### 6.3. Bang `knowledge_chunks`

| Cot | Mo ta |
|---|---|
| id | Primary key |
| chunk_id | Ma chunk |
| document_id | Lien ket tai lieu |
| content | Noi dung chunk |
| metadata | JSON metadata |
| qdrant_point_id | ID trong Qdrant |

### 6.4. Bang `incident_analyses`

| Cot | Mo ta |
|---|---|
| id | Primary key |
| ticket_id | Ticket duoc phan tich |
| model_name | Model LLM |
| retrieval_config | Cau hinh retrieval |
| analysis_json | Ket qua RCA JSON |
| created_at | Thoi gian tao |

### 6.5. Bang `audit_logs`

| Cot | Mo ta |
|---|---|
| id | Primary key |
| actor_id | Nguoi thuc hien |
| action | Hanh dong |
| entity_type | Loai doi tuong |
| entity_id | ID doi tuong |
| before | Gia tri truoc |
| after | Gia tri sau |
| created_at | Thoi gian |

## 7. API du kien

### 7.1. Ticket API

| Method | Endpoint | Mo ta |
|---|---|---|
| POST | `/api/tickets` | Tao ticket |
| GET | `/api/tickets` | Lay danh sach ticket |
| GET | `/api/tickets/{id}` | Lay chi tiet ticket |
| PATCH | `/api/tickets/{id}` | Cap nhat ticket |

### 7.2. Knowledge API

| Method | Endpoint | Mo ta |
|---|---|---|
| POST | `/api/knowledge/upload` | Upload runbook/SOP/ticket history |
| GET | `/api/knowledge/documents` | Danh sach tai lieu |
| GET | `/api/knowledge/documents/{id}` | Chi tiet tai lieu |

### 7.3. Log API

| Method | Endpoint | Mo ta |
|---|---|---|
| POST | `/api/logs/upload` | Upload log phuc vu phan tich |
| GET | `/api/logs/search` | Tim log theo service/time window |

### 7.4. AI API

| Method | Endpoint | Mo ta |
|---|---|---|
| POST | `/api/ai/retrieve` | Tim evidence lien quan |
| POST | `/api/ai/analyze` | Sinh bao cao RCA |
| GET | `/api/ai/analyses/{id}` | Xem ket qua phan tich |

### 7.5. Approval va Dashboard API

| Method | Endpoint | Mo ta |
|---|---|---|
| POST | `/api/approvals` | Tao yeu cau phe duyet |
| PATCH | `/api/approvals/{id}` | Duyet/tu choi |
| GET | `/api/dashboard/stats` | Thong ke he thong |

## 8. Dataset va danh gia

### 8.1. Nhom du lieu can chuan bi

- [x] ~~Historical tickets: 300-500 ban ghi cho MVP.~~
  - Da chuan bi 10.000 ticket chinh trong `data/processed/tickets/normalized_tickets.csv`.
- [x] ~~Runbook/SOP: 30-50 tai lieu.~~
  - Da tao 30 runbook Markdown trong `data/processed/runbooks/`.
- [x] ~~Log events: khoang 10.000 dong cho MVP.~~
  - Da co raw logs khoang 18.000 dong va 1.000 linked logs trong `data/processed/logs/incident_logs.jsonl`.
- [x] ~~Incident synthetic co nhan kich ban: khoang 50 tinh huong.~~
  - Da tao 50 synthetic scenario-label trong `data/eval/incidents.jsonl`; root cause chua duoc expert xac minh, khong goi la production ground truth.
- [x] ~~Evaluation queries: 100-150 cau hoi/truy van.~~
  - Da tao 150 evaluation queries trong `data/eval/evaluation_queries.jsonl` va `data/eval/evaluation_queries.csv`.

### 8.2. Nguyen tac lam dataset

- Loai bo du lieu trung lap.
- Chuan hoa category, service, timestamp.
- Redact password, token, API key, PII.
- Tach train/dev/test theo incident va thoi gian.
- Khong dua loi giai cua incident test vao context.
- Phan biet `verified_root_cause` va `hypothesis`.

### 8.3. Metric danh gia

Retrieval:

- Recall@5.
- Precision@5.
- MRR.
- nDCG@5.

RCA:

- Top-1 root cause accuracy.
- Top-3 root cause accuracy.
- Evidence recall.
- Ty le phat bieu thieu nguon.

He thong:

- p50 latency.
- p95 latency.
- Throughput.
- Error rate.
- RAM usage.

## 9. Lo trinh trien khai 12 tuan

### Tuan 1: Khao sat va chot pham vi MVP

Cong viec:

- [x] ~~Khao sat yeu cau bai toan IT Helpdesk va Incident Assistant.~~
- [x] ~~Xac dinh nguoi dung chinh: nhan vien gui ticket, ky thuat vien, truong nhom van hanh, admin.~~
- [x] ~~Chot pham vi MVP voi 3 nhom su co: network/connectivity, server/API, database.~~
- [x] ~~Ra soat tai lieu tham khao, repo lien quan va dieu kien du lieu co the su dung.~~
- [x] ~~Ve so do kien truc muc cao.~~

San pham:

- [x] ~~Tai lieu pham vi MVP.~~
  - Da ghi trong `docs/03-De-Cuong/plan.md`.
- [x] ~~Danh sach use case chinh.~~
  - Da tao 8 use case trong `docs/04-usecase/`.
- [x] ~~So do kien truc muc cao.~~
  - Da luu tai `docs/02-diagram/diagram-architecture.png`.
- [x] ~~Danh muc nguon du lieu du kien.~~
  - Da chot nguon ticket, runbook, log, metric va evaluation trong `docs/05-thiet-ke-du-lieu/`.

### Tuan 2: Thiet ke du lieu va chuan bi dataset ban dau

Cong viec:

- [x] ~~Thiet ke schema cho ticket, knowledge document, chunk, log/metric, incident analysis va audit.~~
- [x] ~~Tao data dictionary va ERD ban dau.~~
- [x] ~~Thu thap ticket, runbook/SOP va log mau.~~
- [x] ~~Lam sach du lieu, chuan hoa service/category/timestamp.~~
- [x] ~~Tao test set nho de danh gia retrieval va RCA ve sau.~~
- [x] ~~Tao synthetic incident scenario lien ket ticket, runbook, log va metric.~~
- [x] ~~Tao evaluation queries tu synthetic scenario labels.~~

San pham:

- [x] ~~Data dictionary.~~
  - `docs/05-thiet-ke-du-lieu/data-dictionary.md`.
- [x] ~~ERD ban dau.~~
  - `docs/05-thiet-ke-du-lieu/erd.md`.
- [x] ~~Bo ticket/runbook/log mau da lam sach.~~
  - 10.000 ticket: `data/processed/tickets/normalized_tickets.csv`.
  - 9.069 mo ta loi phu tro: `data/processed/tickets/error_descriptions.csv`.
  - 30 runbook: `data/processed/runbooks/`.
  - 1.000 linked logs: `data/processed/logs/incident_logs.jsonl`.
  - 500 linked metrics: `data/processed/metrics/incident_metrics.csv`.
- [x] ~~Tap danh gia thu nghiem.~~
  - 50 synthetic scenario-label (35 train / 7 dev / 8 test), chua expert-verified: `data/eval/incidents.jsonl`.
  - 150 evaluation queries: `data/eval/evaluation_queries.jsonl` va `data/eval/evaluation_queries.csv`.
- [x] ~~Validator cho dataset.~~
  - `scripts/validate_runbooks.py`.
  - `scripts/validate_incident_ground_truth.py`.
  - `scripts/validate_evaluation_set.py`.

### Tuan 3: Backend FastAPI va Ticket CRUD

Cong viec:

- [x] ~~Khoi tao structure backend FastAPI ban dau.~~
  - Da co thu muc `backend/app/`, `backend/app/api/`, `backend/app/db/`, `backend/app/schemas/`, `backend/app/services/`.
- [x] ~~Cau hinh backend settings va `DATABASE_URL`.~~
  - Tao `backend/app/core/config.py`.
  - Doc bien moi truong tu `.env`.
  - Chuan bi PostgreSQL URL dang `postgresql+psycopg://...`.
- [x] ~~Cau hinh PostgreSQL va migration.~~
  - Chuan bi `infra/docker-compose.yml` cho PostgreSQL local.
  - Cau hinh SQLAlchemy engine/session.
  - Khoi tao Alembic trong `backend/migrations/`.
  - Tao migration dau tien cho bang `tickets`.
- [x] ~~Tao SQLAlchemy model cho ticket.~~
  - Bang `tickets` can co `ticket_id`, `title`, `description`, `service`, `category`, `priority`, `impact`, `urgency`, `assigned_team`, `auto_resolve`, `status`, `verified_root_cause`, `resolution`, `source`, `created_at`, `updated_at`.
- [x] ~~Tao Pydantic schema cho ticket.~~
  - `TicketCreate`.
  - `TicketRead`.
  - `TicketListResponse`.
  - `TicketUpdateStatus`.
- [x] ~~Cai dat service layer cho ticket.~~
  - `create_ticket`.
  - `list_tickets`.
  - `get_ticket_by_ticket_id`.
  - `update_ticket_status`.
- [x] ~~Cai dat API tao ticket, xem danh sach, xem chi tiet va cap nhat trang thai.~~
  - `POST /api/tickets`.
  - `GET /api/tickets`.
  - `GET /api/tickets/{ticket_id}`.
  - `PATCH /api/tickets/{ticket_id}/status`.
- [x] ~~Tao seed data mau de test nhanh.~~
  - Doc tu `data/processed/tickets/normalized_tickets.csv`.
  - Seed 500-1.000 ticket dau tien.
  - Tao phan bo status mau: `resolved`, `new`, `in_progress`, `closed`.
- [x] ~~Test API ticket.~~
  - Test `/health`.
  - Test list ticket.
  - Test detail ticket.
  - Test create ticket.
  - Test update status.

San pham:

- [x] ~~Backend chay duoc.~~
  - Da co `backend/app/main.py` va unit test FastAPI pass.
- [x] ~~Database migration khoi tao thanh cong.~~
  - Alembic upgrade da verify bang SQLite tam thoi; PostgreSQL local chay qua Docker Compose khi Docker san sang.
- [x] ~~API CRUD ticket hoat dong.~~
  - Unit test bao phu health, list, detail, create va update status.
- [x] ~~Co seed script du lieu mau.~~
  - `scripts/seed_db.py` doc `data/processed/tickets/normalized_tickets.csv`.
- [x] ~~Co test evidence cho 4 endpoint ticket.~~
  - `backend/tests/unit/test_tickets_api.py`.

### Tuan 4: Knowledge Ingestion co ban

Cong viec:

- [x] ~~Xay dung pipeline nap ticket lich su va runbook/SOP.~~
  - `backend/app/ingestion/pipeline.py`.
  - `scripts/ingest_knowledge.py`.
- [x] ~~Clean va redact du lieu nhay cam.~~
  - `backend/app/ingestion/cleaner.py`.
- [x] ~~Chia chunk tai lieu.~~
  - Ticket: 1 ticket = 1 chunk.
  - Runbook/SOP: chunk theo heading Markdown `##`.
- [x] ~~Gan metadata gom document_id, chunk_id, source, source_type, service, version va access_scope.~~
  - `backend/app/ingestion/enricher.py`.
- [x] ~~Luu metadata vao PostgreSQL.~~
  - Tao bang `knowledge_documents`.
  - Tao bang `knowledge_chunks`.
  - Them migration `20261013_0002_create_knowledge_tables.py`.

San pham:

- [x] ~~Pipeline ingestion co ban.~~
  - Da verify bang SQLite tam: ingest 30 runbook + 5 ticket thanh 35 documents va 215 chunks.
- [x] ~~Tai lieu duoc chia chunk co metadata day du.~~
  - Metadata co `document_id`, `chunk_id`, `source`, `source_type`, `service`, `category`, `version`, `access_scope`.
- [x] ~~Co the truy xuat lai document/chunk theo ID.~~
  - `GET /api/knowledge/documents`.
  - `GET /api/knowledge/documents/{document_id}`.
  - `GET /api/knowledge/chunks/{chunk_id}`.

### Tuan 5: Baseline Retrieval bang TF-IDF hoac BM25

Cong viec:

- [x] ~~Cai dat TF-IDF hoac BM25 keyword retrieval.~~
  - Da cai dat BM25 noi bo trong `backend/app/retrieval/lexical.py`.
- [x] ~~Xay dung API `/api/ai/retrieve` phien ban dau.~~
  - `POST /api/ai/retrieve`.
- [x] ~~Cho phep tim evidence theo ticket description hoac cau hoi.~~
  - Ho tro input `query`.
  - Ho tro input `ticket_id` de backend tu tao query tu title/description/service/category.
- [x] ~~Ap dung filter theo service, source type va access scope.~~
  - Ho tro filter `service`, `category`, `source_types`, `access_scope`.
- [x] ~~Do metric baseline tren tap danh gia nho.~~
  - Da chay E1 BM25 tren split test voi available evidence.

San pham:

- [x] ~~Baseline keyword retrieval.~~
- [x] ~~Endpoint `/api/ai/retrieve` phien ban dau.~~
- [x] ~~Bang ket qua Recall@K va MRR thu nghiem.~~
  - `benchmarks/reports/e1_bm25_baseline.json`.
  - `benchmarks/reports/e1_bm25_baseline.md`.
  - Ket qua test split: Recall@5 = 0.5903, Recall@10 = 0.5903, MRR@10 = 0.6958.

### Tuan 6: Dense Retrieval voi Embedding va Qdrant

Cong viec:

- [x] ~~Tich hop embedding model.~~
  - Da chot model `BAAI/bge-m3`, dimension 1024.
  - Adapter: `backend/app/models/embedding/bge_m3.py`.
- [x] ~~Cau hinh Qdrant collection.~~
  - Da them Qdrant vao `infra/docker-compose.yml`.
  - Collection mac dinh: `knowledge_chunks`.
- [x] ~~Tao embedding cho document chunks.~~
  - Da chay `scripts/build_vector_index.py --recreate` bang BGE-M3 trong `.venv`.
  - PostgreSQL co 10.210 chunks, ca 10.210 chunks deu co `qdrant_point_id`.
- [x] ~~Upsert vector kem metadata vao Qdrant.~~
  - Collection `knowledge_chunks` co 10.210 points, vector 1024 chieu, trang thai green.
- [x] ~~Cai dat dense retrieval service.~~
  - `backend/app/retrieval/dense.py`.
  - `/api/ai/retrieve` da ho tro `method=dense`.
- [x] ~~So sanh dense retrieval voi keyword baseline.~~
  - Cung 24 truy van test, 10.210 chunks va filter: BM25 Recall@5 0.6250, Recall@10 0.6667, MRR@10 0.9028; BGE-M3 dense lan luot 0.2292, 0.2708, 0.3567.
  - Bao cao: `benchmarks/reports/retrieval_comparison_e1_e2.md`.

San pham:

- [x] ~~Qdrant collection.~~
- [x] ~~Dense retrieval hoat dong voi BGE-M3 end-to-end.~~
  - Da nap BGE-M3 trong `.venv`, truy van Qdrant bang `query_points()` va chay benchmark E2 thanh cong.
- [x] ~~Bao cao so sanh TF-IDF/BM25 voi dense retrieval.~~
  - Bao cao thuc te so sanh BM25 va BGE-M3 dense; chua chay TF-IDF rieng.

### Tuan 7: Hybrid Retrieval voi RRF

Cong viec:

- [x] ~~Ket hop BM25 va Dense Retrieval BGE-M3 trong `/api/ai/retrieve` voi `method=hybrid`.~~
- [x] ~~Hop nhat theo `document_id` bang Reciprocal Rank Fusion (`rrf_k=60`), giu chunk dai dien cho citation.~~
- [x] ~~Tune candidate_k tren 21 query dev (20/50/100); chon 20 theo nDCG@5.~~
- [x] ~~Ap dung cung filter service, category, version, source type va access scope cho hai nhanh.~~
- [x] ~~Chay E1, E2 va E3 tren 24 query test, cung corpus va candidate_k=20.~~

San pham:

- [x] ~~Hybrid retrieval pipeline va test RRF/API.~~
- [x] ~~Ket qua E1-E3: `benchmarks/reports/retrieval_comparison_e1_e2_e3.md`.~~
- [x] ~~Bang Recall@5, Precision@5, MRR@10 va nDCG@5.~~

Ket qua test: BM25 Recall@5 0.6250, nDCG@5 0.6555; dense 0.2292 va 0.2218; hybrid 0.5486 va 0.5453. Hybrid chua vuot BM25 tren 24 query tu 8 incident; BM25 van la API default. E1-E3 chi cham ticket va runbook; log/metrics se duoc truy xuat theo service + time window o giai doan incident analysis.

### Tuan 8: Query Rewriting va Cross-Encoder Reranker

Cong viec:

- [x] ~~Cai dat query understanding va rewriting co ban, giu service/ma loi/trieu chung.~~
- [x] ~~Route intent support_question, new_incident, compare_incidents, escalate, chitchat; bo qua retrieval voi chitchat.~~
- [x] ~~Tao candidate evidence pool theo document_id, loc access_scope truoc rerank.~~
- [x] ~~Tich hop BAAI/bge-reranker-v2-m3 vao `method=hybrid_rerank`; rewriting bat/tat bang `rewrite`.~~
- [x] ~~Tune rerank_k=10/20 tren 21 query dev; chon 20 theo nDCG@5.~~
- [x] ~~Do chat luong va latency p50/p95 cua E1, E3, E4 va E4 + rewriting tren 24 query test.~~

San pham:

- [x] ~~Cau hinh E4: `benchmarks/configs/e4_hybrid_reranker.yml`.~~
- [x] ~~Bang ablation: `benchmarks/reports/e4_ablation_test.md` va `.json`.~~
- [x] ~~So lieu tang/giam chat luong va latency khi them reranker.~~

Ket qua test: BM25 nDCG@5 0.6555, p50 19.1 ms; E3 0.5453, 117.3 ms; E4 rerank 0.2465, 1112.4 ms; E4 + rewriting 0.1405, 1133.5 ms. E4 chay end-to-end nhung khong cai thien tren tap test nho nay; BM25 tiep tuc la API default. Chua dua log/metric vao retrieval; cac query tu cung incident co lien he voi nhau.

Chay lai: `.venv/bin/python benchmarks/run_e4_ablation.py --split dev` roi `.venv/bin/python benchmarks/run_e4_ablation.py --split test --rerank-k 20`.

### Tuan 9: Incident Analysis va RCA JSON

Cong viec:

- [x] Xay dung Incident Analysis Service va API `POST /api/ai/analyze`.
- [x] Thiet ke Pydantic RCA JSON schema va schema-constrained Ollama adapter.
- [x] Tong hop ticket hien tai, evidence BM25/hybrid, runbook, logs va metrics loc theo service + UTC time window.
- [x] Loai bo current-ticket knowledge chunk va cac log synthetic ghi san root cause/runbook IDs khoi prompt.
- [x] Tao grounded prompt, redact du lieu nhay cam va gioi han so luong/do dai evidence.
- [x] Validate JSON, evidence IDs va yeu cau operational evidence truoc khi cong bo RCA grounded.
- [x] Test API/filter/grounding bang fake LLM va cau hinh Ollama; `pytest` 29 passed.
- [x] Smoke test Ollama adapter va API voi `llama3:latest` da cai: `/api/ai/analyze` tra 200, `insufficient_evidence`, 24 evidence, khong tu khang dinh root cause.
- [x] Smoke test API end-to-end voi `qwen3.5:4b`: model local tra `insufficient_evidence` hop le sau khi tat thinking va thu gon evidence pack.

San pham:

- [x] API `/api/ai/analyze`, schema RCA JSON, va report co observed_facts, hypotheses, evidence IDs, missing_evidence, verification_steps.
- [x] Tra `insufficient_evidence` neu khong co log/metric trong khoang thoi gian.
- [x] Hanh dong de xuat chi co tinh advisory, `review_required=true`; khong thuc thi lenh production.

Chay thu (can PostgreSQL da seed, knowledge da ingest va Ollama co model):

```bash
ollama pull qwen3.5:4b
cd backend && ../.venv/bin/uvicorn app.main:app --reload
curl -X POST http://127.0.0.1:8000/api/ai/analyze \
  -H 'Content-Type: application/json' \
  -d '{"ticket_id":"TCK-00006","window_start":"2026-09-01T11:00:00Z","window_end":"2026-09-01T11:15:00Z"}'
```

Luu y: can chay `ollama serve` neu daemon chua chay. `OLLAMA_URL`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT_SECONDS` co trong `.env.example`. RCA report can technician review; E5/groundedness evaluation chi lam o Tuan 11.

Bao cao mau rut gon cua unit test (fake LLM, chi dung de kiem tra schema/citation; response thuc te co them service, time window, model va danh sach evidence):

```json
{
  "ticket_id": "TCK-001",
  "status": "grounded",
  "observed_facts": [{"fact": "Timeouts increased", "evidence_ids": ["LOG-1"]}],
  "hypotheses": [{"cause": "Gateway congestion", "supporting_evidence_ids": ["LOG-1", "MET-1"]}],
  "probable_root_cause": "Gateway congestion",
  "root_cause_evidence_ids": ["LOG-1", "MET-1"],
  "confidence": "medium",
  "missing_evidence": ["Upstream trace"],
  "verification_steps": [{"step": "Inspect upstream latency", "evidence_ids": ["MET-1"]}],
  "proposed_actions": ["Ask technician to review gateway capacity"],
  "review_required": true
}
```

### Tuan 10: Frontend React va Demo End-to-End

Cong viec:

- [x] Tao React SPA bang TypeScript, Vite, Tailwind CSS va Lucide.
- [x] Lam ticket list va ticket detail, tao ticket, loc danh sach va cap nhat status qua API.
- [x] Lam knowledge upload text, redaction preview, chunk va luu metadata/chunks vao PostgreSQL.
- [x] Lam incident analysis report dung RCA JSON schema va citation inspector.
- [x] Lam dashboard ticket aggregates va bang E1-E4 exploratory; khong hien KPI chua co du lieu.
- [x] Lam approval review mock ban dau; den Tuan 11 da chuyen sang API persistence va audit database, khong thuc thi production command.
- [x] Hien thi citation/evidence co the bam de xem noi dung, service va timestamp.
- [ ] Chay demo end-to-end voi PostgreSQL, Qdrant va Ollama tren may chay backend; chua duoc xac nhan trong moi truong hien tai.

Gioi han implementation Tuan 10:

- Upload API nhan noi dung text da doc tu trinh duyet, backend redact/chunk/persist; PDF parsing va tu dong upsert embedding sau upload chua co.
- Dashboard dung ticket API va V2 exploratory benchmark; chua co dashboard aggregation API, SLA/MTTR telemetry hay RCA E5 benchmark hop le.
- Approval workflow da duoc noi voi API va audit database trong Tuan 11; actor identity van la demo header, khong phai xac thuc production.

San pham:

- Demo end-to-end tu tao ticket den xem RCA report co citation.
- Giao dien dashboard.
- Approval mock tren UI.

### Tuan 11: Approval, Audit, Security va RCA Evaluation

Cong viec:

- [x] Hoan thien Approval & Audit Service: tao request, list, approve/reject, luu PostgreSQL va audit events append-only qua API.
- [x] Kiem thu role gate, chong tu phe duyet, redaction, prompt-injection markers va evidence ID validation.
- [x] Chay RCA review hien co va retrieval benchmark; luu ro so lieu synthetic va gioi han nhan.
- [x] Ghi nhan false abstention va unsupported facts trong 8 ca legacy test.
- Danh gia rieng correct abstention tren ca thieu evidence, RCA accuracy tren ca du evidence va unsupported-fact rate.
- Ra soat thu cong nhan dinh evidence sufficiency va 20-30 RCA report; khong dung LLM judge lam nhan chuan duy nhat.

San pham:

- [x] Audit trail va approval workflow demo co persistence.
- [x] Ket qua security tests; backend unit/security suite 44 passed, frontend production build thanh cong.
- [x] Bang ket qua RCA synthetic va retrieval evidence Recall@5, kem ghi chu pham vi.
- [x] Danh sach loi phan tich va huong khac phuc trong `docs/05-thiet-ke-du-lieu/week11-security-and-rca-evaluation.md`.
- [ ] Chuyen gia xac nhan ground truth production va review them 20-30 RCA report; day la dieu kien truoc khi tuyen bo hieu nang thuc te.

Pham vi va gioi han danh gia hien tai:

- `data/eval/incidents.jsonl` co 50 incident synthetic, chia 35 train / 7 dev / 8 test. Root cause hien duoc gan theo service de tao kich ban, chua duoc chuyen gia xac minh; chi duoc dien giai la synthetic scenario-label, khong phai RCA ground truth van hanh.
- Metrics synthetic co time series va duoc tao theo profile; ket qua chi cho thay pipeline xu ly duoc tin hieu da mo phong, khong chung minh kha nang chan doan production.
- Danh gia test RCA hien co 8 incident, chua phai 50. Can mo rong test set doc lap truoc khi ket luan tong quat; khong chuyen incident train/dev sang test sau khi da tuning.
- Chi danh dau evidence `sufficient` neu no phan biet duoc mot root cause; symptom/anomaly don le (vi du latency cao) chua du de khang dinh mot nguyen nhan cu the.
- Dung `python scripts/prepare_rca_review.py prepare` de tao/cap nhat mau review test. Danh dau `evidence_sufficiency` la `sufficient` hoac `insufficient` bang danh gia nguoi; dien cac cot RCA sau khi chay model. Dung `python scripts/prepare_rca_review.py evaluate` de tinh ba chi so; gia tri null co nghia la chua du nhan.
- RBAC hien tai dung `X-Actor-Id` va `X-Actor-Role` cho demo local; header nay do client tu gui, khong phai authentication. Khong expose API approval ra mang/prod neu chua thay bang IdP/JWT va server-side role claims.

### Tuan 12: Docker, README, Bao cao va Demo cuoi

Cong viec:

- Tao Docker Compose.
- Viet README cai dat va huong dan chay.
- Viet API contract va test instructions.
- Chay benchmark E1-E5 lan cuoi.
- Hoan thien bao cao ky thuat va demo co the tai lap.

San pham:

- Docker Compose.
- README.
- Test instructions.
- Bang thi nghiem E1-E5.
- Bao cao tong ket.
- Demo cuoi cung.

## 10. Thu tu code de lam thuc te

Khi bat dau code, nen di theo thu tu nay:

1. [x] ~~Tao cau truc repo.~~
2. [x] ~~Tao backend FastAPI.~~
3. [x] ~~Tao PostgreSQL schema.~~
4. [x] ~~Lam CRUD ticket.~~
5. [x] ~~Tao data seed mau.~~
6. [x] ~~Lam ingestion text/ticket.~~
7. [x] ~~Lam TF-IDF/BM25 baseline.~~
8. [x] ~~Tich hop Qdrant va embedding.~~
9. [x] ~~Lam hybrid retrieval.~~
10. [x] ~~Them reranker.~~
11. [x] ~~Lam AI analyze endpoint.~~ Kiem thu bang Qwen3.5:4b con cho cap nhat Ollama.
12. [x] ~~Lam frontend React.~~
13. [x] ~~Lam dashboard.~~
14. [x] ~~Them evaluation scripts.~~
15. [x] ~~Them Docker Compose.~~
16. [ ] Viet README va bao cao.

## 11. Tieu chi nghiem thu

He thong duoc xem la dat MVP neu:

- Tao, xem, cap nhat ticket thanh cong.
- Nap duoc ticket lich su va runbook/SOP.
- Tim duoc evidence lien quan co citation.
- Sinh duoc RCA report co cau truc.
- Phan biet ro observed facts, hypotheses, missing evidence va proposed actions.
- Evidence IDs trong output co that.
- Co it nhat 5 cau hinh thi nghiem E1-E5.
- Co bang metric retrieval va latency.
- Khong tu dong thuc thi lenh nguy hiem.
- Co audit trail cho cac hanh dong quan trong.
- Co Docker Compose va README de chay lai.

## 12. Rui ro va cach giam thieu

| Rui ro | Cach giam thieu |
|---|---|
| Dataset thieu root cause | Tach retrieval evaluation va RCA evaluation, tao synthetic case co nhan |
| Log khong noi truc tiep voi ticket | Chi lien ket khi co evidence ro, khong ghep tuy tien |
| LLM hallucination | Bat buoc citation, validate evidence IDs, refusal khi thieu bang chung |
| Prompt injection trong tai lieu/log | Input isolation, khong coi retrieved text la lenh |
| Model qua nang | Bat dau bang MiniLM va Qwen nho, toi uu top-k |
| Latency cao | Cache embedding, batch retrieval, giam candidates, tuning top-k |
| Ro ri du lieu nhay cam | Redaction, access_scope, RBAC, audit |

## 13. Cau truc thu muc de xuat

```text
IT_helpdesk/
  backend/
    app/
      api/
      core/
      db/
      models/
      schemas/
      services/
      ai/
      evaluation/
    tests/
    Dockerfile
    pyproject.toml
  frontend/
    src/
      components/
      pages/
      services/
      types/
    Dockerfile
    package.json
  data/
    raw/
    processed/
    evaluation/
  docs/
    architecture.md
    api_contract.md
    data_dictionary.md
  docker-compose.yml
  README.md
  plan.md
```

## 14. Nguyen tac phat trien

- Lam MVP nho truoc, mo rong sau.
- Moi output AI phai co evidence hoac noi ro la thieu bang chung.
- Khong dua ket luan RCA nhu su that neu chi la gia thuyet.
- Backend phai validate LLM output.
- Dataset phai tach train/dev/test de tranh ro ri.
- Moi experiment phai ghi model, version, tham so va timestamp.
- Uu tien tinh tai lap hon demo dep nhung kho chay lai.


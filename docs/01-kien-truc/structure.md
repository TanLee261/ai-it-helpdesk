# Cau truc thu muc du an

Tai lieu nay mo ta cau truc hien tai cua project `ai-it-helpdesk`. Khi them, doi ten, di chuyen hoac xoa module quan trong, phai cap nhat file nay trong cung phien lam viec.

## Quy tac dong bo

- Bo qua cac thu muc: `.git`, `node_modules`, `venv`, `__pycache__`, `.idea`, `.vscode`, `dist`, `build`.
- Moi module moi can co chu thich ro vai tro.
- Cau truc trong file nay phai khop voi cau truc thuc te cua code.

## Text tree

```text
ai-it-helpdesk/
├── .gitignore                           # Quy tac bo qua file cache, env that, node_modules, raw data
├── .env.example                         # Mau bien moi truong backend, database, Qdrant, Ollama va observability
├── Makefile                             # Lenh tien ich de cai dat, test, chay service, benchmark
├── README.md                            # Tai lieu gioi thieu va huong dan chay du an
├── backend/                             # Backend FastAPI va cac service xu ly nghiep vu
│   ├── Dockerfile                       # Docker image cho backend
│   ├── pyproject.toml                   # Cau hinh package va dependency Python
│   ├── alembic.ini                      # Cau hinh Alembic migration
│   ├── migrations/                      # Database migration
│   │   ├── .gitkeep
│   │   ├── env.py                       # Alembic runtime, doc DATABASE_URL tu config
│   │   ├── script.py.mako               # Template sinh migration moi
│   │   └── versions/                    # Cac migration versioned
│   │       ├── 20261013_0001_create_tickets.py # Migration tao bang tickets
│   │       ├── 20261013_0002_create_knowledge_tables.py # Migration tao bang knowledge documents/chunks
│   │       ├── 20261016_0003_approval_audit.py # Migration tao approval requests va audit events
│   │       └── 20261016_0004_auth_and_ticket_ownership.py # Migration users, sessions va ownership/response ticket
│   ├── tests/                           # Test backend
│   │   ├── integration/                 # Integration tests
│   │   │   └── .gitkeep
│   │   ├── security/                    # Security tests
│   │   │   ├── .gitkeep
│   │   │   └── test_security_controls.py # RBAC scope, redaction, prompt-injection marker va evidence citation
│   │   └── unit/                        # Unit tests
│   │       ├── .gitkeep
│   │       ├── test_knowledge_ingestion_api.py # Unit test tra cuu va upload/redact knowledge
│   │       ├── test_retrieval_api.py    # API BM25/dense/hybrid/E4 va filter version
│   │       ├── test_incident_analysis.py # API RCA, filter log/metric va citation validation
│   │       ├── test_query_reranking.py  # Query understanding, rewriting, routing va rerank
│   │       ├── test_rrf.py              # Unit test rank fusion va gop chunk theo document
│   │       ├── test_tickets_api.py      # Unit test cho health va Ticket API
│   │       ├── test_approvals_api.py    # Approval workflow, RBAC va audit persistence
│   │       └── test_auth_rbac.py        # Login, forced password change, ownership va RCA publication
│   └── app/                             # Source code chinh cua backend
│       ├── __init__.py
│       ├── main.py                      # Entry point FastAPI
│       ├── core/                        # Config, logging, dependency injection
│       │   ├── __init__.py
│       │   └── config.py                # App settings: database, Qdrant va Ollama
│       ├── api/                         # REST routers theo nhom endpoint
│       │   ├── __init__.py
│       │   ├── tickets.py               # Ticket API va ticket owner scoping
│       │   ├── auth.py                  # Login, session cookie, logout va doi mat khau
│       │   ├── users.py                 # Tao/khoa tai khoan theo role
│       │   ├── knowledge.py             # Knowledge API doc/chunk lookup va ingest text upload
│       │   ├── logs.py                  # Log Upload API
│       │   ├── retrieval.py             # AI Retrieval API /api/ai/retrieve
│       │   ├── analysis.py              # Incident Analysis API /api/ai/analyze
│       │   ├── approvals.py             # Approval API
│       │   └── dashboard.py             # Dashboard API
│       ├── schemas/                     # Pydantic request/response models
│       │   ├── __init__.py
│       │   ├── knowledge.py             # Knowledge read, upload ingestion va response schemas
│       │   ├── retrieval.py             # Retrieval request/response schemas
│       │   ├── ticket.py                # Ticket CRUD, status va technician response schemas
│       │   ├── auth.py                  # Login, password change va user account schemas
│       │   └── approval.py              # Approval create/decision va audit response schemas
│       ├── db/                          # SQLAlchemy models, session, database connection
│       │   ├── __init__.py
│       │   ├── base.py                  # Declarative Base cho ORM
│       │   ├── models.py                # SQLAlchemy ticket, knowledge, approval va audit models
│       │   └── session.py               # Engine, SessionLocal va get_db dependency
│       ├── services/                    # Ticket, approval, audit, dashboard business services
│       │   ├── __init__.py
│       │   ├── knowledge_service.py     # Query knowledge documents va chunks
│       │   ├── retrieval_service.py     # Dieu phoi BM25/dense retrieval va tai lai model BGE-M3
│       │   └── ticket_service.py        # Business logic CRUD ticket
│       ├── ingestion/                   # Knowledge Ingestion Service
│       │   ├── __init__.py
│       │   ├── cleaner.py               # Clean va redact du lieu nhay cam
│       │   ├── chunker.py               # Chia ticket/runbook thanh chunks
│       │   ├── enricher.py              # Gan metadata, document_id va chunk_id
│       │   ├── pipeline.py              # Dieu phoi ingestion, idempotent IDs va upsert knowledge tables
│       │   └── loaders/                 # Bo nap du lieu tu nhieu nguon
│       │       ├── __init__.py
│       │       ├── csv_ticket.py        # Load normalized_tickets.csv thanh knowledge documents
│       │       ├── json_ticket.py       # Load ticket tu JSON
│       │       ├── markdown_sop.py      # Load runbook/SOP Markdown va parse metadata
│       │       └── pdf_sop.py           # Load runbook/SOP PDF
│       ├── retrieval/                   # Retrieval Service va Hybrid RAG
│       │   ├── __init__.py
│       │   ├── lexical.py               # BM25 keyword retrieval baseline
│       │   ├── dense.py                 # Dense retrieval qua Qdrant va BGE-M3
│       │   ├── rrf.py                   # Gop chunk theo document va hop nhat BM25/dense bang RRF
│       │   ├── reranker.py              # Xep hang candidate bang diem Cross-Encoder
│       │   ├── candidate_pool.py        # Loc access_scope va gop document truoc rerank
│       │   ├── evidence_filter.py       # Loc top-k va kiem tra quyen truy cap
│       │   └── query/                   # Xu ly query dau vao
│       │       ├── __init__.py
│       │       ├── understanding.py     # Nhan dien intent, service va ma loi
│       │       ├── rewriting.py         # Loai boilerplate, giu thong tin incident
│       │       └── routing.py           # Bo qua chitchat, route cac query can evidence
│       ├── analysis/                    # Incident Analysis Service
│       │   ├── __init__.py
│       │   ├── trace.py                 # Ghi trace RCA local theo opt-in RCA_TRACE_PATH
│       │   ├── understanding.py         # Trich service, trieu chung, ma loi
│       │   ├── priority_rules.py        # Rule impact x urgency
│       │   ├── log_filter.py            # Loc theo service/time, provenance; tach rieng real telemetry opt-in khoi synthetic
│       │   ├── prompt_builder.py        # Tao evidence pack va grounded prompt cho LLM
│       │   ├── validator.py             # Kiem tra citation ID, measured values, contradictions va operational evidence
│       │   ├── report.py                # Dong goi grounded RCA report cho technician review
│       │   ├── schema.py                # Request, evidence va RCA JSON schema
│       │   └── service.py               # Dieu phoi retrieval can bang source, log/metric, Ollama va safety checks
│       ├── stores/                      # Adapter cho cac data stores
│       │   ├── __init__.py
│       │   ├── qdrant_store.py          # Qdrant collection, vector upsert va metadata filters
│       │   ├── keyword_index.py         # BM25/TF-IDF index
│       │   ├── file_storage.py          # Runbook, SOP, log, dataset files
│       │   └── postgres.py              # Helper PostgreSQL ngoai ORM neu can
│       ├── models/                      # External/model adapters
│       │   ├── __init__.py
│       │   ├── embedding/               # Embedding model adapters
│       │   │   ├── __init__.py
│       │   │   ├── base.py              # Interface chung cho embedding adapters
│       │   │   ├── minilm.py
│       │   │   └── bge_m3.py            # Adapter BAAI/bge-m3 embedding 1024 dimensions
│       │   ├── reranker/                # Reranker model adapters
│       │   │   ├── __init__.py
│       │   │   ├── base.py
│       │   │   └── bge_reranker.py      # BGE-v2-m3 Cross-Encoder adapter
│       │   └── llm/                     # LLM provider adapters
│       │       ├── __init__.py
│       │       ├── base.py              # Interface RCA generator
│       │       ├── ollama.py            # Adapter Ollama local, structured JSON RCA, tat thinking
│       │       └── gemini.py
│       └── security/                    # Security va governance
│           ├── __init__.py
│           ├── rbac.py                  # RBAC tu user session, khong tin header role
│           ├── auth.py                  # Session cookie, token hash, expiry va revocation
│           ├── passwords.py             # Scrypt password hashing va temporary password validation
│           ├── access_scope.py          # Pham vi truy cap theo tai lieu/nguoi dung
│           ├── redaction.py             # Xoa/an danh du lieu nhay cam
│           ├── prompt_injection.py      # Bao ve prompt injection
│           ├── approval_policy.py       # Chinh sach human approval
│           └── audit.py                 # Ghi audit log
├── frontend/                            # React frontend
│   ├── Dockerfile                       # Docker image cho frontend
│   ├── nginx.conf                       # Nginx static hosting va SPA fallback
│   ├── .dockerignore                    # Loai node_modules/dist khoi Docker build context
│   ├── package.json                     # React, Vite, Tailwind va Lucide dependencies/scripts
│   ├── package-lock.json                # Lockfile dependency frontend
│   ├── index.html                       # HTML entry point cho SPA
│   ├── vite.config.ts                   # Vite, React va Tailwind plugins
│   ├── tsconfig.json                    # TypeScript project references
│   ├── tsconfig.app.json                # TypeScript settings cho React app
│   ├── tsconfig.node.json               # TypeScript settings cho Vite config
│   └── src/
│       ├── App.tsx                      # State/workflow ticket -> RCA -> approval
│       ├── main.tsx                     # React SPA bootstrap
│       ├── index.css                    # Tailwind va responsive styles
│       ├── vite-env.d.ts                # Vite client types
│       ├── types.ts                     # Types ticket, knowledge, retrieval va RCA
│       ├── components/                  # UI components dung chung
│       │   ├── AppShell.tsx             # Sidebar, navigation, header va API status
│       │   ├── NewTicketDialog.tsx      # Form tao ticket
│       │   ├── ui.tsx                   # Panels, table, citation inspector va notices
│       │   └── .gitkeep                 # Placeholder duoc giu tu structure ban dau
│       ├── pages/                       # Cac man hinh chinh cua MVP
│       │   ├── TicketListPage.tsx       # Ticket list, filters, KPI va status update
│       │   ├── TicketDetailPage.tsx     # Ticket detail, retrieval va analysis window
│       │   ├── AnalysisReportPage.tsx   # RCA, citations, missing evidence, verification
│       │   ├── KnowledgePage.tsx        # Text upload, redact preview, document/chunk list
│       │   ├── ApprovalPage.tsx         # Approval review qua API, khong thi hanh command
│       │   ├── DashboardPage.tsx        # Ticket aggregates va benchmark exploratory
│       │   └── AuthPages.tsx             # Login, doi mat khau lan dau, quan ly tai khoan
│       │   └── .gitkeep                 # Placeholder duoc giu tu structure ban dau
│       ├── services/                    # API client va du lieu preview
│           ├── api.ts                   # Typed REST client cho ticket, retrieval, RCA, knowledge va approvals
│           ├── mockData.ts              # Preview fixtures va V2 benchmark numbers
│           └── .gitkeep                 # Placeholder duoc giu tu structure ban dau
│       └── types/                       # Reserved type-module directory
│           └── .gitkeep                 # Type definitions hien dat tai src/types.ts
├── data/                                # Du lieu phuc vu dev, ingestion va evaluation
│   ├── real-telemetry/                  # Thu muc local-only cho telemetry export da duoc phe duyet
│   │   ├── .gitignore                   # Chan commit du lieu operational va service map local
│   │   ├── README.md                    # Schema normalized, provenance va quy tac bao ve du lieu
│   │   ├── service-map.example.json     # Vi du map ten resource nguon sang canonical service
│   │   └── backend.log                  # Log local cho Alloy tail read-only, bi Git ignore
│   ├── raw/                             # Du lieu tho, khong commit noi dung that
│   │   ├── .gitignore
│   │   ├── tickets/                     # Ticket raw tai tu nguon ngoai
│   │   │   ├── Final_Balanced_10000_IT_Support_Tickets.csv
│   │   │   └── dataset.csv
│   │   ├── logs/                        # Log raw tham khao tu LogHub
│   │   ├── metrics/                     # Metric raw tham khao tu NAB
│   │   ├── runbooks/                    # Runbook/SOP raw tham khao
│   │   └── evaluation/                  # Seed evaluation raw neu co
│   ├── external/                        # Du lieu phu tro tai tu repo/nguon ben ngoai
│   │   ├── tickets/                     # Ticket external truoc khi chuyen ve raw/processed
│   │   ├── ner/                         # NER annotations tham khao
│   │   └── knowlegd-base/               # Knowledge base external tham khao
│   ├── specs/                           # Dac ta sinh du lieu synthetic co kiem soat
│   │   ├── runbook_specs.yaml           # 30 spec runbook/SOP cho MVP
│   │   └── ticket_telemetry_scenarios.json # 14 scenario symptom-focused, khong gan root cause
│   ├── processed/                       # Du lieu da lam sach
│   │   ├── .gitkeep
│   │   ├── tickets/                     # Ticket da chuan hoa theo schema noi bo
│   │   │   ├── normalized_tickets.csv   # 10.000 ticket chinh co ticket_id, service, category, priority chuan
│   │   │   └── error_descriptions.csv   # 9.069 mo ta loi phu tro tu dataset.csv
│   │   ├── logs/                        # Log evidence synthetic da gan incident_id
│   │   │   └── incident_logs.jsonl      # 1.000 log synthetic linked 50 scenario; da loai bo RCA/runbook answer markers
│   │   ├── metrics/                     # Metric evidence synthetic da gan incident_id
│   │   │   └── incident_metrics.csv     # 500 metric synthetic time-series rows linked 50 scenario
│   │   └── runbooks/                    # Runbook/SOP synthetic sinh tu spec
│   │       └── RB-*.md                  # 30 runbook Markdown cho MVP
│   ├── runbooks/                        # Runbook/SOP mau
│   │   └── .gitkeep
│   ├── synthetic/                       # Du lieu gia lap co gan nhan
│   │   ├── .gitkeep
│   │   └── telemetry-v1/                # Telemetry synthetic theo 14 ticket co trieu chung ro; khong phai du lieu van hanh that
│   │       ├── README.md                # Provenance, gioi han su dung va huong dan generator
│   │       ├── incident_logs.jsonl      # 112 log synthetic co ticket/service/time window va provenance
│   │       ├── incident_metrics.csv     # 112 metric synthetic theo baseline/anomaly/recovery
│   │       └── manifest.json            # Ticket IDs va khung gio synthetic, khong co RCA ground truth
│   └── eval/                            # Tap evaluation dong bang
│       ├── .gitkeep
│       ├── incidents.jsonl              # 50 synthetic scenario-label lien ket ticket, runbook, log, metric; chua expert-verified
│       ├── evaluation_queries.csv       # 150 evaluation queries dang CSV
│       ├── evaluation_queries.jsonl     # 150 evaluation queries dang JSONL
│       ├── evaluation_queries_v2.csv    # 150 English queries theo split stratified V2
│       ├── evaluation_queries_v2.jsonl  # JSONL tuong ung, dung cho benchmark E1-E4 V2
│       ├── rca_review.csv               # Review legacy cua 8 test case cu, giu nguyen de truy vet
│       ├── benchmark_v2_splits.csv      # Split 35/8/7 phan tang theo category, seed co dinh
│       ├── benchmark_v2_review.csv      # Mau review test V2, can review lai tu trang thai unreviewed
│       ├── incident_link_audit.csv      # Audit links khong chua full ticket/root cause, co cot human review
│       └── incident_evidence_review_v3.csv # Phieu blind review ticket, runbook, log va metric; khong hien nhan/flag audit
├── benchmarks/                          # Benchmark retrieval va RCA
│   ├── run_benchmark.py                 # Benchmark E1-E3, tune candidate_k va tinh Recall/Precision/MRR/nDCG
│   ├── run_e4_ablation.py               # Tune rerank_k va do ablation/latency E1/E3/E4
│   ├── ragas_eval.py                    # RAGAS evaluation neu dung
│   ├── evaluate_rca_matrix.py           # Tinh ma tran answer/abstain va RCA/fact metrics
│   ├── run_rca_baselines.py             # Rule baseline va nearest-ticket baseline tren split V2
│   ├── configs/                         # Cau hinh E1-E5
│   │   ├── e1_tfidf.yml
│   │   ├── e2_dense.yml
│   │   ├── e3_hybrid_rrf.yml           # Cau hinh E3 RRF chon tren dev set
│   │   ├── e4_hybrid_reranker.yml      # Cau hinh model, pool va rewriting E4
│   │   └── e5_grounded_rca.yml
│   ├── metrics/                         # Metric implementations/results
│   │   └── .gitkeep
│   └── reports/                         # Bao cao benchmark
│       ├── .gitkeep
│       ├── e1_bm25_baseline.json        # Ket qua benchmark E1 dang JSON
│       ├── e1_bm25_baseline.md          # Bao cao benchmark E1 cu (1.000 ticket)
│       ├── e1_bm25_full_corpus.json    # BM25 tren 10.210 chunks
│       ├── e1_bm25_full_corpus.md      # Tom tat BM25 tren 10.210 chunks
│       ├── e2_dense_bge_m3_full_corpus.json # BGE-M3 dense tren 10.210 chunks
│       ├── e2_dense_bge_m3_full_corpus.md # Tom tat BGE-M3 dense
│       ├── retrieval_comparison_e1_e2.md # So sanh BM25 va dense tren cung corpus
│       ├── e3_hybrid_rrf_dev_tuning.md # Chon candidate_k tren 21 query dev
│       ├── e1_bm25_week7_test.json    # E1 tren 24 query test
│       ├── e1_bm25_week7_test.md      # Tom tat E1 Tuan 7
│       ├── e2_dense_week7_test.json   # E2 tren 24 query test
│       ├── e2_dense_week7_test.md     # Tom tat E2 Tuan 7
│       ├── e3_hybrid_rrf_week7_test.json # E3 tren 24 query test
│       ├── e3_hybrid_rrf_week7_test.md # Tom tat E3 Tuan 7
│       ├── retrieval_comparison_e1_e2_e3.md # Bang so sanh Recall/Precision/MRR/nDCG
│       ├── e4_dev_tuning.md            # Chon rerank_k tren 21 query dev
│       ├── e4_ablation_test.json       # Chi tiet query, metric va latency E4
│       ├── e4_ablation_test.md         # Bang ablation E1/E3/E4 va delta
│       ├── v2_e1_bm25.md               # E1 BM25 tren stratified V2 test
│       ├── v2_e1_bm25.json             # Chi tiet truy van E1 V2
│       ├── v2_e2_dense.md              # E2 BGE-M3 tren stratified V2 test
│       ├── v2_e2_dense.json            # Chi tiet truy van E2 V2
│       ├── v2_e3_rrf.md                # E3 Hybrid RRF V2 test; candidate_k=100
│       ├── v2_e3_rrf.json              # Chi tiet truy van E3 V2
│       ├── v2_e3_rrf_dev_tuning.md     # Chon candidate_k tren V2 dev
│       ├── v2_e4_final_dev_tuning.md   # Chon rerank_k tren V2 dev, candidate_k=100
│       ├── v2_e4_final_test.md         # Ablation E1/E3/E4 tren V2 test
│       ├── v2_e4_final_test.json       # Chi tiet ablation va latency E4 V2
│       └── retrieval_comparison_v2.md  # Tom tat ket qua E1-E4 va gioi han V2
│       ├── rca_baseline_v2_predictions.csv # Du doan baseline va synthetic reference de cham offline
│       ├── rca_baseline_v2.md           # Ket qua smoke baseline va canh bao synthetic shortcut
│       └── rca_data_audit_v3.md         # Audit 50 mapping va cac quyet dinh can human review
├── scripts/                             # Script tien ich ngoai app runtime
│   ├── normalize_tickets.py             # Chuan hoa raw ticket CSV thanh processed ticket schema
│   ├── generate_runbooks.py             # Sinh runbook Markdown tu runbook_specs va ticket da chuan hoa
│   ├── validate_runbooks.py             # Kiem tra so luong va format runbook MVP
│   ├── generate_incident_ground_truth.py # Sinh 50 synthetic scenario-label va evidence lien ket; khong phai expert truth
│   ├── validate_incident_ground_truth.py # Kiem tra lien ket va exact-label leakage
│   ├── prepare_rca_review.py            # Tao mau review RCA va tinh abstention/accuracy/unsupported-fact rate
│   ├── prepare_rca_benchmark_v2.py      # Sinh split stratified va review template V2, khong sua du lieu cu
│   ├── prepare_evaluation_review.py      # Tao/cap nhat blind review sheet cho 50 incident, giu annotations
│   ├── audit_incident_links.py          # Audit ticket/symptom/service/log/metric link, khong auto-relabel
│   ├── generate_ticket_telemetry.py     # Sinh telemetry synthetic rieng, khong ghi de log/metric cu
│   ├── import_real_telemetry.py         # Normalize CSV/JSONL export read-only, UTC, service map va redaction
│   ├── seed_db.py                       # Seed PostgreSQL tickets tu normalized_tickets.csv
│   ├── create_admin.py                  # Bootstrap admin bang prompt, khong co mat khau mac dinh
│   ├── ingest_knowledge.py              # Ingest ticket/runbook vao knowledge_documents va knowledge_chunks
│   ├── build_vector_index.py            # Tao BGE-M3 embeddings va upsert vectors vao Qdrant
│   ├── build_index.py                   # Build keyword/vector indexes
│   └── split_dataset.py                 # Chia train/dev/test
├── docs/                                # Tai lieu du an
│   ├── 01-kien-truc/                    # Tai lieu kien truc he thong
│   │   ├── roadmap-sync.md              # Theo doi roadmap va tien do module
│   │   ├── structure-sync.md            # Quy tac dong bo cau truc thu muc
│   │   └── structure.md                 # Tai lieu cau truc thu muc
│   ├── 02-diagram/                      # So do kien truc va diagram
│   │   └── diagram-architecture.png     # So do kien truc tong the
│   ├── 03-De-Cuong/                     # De cuong, plan va tai lieu bao cao goc
│   │   ├── De_cuong_chi_tiet_AI_IT_Helpdesk_Incident_Assistant.docx
│   │   ├── De_cuong_chi_tiet_AI_IT_Helpdesk_Incident_Assistant_Ke_hoach_12_tuan.pdf
│   │   └── plan.md                      # Ke hoach tong the
│   ├── 04-activity/                     # So do activity PlantUML cho 8 use case
│   │   ├── uc01-tao-ticket-su-co-it.puml
│   │   ├── uc02-quan-ly-vong-doi-ticket.puml
│   │   ├── uc03-nap-du-lieu-tri-thuc.puml
│   │   ├── uc04-tim-evidence-bang-hybrid-rag.puml
│   │   ├── uc05-phan-tich-incident-va-sinh-rca-report.puml
│   │   ├── uc06-xem-citation-va-kiem-tra-bang-chung.puml
│   │   ├── uc07-phe-duyet-hoac-tu-choi-hanh-dong-de-xuat.puml
│   │   └── uc08-xem-dashboard-van-hanh.puml
│   ├── 04-usecase/                      # Dac ta 8 use case chinh cua he thong
│   │   ├── uc01-tao-ticket-su-co-it.md
│   │   ├── uc02-quan-ly-vong-doi-ticket.md
│   │   ├── uc03-nap-du-lieu-tri-thuc.md
│   │   ├── uc04-tim-evidence-bang-hybrid-rag.md
│   │   ├── uc05-phan-tich-incident-va-sinh-rca-report.md
│   │   ├── uc06-xem-citation-va-kiem-tra-bang-chung.md
│   │   ├── uc07-phe-duyet-hoac-tu-choi-hanh-dong-de-xuat.md
│   │   └── uc08-xem-dashboard-van-hanh.md
│   ├── 05-thiet-ke-du-lieu/             # Tai lieu thiet ke du lieu va dataset tuan 2
│   │   ├── data-dictionary.md           # Tu dien du lieu, enum va y nghia cac bang
│   │   ├── auth-rbac-workflow.md         # Role, ownership, RCA review va bootstrap admin
│   │   ├── erd.md                       # ERD ban dau va quan he giua cac bang
│   │   ├── sample-data-plan.md          # Ke hoach ticket/runbook/log/metric mau
│   │   ├── evaluation-set-plan.md       # Ke hoach tap danh gia retrieval va RCA
│   │   ├── real-telemetry-onboarding.md  # Quy trinh import telemetry van hanh va expert-review
│   │   ├── rca-benchmark-protocol.md    # Quy tac split, sufficiency rubric, leakage control va bao cao RCA
│   │   └── week11-security-and-rca-evaluation.md # Approval/audit API, security tests, RCA results va limitations
└── infra/                               # Docker Compose va ha tang local
    ├── .gitkeep
    ├── docker-compose.yml               # Frontend, PostgreSQL, Qdrant va profile observability
    └── observability/                   # Cau hinh local Grafana, Loki, Prometheus va Alloy
        ├── prometheus.yml               # Scrape Helpdesk API va Qdrant
        ├── loki-config.yaml             # Loki filesystem local, retention 7 ngay, dev-only
        ├── alloy-config.alloy           # Tail rieng backend.log read-only va forward toi Loki
        └── grafana/                     # Provision datasource va dashboard
            ├── provisioning/
            │   ├── datasources/datasources.yml
            │   └── dashboards/dashboards.yml
            └── dashboards/helpdesk-overview.json
```


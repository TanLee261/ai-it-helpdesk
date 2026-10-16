# ERD Ban Đầu

Tài liệu này mô tả mô hình quan hệ dữ liệu ban đầu cho MVP. Đây là ERD mức phân tích, chưa phải migration database cuối cùng.

## 1. Các Entity Chính

```text
users
tickets
knowledge_documents
knowledge_chunks
logs
metrics
incident_analyses
approvals
audit_logs
```

## 2. Quan Hệ Tổng Quan

```text
users ──< tickets
users ──< audit_logs
users ──< approvals

tickets ──< incident_analyses
tickets ──< approvals
tickets ──< audit_logs

knowledge_documents ──< knowledge_chunks

incident_analyses ──< approvals

logs / metrics
  └── linked by service + timestamp/time window + trace_id
```

## 3. Sơ Đồ ERD Dạng Text

```text
┌────────────┐
│ users      │
│------------│
│ id         │
│ user_id    │
│ full_name  │
│ email      │
│ role       │
└─────┬──────┘
      │
      │ created_by / assignee_id
      v
┌──────────────┐          ┌────────────────────┐
│ tickets      │          │ audit_logs          │
│--------------│          │--------------------│
│ id           │<─────────│ entity_id           │
│ ticket_id    │          │ entity_type         │
│ title        │          │ actor_id            │
│ description  │          │ action              │
│ service      │          │ before_value        │
│ category     │          │ after_value         │
│ priority     │          │ created_at          │
│ status       │          └────────────────────┘
└──────┬───────┘
       │
       │ ticket_id
       v
┌─────────────────────┐
│ incident_analyses   │
│---------------------│
│ id                  │
│ analysis_id         │
│ ticket_id           │
│ model_name          │
│ retrieval_config    │
│ analysis_json       │
└─────────┬───────────┘
          │
          │ analysis_id
          v
┌─────────────────────┐
│ approvals           │
│---------------------│
│ id                  │
│ approval_id         │
│ analysis_id         │
│ ticket_id           │
│ proposed_action     │
│ risk_level          │
│ decision            │
│ decided_by          │
└─────────────────────┘

┌─────────────────────┐
│ knowledge_documents │
│---------------------│
│ id                  │
│ document_id         │
│ title               │
│ source_type         │
│ source              │
│ service             │
│ version             │
│ access_scope        │
└─────────┬───────────┘
          │ document_id
          v
┌─────────────────────┐
│ knowledge_chunks    │
│---------------------│
│ id                  │
│ chunk_id            │
│ document_id         │
│ content             │
│ metadata            │
│ qdrant_point_id     │
└─────────────────────┘

┌──────────────┐       ┌──────────────┐
│ logs         │       │ metrics      │
│--------------│       │--------------│
│ log_id       │       │ metric_id    │
│ timestamp    │       │ timestamp    │
│ service      │       │ service      │
│ host         │       │ host         │
│ level        │       │ metric_name  │
│ message      │       │ value        │
│ trace_id     │       │ unit         │
└──────────────┘       └──────────────┘
```

## 4. Quan Hệ Chi Tiết

### 4.1. `users` -> `tickets`

Một user có thể tạo nhiều ticket.

```text
users.id = tickets.created_by
users.id = tickets.assignee_id
```

`created_by` bắt buộc, `assignee_id` có thể rỗng khi ticket chưa được phân công.

### 4.2. `tickets` -> `incident_analyses`

Một ticket có thể có nhiều lần phân tích RCA.

```text
tickets.ticket_id = incident_analyses.ticket_id
```

Lý do cho phép nhiều analysis:

- Chạy lại với cấu hình retrieval khác.
- Chạy lại sau khi bổ sung log/evidence.
- So sánh output giữa các model.

### 4.3. `incident_analyses` -> `approvals`

Một analysis có thể tạo nhiều proposed actions, mỗi action có một approval record.

```text
incident_analyses.analysis_id = approvals.analysis_id
```

MVP chỉ ghi nhận quyết định approve/reject, không thực thi lệnh thật.

### 4.4. `knowledge_documents` -> `knowledge_chunks`

Một document được chia thành nhiều chunk.

```text
knowledge_documents.document_id = knowledge_chunks.document_id
```

Các chunk dùng cho:

- Keyword index.
- Qdrant vector index.
- Evidence citation.

### 4.5. `logs` Và `metrics` -> `tickets`

MVP không bắt buộc foreign key trực tiếp từ log/metric đến ticket.

Liên kết phân tích theo:

```text
service
timestamp / time window
trace_id nếu có
```

Ví dụ:

```text
ticket.service = logs.service
ticket.event_window contains logs.timestamp
logs.trace_id = ticket.trace_id nếu ticket có trace_id
```

## 5. Gợi Ý Index

| Bảng | Index gợi ý | Mục đích |
|---|---|---|
| `tickets` | `ticket_id` | Tìm ticket theo mã |
| `tickets` | `service`, `category`, `status` | Lọc ticket |
| `knowledge_documents` | `document_id` | Tìm tài liệu gốc |
| `knowledge_documents` | `service`, `source_type`, `access_scope` | Lọc tài liệu theo quyền và service |
| `knowledge_chunks` | `chunk_id` | Truy ngược evidence |
| `logs` | `service`, `timestamp` | Lọc log theo service và time window |
| `logs` | `trace_id` | Truy log theo trace |
| `metrics` | `service`, `timestamp`, `metric_name` | Lọc metric |
| `incident_analyses` | `analysis_id`, `ticket_id` | Tìm analysis |
| `audit_logs` | `entity_type`, `entity_id`, `created_at` | Truy lịch sử thao tác |

## 6. Ghi Chú Thiết Kế

- `verified_root_cause` trong ticket là dữ liệu đã xác minh, không phải giả thuyết của AI.
- `ranked_hypotheses` trong analysis là giả thuyết có xếp hạng, cần evidence hỗ trợ.
- Evidence ID phải có thể truy ngược về `knowledge_chunks`, `logs`, `metrics` hoặc ticket lịch sử.
- Raw log số lượng lớn không nên đưa thẳng vào vector store trong MVP.
- Qdrant lưu vector và metadata filter; PostgreSQL vẫn là nơi lưu metadata chính.


# Data Dictionary

Tài liệu này mô tả các nhóm dữ liệu cốt lõi của hệ thống AI IT Helpdesk & Incident Assistant trong giai đoạn MVP. Mục tiêu là thống nhất tên bảng, trường dữ liệu, kiểu dữ liệu dự kiến, ý nghĩa nghiệp vụ và các enum dùng chung trước khi triển khai database thật.

## 1. Nguyên Tắc Thiết Kế Dữ Liệu

- Phân biệt rõ dữ liệu đã xác minh và giả thuyết do AI sinh ra.
- Không lưu password, token, API key, dữ liệu cá nhân hoặc thông tin nhạy cảm chưa được redact.
- Timestamp nên dùng chuẩn ISO 8601 và quy đổi về UTC khi lưu.
- Service name, category, priority, status, impact và urgency phải dùng enum thống nhất.
- Evidence phải có ID rõ ràng để truy ngược về ticket, runbook, log hoặc metric.
- Log và metrics trong MVP không nhất thiết có foreign key trực tiếp đến ticket; có thể liên kết bằng `service`, `time window` và `trace_id`.

## 2. Enum Dùng Chung

### 2.1. Ticket Status

| Giá trị | Ý nghĩa |
|---|---|
| `new` | Ticket mới tạo |
| `in_progress` | Đang xử lý |
| `resolved` | Đã xử lý xong |
| `closed` | Đã đóng |

### 2.2. Category

| Giá trị | Ý nghĩa |
|---|---|
| `network` | Lỗi mạng, DNS, VPN, gateway, timeout |
| `server_api` | Lỗi server, API, deployment, HTTP 500, latency |
| `database` | Lỗi database, connection pool, slow query, lock |
| `account` | Lỗi tài khoản, quyền truy cập |
| `other` | Nhóm khác ngoài phạm vi chính |

### 2.3. Priority

| Giá trị | Ý nghĩa |
|---|---|
| `p1` | Nghiêm trọng, ảnh hưởng lớn, cần xử lý ngay |
| `p2` | Cao, ảnh hưởng đáng kể |
| `p3` | Trung bình |
| `p4` | Thấp |

### 2.4. Impact Và Urgency

| Giá trị | Ý nghĩa |
|---|---|
| `low` | Ảnh hưởng/thời gian xử lý không khẩn cấp |
| `medium` | Ảnh hưởng/thời gian xử lý trung bình |
| `high` | Ảnh hưởng/thời gian xử lý cao |

### 2.5. Source Type

| Giá trị | Ý nghĩa |
|---|---|
| `historical_ticket` | Ticket lịch sử |
| `runbook` | Runbook kỹ thuật |
| `sop` | Quy trình vận hành chuẩn |
| `log_summary` | Bản tóm tắt hoặc đoạn log đã lọc |
| `metric_summary` | Bản tóm tắt hoặc đoạn metric đã lọc |

## 3. Bảng `users`

Lưu thông tin người dùng cơ bản để liên kết với ticket, audit và approval.

| Trường | Kiểu dự kiến | Bắt buộc | Mô tả |
|---|---|---:|---|
| `id` | UUID / integer | Có | Khóa chính nội bộ |
| `user_id` | string | Có | Mã người dùng hiển thị hoặc đồng bộ từ hệ thống auth |
| `full_name` | string | Có | Họ tên người dùng |
| `email` | string | Có | Email đăng nhập |
| `role` | string | Có | Vai trò: staff, technician, lead, admin |
| `created_at` | timestamp | Có | Thời điểm tạo |
| `updated_at` | timestamp | Có | Thời điểm cập nhật |

## 4. Bảng `tickets`

Lưu ticket hiện tại và ticket lịch sử đã chuẩn hóa.

| Trường | Kiểu dự kiến | Bắt buộc | Mô tả |
|---|---|---:|---|
| `id` | UUID / integer | Có | Khóa chính nội bộ |
| `ticket_id` | string | Có | Mã ticket hiển thị, ví dụ `TCK-0001` |
| `title` | string | Có | Tiêu đề sự cố |
| `description` | text | Có | Mô tả chi tiết lỗi |
| `service` | string | Có | Service bị ảnh hưởng, ví dụ `payment-api` |
| `category` | enum | Có | Nhóm lỗi theo enum category |
| `priority` | enum | Có | Mức ưu tiên `p1` đến `p4` |
| `status` | enum | Có | Trạng thái ticket |
| `impact` | enum | Có | Mức ảnh hưởng |
| `urgency` | enum | Có | Độ khẩn cấp |
| `assignee_id` | UUID / integer | Không | Người phụ trách |
| `created_by` | UUID / integer | Có | Người tạo ticket |
| `verified_root_cause` | text | Không | Nguyên nhân đã xác minh |
| `resolution` | text | Không | Cách xử lý cuối cùng |
| `created_at` | timestamp | Có | Thời điểm tạo |
| `updated_at` | timestamp | Có | Thời điểm cập nhật |
| `resolved_at` | timestamp | Không | Thời điểm xử lý xong |

## 5. Bảng `knowledge_documents`

Lưu metadata cấp tài liệu cho ticket lịch sử, runbook, SOP, log summary hoặc metric summary.

| Trường | Kiểu dự kiến | Bắt buộc | Mô tả |
|---|---|---:|---|
| `id` | UUID / integer | Có | Khóa chính nội bộ |
| `document_id` | string | Có | Mã tài liệu, ví dụ `RB-001` |
| `title` | string | Có | Tên tài liệu |
| `source_type` | enum | Có | Loại nguồn |
| `source` | string | Có | Đường dẫn file, URL hoặc nguồn nhập |
| `service` | string | Không | Service liên quan |
| `version` | string | Không | Phiên bản tài liệu |
| `access_scope` | string | Có | Phạm vi truy cập |
| `created_at` | timestamp | Có | Thời điểm tạo |
| `updated_at` | timestamp | Có | Thời điểm cập nhật |

## 6. Bảng `knowledge_chunks`

Lưu các đoạn nhỏ đã chunk để phục vụ retrieval.

| Trường | Kiểu dự kiến | Bắt buộc | Mô tả |
|---|---|---:|---|
| `id` | UUID / integer | Có | Khóa chính nội bộ |
| `chunk_id` | string | Có | Mã chunk, ví dụ `RB-001-C001` |
| `document_id` | string / FK | Có | Liên kết đến tài liệu gốc |
| `content` | text | Có | Nội dung chunk |
| `metadata` | JSON | Có | Metadata: service, category, source, version, timestamp |
| `qdrant_point_id` | string | Không | ID vector trong Qdrant |
| `created_at` | timestamp | Có | Thời điểm tạo |

## 7. Bảng `logs`

Lưu log đã lọc hoặc log mẫu phục vụ phân tích incident. Trong MVP, log được lọc theo `service` và `time window` trước khi đưa vào phân tích.

| Trường | Kiểu dự kiến | Bắt buộc | Mô tả |
|---|---|---:|---|
| `id` | UUID / integer | Có | Khóa chính nội bộ |
| `log_id` | string | Có | Mã log, ví dụ `LOG-001` |
| `timestamp` | timestamp | Có | Thời điểm phát sinh log |
| `service` | string | Có | Service phát sinh log |
| `host` | string | Không | Máy chủ hoặc container |
| `level` | string | Có | INFO, WARN, ERROR, DEBUG |
| `message` | text | Có | Nội dung log đã redact |
| `trace_id` | string | Không | Trace ID nếu có |
| `source_file` | string | Không | File log gốc |
| `created_at` | timestamp | Có | Thời điểm nhập vào hệ thống |

## 8. Bảng `metrics`

Lưu metric mẫu hoặc metric đã lọc phục vụ xác minh incident.

| Trường | Kiểu dự kiến | Bắt buộc | Mô tả |
|---|---|---:|---|
| `id` | UUID / integer | Có | Khóa chính nội bộ |
| `metric_id` | string | Có | Mã metric |
| `timestamp` | timestamp | Có | Thời điểm ghi nhận |
| `service` | string | Có | Service liên quan |
| `host` | string | Không | Host/container |
| `metric_name` | string | Có | Tên metric, ví dụ `latency_ms`, `db_pool_usage` |
| `value` | number | Có | Giá trị metric |
| `unit` | string | Không | Đơn vị đo |
| `created_at` | timestamp | Có | Thời điểm nhập vào hệ thống |

## 9. Bảng `incident_analyses`

Lưu kết quả AI phân tích RCA cho ticket.

| Trường | Kiểu dự kiến | Bắt buộc | Mô tả |
|---|---|---:|---|
| `id` | UUID / integer | Có | Khóa chính nội bộ |
| `analysis_id` | string | Có | Mã phân tích |
| `ticket_id` | string / FK | Có | Ticket được phân tích |
| `model_name` | string | Có | Model LLM sử dụng |
| `retrieval_config` | JSON | Có | Cấu hình retrieval E1-E5 hoặc top-k |
| `observed_facts` | JSON | Có | Dữ kiện quan sát được |
| `ranked_hypotheses` | JSON | Có | Danh sách giả thuyết RCA |
| `supporting_evidence_ids` | JSON | Có | Evidence IDs được dùng |
| `missing_evidence` | JSON | Không | Bằng chứng còn thiếu |
| `verification_steps` | JSON | Không | Các bước xác minh |
| `proposed_actions` | JSON | Không | Hành động đề xuất |
| `analysis_json` | JSON | Có | Output đầy đủ của AI |
| `created_at` | timestamp | Có | Thời điểm tạo phân tích |

## 10. Bảng `approvals`

Lưu quyết định approve/reject cho hành động đề xuất. MVP chỉ ghi nhận quyết định, không thực thi lệnh thật.

| Trường | Kiểu dự kiến | Bắt buộc | Mô tả |
|---|---|---:|---|
| `id` | UUID / integer | Có | Khóa chính nội bộ |
| `approval_id` | string | Có | Mã approval |
| `analysis_id` | string / FK | Có | Phân tích liên quan |
| `ticket_id` | string / FK | Có | Ticket liên quan |
| `proposed_action` | text | Có | Hành động AI đề xuất |
| `risk_level` | enum | Có | low, medium, high |
| `decision` | enum | Có | pending, approved, rejected |
| `reason` | text | Không | Lý do approve/reject |
| `decided_by` | UUID / integer | Không | Người quyết định |
| `decided_at` | timestamp | Không | Thời điểm quyết định |
| `created_at` | timestamp | Có | Thời điểm tạo approval |

## 11. Bảng `audit_logs`

Lưu lịch sử thao tác quan trọng.

| Trường | Kiểu dự kiến | Bắt buộc | Mô tả |
|---|---|---:|---|
| `id` | UUID / integer | Có | Khóa chính nội bộ |
| `actor_id` | UUID / integer | Không | Người thực hiện |
| `action` | string | Có | Hành động đã thực hiện |
| `entity_type` | string | Có | Loại đối tượng: ticket, analysis, approval, knowledge |
| `entity_id` | string | Có | ID đối tượng |
| `before_value` | JSON | Không | Giá trị trước thay đổi |
| `after_value` | JSON | Không | Giá trị sau thay đổi |
| `created_at` | timestamp | Có | Thời điểm ghi audit |

## 12. Action Audit Dự Kiến

| Action | Ý nghĩa |
|---|---|
| `create_ticket` | Tạo ticket |
| `update_ticket_status` | Cập nhật trạng thái ticket |
| `upload_knowledge` | Nạp tài liệu tri thức |
| `run_retrieval` | Chạy retrieval |
| `generate_analysis` | Sinh RCA report |
| `view_evidence` | Xem citation/evidence |
| `approve_action` | Phê duyệt hành động |
| `reject_action` | Từ chối hành động |


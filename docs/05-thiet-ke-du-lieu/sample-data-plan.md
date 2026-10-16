# Sample Data Plan

Tài liệu này mô tả kế hoạch chuẩn bị dữ liệu mẫu cho Tuần 2. Mục tiêu là tạo bộ dữ liệu nhỏ, sạch, thống nhất format để phục vụ thiết kế schema, thử retrieval baseline và chuẩn bị cho ingestion pipeline ở các tuần sau.

## 1. Mục Tiêu

Chuẩn bị dữ liệu mẫu gồm:

- Ticket mẫu.
- Runbook/SOP mẫu.
- Log mẫu.
- Metric mẫu.

Quy mô giai đoạn đầu:

| Nhóm dữ liệu | Số lượng gợi ý | Mục đích |
|---|---:|---|
| Ticket mẫu | 10-20 dòng | Kiểm tra schema ticket và retrieval bằng ticket lịch sử |
| Runbook/SOP mẫu | 5-10 tài liệu | Kiểm tra chunking và citation |
| Log mẫu | 50-200 dòng | Kiểm tra lọc theo service + time window |
| Metric mẫu | 20-100 dòng | Kiểm tra evidence dạng số liệu |

## 2. Quy Tắc Chuẩn Hóa Chung

- Timestamp dùng ISO 8601, ưu tiên UTC: `2026-10-12T09:05:00Z`.
- Service name viết thống nhất, ví dụ `payment-api`, `vpn-gateway`, `customer-db`.
- Category dùng enum: `network`, `server_api`, `database`, `account`, `other`.
- Priority dùng enum: `p1`, `p2`, `p3`, `p4`.
- Status dùng enum: `new`, `in_progress`, `resolved`, `closed`.
- Impact và urgency dùng enum: `low`, `medium`, `high`.
- Không dùng dữ liệu thật có chứa mật khẩu, token, API key, email cá nhân hoặc thông tin mạng nhạy cảm.
- Nếu dữ liệu là synthetic, phải ghi rõ là dữ liệu giả lập.

## 3. Ticket Mẫu

### 3.1. Format Đề Xuất

```csv
ticket_id,title,description,service,category,priority,status,impact,urgency,verified_root_cause,resolution,created_at,resolved_at
```

### 3.2. Ví Dụ

```csv
TCK-0001,Payment API trả HTTP 500,Người dùng không thanh toán được,payment-api,server_api,p1,resolved,high,high,connection pool exhausted,Tăng pool size và restart service,2026-10-12T09:00:00Z,2026-10-12T09:45:00Z
TCK-0002,VPN không kết nối được,Nhân viên remote không truy cập được VPN,vpn-gateway,network,p2,resolved,medium,high,dns resolution failure,Cập nhật DNS resolver,2026-10-12T10:00:00Z,2026-10-12T10:40:00Z
TCK-0003,Database query chậm,Báo cáo doanh thu tải rất lâu,reporting-db,database,p2,resolved,medium,medium,missing index,Tạo index cho cột transaction_date,2026-10-12T11:00:00Z,2026-10-12T12:10:00Z
```

### 3.3. Quy Tắc Làm Sạch Ticket

- Loại bỏ ticket trùng `ticket_id`.
- Chuẩn hóa service name.
- Chuẩn hóa category theo enum.
- Nếu chưa có root cause đã xác minh, để trống `verified_root_cause`, không tự bịa.
- Không để resolution chứa lệnh nguy hiểm thật hoặc thông tin nhạy cảm.

## 4. Runbook/SOP Mẫu

### 4.1. Format Đề Xuất

```csv
document_id,title,service,version,access_scope,content
```

### 4.2. Ví Dụ

```csv
RB-001,Kiểm tra lỗi HTTP 500 payment-api,payment-api,v1,it_internal,"Bước 1 kiểm tra log lỗi. Bước 2 kiểm tra database connection pool. Bước 3 kiểm tra deployment gần nhất. Bước 4 xác minh error rate sau khi xử lý."
RB-002,Kiểm tra lỗi VPN không kết nối,vpn-gateway,v1,it_internal,"Bước 1 kiểm tra DNS. Bước 2 kiểm tra trạng thái gateway. Bước 3 kiểm tra tài khoản người dùng. Bước 4 kiểm tra log xác thực."
RB-003,Kiểm tra slow query reporting-db,reporting-db,v1,it_internal,"Bước 1 xác định query chậm. Bước 2 kiểm tra execution plan. Bước 3 kiểm tra index. Bước 4 kiểm tra lock và tài nguyên hệ thống."
```

### 4.3. Quy Tắc Làm Sạch Runbook/SOP

- Giữ nguyên thứ tự các bước xử lý.
- Mỗi runbook cần có `document_id`, `service`, `version`, `access_scope`.
- Không đưa credential, IP nhạy cảm hoặc command production nguy hiểm vào tài liệu mẫu.
- Nếu nội dung lấy từ tài liệu public, cần ghi nguồn ở metadata khi tạo dữ liệu thật.

## 5. Log Mẫu

### 5.1. Format Đề Xuất

```csv
log_id,timestamp,service,host,level,message,trace_id
```

### 5.2. Ví Dụ

```csv
LOG-001,2026-10-12T09:05:00Z,payment-api,payment-01,ERROR,Database connection pool exhausted,trace-pay-001
LOG-002,2026-10-12T09:06:00Z,payment-api,payment-01,WARN,Request latency exceeded 5000 ms,trace-pay-001
LOG-003,2026-10-12T10:05:00Z,vpn-gateway,vpn-01,ERROR,DNS resolver timeout,trace-vpn-001
LOG-004,2026-10-12T11:08:00Z,reporting-db,db-02,WARN,Slow query detected on transaction report,trace-db-001
```

### 5.3. Quy Tắc Làm Sạch Log

- Redact password, token, API key, session ID và dữ liệu cá nhân.
- Chuẩn hóa timestamp về UTC.
- Chuẩn hóa level: INFO, WARN, ERROR, DEBUG.
- Log trong MVP chỉ dùng sau khi lọc theo service + time window.
- Không vector hóa toàn bộ raw logs trong MVP.

## 6. Metric Mẫu

### 6.1. Format Đề Xuất

```csv
metric_id,timestamp,service,host,metric_name,value,unit
```

### 6.2. Ví Dụ

```csv
MET-001,2026-10-12T09:05:00Z,payment-api,payment-01,db_pool_usage,100,percent
MET-002,2026-10-12T09:06:00Z,payment-api,payment-01,latency_p95,5200,ms
MET-003,2026-10-12T10:05:00Z,vpn-gateway,vpn-01,dns_timeout_count,35,count
MET-004,2026-10-12T11:08:00Z,reporting-db,db-02,query_duration_p95,8600,ms
```

### 6.3. Quy Tắc Làm Sạch Metric

- `metric_name` phải thống nhất cách đặt tên.
- `value` phải là số.
- `unit` cần rõ ràng: `ms`, `percent`, `count`, `requests_per_second`.
- Metric dùng để hỗ trợ xác minh RCA, không thay thế evidence từ ticket/runbook/log.

## 7. Checklist Dữ Liệu Mẫu

```text
[ ] Có 10-20 ticket mẫu.
[ ] Có 5-10 runbook/SOP mẫu.
[ ] Có 50-200 dòng log mẫu.
[ ] Có 20-100 dòng metric mẫu.
[ ] Timestamp dùng ISO 8601/UTC.
[ ] Service name thống nhất.
[ ] Category, status, priority, impact, urgency dùng enum.
[ ] Không có password, token, API key hoặc PII.
[ ] Dữ liệu synthetic được ghi rõ là giả lập.
```


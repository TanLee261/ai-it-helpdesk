# 3.1.4.5 UC05 Phân tích incident và sinh RCA report

**Tên use case:** Phân tích incident và sinh RCA report

**Mô tả sơ lược:** Cho phép hệ thống tổng hợp ticket hiện tại với evidence đã tìm được, sau đó dùng LLM tạo báo cáo nguyên nhân gốc rễ có cấu trúc, có kiểm chứng evidence.

**Actor chính:** Kỹ thuật viên IT

**Actor phụ:** LLM Provider (Ollama hoặc API theo cấu hình)

**Tiền điều kiện:** Ticket tồn tại và người dùng đã đăng nhập.

**Hậu điều kiện:** Báo cáo RCA được lưu với các trường observed_facts, ranked_hypotheses, evidence IDs, missing evidence, verification_steps, proposed_actions; có bản ghi audit.

**Luồng sự kiện chính**

| Người dùng | Hệ thống |
|---|---|
| 1. Chọn ticket và yêu cầu phân tích | |
| | 2. Lấy thông tin ticket hiện tại |
| | 3. Thực hiện UC04 để lấy evidence liên quan |
| | 4. Lọc log và metrics theo service và time window |
| | 5. Xây prompt grounded chỉ chứa evidence đã lọc |
| | 6. LLM sinh structured JSON |
| | 7. Evidence Validation: kiểm tra evidence ID có thật, loại claim không có nguồn |
| | 8. Đánh dấu bằng chứng còn thiếu và lưu analysis |
| | 9. Ghi audit log và hiển thị báo cáo |

**Luồng sự kiện thay thế**

6.a1 LLM trả về JSON không đúng schema, hệ thống thử lại tối đa một lần, nếu vẫn lỗi thì báo không tạo được báo cáo.

7.a1 Toàn bộ claim không có evidence hợp lệ, báo cáo chỉ hiển thị observed facts đã xác minh và yêu cầu thêm dữ liệu.

**Luồng ngoại lệ**

E1 LLM Provider không phản hồi quá thời gian cho phép: hệ thống hủy yêu cầu, lưu trạng thái lỗi và cho phép người dùng chạy lại.

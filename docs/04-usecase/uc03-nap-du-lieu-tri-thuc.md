# 3.1.4.3 UC03 Nạp dữ liệu tri thức

**Tên use case:** Nạp dữ liệu tri thức

**Mô tả sơ lược:** Cho phép admin hoặc kỹ thuật viên upload ticket lịch sử, runbook/SOP, log hoặc metrics để hệ thống làm sạch, gắn metadata và lập chỉ mục.

**Actor chính:** Admin, Kỹ thuật viên IT

**Actor phụ:** Không có

**Tiền điều kiện:** Người dùng đã đăng nhập và có quyền nạp dữ liệu.

**Hậu điều kiện:** Dữ liệu được lưu kèm metadata, cập nhật vào keyword index và Qdrant (nếu là tài liệu tri thức), và có bản ghi audit.

**Luồng sự kiện chính**

| Người dùng | Hệ thống |
|---|---|
| 1. Chọn loại dữ liệu và tải file lên | |
| | 2. Kiểm tra định dạng và kích thước |
| | 3. Parse và chuẩn hóa (timestamp UTC, service, category, mã lỗi) |
| | 4. Redact dữ liệu nhạy cảm (mật khẩu, token, API key) |
| | 5. Chia chunk và gắn metadata (document_id, chunk_id, source, version, access_scope) |
| | 6. Lưu file gốc vào File Storage và metadata vào PostgreSQL |
| | 7. Cập nhật keyword index và upsert vector vào Qdrant với ID idempotent |
| | 8. Ghi audit log và hiển thị số chunk đã nạp, số bản ghi bị loại |

**Luồng sự kiện thay thế**

2.a1 Định dạng không được hỗ trợ, hệ thống báo lỗi và dừng.

6.a1 Tài liệu đã tồn tại với cùng version, hệ thống bỏ qua phần trùng và báo số lượng đã bỏ qua.

**Luồng ngoại lệ**

E1 Lỗi khi cập nhật Qdrant: tài liệu được đánh dấu chờ lập chỉ mục. Người dùng có thể thử lại mà không tạo bản trùng nhờ ID idempotent.

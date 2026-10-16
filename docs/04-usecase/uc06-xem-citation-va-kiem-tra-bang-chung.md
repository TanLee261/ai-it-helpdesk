# 3.1.4.6 UC06 Xem citation và kiểm tra bằng chứng

**Tên use case:** Xem citation và kiểm tra bằng chứng

**Mô tả sơ lược:** Cho phép kỹ thuật viên xem từng evidence ID được AI sử dụng, nguồn gốc (ticket, runbook, log) và đoạn trích tương ứng để tự kiểm chứng gợi ý.

**Actor chính:** Kỹ thuật viên IT

**Actor phụ:** Không có

**Tiền điều kiện:** Báo cáo RCA đã được tạo và người dùng có quyền truy cập báo cáo.

**Hậu điều kiện:** Không thay đổi dữ liệu. Lượt xem evidence được ghi audit log.

**Luồng sự kiện chính**

| Người dùng | Hệ thống |
|---|---|
| 1. Mở báo cáo RCA | |
| | 2. Hiển thị danh sách citation (evidence ID) |
| 3. Chọn một citation | |
| | 4. Kiểm tra quyền truy cập access_scope của evidence |
| | 5. Lấy evidence và nguồn gốc (ticket, runbook hoặc log) |
| | 6. Hiển thị đoạn trích, nguồn và liên kết đến bản gốc |
| | 7. Ghi audit log |
| 8. Đối chiếu evidence với kết luận | |

**Luồng sự kiện thay thế**

4.a1 Người dùng không có quyền với evidence, hệ thống hiển thị "Không có quyền xem" mà không lộ nội dung, và ghi audit log.

5.a1 Nguồn gốc đã bị xóa hoặc đổi version, hệ thống hiển thị phiên bản đã lưu tại thời điểm phân tích kèm cảnh báo.

**Luồng ngoại lệ**

E1 Lỗi khi đọc File Storage: hệ thống hiển thị thông báo không tải được nguồn và giữ nguyên báo cáo.

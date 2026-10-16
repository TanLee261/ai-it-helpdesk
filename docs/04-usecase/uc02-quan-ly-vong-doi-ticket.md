# 3.1.4.2 UC02 Quản lý vòng đời ticket

**Tên use case:** Quản lý vòng đời ticket

**Mô tả sơ lược:** Cho phép kỹ thuật viên xem danh sách và chi tiết ticket, cập nhật trạng thái, category, priority và người phụ trách.

**Actor chính:** Kỹ thuật viên IT

**Actor phụ:** Không có

**Tiền điều kiện:** Kỹ thuật viên đã đăng nhập và ticket tồn tại.

**Hậu điều kiện:** Thay đổi được lưu và có bản ghi audit (người thực hiện, thời điểm, giá trị cũ và mới).

**Luồng sự kiện chính**

| Người dùng | Hệ thống |
|---|---|
| 1. Mở danh sách ticket | |
| | 2. Hiển thị danh sách ticket |
| 3. Chọn một ticket | |
| | 4. Hiển thị chi tiết ticket |
| 5. Chọn trường cần cập nhật (status, category, priority, assignee) và xác nhận | |
| | 6. Kiểm tra quyền thực hiện thao tác |
| | 7. Kiểm tra chuyển trạng thái có hợp lệ |
| | 8. Lưu thay đổi và ghi audit log |
| | 9. Hiển thị ticket đã cập nhật |

**Luồng sự kiện thay thế**

6.a1 Người dùng không đủ quyền, hệ thống từ chối thao tác và ghi audit log.

7.a1 Chuyển trạng thái không hợp lệ (ví dụ Closed sang New khi chưa có quy trình mở lại), hệ thống báo lỗi và giữ nguyên trạng thái.

**Luồng ngoại lệ**

E1 Ticket đã được người khác cập nhật sau khi người dùng mở chi tiết: hệ thống báo xung đột và yêu cầu tải lại trước khi lưu.

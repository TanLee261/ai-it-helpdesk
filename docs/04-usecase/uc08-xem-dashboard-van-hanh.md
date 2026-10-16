# 3.1.4.8 UC08 Xem dashboard vận hành

**Tên use case:** Xem dashboard vận hành

**Mô tả sơ lược:** Cho phép trưởng nhóm hoặc admin xem thống kê ticket, incident theo service và category, SLA, latency cùng chất lượng retrieval và RCA.

**Actor chính:** Trưởng nhóm, Admin

**Actor phụ:** Không có

**Tiền điều kiện:** Người dùng đã đăng nhập và có quyền xem dashboard.

**Hậu điều kiện:** Không thay đổi dữ liệu. Lượt truy cập dashboard được ghi audit log.

**Luồng sự kiện chính**

| Người dùng | Hệ thống |
|---|---|
| 1. Mở trang Dashboard | |
| 2. Chọn khoảng thời gian và bộ lọc (service, category) | |
| | 3. Kiểm tra quyền xem dashboard |
| | 4. Tổng hợp số liệu ticket và SLA |
| | 5. Tổng hợp incident theo service và category |
| | 6. Tổng hợp latency và chất lượng retrieval/RCA từ kết quả benchmark và log vận hành |
| | 7. Hiển thị biểu đồ và bảng thống kê |

**Luồng sự kiện thay thế**

3.a1 Người dùng không có quyền, hệ thống từ chối truy cập.

4.a1 Khoảng thời gian không có dữ liệu, hệ thống hiển thị trạng thái rỗng và gợi ý chọn khoảng khác.

**Luồng ngoại lệ**

E1 Tổng hợp dữ liệu quá chậm (vượt ngưỡng thời gian): hệ thống hiển thị dữ liệu đã có sẵn kèm thời điểm cập nhật gần nhất.

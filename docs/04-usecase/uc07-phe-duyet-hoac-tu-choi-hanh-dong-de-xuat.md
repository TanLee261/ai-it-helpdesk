# 3.1.4.7 UC07 Phê duyệt hoặc từ chối hành động đề xuất

**Tên use case:** Phê duyệt hoặc từ chối hành động đề xuất

**Mô tả sơ lược:** Cho phép kỹ thuật viên hoặc trưởng nhóm xem các hành động được AI đề xuất và chọn phê duyệt hoặc từ chối kèm lý do. Trong MVP, hệ thống chỉ ghi nhận quyết định, không thực thi lệnh thật.

**Actor chính:** Kỹ thuật viên IT, Trưởng nhóm

**Actor phụ:** Không có

**Tiền điều kiện:** Báo cáo RCA có proposed actions và người dùng có quyền phê duyệt.

**Hậu điều kiện:** Approval record được lưu với quyết định, người quyết định, lý do và thời điểm. Trạng thái hành động được cập nhật. Không có lệnh nào được thực thi trên hệ thống thật.

**Luồng sự kiện chính**

| Người dùng | Hệ thống |
|---|---|
| 1. Mở danh sách proposed actions của báo cáo | |
| | 2. Hiển thị các hành động kèm mức rủi ro |
| 3. Chọn một hành động | |
| | 4. Kiểm tra approval policy theo mức rủi ro |
| | 5. Nếu rủi ro cao, yêu cầu xác nhận bổ sung |
| 6. Chọn Approve hoặc Reject và nhập lý do | |
| | 7. Lưu approval record và ghi audit log |
| | 8. Cập nhật trạng thái hành động (chỉ ghi nhận) |

**Luồng sự kiện thay thế**

4.a1 Người dùng không có quyền phê duyệt loại hành động này, hệ thống từ chối và ghi audit log.

6.a1 Người dùng không xác nhận ở bước 5, hành động giữ trạng thái chờ duyệt.

**Luồng ngoại lệ**

E1 Hành động đã được người khác quyết định trước đó: hệ thống báo trạng thái hiện tại và không ghi đè quyết định cũ.

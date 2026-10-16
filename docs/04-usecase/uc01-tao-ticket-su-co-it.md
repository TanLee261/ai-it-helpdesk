# 3.1.4.1 UC01 Tạo ticket sự cố IT

**Tên use case:** Tạo ticket sự cố IT

**Mô tả sơ lược:** Cho phép người dùng nhập thông tin sự cố IT (tiêu đề, mô tả lỗi, service bị ảnh hưởng, impact, urgency, file/log đính kèm) để tạo ticket trên hệ thống.

**Actor chính:** Người dùng (nhân viên, kỹ thuật viên)

**Actor phụ:** Không có

**Tiền điều kiện:** Người dùng đã đăng nhập thành công và có quyền tạo ticket.

**Hậu điều kiện:** Ticket được lưu với trạng thái New, có mã ticket duy nhất và có bản ghi trong audit log.

**Luồng sự kiện chính**

| Người dùng | Hệ thống |
|---|---|
| 1. Chọn chức năng tạo ticket mới | |
| | 2. Hiển thị biểu mẫu tạo ticket |
| 3. Nhập tiêu đề, mô tả lỗi, service, impact, urgency và đính kèm file/log (nếu có), sau đó gửi | |
| | 4. Kiểm tra dữ liệu đầu vào |
| | 5. Đề xuất priority theo impact × urgency |
| | 6. Lưu ticket với trạng thái New và ghi audit log |
| | 7. Hiển thị mã ticket và thông tin ticket vừa tạo |

**Luồng sự kiện thay thế**

3.a1 Người dùng hủy thao tác, hệ thống không lưu dữ liệu và quay lại danh sách ticket.

4.a1 Dữ liệu không hợp lệ (thiếu trường bắt buộc, sai định dạng), hệ thống hiển thị lỗi tại trường tương ứng. Người dùng sửa và gửi lại.

**Luồng ngoại lệ**

E1 Lỗi khi lưu vào cơ sở dữ liệu: hệ thống báo lỗi, không tạo ticket và ghi lỗi vào log hệ thống.

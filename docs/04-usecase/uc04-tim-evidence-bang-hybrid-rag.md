# 3.1.4.4 UC04 Tìm evidence bằng Hybrid RAG

**Tên use case:** Tìm evidence bằng Hybrid RAG

**Mô tả sơ lược:** Cho phép hệ thống tìm ticket cũ, runbook hoặc log liên quan đến một ticket hoặc câu hỏi bằng kết hợp BM25/TF-IDF, Dense Retrieval, RRF và Cross-Encoder Reranker.

**Actor chính:** Kỹ thuật viên IT

**Actor phụ:** Hệ thống (Qdrant, keyword index, Reranker)

**Tiền điều kiện:** Người dùng đã đăng nhập và đã có tài liệu tri thức được lập chỉ mục.

**Hậu điều kiện:** Danh sách top-k evidence được trả về kèm evidence_id, nguồn và điểm liên quan; truy vấn được ghi audit log.

**Luồng sự kiện chính**

| Người dùng | Hệ thống |
|---|---|
| 1. Nhập mô tả ticket hoặc câu hỏi | |
| | 2. Query Understanding: xác định intent, service, khoảng thời gian, thực thể |
| | 3. Query Rewriting: tạo truy vấn độc lập, không thêm nguyên nhân |
| | 4. Áp filter metadata và access_scope theo quyền người dùng |
| | 5. Tìm song song bằng BM25/TF-IDF và Dense Retrieval (Qdrant) |
| | 6. Hợp nhất kết quả bằng RRF |
| | 7. Rerank top-20 bằng Cross-Encoder và lọc top-k |
| | 8. Trả về top-k evidence kèm evidence_id và nguồn; ghi audit log |

**Luồng sự kiện thay thế**

2.a1 Độ tin cậy của intent thấp, hệ thống hỏi lại người dùng để làm rõ trước khi tìm kiếm.

7.a1 Không có evidence đạt ngưỡng liên quan, hệ thống thông báo thiếu bằng chứng và gợi ý bổ sung thông tin.

**Luồng ngoại lệ**

E1 Qdrant hoặc keyword index không khả dụng: hệ thống chỉ dùng nhánh còn lại và đánh dấu kết quả là không đầy đủ.

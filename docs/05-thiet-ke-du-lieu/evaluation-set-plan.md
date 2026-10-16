# Evaluation Set Plan

Tài liệu này mô tả kế hoạch tạo tập đánh giá thử nghiệm nhỏ cho retrieval và RCA. Tập này dùng để kiểm tra hệ thống từ sớm, trước khi có dataset lớn.

## 1. Mục Tiêu

Tập đánh giá cần hỗ trợ:

- Đánh giá keyword retrieval.
- Đánh giá dense retrieval.
- Đánh giá hybrid retrieval với RRF.
- Đánh giá reranker.
- Đánh giá RCA có evidence.

Các cấu hình đánh giá tương ứng:

| Cấu hình | Mục đích |
|---|---|
| E1 | TF-IDF/BM25 baseline |
| E2 | Dense retrieval |
| E3 | Hybrid BM25 + Dense + RRF |
| E4 | Hybrid + Cross-Encoder Reranker |
| E5 | Evidence-grounded RCA với log/metrics |

## 2. Quy Mô Ban Đầu

Giai đoạn Tuần 2 chỉ cần test set nhỏ:

| Split | Số case gợi ý | Mục đích |
|---|---:|---|
| `dev` | 10 | Tuning top-k, filter, query rewriting |
| `test` | 5 | Kiểm tra khách quan sau khi tuning |

Khi mở rộng, có thể tăng lên:

```text
100-150 queries cho MVP
500+ queries cho bản mở rộng
```

## 3. Format Evaluation Set

Các trường đề xuất:

```csv
eval_id,question,service,category,relevant_ticket_ids,evidence_ids,expected_root_cause,split,notes
```

Ý nghĩa:

| Trường | Ý nghĩa |
|---|---|
| `eval_id` | Mã case đánh giá |
| `question` | Câu hỏi hoặc mô tả incident |
| `service` | Service liên quan |
| `category` | Nhóm lỗi |
| `relevant_ticket_ids` | Ticket liên quan đúng |
| `evidence_ids` | Evidence đúng cần retrieve |
| `expected_root_cause` | Root cause kỳ vọng |
| `split` | `dev` hoặc `test` |
| `notes` | Ghi chú thêm |

## 4. Ví Dụ Case Đánh Giá

```csv
EV-001,"Payment API trả HTTP 500 và log báo connection pool exhausted, nên kiểm tra gì?",payment-api,server_api,"TCK-0001","RB-001,LOG-001,MET-001","connection pool exhausted",dev,"Kiểm tra retrieval ticket + runbook + log"
EV-002,"VPN không kết nối được và log có DNS resolver timeout",vpn-gateway,network,"TCK-0002","RB-002,LOG-003,MET-003","dns resolution failure",dev,"Kiểm tra lỗi network"
EV-003,"Báo cáo doanh thu tải chậm, metric query duration tăng cao",reporting-db,database,"TCK-0003","RB-003,LOG-004,MET-004","missing index",dev,"Kiểm tra lỗi database slow query"
```

## 5. Metric Retrieval

Các metric cần tính:

| Metric | Ý nghĩa |
|---|---|
| `Recall@5` | Trong top 5 có bao nhiêu evidence đúng được tìm thấy |
| `Precision@5` | Trong top 5 có bao nhiêu kết quả là đúng |
| `MRR` | Kết quả đúng đầu tiên xuất hiện ở vị trí nào |
| `nDCG@5` | Đánh giá chất lượng thứ hạng top 5 |

Giai đoạn đầu chỉ cần tính tối thiểu:

```text
Recall@5
MRR
```

## 6. Metric RCA

Các metric RCA dự kiến:

| Metric | Ý nghĩa |
|---|---|
| `Top-1 root cause accuracy` | Giả thuyết root cause đầu tiên có đúng không |
| `Top-3 root cause accuracy` | Root cause đúng có nằm trong top 3 giả thuyết không |
| `Evidence recall` | Report có dùng đúng evidence cần thiết không |
| `Unsupported claim rate` | Tỷ lệ phát biểu không có evidence |

Trong MVP, RCA chỉ được xem là đạt nếu:

- Có citation/evidence ID.
- Phân biệt observed facts và hypotheses.
- Không kết luận root cause khi evidence chưa đủ.
- Nêu rõ missing evidence nếu thiếu dữ liệu.

## 7. Quy Tắc Chống Data Leakage

- Không đưa lời giải của case test vào context tại thời điểm phân tích.
- Không dùng ticket test để tạo runbook hoặc prompt mẫu.
- Tách `dev` và `test` theo incident, không chỉ tách theo câu hỏi.
- Nếu dùng synthetic data, phải ghi rõ trong `notes`.
- Khi đánh giá retrieval, cố định model, top-k, prompt và tham số liên quan.

## 8. Quy Trình Tạo Evaluation Set Nhỏ

1. Chọn 3 nhóm lỗi chính: network, server/API, database.
2. Với mỗi nhóm lỗi, tạo 3-5 case.
3. Mỗi case phải có ít nhất:
   - Một question.
   - Một relevant ticket.
   - Một runbook hoặc log/metric evidence.
   - Một expected root cause.
4. Chia case thành `dev` và `test`.
5. Kiểm tra lại evidence IDs có tồn tại trong dữ liệu mẫu.

## 9. Checklist Evaluation Set

```text
[ ] Có tối thiểu 10 dev cases.
[ ] Có tối thiểu 5 test cases.
[ ] Mỗi case có question rõ ràng.
[ ] Mỗi case có relevant_ticket_ids.
[ ] Mỗi case có evidence_ids.
[ ] Mỗi case có expected_root_cause.
[ ] Split dev/test không bị trùng incident.
[ ] Synthetic case được đánh dấu rõ.
[ ] Evidence IDs tồn tại trong dữ liệu mẫu.
```


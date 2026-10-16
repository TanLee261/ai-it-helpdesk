# Onboarding telemetry van hanh that

## Muc tieu va gioi han

Quy trinh nay dua telemetry tu export chi-doc vao RCA de thu nghiem co kiem soat. Import thanh cong khong dong nghia du lieu da duoc xac nhan an toan, day du, hay co kha nang chung minh root cause. Ban dau chi chay local/shadow mode; khong gui lenh thay doi he thong dich vu.

Telemetry synthetic hien tai van la demo. Du lieu van hanh phai co provenance `production_export`, service map ro rang, timestamp co timezone va review pham vi du lieu truoc khi bat API doc.

## Giai doan 1: Chon pilot va xin quyen

1. Chon mot service co owner va on-call ro rang, uu tien service co ticket, log va metrics cung co the export.
2. Xin phe duyet read-only export cho dung service va khoang thoi gian can thiet. Khong tao API key admin, khong cap quyen ghi, khong export toan bo organization.
3. Xac dinh retention, noi luu, ai duoc xem, quy dinh PII/secrets va quy trinh xoa ban export.
4. Chon 5-10 incident da dong, co incident/postmortem duoc service owner xac nhan; khong dung incident dang mo lam ground truth.

## Giai doan 2: Export va mapping

Export logs CSV/JSONL va metrics CSV/JSONL tu cong cu observability. Can co timestamp, service/resource, message/metric name, value/unit; record ID nen co neu nguon cung cap. Khong export credentials, headers, request/response bodies, user identifiers hoac payload nhay cam.

Tao ban sao `data/real-telemetry/service-map.json` tu file mau `data/real-telemetry/service-map.example.json`. Map chinh xac ten resource nguon sang service canonical cua project. Khong map bang suy doan tu noi dung ticket. Timestamp phai kem timezone; importer chuyen sang UTC va dung neu timestamp thieu timezone, service chua map, hoac field bat buoc bi thieu.

Chay importer voi duong dan export cua ban:

```bash
.venv/bin/python scripts/import_real_telemetry.py \
  --logs /duong/dan/export/logs.csv \
  --metrics /duong/dan/export/metrics.csv \
  --service-map data/real-telemetry/service-map.json \
  --source-system observability-readonly \
  --loki-url http://127.0.0.1:3100 \
  --timestamp-field timestamp \
  --service-field service \
  --record-id-field event_id \
  --message-field message \
  --level-field level \
  --metric-name-field metric_name \
  --value-field value \
  --unit-field unit
```

Ten cot la vi du; doi cac flag theo export thuc te. Neu metrics khong co `event_id`, importer dung so dong lam source record ID; neu khong co unit, cot `unit` se trong. Importer ghi `logs.jsonl` va `metrics.csv` vao thu muc local-only va tu choi ghi de neu output da ton tai.

`--loki-url` la tuy chon; neu dung, cac log da redacted cung duoc gui vao Loki de xem tren Grafana. Khong them labels co cardinality cao nhu ticket ID, user ID, request ID hay message. Metrics export van nam trong CSV de RCA truy van theo timestamp; Prometheus trong stack local thu thap metrics live tu Helpdesk API va Qdrant, khong thay the telemetry backend cua service pilot.

## Giai doan 3: Kiem tra truoc khi cho RCA doc

Truoc khi bat API doc, kiem tra mau records va xac nhan:

- Timestamp UTC dung va phu dung incident window; khong lech timezone hoac clock.
- Service canonical dung; dashboard/log explorer cua owner hien cung service va khoang gio.
- Metrics co ten, unit, sampling cadence va baseline co y nghia; khong tu dien giai mot gia tri don le thanh anomaly.
- Da loai secrets/PII; importer an email, IPv4 va secret-token patterns nhung khong thay the quy trinh DLP/security cua to chuc.
- Event ID co provenance truy vet nguon; khong dua root-cause label, runbook answer hay incident verdict vao message/metric.

Neu bat ky muc nao chua dat, khong bat integration. So sanh records voi giao dien observability goc va nho service owner review.

## Giai doan 4: Chay read-only local/shadow

Chi sau khi review xong, bat co moi truong:

```bash
ENABLE_REAL_TELEMETRY=true .venv/bin/uvicorn app.main:app --reload
```

Neu chay tu repository root:

```bash
ENABLE_REAL_TELEMETRY=true backend/.venv/bin/uvicorn app.main:app --app-dir backend --reload
```

Mac dinh co nay la `false`; khong bat trong production environment. Khi bat, loader doc rieng telemetry operational, khong tron du lieu synthetic vao cung evidence pack. Chay RCA cho incident da dong voi ticket ID va cua so UTC. Kiem tra citations co record ID operational, service/time window khop, va report van abstain neu evidence yeu/mau thuan. Khong dung synthetic demo evidence de tinh diem real telemetry.

## Stack Grafana/Loki/Prometheus local

Tu project root, chay `GRAFANA_ADMIN_PASSWORD='mat-khau-local-rieng' docker compose -f infra/docker-compose.yml --profile observability up -d prometheus loki alloy grafana`. Grafana tai `http://127.0.0.1:3000`, Prometheus tai `http://127.0.0.1:9090`, Loki tai `http://127.0.0.1:3100`, Alloy UI tai `http://127.0.0.1:12345`. Dang nhap Grafana bang user `admin` va password da chon. Profile nay tach khoi luong chay app thong thuong. Prometheus scrape Helpdesk `/metrics` tren port 8000 va Qdrant; Alloy doc duy nhat log backend qua file read-only va gui vao Loki. Datasource va dashboard duoc provision san.

Stack nay chi danh cho local/dev: Loki chua co authentication rieng trong cau hinh nay, nen khong expose port ra LAN/Internet. Grafana password phai duoc doi; khong dung cau hinh nay cho production.

## Giai doan 5: Ground truth va danh gia

Voi moi incident da dong, service owner/SRE doc postmortem va telemetry goc, sau do ghi root cause da xac nhan, evidence IDs, thoi diem, muc do chac chan va reviewer. Reviewer phai danh gia doc lap voi model output; neu khong chac chan, gan nhan `uncertain`, khong ep thanh label.

Chia train/dev/test theo incident va theo thoi gian; khong de cac query cua cung incident ro ri qua split. Chot protocol truoc khi xem ket qua test. Bao cao rieng retrieval Recall@K/MRR/nDCG, RCA accuracy tren incident du evidence, abstention precision/recall, unsupported-fact rate, citation validity va latency. So sanh BM25, dense, hybrid va reranker tren cung tap du lieu. Khong coi 5-10 incident pilot la ket luan tong quat.

## Tieu chi truoc khi mo rong

- Service owner phe duyet quyen, data scope, service map va time synchronization.
- Khong con record nao bi unmapped/invalid timestamp trong tap pilot.
- Redaction duoc security/data owner chap nhan.
- RCA trace va evidence citations duoc kiem tra; khong co action execution.
- Co incident ground truth duoc chuyen gia xac nhan va benchmark split co dinh.
- Qdrant health check thanh cong truoc khi bao cao E3/E4; neu Qdrant offline, chi ghi nhan BM25 da test.

## Thong tin con can de ket noi connector cu the

Can service pilot, cong cu telemetry (vi du Datadog, Grafana/Loki, Elastic, CloudWatch), format export va header mau da xoa du lieu nhay cam, ten service canonical, timezone, nguoi xac nhan ground truth. Khong dua credential hoac production secrets vao repository/chat.

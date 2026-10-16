# Ticket-Informed Synthetic Telemetry v1

This small, curated set supports MVP demonstrations and pipeline testing only. The log events and metric values are simulated from explicit symptom-focused scenario specifications. They are not real operational telemetry, are not independently observed, and do not establish root cause.

The scenarios intentionally contain no root-cause labels. `ticket_id`, `service`, the stated symptom, and time window are recorded in `manifest.json`; the time windows are synthetic and must not be treated as the actual time of the ticket.

Regenerate from the normalized tickets and reviewed specs with:

```bash
python3 scripts/generate_ticket_telemetry.py
```

For the first scenario, the manifest maps `TCK-00006` to `2026-10-16 10:00-10:15` Vietnam time. Use that ticket and time window in Incident analysis to inspect the synthetic evidence. Other windows and ticket IDs are listed in the manifest.

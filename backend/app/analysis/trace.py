from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import ROOT_DIR


_WRITE_LOCK = threading.Lock()


def write_analysis_trace(record: dict[str, Any]) -> None:
    configured_path = os.getenv("RCA_TRACE_PATH")
    if not configured_path:
        return
    path = Path(configured_path).expanduser()
    if not path.is_absolute():
        path = ROOT_DIR / path
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"recorded_at": datetime.now(timezone.utc).isoformat(), **record}
    line = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    with _WRITE_LOCK, path.open("a", encoding="utf-8") as stream:
        stream.write(line + "\n")

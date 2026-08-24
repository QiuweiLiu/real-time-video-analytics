"""Event JSONL logger — append-only, flush, count."""

import json
from pathlib import Path
from typing import Dict
import uuid


class EventLogger:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # truncate on init (fresh run)
        self._count = 0
        # keep file handle open for append
        self._f = open(self.path, "w", encoding="utf-8")
        self._closed = False

    def log(self, event: Dict) -> str:
        if self._closed:
            raise RuntimeError("logger closed")
        # ensure event_id
        if "event_id" not in event:
            event = dict(event)
            event["event_id"] = uuid.uuid4().hex[:8]
        # deterministic json: no ensure_ascii
        line = json.dumps(event, ensure_ascii=False)
        self._f.write(line + "\n")
        self._f.flush()
        self._count += 1
        return event["event_id"]

    def count(self) -> int:
        return self._count

    def close(self):
        if not self._closed:
            self._f.close()
            self._closed = True

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

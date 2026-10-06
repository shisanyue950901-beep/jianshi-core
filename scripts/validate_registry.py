#!/usr/bin/env python3
import json
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "config" / "source_registry.json"
d = json.loads(p.read_text(encoding="utf-8"))
seen=set()
for s in d["sources"]:
    assert s["code"] not in seen, f"duplicate source: {s['code']}"
    seen.add(s["code"])
    if s["status"] != "GREEN":
        assert s["auto_collect"] is False, f"non-GREEN auto collect forbidden: {s['code']}"
        assert s["redisplay_allowed"] is False, f"non-GREEN redisplay forbidden: {s['code']}"
    if s["status"] == "GREEN":
        assert s.get("policy_url"), f"GREEN requires policy URL: {s['code']}"
print("SOURCE_REGISTRY_PASS", len(seen))

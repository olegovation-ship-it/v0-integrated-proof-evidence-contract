#!/usr/bin/env python3
from __future__ import annotations
import hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];errors=[]
for line in (ROOT/'SHA256SUMS.txt').read_text().splitlines():
    if not line.strip():continue
    h,rel=line.split('  ',1);p=ROOT/rel
    if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=h:errors.append(rel)
print('PASS SHA256SUMS' if not errors else 'FAIL '+','.join(errors));raise SystemExit(1 if errors else 0)

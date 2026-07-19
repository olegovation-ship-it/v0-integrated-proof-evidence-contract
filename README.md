# V0 Integrated Proof-Evidence Contract — WP6

WP6 is the final Gate 2 audit and closure-decision package. The standalone audit passes 19 of 20 gates and deliberately withholds closure until authentic green GitHub Actions evidence is recorded for the four hosted upstream replay jobs.

Local verification:

```bash
PYTHONPATH=checker python scripts/build_wp6_schema_manifest.py --check
PYTHONPATH=checker python scripts/build_wp6_gate2_audit.py --check
PYTHONPATH=checker python scripts/verify_wp6_gate2_audit.py --allow-pending
PYTHONPATH=checker pytest -q
python scripts/verify_sha256s.py
```

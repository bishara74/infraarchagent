# PR-04 offline session-check attribution

Synthetic rejected package; no LLM/scanner/validator executed. Same near-10 MB archive and SHA-256 in every condition. Two warm-ups and ten alternating measured requests per condition; loopback HTTP timing includes full response consumption. Test-only prevalidated_session skips the session touch lookup and is attribution only, not a production endpoint or authenticated compliance result.

| Condition | Count | Median s | Max s | ≤2 s every request |
|---|---:|---:|---:|---|
| session | 10 | 0.700893 | 0.721118 | PASS |
| shared_key | 10 | 0.698920 | 0.730615 | PASS |
| prevalidated_session | 10 | 0.695996 | 0.734234 | PASS |

Per-request session/user time, SQL execution totals and ZIP work are recorded in timings.csv. SQL totals overlap their enclosing operations and must not be added to them. Shared-key skips session/user work; prevalidated_session retains user lookup. Revocation after restoring the original guard returns HTTP 401. These are local descriptive samples, not proof for other machines or provider conditions. Prior 9h measurements remain unchanged. No production authentication guard was removed.

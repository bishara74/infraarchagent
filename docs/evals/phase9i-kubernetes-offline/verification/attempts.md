# Verification attempts

The initial full backend run completed with 1,801 passed, four failed and six
performance tests deselected in 437.70 seconds. The four failures were recorded
LLM-only loop scenarios whose setup disabled the older catalogue but not the new
pod catalogue. Extend that existing test isolation to both automatic paths; keep
all scenario assertions unchanged. New catalogue guard tests cover automatic
acceptance and rejection independently.

Two intermediate backend reruns were interrupted while completing coverage for helper-
resolved container names and whole-document Helm conditional wrappers. The final
backend.txt records a complete run against the final implementation.

Exploratory replay runs were interrupted while fixing source insertion ordering
and expanding supported, provable source/render bindings. Their cache identities
are distinct. The final execution manifest and every package row identify the
final evaluator; only matching rows contribute to the published summary.

Frontend unit tests completed independently: 17 files, 113 tests passed, zero
failed (15.20 seconds). Browser coverage uses the existing stub E2E suite and a
separate disposable PostgreSQL database, with dotenv disabled before Python
startup. Fixture provider/model names in logs do not represent real inference.

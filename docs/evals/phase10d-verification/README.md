# Phase 10d — final offline verification

All three accepted causes are addressed. The [diagnosis](../phase10d-diagnosis/README.md)
was committed before application changes. [Paired replay](../phase10d-replay/README.md)
keeps exports, available candidates and derived groups on separate denominators.
The complete one-round author command is in [RERUN.md](RERUN.md).

| Check | Final result | Evidence |
|---|---|---|
| make lint | Exit 0; Ruff/format 50 scripts and 415 app/test files, mypy 190 sources, ESLint and both TS checks | [log](make-lint.txt) |
| make test | 2,830 passed; 0 failed/skipped; 6 perf deselected; 691.48s | [log](make-test.txt) |
| Supplementary focused tests | 50 passed; 0 failed/skipped, including four final portable S3 cases | [log](supplemental-focused.txt) |
| make frontend-test | 467 passed; 0 failed/skipped; 46 files | [log](make-frontend-test.txt) |
| make test-e2e | 35 passed; 0 failed/skipped; 10.1 minutes | [log](make-test-e2e.txt) |
| make test-perf | 6 passed; 0 failed/skipped; 2,830 deselected; 26.87s | [log](make-test-perf.txt), [measurements](performance/results.json) |
| make secret-scan | Exit 0; 0 findings, 0 scan errors; working tree and all refs/reflogs | [final report](secret-scan/summary.md) |
| Traceability | 59 IDs; 0 uncovered/invalid annotations/collection failures | [report](../phase10d-traceability-release/traceability.md) |
| Evidence-index generation | 45 met / 12 partly met / 1 not met / 1 unverified | [log](evidence-index.txt) |

The unchanged PR-04 10 MB download bound is two seconds; the measured sample is
**1.291972345s**. Performance ran after backend, browser and replay workloads ended.
Its fresh automatic report was relocated to performance/; the console preserves
the original destination. Secret scan reports are likewise relocated; the first
scan precedes final documentation, and secret-scan/ contains the final scan.

## Test isolation and preservation

Verification used the existing dotenv-disabled bootstrap, stub/mocked provider
transports, synthetic credentials and disposable native UTF-8 PostgreSQL 16.
Backend tests used loopback port 55445, browser tests an independent cluster on
55446; browser services used 18145/15145. Owner/app/inspection roles and migrations
retained their existing privileges. No author database, operator dotenv, real key,
real inference, install or external service was used. Existing tools/provider
mirrors were used offline; the replay manifest records versions/source hashes.

All **6,340** protected tracked evidence/specification files retain exact bytes.
Browser verification refreshed 93 historical captures: new bytes are preserved
under ui/refreshed/, and historical files were restored byte-for-byte.
[historical-preservation.json](historical-preservation.json) records every pair.
The canonical evidence index regenerated identically. No policy/profile,
blocking/readiness threshold, prompt, model selection, dependency or schema changed.

The full suite includes the three historical ALB database rollbacks, D-63 ingress
protection, refused-read pending-review/download gates and 39 new unit cases at the full-suite run.
A final coverage audit added four portable S3 encryption/logging cases (whole
candidates and partial groups). The application code stayed unchanged; the
expanded focused subset passed 50 cases, including all four additions and the
real-database replay/input review. The 2,830 full-suite count precedes those four
test-only additions. The release traceability was recollected afterward and
relocated to its linked destination. Unavailable checks remain unavailable; accepted independent
fixes do not certify validity or remove TERRAFORM_FILE_INPUT.

## Corrections made during verification

The section-2 focused run passed 86 cases. Subsequent synthetic context probes
exposed two incomplete fingerprints (non-AWS resource dependencies and the file
call owner's repetition domain): 2 failed / 18 deselected. Resource references,
count/for_each/provider/dynamic bindings and their transitive definitions are now
included. A variable used by a repetition binding is also tested. File refusal
always remained active; these corrections concern acceptance context comparison.

Two preliminary suite/replay runs were stopped while that context coverage was
completed. Their partial logs remain initial*/; they are not passing-suite claims.
The first completed backend run had **2,829 passed / 1 failed / 6 deselected**:
an older test required rejecting an identical not_installed evaluation. The author
explicitly superseded that behavior. Its expectation now requires acceptance,
retention of the unavailable marker and retained_failed=None. The corrected
iteration file passes 10 tests, and the final full suite passes all 2,830.
A local-variable type conflict was corrected before final lint. No production
gate was weakened to satisfy an obsolete test.

One command was not executed when automatic approval review hit an account usage
limit; the author requested continuation and normal reviewed execution resumed.
No approval or sandbox check was bypassed. Intermediate traceability outputs and
incomplete replay observations remain uncommitted; the linked release collection
contains the final parameterized test IDs.

## Replay results and limits

All 59 retained packages were observed, with 177 matching input hashes and
58 exact security reconstructions; one post-security patch is absent. Thirty
available proposal occurrences (14 distinct pairs) produce 26 accepted occurrences
(13 distinct), while four logging occurrences (one distinct pair) still fail for
new blockers. Unavailable candidate rejections fall 12→0 and conformance 18→0;
derived group discards fall 46→4, with 42 groups kept. Accepted pairs conditionally
remove seven frozen identities across five rules. All five input blockers remain.
The 118 retained-diff conformance observations gain zero new rejections.

Export-only correction covers every raw report: empty reasons 52 attempts / 65
error-class counts →0, unknown repairs 15 / 33 →0. Missing focused/validation
candidate bodies and two unmatched deterministic contexts are listed explicitly.
The 17 historical unavailable iterations and 138 historical discarded groups
cannot be extrapolated from these available proposals. No cumulative trajectory,
historical timing, deployment success or new pass rate is claimed. Model variance
and missing evidence remain limits; no new specification open question is added.

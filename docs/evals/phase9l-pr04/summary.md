# Phase 9l PR-04 comparison and parsing reuse

Status: **PASS** for fixed-snapshot parity, five post-fix acceptance samples,
functional tests, lint, the complete performance suite and the secret scan.

Requirements: PR-04, NFR-01, FR-S-04, FR-UI-06.

## Measured comparison

Seconds for the unchanged
`test_ten_megabyte_package_download_under_two_seconds`:

| Sample | Pre-9l `29751f1` | HEAD `7442685` before fix | After one fix |
|---|---:|---:|---:|
| 1 | 2.579621 | 2.133974 | 1.269847 |
| 2 | 2.565886 | 2.106073 | 1.159700 |
| 3 | 2.227745 | 2.252207 | 1.142714 |
| 4 | 2.157149 | 2.405053 | 1.314136 |
| 5 | 2.088913 | 2.369835 | 1.268532 |
| Median | **2.227745** | **2.252207** | **1.268532** |
| Maximum | **2.579621** | **2.405053** | **1.314136** |
| Passed / failed | 0 / 5 | 0 / 5 | 5 / 0 |

The before-fix medians differ by about 1.1%, with overlapping ranges. The
failure predates 9l. The author explicitly approved optimizing this pre-existing
cost after the prompt's stop gate, limited to one evidenced fix and a repeat of
five quiet measurements. The post-fix median is 43.68% lower than HEAD's initial
median. These are descriptive local observations, not a deployment guarantee.

The author stopped unrelated services and closed heavy applications. Only the
project PostgreSQL service and task-created disposable PostgreSQL 16 clusters
were running. No other verification overlapped the acceptance measurements.
Existing project data was untouched. Roles and privileges use the repository
bootstrap. The first disposable migration attempt lacked the inspection role;
that prerequisite was corrected before any measurements.

The pre-9l checkout was a temporary detached worktree outside the repository.
Its expected `.venv` path linked to the existing venv; no installation occurred.
Revision-local working directories, bootstrap paths and application/test imports
were asserted. Five fresh pytest processes per revision ran in alternating
pre-9l/HEAD order. Post-fix samples also use fresh processes; none were discarded.
Every verification parent and child disabled dotenv. No real LLM, API key,
external network service or dependency installation was used.

The test still seeds 10,000,000 source bytes across 50 Terraform paths and times
only the complete ASGI download request. Its two-second assertion and all
content checks are unchanged. ZIP sizes are about 7.58 MB. Fresh run IDs/event
timestamps cause the few-byte variation listed in [timings.csv](timings.csv).
Fixed snapshots, rather than different fresh fixtures, establish byte parity.
[Raw logs and JUnit](raw/) retain every sample, including the ten failures.

## Attribution and correction

Separate request-only profiles include instrumentation overhead and are not
acceptance samples. Nested spans must not be added together.

| Operation | Pre-9l seconds | HEAD before fix seconds | After fix seconds |
|---|---:|---:|---:|
| Whole profiled request | 2.446523 | 2.583997 | 1.246285 |
| Snapshot read/materialization | 0.087459 | 0.090251 | 0.088405 |
| Contextual assessments | 1.663797 | 1.739333 | 0.437631 |
| Public-data safety text processing | 0.287672 | 0.268028 | 0.280732 |
| ZIP construction | 0.382885 | 0.465861 | 0.419244 |
| Lesson provenance | absent | 0.000113 | 0.000137 |

Both revisions perform **250 HCL parses** for the same 50 files. Independent
v1, AES256, v2 graph and v2 legacy evidence constructors repeatedly parse the
same input. The four-file correction shares one parsed `TerraformPackage` and
its evidence within the combined assessment call. AES256 and instance evaluation
accept optional already-parsed inputs; standalone callers retain their behavior.
No persistent cache is introduced. An explicit empty file override still uses
v1's historical fallback and v2's historical empty input. Tests exercise valid
and malformed inputs and 1/50/129 documents, including changed content on the
next call. Archive formatting, hashing, compression and event queries are
unchanged. The separate post-fix profile confirms **50 HCL parses**, down from
250, and assessment work of 0.437631 s. See [profiles.json](profiles.json).

Before editing production code, the deterministic fixture builder captured
actual archive/assessment bytes from HEAD. After editing, all **30 outputs**
matched those bytes exactly: 18 individual ZIPs, six bundles and six serialized
assessments. Fixtures cover approved/automatic/rejected labels, retry/missing
label provenance, HCL/JSON/YAML, contextual exceptions, counted resources,
malformed/unknown input, readiness/lesson filename collisions, lesson use and
secret redaction. This includes readiness, manifests and all included-file and
individual-ZIP hashes. All three complete assessment results also match for
**81 historical packages**. [parity.json](parity.json) records output lengths
and pre/post SHA-256 values; [captured pre-edit outputs](before/) retain the
actual fixed bytes. Unit tests compare independent evaluator inputs and archive
bytes on every run. Source fingerprints and unchanged-surface hashes are saved
with the report; the performance test itself is unchanged from pre-fix HEAD.

## Earlier ~0.73-second evidence

[The quiet Phase 9b evidence](../phase9b-download-quiet/summary.md),
[performance analysis](../../phase9b-performance-gaps.md) and October 20
implementation-log entry record ten alternating samples per authentication
condition after two warm-ups: session median/max 0.700893/0.721118 s,
shared key 0.698920/0.730615 s, prevalidated-session control
0.695996/0.734234 s. The control is attribution only.

That seed creates `benchmark/data-*.txt`, avoiding Terraform parsing, and a
synthetic rejected 9,989,906-byte ZIP. It uses complete loopback HTTP response
timing, not the current ASGI fixture's Terraform paths. Its recorded source is
`1a5fce7` with measurement tooling uncommitted, before contextual-v2. It cannot
serve as the same-test pre-9l baseline. The earlier loaded 7.89–8.07 s probe also
remains a failed historical observation; this investigation does not reconstruct
its contention. The specification's curl method remains distinct (D-55).

## Runner diagnostics and verification

`make test-perf` now uses the same parent settings resolver and backend `perf`
selection as `scripts.run_verification pytest -m perf`. Previously its eager
`Settings(_env_file=None)` ignored normal parent configuration; the common
safe wrapper suppressed the validation reason before tests launched.

The command now prints redacted console output, counts and PR-04 properties.
Results identify setting field names, launch failures, timeouts, test/setup
identifiers and missing/malformed reports. Nonzero test exits are preserved;
missing results cannot become PASS. Configured `SecretStr` values are redacted
from console, structured reports and raw XML/JSON, including encoded forms.
Canary tests cover these surfaces. Verification here bootstraps parents and
children explicitly, without reading the real operator configuration.

- Focused checks: **148 passed, 0 failed/skipped, 1 perf deselected**, 26.05 s.
- `make lint`: **exit 0**, 40 script and 378 app/test files, mypy 181 sources;
  frontend ESLint/TypeScript passed.
- `make test`: **2,509 passed, 0 failed/skipped, 6 perf deselected**, 531.30 s.
- `make test-perf`: **6 passed, 0 failed/skipped, 2,509 deselected**, 27.94 s;
  PR-04 property **1.042764587 s**. The property is from the complete suite,
  separate from the five fresh-process samples above. See the
  [wrapper report](../phase9-backend-perf-20261025T142335903500Z/summary.md).
- `make secret-scan`: **exit 0, 0 findings, 0 scan errors**. See the
  [scan report](../phase9-secret-scan-20261025T142649172692Z/summary.md).

No requirement, threshold, assessment exception, readiness rule, authentication
guard or retention behavior was changed. No new dependency, migration,
specification deviation or open question was introduced. Five samples per
revision on one host and synthetic fixtures do not establish real-provider or
deployment performance. The existing venv uses Python 3.12.3; see
[environment.json](environment.json) and [results.json](results.json).

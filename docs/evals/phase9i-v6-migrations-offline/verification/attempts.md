# phase9i: verification and replay record

All Python commands use INFRAARCH_TEST_BOOTSTRAP=1 with tests/bootstrap first
on PYTHONPATH. Dotenv is disabled before settings instantiate. Full tests use
stub inference and installed PostgreSQL 16, a disposable UTF-8 cluster under
/tmp with synthetic owner/app credentials and normal grants. No Docker startup
or real LLM/cloud calls were needed. The database is stopped after each run.
Native migration tests and the replay run in a user/network namespace with only
loopback, using installed tools and local provider archives.

Focused migration, guidance, coverage and report checks: 59 passed. Native
AWS 6.68 validation: 1 passed (three legacy errors become zero). Historical
reconstruction/guard checks: 19 passed, including all 81 pinned final packages.
Final lint passes: Ruff, mypy 166 application sources, frontend ESLint/TypeScript.
Frontend unit/browser suites were not separately rerun; no frontend code changed.

Initial unit checks exposed ambiguous JSON keys; the transform now skips such
modules. The initial full suite could not collect duplicate unit/integration
basenames; the integration file now has a unique name. The next full suite had
1,929 passed / 1 failed / 6 performance tests deselected. Its historical replay
whole-file guard caught the intentional live-equivalence extension. That helper
now executes its original trusted Git-pinned equivalence implementation while
keeping other source guards and every candidate/retained hash assertion. A test
proves new live hooks are not invoked during historical reconstruction.
Final full-suite results are recorded in backend.txt and verification.json.

An initial inventory pass assumed data blocks used resource-style labels. The
inventory now explicitly flattens named data declarations; both serializations
are tested. It reports no uninspectable declaration labels. One original module
has a parse failure, so the removed-field audit is incomplete there; all retained
round-2 modules are parseable. A provider-block supplement finds only region and
alias fields and no removed endpoint options.

A fully fresh identity replay was interrupted after initial unchanged rows.
Final measurement uses fresh paired native observations for all five changed
proposals, 141 previous native offline observations and 55 frozen round-2
observations for byte-identical cases. Tool/provider versions match and 52
observational sources are unchanged; unchanged validation/report model ASTs and
plan-validation ASTs are checked separately. Each row labels its baseline method.
Old partial rows are overwritten by the complete 201-row result and every final
row is bound to the execution manifest. No identity case receives an attributed
gain. Original generator bytes are audited separately and never replayed as
retained package improvements. No historical evidence files were changed.

Lint logs omit trailing empty lines. A repository/history secret scan reports
zero findings/errors; final source/artifact checks supplement it. No push ran.

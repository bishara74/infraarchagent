# Phase 9l — Curated feedback and prompt-injection boundaries

This is implementation/testing material for Chapters 5–6. The phase prompt
frames the threat as OWASP LLM01 (prompt injection). It adds a human-curated
advisory channel to the existing review workflow; it does not train a model,
automatically summarize feedback or establish improved infrastructure quality.
The specification remains unchanged; the extension and proposed requirement
IDs are recorded in [D-60](../design-deviations.md#d-60--human-curated-advisory-lessons-and-injection-defense-phase-9l).

## Trust boundaries and governance

Approve/Reject reasons remain immutable decision evidence. They are never
copied into model messages or prefilled into a proposal. Deterministic admin
insights count categories, variants, decisions and recorded blocking rules;
count links lead to matching decisions. Historical rule snapshots that do not
exist are reported as unavailable. No LLM participates in these operations.
The existing explicit remediation-feedback action (FR-S-09) is separate and
retains its existing behavior.

A named decision owner writes one structured lesson: a fixed role, fixed
curation tags, a D-47 category and one line of at most 280 normalized Unicode
code points. An administrator inspects the linked decision, filter and exact
prompt preview. The default policy requires a different administrator to
approve. Edits create immutable successor revisions. Lifecycle and runtime
changes leave append-only audits with actor, application UTC time and previous
revision reference.

The explicit single-operator exception,
`LESSONS_REQUIRE_SECOND_APPROVER=false`, permits self-approval only after a
second confirmation showing a freshly computed filter and prompt preview.
Its one-use, five-minute token is stored hashed and bound to the actor,
session, revision, current set, filter and policy. This is one person's review:
it weakens independence and is visibly marked `self_approved` in governance,
run and archive evidence. It must not be described as four-eyes approval.

## Layered defenses

| Boundary | Mechanism and verification |
|---|---|
| Structured input | Strict enums; NFKC normalization; reject control, invisible, bidi and multiline input before normalization; normalized length limit. Unit/API tests exercise these constraints. |
| Suspicion screening | Versioned server config rejects recognized overrides, role markers, markup/templates, links/email, paths, shell/Terraform fragments, opaque encodings and shared secret-scan patterns. Screening repeats on approval; UI patterns do not decide authorization. |
| Human authorization | Named-session ownership, admin lifecycle privileges and default four-eyes approval. Integration tests prove unapproved syntax survivors never enter snapshots/hooks. |
| Prompt delimiting | One escaped, numbered advisory block in the user message; fixed data-only preface; deterministic role selection/order; at most eight complete entries and 2,000 total block characters. System messages and schemas remain unchanged. |
| Output controls | Existing schema/Terraform validation, scanner findings and readiness retain authority. Regressions show a lesson cannot relabel a package or unblock a finding; generated archive bytes are unchanged. |
| Operational control | Hard server gate plus persisted runtime switch, both off initially. Disable detaches hooks before later attempts, including retries, without waiting for in-flight HTTP. Re-enabling applies only to newly accepted runs. |

Tags aid curation; they do not select lessons based on inferred resources.
Architect and each Generator receive only role-matching approved content;
`all_generators` applies to each Generator. No lesson hook is installed on
the Fixer/SecurityAgent. Delimiters express a trust boundary to the model;
they do not enforce it in the way deterministic validation does.

## Reproducibility and disabled behavior

Every run freezes a canonical active-set snapshot, version and SHA-256.
Durable dispatch-authorization events and completed-attempt telemetry share
call IDs, allowing actual use to be deduplicated and distinguished from
acceptance eligibility. Run results, readiness evidence and ZIP metadata retain
that provenance, selected revisions, suppression reasons and self-approved use.
Older runs disclose missing configuration rather than inventing it.

Disabled, unconfigured, benchmark and empty-role adapters have no hook or
lesson gate installed; the ordinary send path does not invoke a no-op lesson
callback. Forty-eight mocked-HTTP comparisons cover four roles, three format
modes and four ineligible contexts. Each compares the complete serialized body
against captured pre-integration fixtures and asserts zero hook/dispatcher and
governance-query invocations. Header-authenticated benchmarks remain isolated
even when both lesson gates are enabled. These checks establish request
compatibility; they do not establish a real provider's model behavior.

The supported server remains a single process. Its short asynchronous gate
orders eligibility checks, durable use recording and transport-task creation
against disabling. Already-authorized transport cannot be recalled. Durable
disable generations stop an earlier run resuming after re-enable, including
adapters created later in that run. Distributed dispatch would require another
coordination design; the existing single-worker limitation remains.

## Corpus results and interpretation

The versioned 46-case corpus includes direct overrides, role markers,
homoglyph/invisible/bidi obfuscation, encodings, URLs/email, paths, secrets,
code, overlong/multiline input, benign controls and semantic residuals.

| Layer | Observed result |
|---|---|
| Structured input | 10/46 rejected |
| Filter after structure/normalization | 28 additional rejected; 38/46 cumulative |
| Filter independently on raw payloads | 29/46 rejected; separate measurement, not additive |
| Human approval | All eight syntax survivors excluded while proposed (six benign controls and two residual attacks) |
| Delimiting/output/kill switch | Boundary regressions; no universal attack-detection count is claimed |

Independent and sequential counts differ because normalization exposes some
patterns and structurally rejected values do not proceed to screening.
The [payload-free report](../evals/phase9l-security/corpus.json) records case
IDs, layer outcomes, rule IDs and source hashes. Synthetic secret fragments
are assembled only inside tests. [UI captures](../evals/phase9l-ui/README.md)
show the real local API workflow at 1280×800. Full command results and source
fingerprints are retained in the final verification evidence.

## Residual risks and evaluation limits

Semantic persuasion can pass a syntactic filter. The bounded confusable map,
encoded-blob heuristics and secret patterns cannot cover every evasion or
credential format. A malicious/careless administrator can approve harmful
preferences; self-approval removes independent review. Escaping and a clean
preview cannot prove safe model interpretation. Validation/scanners cover
their implemented rules, not every unsafe design.

No real inference, deployment or output-quality experiment forms part of this
phase. Whether lessons improve quality, cost or security requires separate
author-run evaluation with frozen sets and disclosed confounders. The optional
PR-04 archive-performance probe failed its unchanged two-second bound locally;
the cause is unestablished. Functional verification does not resolve that
performance limitation.

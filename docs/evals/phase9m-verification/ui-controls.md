# Phase 9m gated-control inventory

All predicates below retain their previous availability rule. Native disabled
controls remain disabled; ActionGate adds a focusable group, associated reason
and recovery hint, hover/focus/click disclosure and polite announcement. Its
stable wrapper preserves input/button identity and focus across busy changes.
Escape dismisses an open hint before a parent dialog. Links in hints retain
normal activation. Enabled wrappers use display:contents with no extra tab stop.

| Controls | Gate | Explanation / next step |
|---|---|---|
| Generate | submitting, active run, draft discard | State the operation; link to active progress or wait. |
| Description, Restore, Discard, Dismiss, example prompts | discarding | Wait for discard before editing/restoring. |
| View results | run not terminal | Watch progress until the run settles. |
| Download all three | missing variant or any backend downloadable=false; busy | Name outstanding variants; link to their reviews/progress, or new request for failed generation. |
| Download this variant / Download ZIP | backend downloadable=false; busy | Inspect and complete review or wait; busy preparation is explicit. |
| Approve / Retry with feedback / Reject | backend review_actions, run/retry lock; busy | Explain pending/settled decision or retained retry lock; inspect reports/wait. |
| Submit retry, Feedback, target fieldset | busy | Wait for current review request. |
| Target checkbox beyond five | five selected, current checkbox unselected | Uncheck an existing target first. |
| Propose a lesson | no decision or not named authenticated decision owner | Record an eligible owned decision / sign in as owner. |
| Lesson form fields / submit / cancel | busy | Wait for proposal submission. |
| Approve lesson | lifecycle, filter, controls loaded, four-eyes policy, busy | Correct filter reasons, wait for controls/action, or ask a different named admin. |
| Reject / Retire lesson | lifecycle; busy | Only proposed can reject, only active can retire; inspect history. |
| Propose new version | proposer ownership; busy | Ask owner to submit a revision / wait. |
| Self-approval confirm/cancel, destructive confirm/cancel | current preview/selection; busy | Reinspect/correct or wait. Existing confirmation/selection policy stays authoritative. |
| Use approved lessons | server gate off; busy | Ask operator to enable server gate/restart, or wait. |
| Disable lessons | busy | Wait for the in-flight action; immediate disabling policy is unchanged. |
| Previous/Next (history, lessons, versions) | first/last page | Explain boundary; choose another view/filter/page. |
| Model default option | existing capability rejection | Explain the incompatible default and choose another confirmed model/default. Arrow selection still skips it; Tab/focus/click can inspect its explanation. |
| Thinking selects | missing model/effective choice, mixed generator defaults, model lacks reasoning | Retry/select a confirmed model; configure each variant in Advanced; choose reasoning-capable model. |
| Provider Test | key missing or working | Enter key / wait. |
| Save and use provider | storage unavailable, working, no accepted probe | Configure storage/restart, wait, or test a valid key (no-credit remains accepted). |
| Saved credential Test / Use / Revoke | revoked, selected (Use only), busy | Add replacement, retain current selection or select another, wait. |
| Confirm revoke | busy | Wait; existing confirmation remains required. |
| Create reviewer / reset password / enable / disable / reset cancel | busy; existing role boundary | Wait; administrator-only access and reviewer-only enable/disable remain unchanged. |
| Change password / login / setup / logout | busy | Wait for the active request. |
| Export CSV / JSON | busy | Wait for export preparation. |
| Load/save/catalogue retry, restore conflict/draft, clear filters, custom-model declarations | relevant error/draft/filter/provider state | Existing visible contextual notices provide the recovery action. Role-restricted settings retain the existing Ask an administrator access boundary; privileged data is not exposed to make controls visible. |

Verification: ActionGate.test.tsx checks native button/select/checkbox/textarea/
fieldset semantics, keyboard activation and no forbidden action, concrete bundle
review links, retry controls, proposal forms and version pagination.
BusyActions.test.tsx checks actual authentication/account/users/providers/history
screens. Existing screen/model/lesson/review suites retain predicate and focus
regressions. phase9m-gates.spec.ts exercises actual browser screens with synthetic
API responses and held requests for hover/focus/click, modal behavior and zero
additional mutation requests. The full real-backend stub flow remains part of
make test-e2e; mocked edge states are not real-provider evidence.

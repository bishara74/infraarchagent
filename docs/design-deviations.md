# Design Deviations and Open Questions

Every place where the implementation differs from the thesis specification
(`docs/spec/`), and every unresolved ambiguity. This file feeds the
"Design deviations" section of thesis Chapter 5.

Status values:
- **In thesis:** the decision was made during design review and is now part
  of the thesis design (text and diagrams). No difference remains, but
  Chapter 5 may still describe it as a design refinement.
- **Accepted:** implemented; the thesis does not yet describe it.
- **Proposed:** awaiting the author's confirmation.
- **Superseded:** replaced by a later entry.

---

## Deviations

### D-01 — `agent_events.seq` ordering column (In thesis)
- **Spec:** `agent_events` has UUID `event_id` and `timestamp`; SSE replays
  history from the database.
- **Implementation:** add `seq BIGINT GENERATED ALWAYS AS IDENTITY (CACHE 1)`,
  unique, with an index on `(run_id, seq)`. `event_id` stays the primary key.
- **Reason:** UUIDs are not orderable and timestamps can tie. SSE reconnection
  (`Last-Event-ID`) needs a monotonic value to resume from.
- **Guarantee and its conditions:** An identity value is assigned at insert
  time, before commit, so on its own `seq` does not guarantee that commit
  order equals `seq` order. The guarantee holds because every writer goes
  through `EventLog.append()`, which takes
  `pg_advisory_xact_lock(<run id>)` before inserting and publishes to the
  in-memory broker only after commit. Per run, therefore, commit order equals
  `seq` order. Across runs, `seq` values interleave, so one run's `seq`
  values have gaps; nothing may assume they are consecutive.
- **In thesis:** ERD (`seq` column note) and sequence diagram (EventLog
  note).
- **Assumption:** single application process (the in-memory broker already
  requires it). The advisory lock keeps database ordering correct even with
  several writers; live publish ordering relies on the single process.

### D-02 — `TIMESTAMPTZ` instead of `TIMESTAMP` (In thesis)
- **Spec:** ERD uses `TIMESTAMP`.
- **Implementation:** all time columns are `TIMESTAMPTZ`; the application
  writes timezone-aware UTC values.
- **Reason:** unambiguous durations for PR-01 and the retention cutoff.
- **In thesis:** ERD.

### D-03 — Retention enforcement and foreign keys (In thesis)
- **Spec:** "Generated package data older than 30 days is eligible for
  deletion. `pipeline_runs` and `agent_events` rows are retained indefinitely
  for audit purposes."
- **Implementation:**
  - The retention sweep deletes only from `generated_packages`, by
    `created_at`, which is indexed. It never touches runs or events.
    **The retention policy is enforced by this sweep.**
  - Foreign keys from both child tables use `ON DELETE RESTRICT`. This is
    protection only: it blocks deleting a run that still has child rows, but
    a run with no events or packages could still be deleted by a privileged
    role, so RESTRICT alone does not guarantee retention.
  - Database-level prohibition: the application role `infraarch_app` has no
    DELETE privilege on `pipeline_runs` and no UPDATE or DELETE on
    `agent_events` (append-only audit log). See D-04.
- **In thesis:** ERD (RESTRICT on both relationships, `created_at` index
  note, retention note). Section 4.2 text still describes retention only as
  "eligible for deletion"; see the list at the end.

### D-04 — Two database roles (Accepted; privileges in thesis)
- **Spec:** not specified.
- **Implementation:** `infraarch_owner` owns the schema and runs migrations;
  `infraarch_app` is used at runtime with least-privilege grants:
  - `pipeline_runs`: SELECT, INSERT, UPDATE
  - `agent_events`: SELECT, INSERT
  - `generated_packages`: SELECT, INSERT, UPDATE, DELETE
- **Reason:** enforces D-03 in the database and limits damage from bugs.
- **In thesis:** the privilege consequences are noted on the ERD. The
  two-role setup itself (owner for migrations, app role at runtime) is an
  implementation detail for Chapter 5.

### D-05 — `files` JSONB shape and path validation (In thesis)
- **Spec:** `files JSONB`, `IaCPackage.files: dict`.
- **Implementation:** a map of relative POSIX path → file content. Paths are
  validated when an `IaCPackage` is constructed and again by the ZIP writer:
  relative only; no leading `/`, drive letters, backslashes, NUL bytes,
  `..`, `.` or empty segments; restricted character set; at most 255
  characters and 8 levels; no case-insensitive duplicates.
- **Reason:** prevents path traversal (e.g. `../`) when writing ZIPs or
  scanning files on disk.
- **In thesis:** class diagram (`IaCPackage.files: dict[str, str]` note).

### D-06 — Package outcomes after validation: Option C (In thesis)
- **Spec conflict (original):** the package state diagram showed
  `validation_error → production_ready` (unvalidated code labelled
  production-ready), while FR-UI-06, FR-V-05 and the run-state table treated
  `invalid` and `validation_error` as final, downloadable states. That let a
  package be delivered without an engineer decision, even with unresolved
  security violations. Both readings contradicted the human-in-the-loop
  principle (Section 3.1).
- **Decision (Option C):** a package becomes `production_ready`
  automatically only if its scan was clean AND validation passed. Every
  other outcome that produces a package (`scan_exhausted`, `invalid`,
  `validation_error`) goes to `pending_review`.
  - `invalid` and `validation_error` are intermediate states, recorded as
    events and shown as review reasons.
  - Final labels are only `production_ready` and `not_production_ready`, and
    only those are downloadable.
  - A retry's fix prompt includes the engineer's feedback and any failed
    validation checks (Phase 5).
- **Where in code:** `app/domain/states.py` (transition table,
  `readiness_after_validation`, `review_reasons`, `is_downloadable`).
- **In thesis:** text (FR-S-07, FR-S-09, FR-V-05, FR-UI-06, UC-08,
  run-state table, Chapter 4) and diagrams (package states, run states,
  sequence diagram 5/5a, class diagram `SecurityAgent.remediate`).

## Clarifications (spec is silent; the diagrams decide)

### CL-01 — Where the iteration limit is checked
- **Spec:** the text says only that the loop "exits with unresolved
  violations". The package state diagram draws `remediating →
  scan_exhausted` ("iteration limit reached with violations remaining") and
  has no `scanning → scan_exhausted` edge.
- **Implementation:** `scanning → remediating | scan_clean | scan_error`;
  `remediating → scanning | scan_exhausted`. When a scan finds violations,
  the package enters `remediating`. There, if the iteration budget is used
  up, it moves to `scan_exhausted` without applying a fix; otherwise it
  applies a fix pass, increments `iteration_count` and returns to
  `scanning`. `iteration_count` therefore counts completed fix passes, and
  it never exceeds `max_iterations`.

---

## Open questions

### OQ-01 — HTTP 410 for expired packages (Deferred)
A missing package row cannot justify 410 on its own: the ERD allows 0–3
packages per run, so absence may mean "generation failed" or "removed by
retention". 410 needs a durable record of which variants once existed, for
example an `agent_events` row with a defined payload such as
`{"kind": "package_stored", "variant": "cost"}`. Decide in Phase 4 (event
payload schema) or Phase 7 (download/results endpoints). Until then, no 410.

### OQ-02 — Terminality of `invalid` and `validation_error` (Resolved)
Resolved by D-06 (Option C).

### OQ-03 — 30-second per-attempt LLM timeout
A full multi-file package may take longer than 30 s to generate. Measure it
in the Phase 1 spike before building on it.

### OQ-04 — Single-process assumption
The in-memory SSE broker requires a single backend process. This should be
stated explicitly in the thesis design (Section 4.4 or the deployment
section).

---

## Thesis text to update (collected)
- Section 4.2 retention paragraph: say that the sweep deletes only packages
  and that the app role cannot delete runs or modify events (D-03, D-04).
  The ERD already shows this; the paragraph does not yet.
- Section 4.4: state the single-process assumption for SSE (OQ-04).
- Optional class-diagram polish: `run_id: UUID`, `llm_provider:
  LLMProvider`, `variant: Variant`, and field types for `DeploymentPlan`
  and `Violation`.

# Use of AI tools in this repository

This repository is the implementation of the BSc thesis *InfraArchAgent: A
Multi-Agent System for Secure Cloud Infrastructure Generation from Natural
Language* (ELTE Faculty of Informatics). AI tools were used with the
supervisor's permission and under the Faculty's Dean's Directive No. 1/2026 on
the Usage of AI Tools. The thesis summarises all AI use in Section 5.8, "Use of
AI Tools", and the signed declaration is submitted with the thesis.

## Tools and how they were used

| Tool | Purpose and method | Where |
|---|---|---|
| OpenAI Codex | Wrote backend, frontend and test code from the author's task descriptions, under the fixed rules in `AGENTS.md`: no real model calls or API keys, never opening `.env`, no pushing. The author ran the tests, reviewed every change, modified the code where needed and decided what was committed. | Source and test code (`backend/`, `frontend/`, `tools/`, `docker/`, `Makefile`, Dockerfiles) |
| Claude (Anthropic, Opus models via claude.ai) | Planning the implementation phases, drafting the task descriptions given to Codex, reviewing results and maintaining the project. | Phase plans and task descriptions (`docs/prompts/`) |

## Point-of-use marking

Every source, test and build file written with Codex carries this comment at
the top (after a shebang line where there is one):

```
AI assistance: written with OpenAI Codex from the author's task
descriptions; reviewed and modified by the author. See AI_USE.md.
```

The comment was added in one documentation-only commit after release
`v1.0.1`; it changes no code. Data files that cannot carry comments (JSON,
lock files, test fixtures) and third-party material under `.agents/skills/`
are not marked. Empty `__init__.py` files are not marked either. Three files
are left without the comment because a replay test checks that they are
byte-identical to an earlier pinned commit: `backend/app/validation/formats.py`,
`backend/app/security/addressing.py` and `backend/app/security/defaults.py`.
They were written with Codex in the same way as the rest. The evidence replay
scripts under `backend/scripts/` that compare source-file hashes should be run
on `v1.0.1`, the revision the evidence was recorded against. Notes and logs
under `docs/` were written with the same tools during the same tasks and
reviewed by the author; the frozen specification in `docs/spec/` is the
approved thesis text and was not changed.

## What was not handed to an AI tool

No password, API key or master key was entered into either tool. The language
models that InfraArchAgent calls at runtime are part of the system under study,
not authoring help. The complete conversation logs of both tools are kept by
the author and can be shown to the supervisor on request until the thesis
evaluation is finished. The author is responsible for all code in this
repository.

## Formatting (v1.0.3)

Release `v1.0.3` reformats the frontend TypeScript and CSS with Prettier
3.9.10 (`printWidth` 100) in one formatting-only commit; no logic changed.
The Prettier set-up (`.prettierrc.json`, `.prettierignore` and the `format`
and `format:check` npm scripts, now part of `npm run lint`) was suggested by
Claude and reviewed by the author. `frontend/src/constants/examples.ts` keeps
its original layout because a backend test reads it with a regular expression.

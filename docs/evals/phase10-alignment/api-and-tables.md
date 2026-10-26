# Final API and data-model inventory

Static source inventory; framework documentation/static routes are excluded.

46 method/path definitions versus the chapter's four REST endpoints and one SSE stream.

| Method | Endpoint | Introducing / extending deviation |
|---|---|---|
| GET | `/api/auth/session` | D-49/D-50/D-58 |
| GET | `/api/auth/users` | D-49/D-50/D-58 |
| GET | `/api/benchmark/settings` | D-43/D-59 |
| GET | `/api/health` | D-35/D-61 |
| GET | `/api/lessons` | D-60 |
| GET | `/api/lessons/control` | D-60 |
| GET | `/api/lessons/history` | D-60 |
| GET | `/api/lessons/{identity}` | D-60 |
| GET | `/api/me/preferences` | D-53 |
| GET | `/api/me/recent-runs` | D-53 |
| GET | `/api/models` | D-52/D-58 |
| GET | `/api/models/defaults` | D-52/D-58 |
| GET | `/api/pipeline/{run_id}/download-all` | D-58 |
| GET | `/api/pipeline/{run_id}/download/{variant}` | Original interface; D-18/D-37/D-47 extend contracts |
| GET | `/api/pipeline/{run_id}/events` | Original interface; D-18/D-37/D-47 extend contracts |
| GET | `/api/pipeline/{run_id}/results` | Original interface; D-18/D-37/D-47 extend contracts |
| GET | `/api/pipeline/{run_id}/stream` | Original interface; D-18/D-37/D-47 extend contracts |
| GET | `/api/providers` | D-51 |
| GET | `/api/reviews/history` | D-58/D-60 |
| GET | `/api/reviews/history/export` | D-58/D-60 |
| GET | `/api/reviews/history/insights` | D-58/D-60 |
| POST | `/api/auth/login` | D-49/D-50/D-58 |
| POST | `/api/auth/logout` | D-49/D-50/D-58 |
| POST | `/api/auth/password` | D-49/D-50/D-58 |
| POST | `/api/auth/setup` | D-49/D-50/D-58 |
| POST | `/api/auth/users` | D-49/D-50/D-58 |
| POST | `/api/auth/users/{user_id}/disable` | D-49/D-50/D-58 |
| POST | `/api/auth/users/{user_id}/enable` | D-49/D-50/D-58 |
| POST | `/api/auth/users/{user_id}/password` | D-49/D-50/D-58 |
| POST | `/api/benchmark/preflight` | D-43/D-59 |
| POST | `/api/lessons` | D-60 |
| POST | `/api/lessons/check` | D-60 |
| POST | `/api/lessons/{identity}/confirmation` | D-60 |
| POST | `/api/lessons/{identity}/{action}` | D-60 |
| POST | `/api/pipeline/run` | Original interface; D-18/D-37/D-47 extend contracts |
| POST | `/api/pipeline/{run_id}/packages/{variant}/review` | Original interface; D-18/D-37/D-47 extend contracts |
| POST | `/api/providers` | D-51 |
| POST | `/api/providers/environment` | D-51 |
| POST | `/api/providers/probe` | D-51 |
| POST | `/api/providers/{credential_id}/default` | D-51 |
| POST | `/api/providers/{credential_id}/revoke` | D-51 |
| POST | `/api/providers/{credential_id}/test` | D-51 |
| PUT | `/api/lessons/control` | D-60 |
| PUT | `/api/me/preferences` | D-53 |
| PUT | `/api/me/recent-runs/{run_id}` | D-53 |
| PUT | `/api/models/defaults` | D-52/D-58 |

14 application tables versus the original three. Alembic's revision table is migration metadata.

| Table | Introducing deviation |
|---|---|
| `pipeline_runs` | Original model; D-01–06/D-23/D-38/D-47/D-48 extend columns |
| `generated_packages` | Original model; D-01–06/D-23/D-38/D-47/D-48 extend columns |
| `agent_events` | Original model; D-01–06/D-23/D-38/D-47/D-48 extend columns |
| `auth_sessions` | D-49 |
| `users` | D-50 |
| `provider_credentials` | D-51/D-52 |
| `llm_settings` | D-51/D-52 |
| `user_preferences` | D-53 |
| `user_recent_runs` | D-53 |
| `lesson_revisions` | D-60; Phase 10 additive provenance migration 0015 |
| `lesson_sets` | D-60; Phase 10 additive provenance migration 0015 |
| `lesson_control` | D-60; Phase 10 additive provenance migration 0015 |
| `lesson_audit_events` | D-60; Phase 10 additive provenance migration 0015 |
| `lesson_confirmations` | D-60; Phase 10 additive provenance migration 0015 |

# Author container build and run

Status: **statically checked only**. No image was built/pulled and no container
deployment was run during Phase 10. Base image availability, dependency resolution,
provider permissions and runtime behavior need author verification. Exact base
tags are used; registry digests should be recorded from the author's actual build.

The backend runs as UID 10001 with one worker. It installs application versions
under the committed constraints, Checkov 3.3.21, checksum-verified Trivy 0.69.3 and
Terraform 1.16.4. Its isolated Checkov environment does not change application
dependencies. Missing optional linters are reported as skips (D-35). Add them
only through the documented pinned validator procedure if their coverage is
needed. No generated infrastructure is applied. The frontend uses a locked Node
build and non-root nginx, preserving same-origin cookies, Host and unbuffered SSE.

Build context is deny-by-default: no dotenv, credentials, Git history, caches,
evidence or runtime master key enters a layer. Supply runtime secrets through
the author's process environment only; never use Docker build arguments for keys.
The backend has only app-role credentials. The separate one-shot migration service
gets the owner credential. PostgreSQL has no published host port in this stack.

Author prerequisites: Docker/Compose, exported `POSTGRES_PASSWORD`,
`INFRAARCH_OWNER_PASSWORD`, `INFRAARCH_APP_PASSWORD`, `API_KEY` and the persistent
`CREDENTIAL_ENCRYPTION_KEY`. Generate them privately; `.env.example` contains only
placeholders. Provision `.cache/terraform-providers/` and
`.cache/terraform-provider-schemas/` with `make providers` and `make provider-schema`
on the author machine first. Mirrors are mounted **read-only**; runtime cannot
provision them. Preserve the seven pinned provider versions and linux_amd64.

```bash
docker compose --env-file /dev/null -f docker-compose.full.yml build backend frontend
docker compose --env-file /dev/null -f docker-compose.full.yml up -d --wait postgres
docker compose --env-file /dev/null -f docker-compose.full.yml --profile ops run --rm migrate
docker compose --env-file /dev/null -f docker-compose.full.yml up -d --wait backend frontend
curl --fail http://127.0.0.1:8080/api/health
```

The recipe requires a configured API key for the backend's internal network bind;
it preserves the localhost-only open-mode restriction. The frontend proxy is not
a local peer for first-account setup, so bootstrap **inside the backend container**
with its existing `/api/auth/setup` route. This command prompts privately, sends
the existing key in a header and prints only the HTTP status:

```bash
docker compose --env-file /dev/null -f docker-compose.full.yml exec backend python -c \
'import getpass,http.client,json,os; u=input("Admin username: "); p=getpass.getpass("Admin password (12+ characters): "); c=http.client.HTTPConnection("127.0.0.1",8000); c.request("POST","/api/auth/setup",json.dumps({"username":u,"password":p}),{"Content-Type":"application/json","X-API-Key":os.environ["API_KEY"]}); r=c.getresponse(); print("Setup HTTP",r.status); c.close()'
```

Then open `http://127.0.0.1:8080`, log in and submit a **stub** run. Record health,
actual image digests/versions, migration result and three package outcomes in a
new author evidence folder. Complete the browser checklist in `deployment.md`.
HTTP is loopback-only here; network/HTTPS production hosting remains outside scope.

Stop with `docker compose --env-file /dev/null -f docker-compose.full.yml stop`.
Keep the volume and master key for restart. Run migrations explicitly before
starting new code; the application never migrates automatically.

# HC Instagram Worker 1.1.0

Deployable retrieval service for the installed HC Instagram Auto-Sync 1.1.0 WordPress plugin. This archive is a server application, not a WordPress plugin. Do not upload it through WordPress Plugins.

## Current status

Built and tested locally. Not deployed, no public Worker URL exists yet. The Instagram request for aamersiddiqui did not retrieve media from the build environment. Local service tests prove the HTTP/authentication/cache behavior, not that Instagram will allow collection from a deployed server.

## Deployment route

The package contains a Dockerfile and a Render Blueprint (render.yaml). Add and connect the Render app in ChatGPT to enable account-side deployment work. Creating a service also requires an accessible Git repository containing this package; place these source files at the repository root. Do not commit .env, operator sessions, or tokens. No repository has been created or changed as part of this build.

The Blueprint uses a free web-service plan for an initial staging test, with /health as its health check, and asks Render to generate HC_WORKER_TOKEN. The free service may sleep when inactive and incur a cold start; do not treat it as tested production hosting for 2,000 creators. Persistent operator-session handling for Stories must be configured separately. No paid hosting plan is provisioned or authorized by this package.

The Docker command listens on Render's PORT environment variable. One worker process is intentional: Instagram session use is serialized and cache state is local to the process. There is no scheduled scan of creator accounts. WordPress calls /feed/USERNAME only when a visited profile needs a refresh.

If deploying manually on a Python-capable host, use Python 3.12, set HC_WORKER_TOKEN and HC_ALLOWED_USERNAMES, install requirements.txt, and run:

    uvicorn app:create_app --factory --host 0.0.0.0 --port 8000 --workers 1 --no-access-log

For a VPS, bind to localhost behind an HTTPS reverse proxy instead of exposing an HTTP port directly. The WordPress plugin expects a publicly resolvable HTTPS base URL. Do not run this inside a public WordPress document root. Your existing Woo Premium website can remain where it is; this service needs a Python-capable host.

## After successful deployment

1. Verify SERVICE_BASE_URL/health returns {"ok":true}.
2. Verify /status rejects a request without the bearer token and responds with service version and session status when authorized.
3. Verify a real /feed/aamersiddiqui?types=media request with the token returns a nonempty media array. If it returns media_error or 502, deployment alone has not solved collection. Investigate Instagram access/session status before promising a functioning feed.
4. In WordPress Settings > HC Instagram Sync, paste the actual deployed HTTPS base URL in Worker URL. Do not enter instagram.com. Paste the generated HC_WORKER_TOKEN in the bearer-token field.
5. Click Test worker, then visit /test/. Keep manual galleries until real Posts/Reels are visibly fetched. Verify Stories separately.

No service address or token in this file is a live credential. The real address is assigned by the host after deployment, and the token is generated/configured privately there.

## Configuration

- HC_WORKER_TOKEN: required secret, at least 32 characters. Sent only by the WordPress server.
- HC_ALLOWED_USERNAMES: allowed public usernames, comma-separated. Initial Blueprint values: aamersiddiqui,hyderabadcreators. After staging verification, * accepts dynamic usernames from authenticated WordPress requests. Authentication stays mandatory.
- HC_SESSION_USERNAME and HC_SESSION_FILE: optional pair for an operator-owned Instagram session. Both must be set together. Session files are private server material and must never be uploaded to a public repository or WordPress folder.

The included Instaloader collector uses no official Meta developer integration. Creators do not log in. Anonymous public Posts/Reels can still be denied by Instagram; active Stories require a valid operator-owned server session in this implementation. Private Instagram profiles are always rejected. No bypass of Instagram access controls is included.

An operator can create a session interactively on a private machine using `instaloader --login YOUR_OPERATOR_ACCOUNT`, then securely supply its session file to the hosted service. Do not put an Instagram password in Worker URL or bearer token. File mounts/secret files must be readable by Docker UID 10001. A free stateless host is not a durable session-store solution by itself.

## Endpoints

- GET /health: public connectivity check only; it does not contact Instagram.
- GET /status: bearer-authenticated service version/session/cache status. It does not reveal credentials or server paths.
- GET /feed/{username}?types=media,stories: bearer-authenticated public-content retrieval. Types can be media, stories, or both. Media is up to 20 profile posts plus 20 reels, deduplicated. Stories are up to 40 active entries.

Returned media entries contain id, kind, Instagram permalink, thumbnail URL, and a short caption. Story entries include expires_at. Cards link to Instagram for full content; this service does not download/store video files or provide an in-page video player.

Missing/blocked content types return an error field and omit that type's successful array. A valid empty stories array means the collection succeeded and no active Stories were returned. WordPress must preserve prior cache on retrieval failures (the installed plugin already does this).

Security: bearer authentication, public-account checks, username/type validation, one-second busy queue limit, short duplicate-request cache, no API docs exposure, no-access-log startup, sanitized upstream failures, and no-store response headers. No global creator account scans. Instagram may still block or rate-limit the service; a running HTTP endpoint is not a guarantee of live content.

## Validation

- 18 automated tests passed: 12 HTTP API/authentication/cache tests and 6 collector tests with controlled fixtures.
- Live local Uvicorn HTTP checks passed for /health, unauthorized /status, and authorized /status.
- Python compilation passed.
- One anonymous live Instagram attempt did not retrieve content.
- Container build, Render deployment, hosted Instagram retrieval, operator-session collection, and large-scale throughput have not been tested.

To run tests, install pytest and httpx alongside requirements.txt, then run `python -m pytest tests -q` from this directory.

## Primary references

https://render.com/docs/deploy-fastapi
https://render.com/docs/blueprint-spec
https://render.com/docs/free
https://instaloader.github.io/as-module.html
https://instaloader.github.io/module/instaloader.html

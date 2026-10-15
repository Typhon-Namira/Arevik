# Arevik authenticated HTTPS deployment runbook

The API is still bound to 127.0.0.1:8000 on the EC2 host. Caddy currently serves a maintenance page.
**Do not swap Caddy to reverse proxy until the new app has passed an authenticated local test.**

## Changes

- User email/password registration; password hashed with scrypt + per-user random salt.
- 7-day random opaque sessions persisted as SHA-256 hashes in SQLite, with logout revocation.
- Authentication required on audio and experimental text translation.
- Registry closed unless `AREVIK_ALLOW_REGISTRATION=true`.
- TLS termination continues at Caddy; no shared API secret is shipped in mobile APK.

## Important release blockers

This is an initial account backend, *not a security-audited production identity provider*.
Before untrusted/public sign-up add perimeter rate limits for registration/login,
email verification, reset/recovery, abuse throttling, backup/restore, monitoring,
account deletion/privacy policy, and authenticated WebSocket sessions.
Never send passwords or bearer tokens over HTTP.
Multiple worker/process deployment requires database/concurrency review.

## EC2 safe deployment checklist

1. Save backups of local `compose.yaml` and `infra/Dockerfile.server`.
2. Fetch the feature branch files; do not reset local Docker changes.
3. Modify `compose.yaml` so the API service uses env:
   `AREVIK_AUTH_DB=/opt/arevik/data/auth.sqlite3`,
   `AREVIK_ALLOW_REGISTRATION=false` for initial closed rollout.
   Add named volume `arevik-auth:/opt/arevik/data` to preserve identities.
   Keep the existing model volume untouched.
4. Rebuild API and inspect `docker compose ps`, `curl http://127.0.0.1:8000/health`.
5. An unauthenticated POST with a valid multipart body to `/api/v1/translate/file`
   must return 401. An authenticated round-trip /register (temporarily enabled
   only behind local loopback), /login, /me, /logout must work.
6. Run Caddy with **host networking** on Linux so reverse_proxy can access
   `127.0.0.1:8000`. Do not merely use `host.docker.internal` because the
   current API port is bound to loopback. Preserve named Caddy volumes.
7. Caddyfile:
   ```caddy
   api.arevikai.com {
       encode zstd gzip
       request_body {
           max_size 16MB
       }
       reverse_proxy 127.0.0.1:8000
   }
   ```
   Note: Caddy built-in request_body max_size applies to request body, not
   to HTTP login rate limits. Add and verify a separate perimeter limiter
   before enabling open public registration.
8. Test externally: `curl -i https://api.arevikai.com/health` should be 200
   and unauthenticated inference should be 401; `/api/v1/auth/me` must be 401.
   Confirm automatic certificate renewal and firewall: expose 80/443, not 8000.
9. Build Android APK from GitHub Actions after workflow success. The Flutter app
   should use `https://api.arevikai.com`; test signup/login and microphone on a
   physical Android phone.

Never paste passwords, session tokens, entire environment files, or raw credentials
into a chat or CI logs.

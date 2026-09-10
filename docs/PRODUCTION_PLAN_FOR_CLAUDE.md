# DairyPro Production Plan for Claude

## 1. Objective

Prepare DairyPro for real farm use with:

- A production FastAPI backend
- A responsive web/PWA frontend
- A native Android client that works offline
- Automatic synchronization when connectivity returns
- Reliable email delivery
- Secure HTTPS access
- Persistent and recoverable farm data

The existing Docker Compose deployment is suitable for local testing. This plan
covers the work required before production use.

## 2. Current baseline

The repository currently contains:

- FastAPI backend with JWT authentication
- React/Vite frontend served by Nginx
- Docker Compose deployment
- SQLite storage by default
- Optional PostgreSQL support
- SMTP integration with a local fallback email log
- PWA manifest and service worker
- IndexedDB offline queue for the Quick Log milk and health workflows
- Generic entity API backed by SQLAlchemy

The current LAN deployment is not production deployment. It uses HTTP and a
private IP address, so it should not be exposed directly to the public internet.

## 3. Target production architecture

```text
Android app / Web browser
          |
          | HTTPS
          v
   Reverse proxy / TLS
          |
          +--------------------+
          |                    |
       Frontend             Backend API
       Nginx                 FastAPI
                               |
                         PostgreSQL
                               |
                         Backups
```

Recommended production components:

- Domain name: `app.example.com`
- API endpoint: same domain through `/api`, or `api.example.com`
- Caddy or managed load balancer for HTTPS
- FastAPI running in Docker
- PostgreSQL for concurrent multi-user operation
- Managed SMTP provider
- Automated database backups
- Android app using Room and WorkManager

## 4. Phase 1: Stabilize the existing application

### Backend

- Confirm all secrets come from environment variables.
- Reject the default secret at startup in production mode.
- Set production CORS to only the real HTTPS frontend origin.
- Add structured logging without logging passwords, tokens, or SMTP secrets.
- Add request IDs and useful error responses.
- Add database indexes for entity type, timestamps, and frequently queried fields.
- Add explicit production configuration validation.
- Confirm upload paths have size and type restrictions.
- Review authorization for every write endpoint.

### Frontend

- Commit a valid `frontend/package-lock.json` and use `npm ci` for reproducible builds.
- Keep `VITE_API_URL` configured at build time.
- Remove development LAN URLs from production configuration.
- Add visible handling for expired sessions and failed synchronization.
- Confirm the service worker does not cache private API responses.
- Add an application version displayed in diagnostics or settings.

### Data

- Use PostgreSQL for production multi-user workloads.
- Keep SQLite only for local development or a single-user installation.
- Define a backup and restore procedure before onboarding real data.
- Test restoring a backup into a clean environment.

## 5. Phase 2: Production deployment

### Environment configuration

Set production values through the hosting platform's secret manager or a
protected environment file:

```env
DAIRYPRO_SECRET_KEY=<unique-long-random-secret>
DAIRYPRO_CORS_ORIGINS=https://app.example.com
DATABASE_URL=postgresql://<user>:<password>@postgres:5432/dairypro
SMTP_HOST=<provider-host>
SMTP_PORT=587
SMTP_USER=<provider-user>
SMTP_PASSWORD=<provider-password>
SMTP_FROM=DairyPro <no-reply@example.com>
SMTP_TLS=true
```

Never commit `.env`, SMTP passwords, database passwords, or API keys.

### Deployment steps

1. Provision a server or managed container platform.
2. Configure DNS for the application domain.
3. Deploy PostgreSQL with persistent storage.
4. Deploy the backend container on a private network.
5. Deploy the frontend container on a private network.
6. Put Caddy or a managed reverse proxy in front of both services.
7. Enable HTTPS and automatic certificate renewal.
8. Build the frontend with the public API URL.
9. Run database initialization and verify health checks.
10. Create the first administrator account.
11. Send a test invite email.
12. Verify browser, Android, backup, and restore workflows.

### Production health checks

```bash
docker compose ps
curl -fsS https://app.example.com/api/health
curl -fsSI https://app.example.com/
```

## 6. Phase 3: Email setup

Use a transactional email provider rather than a personal mailbox for
production. Suitable options include SendGrid, Mailgun, SMTP2GO, Amazon SES,
or a managed Microsoft 365 mailbox.

Required verification:

- Sender/domain verification completed
- SPF record configured
- DKIM record configured
- DMARC policy configured
- Invite email delivered successfully
- Shopping-list alert delivered successfully
- Failed delivery logged without exposing credentials
- Email fallback log disabled or protected in production

Add an email test operation restricted to administrators and record delivery
status without storing SMTP passwords.

## 7. Phase 4: Native Android offline application

The native Android app should use the existing FastAPI backend as its central
server and maintain a local database for field work.

### Recommended stack

- Kotlin
- Jetpack Compose
- Room for local SQLite storage
- WorkManager for reliable background synchronization
- Retrofit or Ktor for HTTP requests
- Android Keystore for tokens and encryption keys

### Local database

Create local tables for the entities needed in the field first:

- Cattle
- MilkProduction
- HealthRecord
- BreedingRecord
- Inventory
- Task
- SyncOperation

Every local record must include:

- `id`
- `server_id`, nullable until synchronized
- `updated_at`
- `sync_state`
- `deleted_at`, when using tombstones
- `device_id`

### Sync protocol

Add explicit backend endpoints:

```text
POST /api/sync/push
GET  /api/sync/changes?cursor=<cursor>
```

The push response should include:

- Accepted operations
- Server IDs
- Updated records
- Rejected operations
- Conflict details
- A new synchronization cursor

The protocol must be idempotent. Each operation needs a client-generated
operation ID so retrying after a timeout cannot create duplicate records.

### Sync behavior

1. Save field changes locally immediately.
2. Add each change to the local sync queue.
3. Display pending, synchronized, and failed states.
4. Trigger WorkManager when connectivity is available.
5. Upload operations in small batches.
6. Retry transient failures with exponential backoff.
7. Keep permanent failures visible for user action.
8. Pull remote changes after successful uploads.
9. Advance the cursor only after changes are safely stored locally.
10. Preserve data when the app is terminated during synchronization.

### Conflict policy

Use version numbers or server timestamps. Start with this policy:

- Non-conflicting creates are accepted.
- Updates with an older version are rejected as conflicts.
- The client downloads the server version.
- The user can review and choose which version to keep.
- Deletes use tombstones so deleted records do not reappear during pull.

Do not rely only on device time for conflict resolution.

## 8. Android security and release

- Use HTTPS only in release builds.
- Store access tokens in encrypted storage backed by Android Keystore.
- Do not embed database passwords or SMTP credentials in the APK.
- Disable cleartext traffic in the release manifest.
- Sign the APK or Android App Bundle with a protected release key.
- Keep debug logging disabled in release builds.
- Test installation, update, logout, and token expiration.
- Prefer publishing an Android App Bundle to Google Play; use a signed APK for
  controlled internal distribution.

## 9. Testing plan

### Automated tests

- Backend authentication and role tests
- CRUD and validation tests for each entity
- Sync push/pull and idempotency tests
- Conflict resolution tests
- Email success and failure tests
- Database backup/restore tests
- Frontend build and lint checks
- Android Room migration tests
- Android WorkManager retry tests

### Manual acceptance tests

- Register the first administrator
- Invite a manager, staff user, and viewer
- Create milk and health records online
- Enter milk and health records offline
- Kill the Android app while records are pending
- Restore connectivity and verify synchronization
- Repeat synchronization and confirm no duplicates
- Edit the same record on two devices and verify conflict handling
- Verify data survives container recreation
- Restore a database backup
- Receive an invite and shopping-list email
- Install and update the Android release

## 10. Observability and operations

Add:

- Container health checks
- Centralized application logs
- Database disk and connection monitoring
- Error tracking
- Backup success alerts
- Email delivery monitoring
- Sync failure metrics
- Deployment version tracking

Operational procedures must cover:

- Restarting services
- Rotating secrets
- Restoring backups
- Revoking a compromised account
- Recovering a lost Android device
- Rolling back a release
- Handling a failed database migration

## 11. Rollout order

1. Finish backend and frontend security review.
2. Move production storage from SQLite to PostgreSQL.
3. Configure domain, HTTPS, and email delivery.
4. Deploy a staging environment.
5. Test backup and restore.
6. Add and test explicit synchronization endpoints.
7. Build the Android offline client.
8. Pilot with one farm manager and one field worker.
9. Monitor sync failures and conflicts.
10. Expand to the full farm team.
11. Publish the Android app or distribute signed APKs.

## 12. Definition of production ready

DairyPro is production ready when:

- All public traffic uses HTTPS.
- Production secrets are stored outside source control.
- PostgreSQL backups are automated and restore-tested.
- Emails are delivered through a verified SMTP provider.
- Android offline changes survive restarts and synchronize without duplicates.
- Conflicts are visible and recoverable.
- Role permissions are tested.
- Health checks and error monitoring are active.
- A rollback and recovery procedure has been rehearsed.

## 13. Instructions for Claude

When implementing this plan:

1. Inspect the existing code before changing it.
2. Preserve the current API contracts unless a migration is documented.
3. Make one focused change at a time.
4. Add tests for every synchronization and security behavior.
5. Never print or commit secrets.
6. Prefer PostgreSQL-compatible, production-safe behavior.
7. Keep offline writes durable across process termination.
8. Make retries idempotent.
9. Report changed files, validation commands, and remaining risks.
10. Do not claim production readiness until the acceptance criteria above pass.

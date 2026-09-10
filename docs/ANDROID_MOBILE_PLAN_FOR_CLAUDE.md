# DairyPro Android Mobile Application Plan for Claude

## 1. Objective

Build a native Android application for DairyPro that:

- Works without an internet connection
- Stores field data locally and safely
- Synchronizes cached changes with the DairyPro server when connectivity returns
- Prevents duplicate records during retries
- Makes synchronization status visible to the user
- Uses the existing FastAPI backend as the central system of record
- Can be distributed as a signed APK or Android App Bundle

The existing React/PWA frontend and FastAPI backend remain valid. The Android
application is a new client of the same backend, not a replacement for it.

## 2. Existing architecture to preserve

The backend currently provides:

- JWT authentication
- Generic entity CRUD endpoints
- SQLAlchemy persistence
- SQLite by default, with PostgreSQL support
- Role-based write permissions
- Entities including cattle, milk, health, breeding, inventory, tasks, and finance

The web frontend already has a limited offline implementation:

- IndexedDB cache
- IndexedDB write queue
- Temporary local IDs
- Automatic replay when connectivity returns
- Offline Quick Log for milk and health records

Use this existing behavior as the conceptual starting point, but implement the
native Android version with a durable Room database and WorkManager.

## 3. Recommended Android technology

- Kotlin
- Jetpack Compose
- Room for local SQLite storage
- WorkManager for background synchronization
- Retrofit or Ktor Client for API requests
- Kotlin serialization or Moshi for JSON
- Android Keystore-backed encrypted storage for credentials
- Hilt for dependency injection if the project already uses it

Use current stable Android libraries compatible with the project's chosen
compile and target SDK. Keep the minimum Android version appropriate for the
farm devices that will be supported.

## 4. Android application structure

Use clear boundaries:

```text
app/
  data/
    local/
      DairyDatabase
      entities/
      dao/
    remote/
      DairyApi
      dto/
    repository/
    sync/
  domain/
    model/
    usecase/
  ui/
    navigation/
    screens/
    components/
  security/
  workers/
```

The UI must communicate through repositories or use cases. Screens should not
make raw network or database calls directly.

## 5. Local database design

Start with the field workflows that benefit most from offline operation:

- Cattle
- MilkProduction
- HealthRecord
- BreedingRecord
- Inventory
- Task
- SyncOperation

Each locally stored business record should include:

- `id`: stable client-side UUID
- `serverId`: nullable until accepted by the server
- `entityType`
- `updatedAt`
- `syncState`: `SYNCED`, `PENDING`, `FAILED`, or `CONFLICT`
- `deletedAt`: nullable tombstone timestamp
- `deviceId`
- `serverVersion`: nullable version returned by the server

The `SyncOperation` table should include:

- `operationId`: unique UUID generated once on the device
- `entityType`
- `localRecordId`
- `serverRecordId`: nullable
- `operationType`: `CREATE`, `UPDATE`, or `DELETE`
- `payload`
- `baseVersion`: version the edit started from
- `createdAt`
- `attemptCount`
- `lastAttemptAt`
- `lastError`
- `state`

Never delete a queued operation merely because an upload attempt timed out.

## 6. Offline behavior

When the device is offline:

1. Save the user's change to Room immediately.
2. Generate a client-side UUID.
3. Mark the local record as `PENDING`.
4. Create one durable `SyncOperation` row.
5. Update the UI immediately from local data.
6. Show the pending-sync state to the user.

The user must be able to close or restart the app without losing pending data.

Reads should use local Room data first. When online, refresh local records from
the server and retain a usable local cache for the next offline period.

## 7. Synchronization protocol

Add explicit synchronization endpoints to the FastAPI backend:

```text
POST /api/sync/push
GET  /api/sync/changes?cursor=<cursor>
```

### Push request

The client sends a batch of operations:

```json
{
  "device_id": "device-uuid",
  "operations": [
    {
      "operation_id": "operation-uuid",
      "entity_type": "MilkProduction",
      "operation": "create",
      "record_id": "client-uuid",
      "server_id": null,
      "base_version": null,
      "payload": {}
    }
  ]
}
```

### Push response

The server returns a result for every operation:

```json
{
  "results": [
    {
      "operation_id": "operation-uuid",
      "status": "accepted",
      "server_id": "server-record-id",
      "server_version": 1,
      "record": {}
    }
  ],
  "next_cursor": "cursor-value"
}
```

Possible operation statuses:

- `accepted`
- `already_applied`
- `conflict`
- `validation_error`
- `unauthorized`
- `retryable_error`

The server must persist or otherwise recognize `operation_id` values. Repeating
the same operation after a timeout must return the original result rather than
creating a duplicate record.

### Pull request

The client calls:

```text
GET /api/sync/changes?cursor=<last-known-cursor>
```

The response must include created, updated, and deleted records since the
cursor, plus a new cursor. The client should write the changes transactionally
to Room before advancing its cursor.

Use tombstones for deletes so an old device cannot accidentally re-create a
record that was deleted on the server.

## 8. Synchronization algorithm

1. Check that the user is authenticated and the device has connectivity.
2. Load pending operations ordered by creation time.
3. Upload a small batch to `/api/sync/push`.
4. Process every result independently.
5. Convert accepted temporary IDs to server IDs.
6. Mark accepted local records as `SYNCED`.
7. Keep retryable failures queued.
8. Mark validation errors and conflicts as `FAILED` or `CONFLICT`.
9. Pull server changes using the saved cursor.
10. Apply pulled changes in one Room transaction.
11. Advance the cursor only after the transaction succeeds.
12. Schedule another WorkManager run if operations remain.

Use exponential backoff for transient failures. Do not retry authentication,
validation, or conflict errors forever.

## 9. Conflict handling

Do not rely only on the device clock. Use a server-issued version number or
revision token.

Recommended initial policy:

- Creates with a new operation ID are accepted once.
- Updates include `base_version`.
- If `base_version` matches the server version, accept the update.
- If it does not match, return `conflict` with both versions.
- Store the conflict locally and show it to the user.
- Allow the user to keep the server version, keep the local version, or merge
  fields where a merge is safe.
- Deletes create server tombstones and participate in version checks.

Begin with explicit conflict visibility rather than silently overwriting field
work.

## 10. Authentication and security

- Use HTTPS for every release environment.
- Store JWTs in encrypted Android storage backed by Android Keystore.
- Never place database, SMTP, or Anthropic credentials in the APK.
- Do not log tokens, passwords, request payload secrets, or personal data.
- Clear local user data and credentials on logout where policy requires it.
- Handle token expiry by refreshing securely or requiring login again.
- Use Android network security configuration to disable cleartext traffic in
  release builds.
- Consider encrypting the Room database if the threat model requires it.
- Support device revocation from the backend for lost phones.

For local development only, the app may use the LAN backend URL. Release builds
must use an HTTPS API URL.

## 11. WorkManager sync worker

Implement a `CoroutineWorker` with these properties:

- Network constraint: connected network required
- Unique work name: one sync worker per account/device
- Existing work policy: keep or replace deliberately, never run uncontrolled
  parallel sync workers
- Retry transient network and server errors
- Stop safely when the process is killed
- Resume from durable Room state on the next run
- Emit progress for the UI

Trigger synchronization:

- When network connectivity returns
- After an offline write
- When the app starts or resumes
- From a user-visible “Sync now” action
- Periodically, subject to Android battery restrictions

## 12. User experience requirements

Display:

- Online/offline status
- Number of pending changes
- Last successful synchronization time
- Current synchronization progress
- Failed operations requiring attention
- Conflicts requiring review

The app should remain useful while synchronization is pending. Do not block
field data entry because the server is unavailable.

For the first release, prioritize these screens:

1. Login
2. Dashboard with sync status
3. Cattle list and details
4. Milk entry
5. Health entry
6. Breeding entry
7. Inventory lookup and adjustment
8. Task list and completion
9. Sync queue and conflict review
10. Settings and logout

## 13. Backend changes required

Implement the following backend capabilities before relying on the Android app:

- Sync request and response schemas
- Idempotency storage for operation IDs
- Server record versions or revision tokens
- Changes feed with cursor pagination
- Tombstones for deletes
- Conflict responses containing server and client context
- Batch size limits
- Transactional push handling
- Per-user authorization on all sync operations
- Device registration and optional device revocation
- Tests for duplicate requests and interrupted syncs

Do not expose the database directly to Android. All synchronization must use
authenticated API endpoints.

## 14. Testing plan

### Local database tests

- Create, update, and delete records offline
- Restart the app with pending operations
- Migrate the Room schema safely
- Preserve tombstones
- Preserve queue ordering
- Handle duplicate operation IDs locally

### Synchronization tests

- Successful create, update, and delete
- Network loss during upload
- Server timeout after accepting an operation
- Repeated upload of the same operation
- Multiple pending batches
- Partial batch success
- Token expiration during synchronization
- Validation failure
- Conflict response
- Pull cursor failure and retry
- App termination during a Room transaction

### Device tests

- Airplane mode field entry
- Wi-Fi reconnect
- Mobile data reconnect
- Low battery/background restrictions
- Android process termination
- Device reboot
- Slow network
- Large cached dataset
- Two devices editing the same record

### Acceptance test

1. Log in on Android.
2. Download the required farm data.
3. Enable Airplane Mode.
4. Create milk and health records.
5. Close and reopen the app.
6. Confirm records remain visible and pending.
7. Restore connectivity.
8. Confirm WorkManager synchronizes the records.
9. Confirm the server contains exactly one copy of each record.
10. Repeat synchronization and confirm no duplicates.
11. Create an intentional conflict and verify it is visible and recoverable.

## 15. APK and Play Store release

For internal testing:

- Build a signed APK.
- Install it on approved farm devices.
- Use an HTTPS staging backend.
- Keep the signing key protected.

For public or managed distribution:

- Prefer an Android App Bundle (`.aab`) for Google Play.
- Configure application ID, version code, and version name.
- Create separate debug, staging, and release configurations.
- Never ship LAN URLs in release builds.
- Enable Play App Signing or protect the release key securely.
- Provide a privacy policy if distributing publicly.
- Test upgrades with existing local data and pending sync operations.

## 16. Rollout sequence

1. Finalize the Android data model.
2. Add backend sync schemas and idempotency handling.
3. Add server versions, changes cursor, and tombstones.
4. Build Room repositories and offline screens.
5. Add WorkManager synchronization.
6. Add conflict review UI.
7. Test with the existing seeded dataset.
8. Deploy an HTTPS staging backend.
9. Pilot with one Android device and one farm user.
10. Monitor pending operations, failures, and conflicts.
11. Expand to additional devices.
12. Publish a signed APK or Android App Bundle.

## 17. Definition of done

The Android application is ready for production when:

- Core field workflows work without a network.
- Pending data survives app termination and device reboot.
- Sync is idempotent and creates no duplicates.
- Conflicts are detected and recoverable.
- Deletes cannot reappear through stale synchronization.
- Authentication and local credentials are protected.
- All production traffic uses HTTPS.
- WorkManager retries transient failures safely.
- The app has been tested on the actual farm devices and network conditions.
- A signed release artifact and rollback process exist.

## 18. Instructions for Claude

When implementing this mobile application:

1. Inspect the existing Android folder and architecture before adding files.
2. Reuse existing models, API conventions, and design patterns where possible.
3. Preserve the web frontend and current backend behavior unless a migration is
   documented.
4. Implement the sync protocol before building broad offline screens.
5. Make every queued operation durable and idempotent.
6. Add tests before expanding to more entities.
7. Never put secrets in source code or the APK.
8. Test process termination and network loss, not only the happy path.
9. Report changed files, migration requirements, test commands, and residual
   risks.
10. Do not claim offline production readiness until the acceptance test passes.

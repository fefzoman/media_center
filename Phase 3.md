# Phase 3 — Torrent Discovery, Prowlarr Configuration Sync, and Release Selection

## Goal

Add automatic torrent-source discovery for catalog movies and make Prowlarr indexer configuration reproducible.

This phase must support **both** ways of managing indexers:

```text
Git/YAML
   ↓
config/indexers.yaml

AND

Prowlarr Web UI
   ↓
http://SERVER:9696
```

Neither workflow should be removed.

The system must provide synchronization between:

```text
config/indexers.yaml
        ⇅
Prowlarr runtime configuration
        ⇅
Prowlarr Web UI
```

The user must be able to:

```text
edit YAML → sync → see changes in Prowlarr UI

or

edit Prowlarr UI → sync → see changes in YAML
```

The system must detect conflicts rather than silently overwriting simultaneous changes.

For playback, the finished flow becomes:

```text
Movie
  ↓
search configured indexers
  ↓
collect normalized torrent candidates
  ↓
rank/select candidate
  ↓
obtain magnet/torrent URL
  ↓
TorrentBackend
  ↓
TorrServer
  ↓
playback
```

Use indexers and media sources only where the operator is authorized to access the content.

---

# 1. Architecture

```text
                           Git repository

                       config/indexers.yaml
                               │
                               │
                               ▼
                    Indexer Configuration
                         Reconciler
                         ⇅       ⇅
                    YAML         Prowlarr API
                                   │
                                   ▼
                          Prowlarr Runtime
                                   │
                                   ▼
                            Prowlarr Web UI


                              FastAPI
                                 │
                                 ▼
                         PlaybackService
                         /             \
                        /               \
                       ▼                 ▼
               IndexerProvider      TorrentBackend
                       │                 │
                       ▼                 ▼
                   Prowlarr          TorrServer
                       │                 │
                       ▼                 ▼
                  indexers        BitTorrent peers
                       │
                       ▼
                ReleaseCandidate[]
                       │
                       ▼
                 ReleaseSelector
                       │
                       ▼
                selected release
```

Responsibilities remain separated:

```text
Prowlarr
    discovery/indexer runtime

Torznab
    standardized torrent-search protocol

IndexerConfigReconciler
    YAML ↔ Prowlarr synchronization

IndexerProvider
    application search abstraction

ReleaseSelector
    release selection policy

TorrentBackend
    torrent streaming abstraction

TorrServer
    torrent pieces/cache/HTTP streaming
```

Prowlarr currently supports configuring indexers through its UI and supports built-in, Generic Torznab, and custom YAML/Cardigann definitions.

---

# 2. Configuration Model

Add:

```text
config/
├── indexers.yaml
└── release-policy.yaml
```

`indexers.yaml` contains the desired indexer configuration.

`release-policy.yaml` contains candidate-selection rules.

Secrets must not be stored directly in either file.

---

# 3. indexers.yaml

Example:

```yaml
version: 1

sync:
  mode: bidirectional

  conflict_policy: fail

  delete_unmanaged: false

  drift_check_seconds: 60

indexers:

  - id: public_movies

    name: Public Movies

    enabled: true

    provider: torznab

    url: https://example.invalid/api

    priority: 20

    capabilities:
      movies: true
      tv: false

    settings:
      api_key: env:PUBLIC_MOVIES_API_KEY

    tags:
      - movies


  - id: private_media

    name: Private Media

    enabled: true

    provider: prowlarr_builtin

    implementation: ExampleTracker

    priority: 10

    settings:
      username: env:PRIVATE_TRACKER_USERNAME
      password: env:PRIVATE_TRACKER_PASSWORD

    tags:
      - movies
      - private
```

`id` is a Media Center stable identifier.

Do not use the Prowlarr database ID as the permanent identifier because Prowlarr IDs may change after rebuilding Prowlarr.

---

# 4. Secrets

Secrets must be referenced, not stored.

Example:

```yaml
settings:
  api_key: env:PUBLIC_MOVIES_API_KEY
```

Actual value:

```env
PUBLIC_MOVIES_API_KEY=...
```

`.env` must remain ignored by Git.

`.env.example` may contain:

```env
PUBLIC_MOVIES_API_KEY=
PRIVATE_TRACKER_USERNAME=
PRIVATE_TRACKER_PASSWORD=
```

Never serialize secret values obtained from Prowlarr into YAML.

---

# 5. Two-Way Synchronization

Implement:

```text
IndexerConfigReconciler
```

under:

```text
backend/src/media_center/indexer_config/
```

Suggested structure:

```text
indexer_config/
├── models.py
├── loader.py
├── secrets.py
├── diff.py
├── reconciler.py
├── exporter.py
└── cli.py
```

The reconciler communicates with Prowlarr through its HTTP API.

Prowlarr exposes API operations for listing, creating, updating, deleting, testing and retrieving indexer schemas.

---

# 6. Supported Synchronization Operations

Provide four distinct operations.

## Plan

```bash
make plan-indexers
```

or:

```bash
media-center indexers plan
```

Compare:

```text
YAML desired state
        VS
Prowlarr current state
```

Example:

```text
Indexer synchronization plan

= KEEP    public_movies
~ UPDATE  private_media
+ CREATE  archive_movies
! DRIFT   experimental_indexer
```

Plan must never modify either YAML or Prowlarr.

---

## Push

```bash
make push-indexers
```

Equivalent:

```text
YAML
  ↓
Prowlarr
```

Actions may include:

```text
CREATE
UPDATE
ENABLE
DISABLE
```

Deletion should only occur when explicitly enabled:

```yaml
sync:
  delete_unmanaged: true
```

Default:

```yaml
delete_unmanaged: false
```

---

## Pull

```bash
make pull-indexers
```

Equivalent:

```text
Prowlarr
  ↓
YAML
```

This captures changes performed manually in the Prowlarr UI.

For example:

```text
Prowlarr UI

priority:
20 → 10

        ↓

make pull-indexers

        ↓

config/indexers.yaml

priority: 10
```

The exporter must preserve deterministic YAML ordering and formatting so Git diffs remain readable.

---

## Reconcile

```bash
make sync-indexers
```

or:

```bash
media-center indexers sync
```

This performs bidirectional reconciliation.

It must first detect whether either side changed.

Do not automatically choose a winner when both sides changed incompatibly.

---

# 7. Manual Prowlarr UI Remains Supported

The user must always be able to open:

```text
http://SERVER_IP:9696
```

and use normal Prowlarr functionality:

```text
Indexers
   ↓
Add Indexer

Indexers
   ↓
Edit Indexer

Indexers
   ↓
Test

Indexers
   ↓
Enable / Disable
```

Prowlarr officially supports adding and editing indexers through this interface.

The Media Center must not disable or replace this UI.

Instead:

```text
UI modification
      ↓
Prowlarr database
      ↓
drift detected
      ↓
pull/sync
      ↓
indexers.yaml updated
```

---

# 8. Drift Detection

Run a lightweight drift check periodically.

Example:

```yaml
sync:
  drift_check_seconds: 60
```

The drift checker does **not** automatically overwrite configuration.

It determines:

```text
IN_SYNC

YAML_AHEAD

PROWLARR_AHEAD

CONFLICT

UNMANAGED
```

Example:

```text
public_movies       IN_SYNC

private_movies      PROWLARR_AHEAD

archive_movies      YAML_AHEAD

legacy_tracker      UNMANAGED
```

Expose this information through:

```http
GET /api/v1/admin/indexers/status
```

Example:

```json
{
  "status": "drift",
  "indexers": [
    {
      "id": "private_movies",
      "state": "prowlarr_ahead"
    }
  ]
}
```

---

# 9. Conflict Handling

Default:

```yaml
sync:
  conflict_policy: fail
```

A conflict occurs when:

```text
last synchronized value:

priority = 20


YAML changed:

priority = 15


Prowlarr UI changed:

priority = 10
```

The system must not silently choose:

```text
15
```

or:

```text
10
```

Instead:

```text
CONFLICT private_movies.priority

YAML:      15
Prowlarr:  10
Previous:  20
```

Then the user chooses:

```bash
media-center indexers sync --prefer yaml
```

or:

```bash
media-center indexers sync --prefer prowlarr
```

The normal `sync` command must fail on unresolved conflicts.

---

# 10. Synchronization State

Maintain a small local synchronization-state file or database table.

Example conceptual state:

```text
IndexerSyncState

indexer_id
last_synced_hash
last_synced_at
prowlarr_runtime_id
```

Do not store secrets.

The purpose is to distinguish:

```text
YAML changed

from

Prowlarr changed

from

both changed
```

Do not use Prowlarr runtime IDs as the canonical identity.

---

# 11. UI-Created Indexers

If the user creates a completely new indexer through Prowlarr UI:

```text
Prowlarr UI
      ↓
Add Indexer
      ↓
Save
```

the drift detector reports:

```text
UNMANAGED
```

Running:

```bash
make pull-indexers
```

must create an equivalent YAML entry.

Example:

```yaml
- id: my_new_indexer

  name: My New Indexer

  enabled: true

  provider: prowlarr_builtin

  implementation: SomeIndexer

  priority: 25
```

---

# 12. Secrets During UI → YAML Pull

A special rule is required for secrets.

Suppose an indexer was created through Prowlarr UI using:

```text
API key = abcdef123456
```

The YAML exporter must NOT write:

```yaml
api_key: abcdef123456
```

Instead it should generate a secret reference:

```yaml
api_key: env:MY_NEW_INDEXER_API_KEY
```

and report:

```text
Secret mapping required:

MY_NEW_INDEXER_API_KEY
```

The currently running Prowlarr instance may continue using its existing stored credential.

However, complete reproducibility requires the user to put the secret into the runtime secret store:

```env
MY_NEW_INDEXER_API_KEY=...
```

If an existing YAML secret reference already exists, preserve it during pull.

---

# 13. Prowlarr Custom Definitions

Custom Prowlarr indexer definitions remain separate from configured indexer instances.

Use:

```text
infra/
└── prowlarr/
    └── definitions/
        └── custom/
            └── *.yml
```

Mount them read-only:

```yaml
volumes:
  - ./data/prowlarr:/config
  - ./infra/prowlarr/definitions/custom:/config/Definitions/Custom:ro
```

Prowlarr documents `/config/Definitions/Custom` as the Docker location for custom Cardigann-compatible YAML definitions.

Difference:

```text
config/indexers.yaml

    WHICH indexer instances exist
    enabled/disabled
    priority
    URL
    tags
    settings


infra/prowlarr/definitions/custom/*.yml

    HOW Prowlarr communicates
    with a custom indexer
```

Do not mix these concepts.

---

# 14. Prowlarr Runtime State

Keep:

```text
data/prowlarr/
```

persistent and Git-ignored.

Example:

```text
media-center/
├── config/
│   ├── indexers.yaml
│   └── release-policy.yaml
│
├── infra/
│   └── prowlarr/
│       └── definitions/
│
└── data/
    └── prowlarr/
```

`.gitignore`:

```gitignore
.env
data/prowlarr/
```

Prowlarr runtime state is useful for normal operation but must not be required to reconstruct the intended configuration.

The reproducible state is:

```text
Git configuration
        +
secrets
```

---

# 15. IndexerProvider

Torrent searching must remain separate from configuration synchronization.

Create:

```text
backend/src/media_center/indexers/
```

with:

```text
indexers/
├── base.py
├── models.py
└── prowlarr.py
```

Interface:

```python
class IndexerProvider:
    async def health(self) -> bool:
        ...

    async def search_movie(
        self,
        query: MovieSearch,
    ) -> list[ReleaseCandidate]:
        ...
```

Initial implementation:

```text
ProwlarrIndexerProvider
```

Do not implement direct torrent-site integrations.

---

# 16. MovieSearch

```python
class MovieSearch:
    title: str
    year: int | None
    tmdb_id: str | None
    imdb_id: str | None
```

Preferred search order:

```text
metadata ID
    ↓
title + year
    ↓
title-only fallback
```

Search capabilities vary between indexers, so unsupported query parameters must be handled gracefully.

---

# 17. ReleaseCandidate

Normalize Prowlarr responses:

```python
class ReleaseCandidate:
    id: str

    title: str
    indexer: str

    size_bytes: int | None
    seeders: int | None
    leechers: int | None

    publish_time: datetime | None

    resolution: str | None
    video_codec: str | None
    audio_codec: str | None
    hdr: str | None
    language: str | None

    magnet_uri: str | None
    download_url: str | None
```

Prowlarr-specific response models must not escape the adapter layer.

---

# 18. ReleaseSelector

Create:

```text
backend/src/media_center/releases/
├── models.py
└── selector.py
```

Flow:

```text
Prowlarr
    ↓
ReleaseCandidate[]
    ↓
ReleaseSelector
    ↓
selected ReleaseCandidate
    ↓
TorrentBackend
```

Selection policy belongs here, not inside `ProwlarrIndexerProvider`.

---

# 19. release-policy.yaml

Example:

```yaml
version: 1

availability:
  minimum_seeders: 3

quality:
  preferred_resolution: 2160p

  fallback:
    - 1080p
    - 720p

limits:
  max_size_gb: 80

compatibility:
  prefer_direct_play: true

  preferred_video_codecs:
    - hevc
    - h264

  preferred_audio_codecs:
    - aac
    - ac3
```

Keep policy separate from indexer configuration.

---

# 20. Candidate Selection

Initial deterministic policy:

```text
remove unusable candidates
          ↓
check movie/title/year match
          ↓
check availability
          ↓
check LG compatibility hints
          ↓
apply preferred quality
          ↓
consider seeders
          ↓
consider size
          ↓
select release
```

Do not introduce ML ranking.

Selection should be explainable and covered by tests.

---

# 21. Playback Integration

Before Phase 3:

```text
Movie
  ↓
stored torrent_uri
  ↓
TorrentBackend
```

After Phase 3:

```text
Movie
  ↓
existing usable MediaSource?
  │
  ├── YES
  │     ↓
  │   use source
  │
  └── NO
        ↓
   IndexerProvider
        ↓
     Prowlarr
        ↓
 ReleaseCandidate[]
        ↓
 ReleaseSelector
        ↓
 selected source
        ↓
 TorrentBackend
        ↓
 playback
```

The LG frontend must not know whether a source was:

```text
already cached in MediaSource

or

discovered moments before playback
```

---

# 22. Playback API Contract

Keep:

```http
POST /api/v1/movies/{movie_id}/play
```

stable.

Example response:

```json
{
  "session_id": "session_123",
  "mode": "direct",
  "url": "/play/session_123"
}
```

Do not expose Prowlarr mechanics to the TV client.

---

# 23. Admin API

Add:

```http
GET /api/v1/admin/indexers/status
```

Returns configuration drift status.

Optional:

```http
POST /api/v1/admin/indexers/plan
POST /api/v1/admin/indexers/push
POST /api/v1/admin/indexers/pull
POST /api/v1/admin/indexers/sync
```

CLI/Makefile commands remain the primary management interface for MVP.

These admin endpoints must not be exposed outside the trusted LAN.

---

# 24. Docker Compose

Add:

```text
prowlarr
```

to the stack.

Conceptually:

```yaml
services:

  nginx:
    ...

  backend:
    ...

  torrserver:
    ...

  prowlarr:
    ...
```

Backend communicates using:

```text
http://prowlarr:9696
```

Prowlarr UI may be exposed to the LAN:

```text
http://SERVER_IP:9696
```

but must not be publicly exposed to the Internet.

---

# 25. Environment Configuration

Extend `.env.example`:

```env
INDEXER_PROVIDER=prowlarr

PROWLARR_BASE_URL=http://prowlarr:9696
PROWLARR_API_KEY=

INDEXER_CONFIG_PATH=/config/indexers.yaml
RELEASE_POLICY_PATH=/config/release-policy.yaml
```

Indexer-specific secret variables are added as required.

---

# 26. Health

Extend:

```http
GET /api/v1/health
```

Example:

```json
{
  "status": "ok",
  "database": "ok",
  "torrserver": "ok",
  "prowlarr": "ok",
  "indexer_config": "in_sync"
}
```

Possible indexer states:

```text
in_sync
drift
conflict
error
```

Prowlarr being unavailable should not necessarily prevent playback of an already resolved `MediaSource`.

Overall service state may therefore be:

```text
degraded
```

rather than:

```text
down
```

---

# 27. Observability

Add structured events:

```text
indexer_sync_plan
indexer_sync_started
indexer_sync_completed
indexer_sync_conflict
indexer_drift_detected
indexer_created_from_yaml
indexer_updated_from_yaml
indexer_exported_to_yaml

release_search_started
release_search_completed
release_search_failed
release_selected

prowlarr_unavailable
```

Never log:

```text
passwords
cookies
API keys
authentication tokens
```

---

# 28. Tests

Unit tests must cover:

```text
YAML parsing

environment-secret resolution

YAML → Prowlarr diff

Prowlarr → YAML diff

no-change reconciliation

YAML-only change

Prowlarr-only change

two-sided conflict

UI-created indexer export

secret redaction

stable YAML serialization

Prowlarr response normalization

release filtering

release selection

timeout/error handling
```

Mock Prowlarr for unit tests.

Integration tests may use a real local Prowlarr container.

---

# 29. Manual Synchronization Acceptance Test

Test this complete workflow:

```text
1. Define indexer in indexers.yaml.

2. Run:
      make push-indexers

3. Open Prowlarr UI.

4. Verify indexer exists.

5. Change its priority manually in Prowlarr UI.

6. Run:
      make plan-indexers

7. Verify:
      PROWLARR_AHEAD

8. Run:
      make pull-indexers

9. Open indexers.yaml.

10. Verify new priority is present.

11. Modify priority again in YAML.

12. Run:
      make push-indexers

13. Refresh Prowlarr UI.

14. Verify the UI shows the YAML value.
```

This flow is mandatory.

---

# 30. Conflict Acceptance Test

Starting state:

```text
priority: 20
```

Then modify:

```text
YAML:
priority: 15
```

and manually change Prowlarr UI to:

```text
priority: 10
```

Run:

```bash
make sync-indexers
```

Expected:

```text
CONFLICT

Indexer: example
Field: priority

Previous: 20
YAML:     15
Prowlarr: 10
```

No state must be modified.

Explicit resolution:

```bash
media-center indexers sync --prefer yaml
```

or:

```bash
media-center indexers sync --prefer prowlarr
```

---

# 31. Phase Acceptance Criteria

Phase 3 is complete when:

1. Prowlarr runs in Docker Compose.
2. Prowlarr UI remains fully usable.
3. Indexers can be created manually through Prowlarr UI.
4. Indexers can be defined through `config/indexers.yaml`.
5. YAML configuration can be pushed into Prowlarr.
6. Manual Prowlarr changes can be pulled into YAML.
7. Drift is detected.
8. Simultaneous conflicting changes are detected instead of silently overwritten.
9. Secrets are never written into Git-tracked YAML.
10. Custom Prowlarr definitions can be stored in Git.
11. Backend can search configured indexers through `IndexerProvider`.
12. Search results normalize into `ReleaseCandidate`.
13. `ReleaseSelector` selects a deterministic candidate.
14. Selected source can be passed to `TorrentBackend`.
15. `POST /api/v1/movies/{movie_id}/play` remains unchanged from the TV client's perspective.
16. Adding/removing an indexer does not require modifying Media Center application code.

Expected configuration workflow:

```text
          Git/YAML
             ⇅
      Config Reconciler
             ⇅
          Prowlarr
             ⇅
        Prowlarr UI
```

Expected playback workflow:

```text
Movie
  ↓
Prowlarr
  ↓
configured indexers
  ↓
ReleaseCandidate[]
  ↓
ReleaseSelector
  ↓
TorrentBackend
  ↓
TorrServer
  ↓
LG TV
```

---

# 32. Non-Goals

Do not implement during this phase:

```text
custom scraping logic in FastAPI
browser automation against torrent sites
machine-learning release ranking
public Internet access to Prowlarr
automatic Git commits
automatic Git pushes
automatic conflict resolution
multiple Prowlarr clusters
```

In particular:

```text
Prowlarr UI edit
```

may update the working YAML file through an explicit pull/sync operation, but the application must **not automatically commit or push that file to Git**.

Git operations remain under user control.

---

# 33. Codex Task

```text
Implement Phase 3 — Torrent Discovery, Prowlarr Configuration Sync,
and Release Selection from IMPLEMENTATION_PLAN.md.

Prowlarr configuration must support both workflows:

1. declarative configuration through config/indexers.yaml
2. manual configuration through the Prowlarr Web UI

Implement bidirectional synchronization between them.

Add an IndexerConfigReconciler with:

- plan
- push
- pull
- sync
- drift detection
- conflict detection

Do not silently resolve conflicts.

Support explicit:

    --prefer yaml

and:

    --prefer prowlarr

resolution.

Never export secrets from Prowlarr into Git-tracked YAML.

Existing YAML secret references such as:

    env:MY_INDEXER_API_KEY

must be preserved.

For indexers created manually through the Prowlarr UI, generate environment
variable placeholders for secret fields when exporting them to YAML.

Keep Prowlarr runtime configuration persistent under data/prowlarr and
Git-ignore that directory.

Keep custom Prowlarr Cardigann definitions under:

    infra/prowlarr/definitions/custom/

Implement IndexerProvider independently from the configuration reconciler.

Implement ProwlarrIndexerProvider as the first search provider.

Normalize Prowlarr search results into application-owned ReleaseCandidate
models.

Implement ReleaseSelector separately from ProwlarrIndexerProvider.

Integrate discovery into:

    POST /api/v1/movies/{movie_id}/play

without changing the TV-facing API contract.

Add Makefile commands:

    make plan-indexers
    make push-indexers
    make pull-indexers
    make sync-indexers

Add tests covering:

- YAML parsing
- secret references
- Prowlarr API normalization
- YAML -> Prowlarr changes
- Prowlarr -> YAML changes
- drift detection
- conflict detection
- UI-created indexer export
- secret redaction
- deterministic YAML serialization
- release selection
- errors and timeouts

Run linting and all tests.

At completion report:

1. files changed
2. synchronization architecture
3. configuration schema
4. Prowlarr API operations used
5. commands for YAML -> UI synchronization
6. commands for UI -> YAML synchronization
7. conflict behavior
8. test results
9. limitations before Phase 4
```

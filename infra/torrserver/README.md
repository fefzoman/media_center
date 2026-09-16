# TorrServer-LT-gst — Phase 1

This directory reserves the integration boundary. Phase 0 deliberately runs
only nginx and the backend; it does not substitute a different torrent engine
or claim that TorrServer is healthy.

Before adding a service, verify the upstream image/build, API, supported
architectures and exact configuration format. Configure `UseDisk=false` and
approximately 1024 MB RAM cache, then verify the effective engine settings.
`TORRENT_*` variables are currently application configuration placeholders.

Keep the engine API internal, route all calls through `media_center.torrents`,
use explicit timeouts, and document any host/peer networking requirement.
Do not add persistent movie storage. Test with an authorized video torrent.

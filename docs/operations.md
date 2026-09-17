# Operations

The target is Debian 13 on the Dell, connected by Ethernet with a DHCP
reservation. The initial service is for a trusted home LAN with no authentication.
Do not configure public router port forwarding.

## Start and stop

1. Copy `.env.example` to `.env` if it does not exist.
2. Set `TV_BASE_URL` to the Dell's LAN origin, including a non-default port.
3. Run `docker compose up --build -d --wait` (or `make up`).
4. Run `make smoke BASE_URL=http://localhost` with the configured port.
5. Open `/tv/` from a desktop, then from the LG browser.

`docker compose ps` shows container state, `docker compose logs -f` shows
stdout/stderr logs, and `docker compose down` stops the stack without deleting
the named data volume. Containers currently use Compose's default restart
behavior; unattended recovery and log rotation are Phase 7 hardening tasks.

## Configuration

| Variable | Default | Behavior |
| --- | --- | --- |
| `HTTP_BIND_ADDRESS` | `0.0.0.0` | Host interface nginx binds to |
| `HTTP_PORT` | `80` | Published nginx port |
| `MEDIA_CENTER_HOST` | `0.0.0.0` | Backend listener; keep reachable by nginx |
| `MEDIA_CENTER_PORT` | `8000` | Backend listener, health probe and nginx upstream |
| `TORRSERVER_BASE_URL` | `http://torrserver:8090` | Internal engine origin |
| `TORRSERVER_VERSION` | `MatriX.142.LT-1.1.8` | Checksum-pinned engine release |
| `TORRSERVER_REQUEST_TIMEOUT_SECONDS` | `10` | Engine HTTP request timeout |
| `TORRSERVER_METADATA_TIMEOUT_SECONDS` | `120` | Metadata polling deadline |
| `TORRSERVER_POLL_INTERVAL_SECONDS` | `1` | Metadata polling interval |
| `TORRENT_PEER_PORT` | `32000` | Published TCP/UDP peer port |
| `TORRENT_CACHE_MB` | `1024` | Engine RAM cache size, applied at startup |
| `TORRENT_USE_DISK` | `false` | Engine movie-cache mode; keep false for RAM only |
| `ENABLE_DEBUG_ENDPOINT` | `true` | Enables the Phase 1 developer resolver |
| `DATABASE_URL` | `sqlite:////data/media-center.db` | Reserved absolute container path |
| `TV_BASE_URL` | `http://192.168.1.50` | Reserved public origin |
| `DEFAULT_CLIENT_ID` | `lg-living-room` | Reserved client identifier |

Compose reads `.env` for interpolation. Local `make dev` reads exported process
environment only. `.env` is ignored by Git. Do not put secrets in frontend files.
The `media-data` volume is mounted for future metadata persistence. The
`torrserver-config` volume stores engine settings only. Movie data stays in RAM
when `TORRENT_USE_DISK=false`.

## Troubleshooting

- Port conflict: change `HTTP_PORT` and rerun `make up`.
- Invalid configuration: inspect backend logs and correct `.env`.
- Backend unhealthy: `docker compose logs backend`; the health probe has a
  three-second HTTP timeout and uses the configured internal port.
- TorrServer initialization fails: inspect `docker compose logs torrserver
  torrserver-init`. Startup deliberately stops if GStreamer is absent or the
  required cache settings cannot be verified.
- Magnet metadata times out: retry with a healthy authorized torrent or valid
  trackers. A magnet needs reachable peers before it contains a file list.
- Stream is unavailable: confirm peer or web-seed availability and that TCP/UDP
  `TORRENT_PEER_PORT` is allowed by the Dell firewall/router.
- Proxy configuration: `docker compose exec nginx nginx -t`.
- TV cannot connect: check the Dell LAN IP, published interface/port and host
  firewall. The backend's port 8000 is intentionally not published.
- Connection check fails: the TV page displays a retry action after five seconds.

## Verify the engine settings

After startup, this internal check should report the configured byte count,
`UseDisk: false`, and `GStreamerBuiltIn: true`:

```sh
docker compose exec -T backend python - <<'PY'
import httpx
settings = httpx.post(
    "http://torrserver:8090/settings", json={"action": "get"}, timeout=10
).json()
gst = httpx.get("http://torrserver:8090/gst/settings", timeout=10).json()
print({
    "CacheSize": settings["CacheSize"],
    "UseDisk": settings["UseDisk"],
    "GStreamerBuiltIn": gst["built_in"],
})
PY
```

The administrative port 8090 is intentionally not published. Use the public
health and debug APIs through nginx for routine checks.

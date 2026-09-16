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

| Variable | Default | Phase 0 behavior |
| --- | --- | --- |
| `HTTP_BIND_ADDRESS` | `0.0.0.0` | Host interface nginx binds to |
| `HTTP_PORT` | `80` | Published nginx port |
| `MEDIA_CENTER_HOST` | `0.0.0.0` | Backend listener; keep reachable by nginx |
| `MEDIA_CENTER_PORT` | `8000` | Backend listener, health probe and nginx upstream |
| `TORRSERVER_BASE_URL` | `http://torrserver:8090` | Reserved for Phase 1 |
| `TORRENT_CACHE_MB` | `1024` | Validated positive integer; reserved for Phase 1 |
| `TORRENT_USE_DISK` | `false` | Validated boolean; reserved for Phase 1 |
| `DATABASE_URL` | `sqlite:////data/media-center.db` | Reserved absolute container path |
| `TV_BASE_URL` | `http://192.168.1.50` | Reserved public origin |
| `DEFAULT_CLIENT_ID` | `lg-living-room` | Reserved client identifier |

Compose reads `.env` for interpolation. Local `make dev` reads exported process
environment only. `.env` is ignored by Git. Do not put secrets in frontend files.
The `media-data` volume is mounted for future metadata persistence; Phase 0
creates no database and therefore has no application data to back up yet.

## Troubleshooting

- Port conflict: change `HTTP_PORT` and rerun `make up`.
- Invalid configuration: inspect backend logs and correct `.env`.
- Backend unhealthy: `docker compose logs backend`; the health probe has a
  three-second HTTP timeout and uses the configured internal port.
- Proxy configuration: `docker compose exec nginx nginx -t`.
- TV cannot connect: check the Dell LAN IP, published interface/port and host
  firewall. The backend's port 8000 is intentionally not published.
- Connection check fails: the TV page displays a retry action after five seconds.

## Phase 1 prerequisites

Verify a maintained TorrServer-LT-gst image/build for the Dell's amd64 platform,
its exact API, RAM cache settings, and any peer networking requirements. Add
the service without publishing its administrative API to the LAN. Validate
progressive playback using an authorized, healthy test torrent. No test media
or torrent source is included in the bootstrap.

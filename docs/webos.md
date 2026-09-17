# LG webOS validation

Develop in a desktop browser first, then open `http://DELL_LAN_IP/tv/` in
the LG built-in browser. The current frontend provides a connection check with a visible
focus outline; Enter activates the focused button. Full remote navigation,
catalog and playback are later phases.

Record TV model, webOS/browser version, date and observations when testing.
Phase 1 streaming has been validated in a desktop client. Actual TV playback
still needs validation on the target LG model.

Browser playback must work before implementing the Phase 6 launcher/IPK.
The planned launcher loads the Dell-hosted UI; if the TV restricts hosted
applications, package the same frontend locally and keep the APIs on the Dell.

Future playback compatibility matrix (all untested):

| Video | Container | Audio | Direct | HLS | Notes |
| --- | --- | --- | --- | --- | --- |
| H.264 | MP4 | AAC | — | — | Test actual TV |
| H.264 | MKV | AC3 | — | — | Test actual TV |
| HEVC | MKV | AAC | — | — | Test actual TV |
| HEVC | MKV | EAC3 | — | — | Test actual TV |
| HEVC | MKV | DTS | — | — | Test actual TV |

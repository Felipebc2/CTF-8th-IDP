# Nomes

- **Category:** NET
- **Points:** 184 (final dynamic value)
- **Description:** "Say my name."
- **Access:** `nomes.<DOMAIN>` (no A record at the browser resolver: `DNS_PROBE_POSSIBLE`)
- **Status:** ✅ solved
- **Flag:** `IDP{n0m3_s0br3n0m3_3_c0rr31o}`

## Solve path

1. `dig nomes.<DOMAIN> TXT` → `"IDP{n0m3_ - you actin kinda shady, aint mailin me baby"` (part 1 + hint to MX)
2. `dig nomes.<DOMAIN> MX` → `10 sobrenome.<DOMAIN>.`
3. `dig sobrenome.<DOMAIN> TXT` → `"s0br3n0m3_3_c0rr31o}"` (part 2)

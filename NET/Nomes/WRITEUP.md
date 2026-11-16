<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=Nomes" alt="Typing SVG" /></a>

</div>

# Nomes — NET · 🟢 EASY

- **Status:** ✅ SOLVED — flag split across two DNS records, chained by an MX record
- **Points:** 184 (final dynamic value)
- **Flag:** `IDP{n0m3_s0br3n0m3_3_c0rr31o}`
- **Target:** `nomes.<DOMAIN>`
- **Prompt:** *"Say my name."*

---

## TL;DR

1. `nomes.<DOMAIN>` has no A/AAAA record, so the browser fails with `DNS_PROBE_POSSIBLE`. The challenge lives in DNS, not on a web server.
2. Its TXT record holds the first half of the flag plus a hint about mail. Its MX record points to `sobrenome.<DOMAIN>`.
3. The TXT record of `sobrenome` holds the second half. Nome + sobrenome + correio (name + surname + mail).

## Analysis

### The site that doesn't exist

Opening `http://nomes.<DOMAIN>/` in a browser gives *"This site can't be reached — DNS address could not be found"*. DevTools shows the request never gets a response. The `data:image/png` entries next to it are just Chrome's own error-page assets (the sad-document icon and the offline dinosaur sprites), not something served by the challenge.

The title "Nomes" ("names") and the prompt "Say my name." point at the Domain *Name* System, so the next step is to ask DNS for every record type instead of only A.

### Record enumeration

```bash
for t in A AAAA TXT CNAME MX SOA SRV HINFO ANY; do
  echo "== $t"
  dig nomes.<DOMAIN> $t +noall +answer +authority +comments | grep -E 'status:|IN'
done
```

Every query returns `NOERROR`, so the name exists. A, AAAA, CNAME, SRV and HINFO only return the zone SOA (empty answer). Two record types have data:

```
nomes.<DOMAIN>.  3600  IN  TXT  "IDP{n0m3_ - you actin kinda shady, aint mailin me baby"
nomes.<DOMAIN>.  3600  IN  MX   10 sobrenome.<DOMAIN>.
```

The TXT record gives the start of the flag, `IDP{n0m3_` ("nome", i.e. name), followed by a hint: *"aint mailin me baby"*. Mail in DNS means MX, and the MX record points to the next name, `sobrenome` ("surname").

### Following the mail exchanger

```bash
for t in A AAAA TXT CNAME MX SOA SRV HINFO CAA NS ANY; do
  echo "== $t"
  dig sobrenome.<DOMAIN> $t +noall +answer +comments | grep -E 'status:|IN'
done
```

Only the TXT record has data:

```
sobrenome.<DOMAIN>.  3600  IN  TXT  "s0br3n0m3_3_c0rr31o}"
```

This part ends with `}`, so the chain is complete:

```
IDP{n0m3_ + s0br3n0m3_3_c0rr31o} = IDP{n0m3_s0br3n0m3_3_c0rr31o}
```

The flag reads "nome, sobrenome e correio" ("name, surname and mail"), which is exactly the path: the TXT of `nomes`, the MX (mail), then the TXT of `sobrenome`.

## What didn't work

| Hypothesis | Result | Why |
|---|---|---|
| HTTP service behind the hostname | ✗ | No A/AAAA record, so there is nothing to connect to |
| Flag in A/AAAA/CNAME/SRV/HINFO/CAA/NS | ✗ | All return an empty answer with the zone SOA in the authority section |
| Data hidden in the SOA (rname/serial) | ✗ | The SOA is the registrar's default (`dns.jomax.net`, date-based serial) |

## Conclusion

The challenge is a short DNS record chain. The "unreachable" site is the hint: query the name for every record type, read the TXT, follow the MX to the next name, and read its TXT. Nothing beyond standard `dig` queries against public resolvers was needed.

---

## Appendix — tools

- `dig` — the two enumeration loops above are the whole solve.

<!--
  Real credentials (session cookie, emails) and infra hostnames anonymized as <...>.
  Challenge-derived values (the flag) stay.
-->
<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=Correio" alt="Typing SVG" /></a>

</div>

# Correio — OSINT · 🟡 MEDIUM

- **Status:** ✅ SOLVED — the flag was a base64 string inside an **old, unopened e-mail** from the organizers.
- **Points:** 259 (final dynamic value)
- **Flag:** `IDP{eu_nA0_t1nh4_ab3rt0_esse_EM41L_ANT3S}`
- **Target:** none downloadable — platform challenge, text only
- **Prompt:** *"Nunca decorei meu CEP."* ("I never memorized my postal code.")

---

## TL;DR

1. `Correio` is one of **six OSINT challenges** that form a single trail over the event's online presence. The title and prompt are deliberate misdirection.
2. **`Correio` means e-mail** (correio eletrônico), **not** the postal service — and `Nunca decorei meu CEP` is pure flavor to push you toward postal codes. The real action is: *read your mail*.
3. An **older e-mail** from the organizers (one you likely never opened) contained a **base64** blob. Decoding it gives the flag — whose text literally reads *"eu não tinha aberto esse e-mail antes"*.

## Analysis

### The challenge is literally the prompt

The platform is **CTFd** (custom theme `idp`, `dynamic_challenges` plugin). The challenge, straight from the API, has no file / hint / `connection_info` — the whole payload is the title `Correio` and the line `Nunca decorei meu CEP.`:

```bash
COOKIE='session=<SESSION_COOKIE>'; BASE='https://<CTF_HOST>'
curl -s -H "Cookie: $COOKIE" "$BASE/api/v1/challenges/28" | python3 -m json.tool
# description: "Nunca decorei meu CEP."  files: []  hints: []  connection_info: ""
```

Nothing is hidden in the card — it is a pure OSINT riddle.

### Decoding the misdirection

Two layers of misdirection, both confirmed by teammates and by the final flag:

- **Title `Correio`** → you think *Correios* (postal service). Wrong. `Correio` = **e-mail**.
- **Prompt `Nunca decorei meu CEP`** → you think *postal code / address lookup*. Pure flavor; the CEP never mattered.

The real pointer is just *"go check your mail."* The intended e-mail is **not** the obvious "É HOJE!" launch blast — it is an **older message** from the organizers that most people never opened. The flag's plaintext spells this out: `eu_nA0_t1nh4_ab3rt0_esse_EM41L_ANT3S` = *"I hadn't opened this e-mail before."*

### The flag

The e-mail body carried a base64 string. `SURQe...` is the base64 prefix of `IDP{`:

```bash
echo 'SURQe2V1X25BMF90MW5oNF9hYjNydDBfZXNzZV9FTTQxTF9BTlQzU30=' | base64 -d
# IDP{eu_nA0_t1nh4_ab3rt0_esse_EM41L_ANT3S}
```

### The OSINT series (context)

`Correio` is the last of six OSINT challenges, each a first-person line pointing at **one channel** of the event's online presence, with the flag planted there:

| ID | Name | Prompt | Channel |
|---|---|---|---|
| 24 | Bem-vindo | *"...ler as regras..."* | event rules document |
| 25 | Propaganda | *"Por onde você ficou sabendo do evento?"* | the announcement post |
| 26 | Grupo | *"Já que eu estou aqui."* | WhatsApp group (incl. `audio.mp3`) |
| 27 | Newsletter | *"Toda semana tem novidades."* | a message carrying a hex string |
| 30 | Apresentação | *"Todo ano tem né."* | annual presentation |
| **28** | **Correio** | ***"Nunca decorei meu CEP."*** | **an old organizer e-mail (base64 in the body)** |

Each flag is a leetspeak phrase echoing its own prompt.

## What didn't work

The title/prompt misdirection sent the investigation down a long series of dead ends before the e-mail angle was confirmed:

| Hypothesis | Result | Why |
|---|---|---|
| Literal postal CEP / Correios lookup | ✗ | CEP was a red herring; `Correio` ≠ postal |
| The obvious "É HOJE!" HubSpot launch e-mail (text/headers/HTML/images/stego) | ✗ | Legitimate marketing blast, 100% clean — wrong e-mail |
| The two banner images in that e-mail | ✗ | Event branding only; clean EXIF/strings/`zsteg`/`binwalk` |
| Hidden content in the challenge card HTML / CTFd metadata | ✗ | API: empty `files`/`hints`/`connection_info` |
| Instagram bio / Linktree (`@idpgraduacao`) | ✗ | IDP marketing links only |
| `Campus` highlight → Google Maps reviews / Q&A / photos | ✗ | Nothing on the IDP Asa Sul listing |
| CTFd e-mail flow / notifications | ✗ | No outgoing mail wired; 2 unrelated broadcasts |
| Exact phrase on open web / TikTok / YouTube | ✗ | Generic phrase, no event-linked result |

**Key lesson:** the first-person flavor text was a trap. `Correio` plainly means "e-mail", and the right one was an **old, unread** message — not the loud launch announcement everyone saw.

## Conclusion

`Correio` = e-mail; `Nunca decorei meu CEP` = flavor. The flag was a **base64 blob in an older organizer e-mail** the solver had never opened. Decode → `IDP{eu_nA0_t1nh4_ab3rt0_esse_EM41L_ANT3S}`.

---

## Appendix — commands

```bash
# decode the flag found in the e-mail body
echo 'SURQe2V1X25BMF90MW5oNF9hYjNydDBfZXNzZV9FTTQxTF9BTlQzU30=' | base64 -d ; echo

# a flag begins with IDP{ → hex 4944507b / base64 SURQ — search any artifact for an encoded flag
grep -raoiE "4944507b[0-9a-f]+|SURQ[A-Za-z0-9+/=]+" ~/Downloads/
```

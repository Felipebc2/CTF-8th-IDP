<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=My+Little+Plone" alt="Typing SVG" /></a>

</div>

# My Little Plone — WEB · 🔴 HARD

- **Status:** ❌ UNSOLVED — flag not captured, by us or by any other team (the only challenge with 0 solves at the end). An **anonymous TALES-injection primitive is confirmed** on the CMFEditions `portal_modifier` subsystem (store + read-back a `python:` expression with no session). The chain stops **one hop short of RCE**: the restricted-Python sandbox escape (reaching a callable in `os`/`subprocess`) was not completed before the container's short TTL.
- **Points:** 500 (final value; no team solved it)
- **Flag:** `IDP{...}` (not captured)
- **Target:** `<HOST>:<PORT>` (ephemeral container, ~20 min TTL; port rotates every respawn)
- **Prompt:** *"n-day sem público, o melhor que tem pra aprender."*

---

## TL;DR

1. Target is a **Plone 6 Classic UI** site (Zope / Waitress, Barceloneta theme, dressed as the fictional news portal *"equestria agora"*).
2. The prompt — *"n-day sem público"* — points straight at **Plone Security Hotfix 20261110**, released **2026-11-11**, three days before the CTF, with **no public PoC**. It is an unauthenticated RCE chain through the CMFEditions `portal_modifier` tool. This is the intended bug, not the authenticated portlet CVE (CVE-2026-57149) that recon first chased.
3. The front half of that chain is **confirmed live**: anonymous store + evaluated read-back of an arbitrary `python:` TALES expression (`python:42` → `42`). The back half — escaping restricted Python to run a shell command — was not completed: you can *reach* the `os` module object, but `os.popen` is blocked by `guarded_getattr`. The escape needs a directly-imported **callable**, and enumerating one from the exact build ran out against the container TTL.

## Analysis

### Fingerprinting
- `Server: waitress`, `X-Powered-By: Zope (www.zope.dev), Python (www.python.org)`.
- Footer: *"Powered by Plone — CMS/WCM ... 2000-2026 Fundação Plone"*. Classic UI (Barceloneta), not Volto.
- `/author/admin` exists → confirms an `admin` user and lists its published content.
- Exact version did not leak: `/@@plone-version`, `/CMFPlone/version.txt`, the static bundle path and `/zope.conf` all returned `{"error_type": "NotFound"}` / 404.
- `robots.txt` is the stock Plone boilerplate — nothing planted.
- Behaviour of `portal_modifier` (see below) matches the **pre-6.1.6 / unpatched CMFEditions** line: the anonymous `edit` method is still reachable, which a patched instance would gate.

### The intended vulnerability — Plone Security Hotfix 20261110 (anonymous RCE)
Released 2026-11-11 by the Plone/Zope security team. It is a **chain of five flaws** that together let an anonymous visitor run code on the server. Two matter here:

1. **`Products.CMFEditions` — missing security declarations on the conditional modifier classes.** `ConditionalModifier.edit` / `ConditionalTalesModifier.edit` (in `Products/CMFEditions/Modifiers.py`) carry no permission check, so an **anonymous** caller can set a modifier's TALES `condition`. `ConditionalTalesModifier.edit` compiles the attacker string with `Expression(condition)`; it is evaluated later in `isApplicable` (and also whenever an editor saves versioned content). That is an unauthenticated, stored, *read-back* expression-evaluation primitive.

2. **Overly broad `allow_module` declarations — the sandbox escape.** TALES/RestrictedPython should only see names a package explicitly declares public. Four core packages instead opened **whole modules** with `allow_module`, which publishes *every name in the module, including everything it imported*:

   | Package (core — always installed) | `allow_module(...)` |
   |---|---|
   | `Products.CMFPlone` | `Products.CMFPlone.utils`, `Products.CMFPlone.browser.navtree`, `OFS.ObjectManager` |
   | `Products.MimetypesRegistry` | `Products.MimetypesRegistry.common` |
   | `plone.batching` | `plone.batching` |
   | `plone.restapi` | `json` (stdlib) |

   Because those modules `import os` (etc.) at top level, the imported `os` is reachable from inside the restricted expression — the sandbox boundary leaks through the import graph.

**Fixed package set (Plone 6.1):** CMFPlone 6.1.6, CMFEditions 4.0.7, MimetypesRegistry 3.0.2, plone.batching 2.0.8, plone.restapi 9.15.8. The fix replaces each blanket `allow_module` with a narrow `ModuleSecurityInfo(...).declarePublic(...)`, and decorates the modifier `edit` with `@security.protected(ManagePortal)`.

References:
- Ostorlab deep-dive — https://blog.ostorlab.co/plone-unauthenticated-rce-hotfix-20261110.html
- oss-sec announcement — https://seclists.org/oss-sec/2026/q4/650
- Plone community advisory — https://community.plone.org/t/plone-security-hotfix-20261110/23313
- CMFEditions GHSA — https://github.com/plone/Products.CMFEditions/security/advisories/GHSA-67qm-q795-jh7h

### The confirmed primitive — anonymous `portal_modifier` TALES store + read-back
Live testing confirmed the front half of the chain. A conditional TALES modifier under `portal_modifier` exposes its `edit` method with no auth check, so an anonymous caller can **store** a TALES condition and **read its evaluated result** through the public `isApplicable` view.

- **Store (write).** The write has to go over **XML-RPC**, not plain HTTP: a plain HTTP `POST` makes Zope render the protected edit *form* and roll the transaction back, so the condition is never persisted. Over XML-RPC with `REQUEST=None` the method commits:

  ```
  POST /portal_modifier/SkipParentPointers   (Content-Type: text/xml)
  methodName = edit
  params     = (True, "python:<TALES>", "ctf", None)
  ```

- **Trigger / read-back.** `isApplicable` is public and returns the evaluated value:

  ```
  GET /portal_modifier/SkipParentPointers/isApplicable?obj=x
  ```

- **Confirmed:** `python:42` → `42` (round-trip).
- **Gotcha worth recording:** the condition is parsed as a TALES expression, so it **must** carry the `python:` prefix — a bare expression makes Zope's `Expression()` raise `CompilerError`.

That is a genuine unauthenticated expression-evaluation primitive. What it is **not**, yet, is RCE.

### The wall — reaching `os` is not the same as calling `os.popen`
This is where the attempt and the naive payload (`python:modules['os'].popen('cat /flag*').read()`) diverge — and why that payload cannot work as written:

- `os`, `sys`, `subprocess`, `shutil` are **not public by default** in Zope's restricted sandbox (baseline, not special hardening), so `modules['os']` is denied — `302 Unauthorized`.
- The escape is *indirect*: an `allow_module`-opened module M is fully public, so `M.<anything>` is readable. If M did `import os`, then `M.os` hands you the **`os` module object** — and that part works (observed: `OFS.ObjectManager.os`, `Products.CMFPlone.utils.sys`, etc. all return the module).
- But `os` itself was never made public. Reading `os.popen` off that object goes through `guarded_getattr(os, 'popen')` → `popen` has no security declaration → **`302 Unauthorized`**. Holding the module ≠ calling its guarded attributes.

So the real missing piece is **not** "which package re-enables `os`" (the four above already expose the import graph). It is: **find a directly-bound dangerous callable sitting in a public namespace** — i.e. a module in the exposed set (or in *its* transitively-imported, now-public modules) that did `from os import system` / `from subprocess import check_output` / `from os import popen` rather than `import os`. A `from … import <callable>` binding is a name *in that module's namespace*, so it is public via `allow_module` and directly callable, with no second `guarded_getattr`. That is precisely the piece the advisory and the Ostorlab write-up deliberately **do not publish** (vendor held the request sequence back).

The way to find it is **source enumeration, offline** — not blind guessing against the live box: walk the imports of `Products.CMFPlone.utils`, `Products.CMFPlone.browser.navtree`, `OFS.ObjectManager`, `Products.MimetypesRegistry.common`, `plone.batching` (and their transitive imports) for the exact 6.1.x pins, and grep for a `from {os,subprocess,shutil,posix,popen2,commands} import …` that lands a callable in a public namespace. Then the payload becomes `python:modules['<that.module>'].<that_callable>('…')`, driven through the same XML-RPC `edit` + `isApplicable` round-trip. This step was not finished before the TTL expired.

### Authenticated fallback — CVE-2026-57149 (portlet TALES)
A *separate*, independently-tracked CVE, initially recon's lead before the hotfix chain was identified as the intended bug.

- Affected: `plone.app.portlets` 5.0.0–5.0.7, 6.0.0–6.0.3, 7.0.0–7.0.1 (fixed 5.0.8 / 6.0.4 / 7.0.2).
- **Sink:** the Classic portlet evaluates `context/<Template>` (optionally `…/macros/<Macro>`) as a raw TALES *path* expression — a clean RCE primitive, value rendered straight into the portlet HTML.
- **Reach:** filling those fields needs `plone.app.portlets: Manage portlets`, **`Manager`-only by default** — so unlike the hotfix chain it is *not* anonymous unless the instance intentionally granted `Anonymous` that permission. Confirmable with no exploit: GET `/@@manage-portlets` and the add-form `/++contextportlets++plone.rightcolumn/+/portlets.Classic` with no cookie — `200`+form = reachable unauth, `302 → login` = authenticated-only.
- References: GHSA-rr49-f9g6-c9r5 · OSV CVE-2026-57149 · fix commit `plone/plone.app.portlets@8a0641dc`.

This path needs a session. None was obtained: weak admin passwords (`admin`, `admin123`, `password`, `plone`, `changeme`, `secret`) all returned *"Falha no acesso"*; `/@@register` 302s to `/login` (self-registration disabled); `mail_password_form` only emails a reset link; no credential surfaced in the admin's public content or site search within the TTL.

## What didn't work

| Hypothesis | Result | Why |
|---|---|---|
| Weak admin credentials | ✗ | All common defaults rejected at `/login_form` |
| Open self-registration (`/@@register`) | ✗ | Redirects to `/login`; registration disabled |
| Version leak for exact range match | ✗ | All version endpoints return NotFound/404 |
| Credential planted in public content / robots | ✗ | robots is stock; admin content not fully triaged before TTL |
| CVE-2026-57149 (portlet) as the anonymous vector | ✗ | Wrong subsystem; `Manage portlets` is `Manager`-only by default — authenticated path |
| Anonymous `portal_modifier` TALES store + read-back | ✓ | Confirmed (`python:42`→`42`) via XML-RPC `edit` (`REQUEST=None`) + public `isApplicable`; needs `python:` prefix |
| `python:modules['os'].popen(...)` | ✗ | `os` is not public → `302`; and even via an exposed module, `os.popen` is blocked by `guarded_getattr` |
| Sandbox escape via exposed module paths | ◐ | `…utils.os` / `ObjectManager.os` return the **module** object, but calling a guarded attribute (`.popen`, `.system`) → `302`; `misc_/ImageFile`+`setattr` → `guarded_setattr` TypeError. Needs a *directly-imported callable*, not the bare module |

## Conclusion

The prompt's *"n-day sem público"* resolves to **Plone Hotfix 20261110**, and its anonymous front half is confirmed working against the target: an unauthenticated, stored, read-back TALES expression primitive via CMFEditions `portal_modifier`. The flag was not captured because the restricted-Python **sandbox escape was not completed** — reaching the `os` module object succeeds, but turning that into a shell command needs a directly-bound callable (`from os import …`) exposed by one of the four `allow_module` modules, and that enumeration ran out against the ~20-minute container TTL.

**To finish (highest-value first):**
1. **Complete the sandbox escape offline.** For the exact 6.1.x package pins, statically walk the imports of the exposed modules (`Products.CMFPlone.utils`, `…browser.navtree`, `OFS.ObjectManager`, `Products.MimetypesRegistry.common`, `plone.batching`) and their transitive imports, and grep for a `from <os|subprocess|shutil|posix> import <callable>` binding living in a now-public namespace. That binding is the escape; the final payload is `python:modules['<module>'].<callable>('cat /flag* 2>/dev/null')` driven through the XML-RPC `edit` + `isApplicable` round-trip. No live guessing needed to find the name.
2. **Or take the authenticated fallback** — any member credential makes CVE-2026-57149 a one-shot with no sandbox fight. Harvest usernames from the *"Expediente"* article + author listing, pair with weak passwords (one attempt each, no brute forcing per rules); triage *"Todo o conteúdo criado por admin"* and site search (`senha`, `password`, `flag`, `token`); check whether a sibling challenge leaks a reused credential.
3. **Regardless of the flag**, the confirmed anonymous **injection + read-back** primitive — and the precise reason the naive `os.popen` payload fails (`guarded_getattr`, not a missing module) — is solid, teachable write-up material.

---

## Appendix — recon

- `recon.txt` — raw fingerprint output and the (initial, portlet-CVE) attack plan.

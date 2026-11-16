<div align="center">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=700&pause=1000&color=E8423F&center=true&vCenter=true&repeat=false&width=500&height=35&lines=ESCRITA+A+MAO" alt="Typing SVG" /></a>

</div>

# Escrita à mão — WEB · 🟡 MEDIUM

- **Status:** ✅ SOLVED — RCE via OCR injection into an attacker-named `.php` file.
- **Points:** 259 (final dynamic value)
- **Flag:** `IDP{v0c3_d3s3nh0u_tuD0_oaRVvcDm7k}`
- **Target:** `<HOST>:<PORT>` (PHP/Apache, ephemeral container)
- **Prompt:** *"Pratique a sua caligrafia."* (Practice your handwriting.)

---

## TL;DR

1. A handwriting app: you draw on a canvas, the server OCRs the PNG and you can **save the recognized text to a file you name**.
2. The save endpoint lets the filename end in **`.php`**, and the file is served/executed by Apache. The OCR transcribes clean **printed** text faithfully — so instead of drawing, I render a PHP payload *as an image* and let the server "recognize" it back into **PHP source**.
3. Save that as `shell.php`, request it → code runs. `<?php phpinfo(); ?>` dumps the environment, where the flag was stored.

## Analysis

### The SPA and its API (`app.js`)

The front-end is a hash-routed SPA talking to a single backend, `api.php?acao=<acao>` (POST JSON), with three actions:

| Action | Body | Behavior |
|---|---|---|
| `reconhecer` | `{imagem: <dataURL>}` | OCRs the PNG, returns `{id: <16 hex>, texto: <ocr>}` and stores `texto` under `id` |
| `salvar` | `{id, nome}` | writes the stored `texto` to `/arquivos/<md5(session)>/<nome>`, returns its URL |
| `listar` | — | lists files in the session directory |

`nome` is fully client-controlled. The written file is then served statically by Apache under `/arquivos/<dir>/<nome>`.

### Probing the two parameters

- **`id` is validated** — any traversal (`../../etc/passwd`) returns `{"erro":"Identificador inválido."}`. No arbitrary-read via the source id.
- **`nome` is charset-restricted** — `../`, `/`, subpaths all return *"Nome de arquivo inválido. Use letras, números, ponto, hífen e sublinhado."* No path traversal. **But `.php` is accepted**: `nome=teste.php` saved fine to `/arquivos/<dir>/teste.php`. That is the whole bug — an attacker-named executable file in a web-served directory.
- `salvar`/`reconhecer` ignore any injected `texto`/`conteudo` field; **the file content is strictly the OCR output**. So to control the content of `shell.php`, I must control what the OCR reads.

### Controlling the content: OCR injection

The OCR is accurate on **clean printed** text (not just messy handwriting). Rendering text with PIL and POSTing it:

```
"HELLO 123"            -> texto = "HELLO 123"              (exact)
"<?php echo 49; ?>"    -> texto = "<?php\necho\n49;\n?>"   (exact; spaces -> newlines, valid PHP)
"<?php system($_GET[0]); ?>" -> "<?php\nsystem ( b\nGETTOD):\n?>"   (mangled)
```

The engine nails `< ? ; ( ) >`, letters and digits, but mangles `$ _ [ ] " '`. So the payload must avoid those characters — which rules out a `$_GET` webshell but **not** a self-contained one:

```php
<?php phpinfo(); ?>
```

Only letters and `();` — transcribed perfectly. `phpinfo()` dumps `$_ENV`/`$_SERVER`, and the flag was planted as an environment variable, so it appears directly in the output.

### Chain

1. `reconhecer` a rendered PNG of `<?php phpinfo(); ?>` → get `id`.
2. `salvar` `{id, nome: "shell.php"}` → file written to `/arquivos/<dir>/shell.php`.
3. `GET /arquivos/<dir>/shell.php` → PHP executes, environment dumped, flag in output.

`solve.py` automates the whole chain.

## What didn't work

| Hypothesis | Result | Why |
|---|---|---|
| `id` path traversal → arbitrary file read | ✗ | `id` validated: `"Identificador inválido."` |
| `nome` path traversal (`../`, `sub/x`) | ✗ | filename charset-restricted to `[A-Za-z0-9._-]` |
| Inject content via `texto`/`conteudo` field | ✗ | ignored; content is strictly the OCR result |
| PNG `tEXt` chunk as fake-OCR source | ✗ | real pixel OCR, metadata ignored |
| `$_GET`-based parametric webshell | ✗ | OCR mangles `$ _ [ ]`; use a self-contained payload instead |
| Large image POST | ✗ (transient) | crashed/hung the container; small grayscale PNG works |

## Conclusion

The intended bug is **unrestricted file extension on save + an OCR that transcribes printed text** = write arbitrary PHP by drawing it. The filename/id filters are decoys that only block the obvious traversal; the real primitive is content-control through the recognizer. Avoiding the OCR-hostile characters (`$ _ [ ] " '`) makes `<?php phpinfo(); ?>` the shortest reliable payload, and the flag is sitting in the environment.

> The flag itself — `v0c3_d3s3nh0u_tuD0` ("you drew everything") — confirms the intended path: you *draw* the exploit.

---

## Appendix — tools

- `solve.py` — `python3 solve.py http://<HOST>:<PORT> '<?php phpinfo(); ?>' shell.php`: renders the payload, drives `reconhecer`→`salvar`, fetches the executed `.php`, and extracts the flag. Needs `Pillow`.
- `recon/app.js` — the saved front-end that revealed the API shape.

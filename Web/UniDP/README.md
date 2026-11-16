# UniDP — WEB · 🔴 HARD

- **Status:** ✅ SOLVED
- **Points:** 259 (final dynamic value)
- **Flag:** `IDP{r3s3t_m4il_t4mp3r_K3zvMzAUhg}`
- **Target:** `<HOST>:<PORT>` (Flask + gunicorn, ephemeral)
- **Prompt:** *"Gerencie sua vida acadêmica, ou procure quem pode fazer isso junto com você."*

Flask "Portal do Aluno" whose signed cookie carries `{is_coordinator, uid}`. Weak
`SECRET_KEY='dev'` (recovered offline with `flask-unsign`) → forge sessions. The
`/coordination` route re-checks the role in the DB by `uid`, so forge
`is_coordinator:true` **and** point `uid` at the real coordinator (`uid=1`,
Profa. Linik Mayara Meireles). Her `/profile` leaks the flag in an "Informação
reservada" field.

See [`WRITEUP.md`](WRITEUP.md) · solver: [`solve.py`](solve.py).

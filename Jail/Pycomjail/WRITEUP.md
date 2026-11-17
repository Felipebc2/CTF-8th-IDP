* [ ] 

<div align="center">

# Pycomjail — JAIL

- **Status:** ✅ SOLVED — the recorded payload returned the flag; reproduced locally with a test flag.
- **Points:** 184 in the supplied event screenshot; the score at solve time is unconfirmed.
- **Flag:** `IDP{f1l3_d3scr1pt0r_na0_t3m_ord3m_m4s_tEm_2Bdf4M4BAa}`
- **Target:** dynamically provisioned service at `<HOST>:<PORT>`.
- **Original prompt:** *“Agora sim eu quero ver.”*

---

## TL;DR

1. The service opens `flag.txt` and unlinks its pathname, but keeps the file open while processing inputs.
2. The jail still permits the `open` and `print` builtins and string literals containing underscores.
3. Read the open file via `/proc/self/fd/3` to recover the flag.

## Analysis

The service prints its own [source code](main.py). Its `verifica` function parses each input as Python and rejects import statements and identifier or attribute names beginning with `_`. It also removes selected builtins, including `__import__`, `eval` and `exec`, from the environment used for executing the input. The builtins `open` and `print` remain available.

Before accepting commands, the program enters `with open('./flag.txt'):` and calls `os.unlink('./flag.txt')`. Unlinking removes the directory entry, but the open file remains accessible through its file descriptor for the lifetime of that `with` block. On the observed service, it was descriptor `3`. Linux exposes the current process's open descriptors through `/proc/self/fd/`.

The underscore check examines AST names and attributes, not the contents of string literals. The following [payload](payload.txt) therefore passes the filter and opens the still-live file through procfs:

```python
print(open('/proc/self/fd/3').read())
```

Send the line to the instance, for example:

```sh
cat payload.txt | nc <HOST> <PORT>
```

The recorded solve produced `IDP{f1l3_d3scr1pt0r_na0_t3m_ord3m_m4s_tEm_2Bdf4M4BAa}`. A local run with a disposable `flag.txt` containing `IDP{local_test}` also printed that test value after the file was unlinked. Descriptor numbers depend on what files the process already has open; `3` is the value observed here rather than a universal guarantee.

## Conclusion

Deleting a filename did not close the file, and allowing unrestricted `open` access left the descriptor reachable through procfs. The AST filter did not need to be bypassed with an import or a forbidden identifier.
